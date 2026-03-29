"""
api.py  —  Flask REST API for ADS Parser
==========================================
POST /api/parse      Upload a .docx, get back ADS JSON
GET  /api/suppliers  List all known suppliers
POST /api/suppliers  Add / update a supplier record
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, Response
from werkzeug.utils import secure_filename

from parser import parse_itinerary
from supplier_db import SUPPLIER_DB, lookup_supplier, normalise

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"docx"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def json_response(data: dict, status: int = 200) -> Response:
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        status=status,
        mimetype="application/json; charset=utf-8"
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/api/parse")
def parse_document():
    """
    Upload a Chinese .docx itinerary and receive structured ADS JSON.

    Form fields:
      - file:    (required) The .docx file
      - api_key: (optional) Override ANTHROPIC_API_KEY env var

    Response shape:
    {
      "success": true,
      "data": { ...ADS JSON... },
      "warnings": [...],
      "missing_suppliers": 2
    }
    """
    if "file" not in request.files:
        return json_response({"success": False, "error": "No file part in request."}, 400)

    file = request.files["file"]
    if not file.filename:
        return json_response({"success": False, "error": "No file selected."}, 400)

    if not allowed_file(file.filename):
        return json_response({"success": False,
                               "error": "Invalid file type. Only .docx is accepted."}, 400)

    api_key = request.form.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return json_response({"success": False,
                               "error": "ANTHROPIC_API_KEY not set."}, 500)

    # Save to temp file, parse, clean up
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        file.save(tmp_path)

    try:
        ads_data = parse_itinerary(tmp_path, api_key=api_key)
    except json.JSONDecodeError as e:
        return json_response({"success": False,
                               "error": f"LLM returned invalid JSON: {e}"}, 502)
    except Exception as e:
        logger.exception("Unexpected error during parsing")
        return json_response({"success": False, "error": str(e)}, 500)
    finally:
        tmp_path.unlink(missing_ok=True)

    meta = ads_data.get("parse_metadata", {})
    return json_response({
        "success": True,
        "data": ads_data,
        "warnings": meta.get("warnings", []),
        "missing_suppliers": meta.get("missing_suppliers", 0),
    })


@app.get("/api/suppliers")
def list_suppliers():
    """
    Return all known suppliers in the DB.
    Query params:
      - category: filter by Hotel | Restaurant | Transport | Attraction
      - q:        search by name (substring, case-insensitive)
    """
    category_filter = request.args.get("category", "").lower()
    query = request.args.get("q", "").lower()

    results = []
    for key, record in SUPPLIER_DB.items():
        if category_filter and record["category"].lower() != category_filter:
            continue
        if query and query not in key:
            continue
        results.append({"db_key": key, **record})

    return json_response({"count": len(results), "suppliers": results})


@app.post("/api/suppliers")
def add_supplier():
    """
    Add or update a supplier record (for manual completion of missing entries).

    Request body (JSON):
    {
      "name_en":      "Some Hotel Name",
      "name_zh":      "某酒店",
      "category":     "Hotel",
      "address":      "123 Main St...",
      "phone":        "(03) 0000 0000",
      "email":        "info@...",
      "contact_name": "..."
    }
    """
    body = request.get_json(force=True, silent=True)
    if not body or "name_en" not in body:
        return json_response({"success": False,
                               "error": "Request body must include 'name_en'."}, 400)

    key = normalise(body["name_en"])
    record = {
        "name_en":      body["name_en"],
        "name_zh":      body.get("name_zh"),
        "category":     body.get("category", "Other"),
        "address":      body.get("address"),
        "phone":        body.get("phone"),
        "email":        body.get("email"),
        "contact_name": body.get("contact_name"),
    }

    is_update = key in SUPPLIER_DB
    SUPPLIER_DB[key] = record

    return json_response({
        "success": True,
        "action": "updated" if is_update else "created",
        "db_key": key,
        "record": record,
    }, 200 if is_update else 201)


@app.get("/api/health")
def health():
    return json_response({"status": "ok", "supplier_count": len(SUPPLIER_DB)})


# ── Dev Server ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
