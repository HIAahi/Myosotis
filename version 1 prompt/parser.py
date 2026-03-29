"""
parser.py  —  Chinese Word → ADS JSON Pipeline
================================================
Stage 1: Extract raw text from .docx (python-docx)
Stage 2: Feed structured prompt + few-shot examples to Claude API
Stage 3: Validate JSON output, resolve suppliers, flag missing entries
"""

import re
import json
import uuid
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any

import anthropic
from docx import Document

from supplier_db import lookup_supplier
from ads_schema import ADS_JSON_SCHEMA

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
PARSER_VERSION = "1.0.0"

# IATA city code mappings (extend as needed)
IATA_TO_CITY = {
    "KMG": "Kunming", "HAK": "Haikou", "PVG": "Shanghai", "PEK": "Beijing",
    "MEL": "Melbourne", "SYD": "Sydney", "BNE": "Brisbane", "PER": "Perth",
    "CBR": "Canberra", "ADL": "Adelaide", "HKG": "Hong Kong", "SIN": "Singapore",
    "NAN": "Nadi (Fiji)", "AKL": "Auckland", "CHC": "Christchurch",
}

AIRLINE_CODES = {
    "HU": "Hainan Airlines", "CA": "Air China", "MU": "China Eastern",
    "CZ": "China Southern", "QF": "Qantas", "VA": "Virgin Australia",
    "JQ": "Jetstar", "TT": "AirAsia", "EK": "Emirates", "SQ": "Singapore Airlines",
}

# ── Few-Shot Examples for LLM ─────────────────────────────────────────────────
FEW_SHOT_EXAMPLES = """
EXAMPLE INPUT (excerpt from Chinese itinerary):
---
第一天 4.20（周一）昆明—悉尼
HU7092 KMG→SYD 23:55-次日09:10
住宿：Novotel Sydney on Darling Harbour（网评四星半）
早：各自解决   午：各自解决   晚：各自解决
---
EXPECTED OUTPUT (partial):
{
  "day_number": 1,
  "date": "20/04/2026",
  "day_title": "Departure from Kunming to Sydney",
  "hotel": "Novotel Sydney on Darling Harbour",
  "meals": {"breakfast": null, "lunch": null, "dinner": null},
  "activities": [
    {
      "time": "23:55",
      "category": "Flight",
      "description_en": "Depart Kunming (KMG) on Hainan Airlines HU7092. Overnight flight arriving Sydney next morning.",
      "description_zh": "昆明出发乘坐海南航空HU7092，次日抵达悉尼",
      "supplier_ref": null
    }
  ]
}

EXAMPLE INPUT (excerpt):
---
第三天 4.22（周三）悉尼市区观光
上午参观悉尼歌剧院，海港大桥拍照，下午前往悉尼最大海鲜市场午餐，各种海鲜应有尽有。
晚餐：唐人街中餐（含餐）
住宿：Novotel Sydney on Darling Harbour
---
EXPECTED OUTPUT (partial):
{
  "day_number": 3,
  "date": "22/04/2026",
  "day_title": "Sydney City Sightseeing",
  "hotel": "Novotel Sydney on Darling Harbour",
  "meals": {"breakfast": "hotel", "lunch": "Sydney Fish Market", "dinner": "Chinatown Chinese Restaurant"},
  "activities": [
    {
      "time": "09:00",
      "category": "Sightseeing",
      "description_en": "Visit the iconic Sydney Opera House and photograph the Harbour Bridge, two of Australia's most recognised landmarks.",
      "description_zh": "参观悉尼歌剧院，海港大桥拍照",
      "supplier_ref": "Sydney Opera House"
    },
    {
      "time": "12:30",
      "category": "Meal",
      "description_en": "Lunch at Sydney Fish Market, the largest market of its kind in the Southern Hemisphere, offering a vast selection of fresh seafood.",
      "description_zh": "前往悉尼最大海鲜市场午餐",
      "supplier_ref": "Sydney Fish Market"
    },
    {
      "time": "19:00",
      "category": "Meal",
      "description_en": "Dinner at a Chinatown Chinese restaurant (included).",
      "description_zh": "唐人街中餐（含餐）",
      "supplier_ref": "Chinatown Chinese Restaurant"
    }
  ]
}
"""


# ── Stage 1: Extract text from .docx ──────────────────────────────────────────

def extract_docx_text(file_path: str | Path) -> str:
    """
    Extract full text from a .docx file, preserving paragraph structure.
    Tables are extracted row-by-row with | separators for context.
    """
    doc = Document(str(file_path))
    sections = []

    for block in doc.element.body:
        tag = block.tag.split("}")[-1]

        if tag == "p":
            # Paragraph
            para_text = "".join(run.text for run in block.iterchildren()
                                if run.tag.split("}")[-1] == "r"
                                for t in run.iterchildren()
                                if t.tag.split("}")[-1] == "t")
            if para_text.strip():
                sections.append(para_text.strip())

        elif tag == "tbl":
            # Table — flatten to pipe-delimited rows
            for row in block.iterchildren():
                if row.tag.split("}")[-1] != "tr":
                    continue
                cells = []
                for cell in row.iterchildren():
                    if cell.tag.split("}")[-1] == "tc":
                        cell_text = " ".join(
                            p.text_content() if hasattr(p, "text_content")
                            else "".join(t.text or "" for t in p.iter())
                            for p in cell.iterchildren()
                        ).strip()
                        cells.append(cell_text)
                if any(cells):
                    sections.append(" | ".join(cells))

    return "\n".join(sections)


# ── Stage 2: LLM Parsing ───────────────────────────────────────────────────────

def build_system_prompt() -> str:
    return f"""You are a professional travel document parser specialising in converting Chinese group tour itineraries into structured JSON for the ADS (Automated Document System).

CORE RULES:
1. Date format: Always output dates as DD/MM/YYYY. Infer the full year from the group code or document header (e.g., "26年" → 2026). Input like "4.20" means April 20th.
2. Overnight flights: If a flight departs late (e.g., 23:55) and arrives "次日" (next day), set "arrives_next_day": true and assign the flight to the day it DEPARTS.
3. Early morning arrivals: Flights arriving at e.g. 02:55 belong to the day they land. Check "次日" markers.
4. Translation style: DO NOT literally translate. Write polished, promotional English. See examples below.
5. Meals coded as "各自解决" = null (on own). "含餐" = included. Extract named restaurants as supplier refs.
6. Room types: "标准间"=TWN, "大床房"=DBL, "单人间"=SGL, "三人间"=TRPL. "网评四星"=4-star review rating.
7. Supplier names: Extract the FULL English name when present (e.g., "Novotel Melbourne Preston"). If only Chinese, transliterate or translate naturally.
8. Output ONLY valid JSON matching the schema. No markdown, no explanation.

JSON SCHEMA SUMMARY:
- group_info: group_code, tour_name, year, departure_date, return_date, total_days, destination
- pax_details: total_pax, room_config (SGL/TWN/DBL/TRPL counts), upgrade_notes
- flights: array of flight objects with full datetime strings
- daily_itinerary: array of day objects, each with activities array
- suppliers: deduplicated list of all suppliers referenced in itinerary

{FEW_SHOT_EXAMPLES}

Respond ONLY with the JSON object. No preamble, no backticks, no explanation."""


def call_llm(raw_text: str, client: anthropic.Anthropic) -> dict:
    """Send extracted text to Claude and parse the JSON response."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        system=build_system_prompt(),
        messages=[{
            "role": "user",
            "content": f"Parse the following Chinese tour itinerary into ADS JSON:\n\n{raw_text}"
        }]
    )

    raw_json = response.content[0].text.strip()

    # Strip accidental markdown fences
    if raw_json.startswith("```"):
        raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json)
        raw_json = re.sub(r"\n?```$", "", raw_json)

    return json.loads(raw_json)


# ── Stage 3: Post-process & Supplier Resolution ────────────────────────────────

def resolve_suppliers(ads_data: dict) -> dict:
    """
    Cross-reference every supplier in the parsed output against SUPPLIER_DB.
    Enriches confirmed suppliers, flags missing ones for manual review.
    """
    seen: dict[str, dict] = {}  # name_en → enriched record
    warnings: list[str] = []

    # Collect all supplier mentions from daily itinerary
    for day in ads_data.get("daily_itinerary", []):
        day_num = day.get("day_number", 0)

        # Hotel
        hotel_name = day.get("hotel")
        if hotel_name:
            _register_supplier(hotel_name, "Hotel", day_num, seen, warnings)

        # Meals
        for meal_type, meal_val in (day.get("meals") or {}).items():
            if meal_val and meal_val not in ("hotel", "on own"):
                _register_supplier(meal_val, "Restaurant", day_num, seen, warnings)

        # Activity suppliers
        for act in day.get("activities", []):
            ref = act.get("supplier_ref")
            if ref:
                cat = _infer_category(act.get("category", "Other"))
                _register_supplier(ref, cat, day_num, seen, warnings)

    # Build deduplicated supplier list with IDs
    suppliers = []
    for idx, (name, record) in enumerate(seen.items(), start=1):
        record["supplier_id"] = f"SUP-{idx:03d}"
        suppliers.append(record)

    ads_data["suppliers"] = suppliers
    ads_data.setdefault("parse_metadata", {})["missing_suppliers"] = sum(
        1 for s in suppliers if s["status"] == "missing"
    )
    ads_data["parse_metadata"]["warnings"] = warnings
    ads_data["parse_metadata"]["parsed_at"] = datetime.utcnow().isoformat() + "Z"
    ads_data["parse_metadata"]["parser_version"] = PARSER_VERSION

    return ads_data


def _register_supplier(name: str, default_category: str,
                        day_num: int, seen: dict, warnings: list) -> None:
    if not name:
        return
    key = name.strip()
    if key in seen:
        # Add day reference if not already there
        if day_num not in seen[key].get("day_references", []):
            seen[key].setdefault("day_references", []).append(day_num)
        return

    db_record, status = lookup_supplier(key)

    if db_record:
        entry = {**db_record, "status": status, "day_references": [day_num]}
        if status == "fuzzy_match":
            warnings.append(
                f"Supplier '{key}' matched by fuzzy search to '{db_record['name_en']}' — please verify."
            )
    else:
        entry = {
            "name_en":      key,
            "name_zh":      None,
            "category":     default_category,
            "address":      None,
            "phone":        None,
            "email":        None,
            "contact_name": None,
            "status":       "missing",
            "day_references": [day_num],
        }
        warnings.append(f"Supplier '{key}' NOT FOUND in database — manual entry required.")

    seen[key] = entry


def _infer_category(activity_category: str) -> str:
    mapping = {
        "Flight": "Transport", "Transfer": "Transport",
        "Meal": "Restaurant", "Sightseeing": "Attraction",
        "Hotel Check-in": "Hotel", "Hotel Check-out": "Hotel",
        "Shopping": "Attraction", "Activity": "Attraction",
    }
    return mapping.get(activity_category, "Other")


# ── Main Entry Point ───────────────────────────────────────────────────────────

def parse_itinerary(file_path: str | Path,
                    api_key: str | None = None) -> dict:
    """
    Full pipeline: docx → text → LLM JSON → supplier resolution → final ADS dict.

    Args:
        file_path: Path to the Chinese .docx itinerary file.
        api_key:   Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.

    Returns:
        Fully enriched ADS JSON dict ready for PDF generation.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.info(f"[1/3] Extracting text from {path.name}")
    raw_text = extract_docx_text(path)
    logger.info(f"      Extracted {len(raw_text)} characters.")

    logger.info("[2/3] Sending to LLM for structured parsing...")
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    ads_data = call_llm(raw_text, client)

    # Inject filename into metadata
    ads_data.setdefault("parse_metadata", {})["source_filename"] = path.name

    logger.info("[3/3] Resolving suppliers against database...")
    ads_data = resolve_suppliers(ads_data)

    missing = ads_data["parse_metadata"]["missing_suppliers"]
    if missing:
        logger.warning(f"      {missing} supplier(s) missing from database — flagged for review.")
    else:
        logger.info("      All suppliers resolved successfully.")

    return ads_data


# ── CLI Usage ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import os

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_itinerary.docx> [output.json]")
        sys.exit(1)

    docx_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "ads_output.json"

    result = parse_itinerary(docx_path)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nOutput saved to: {out_path}")
    print(f"Missing suppliers: {result['parse_metadata']['missing_suppliers']}")
    for w in result["parse_metadata"].get("warnings", []):
        print(f"  [WARN] {w}")
