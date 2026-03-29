"""
ADS Output JSON Schema
Defines the canonical structure expected from the parser pipeline.
"""

ADS_JSON_SCHEMA = {
    "type": "object",
    "required": ["group_info", "pax_details", "flights", "daily_itinerary", "suppliers"],
    "properties": {

        # ── 团队基础信息 ──────────────────────────────────────────────
        "group_info": {
            "type": "object",
            "required": ["group_code", "tour_name", "year", "departure_date", "return_date", "total_days"],
            "properties": {
                "group_code":     {"type": "string", "example": "AU-MEL-26001"},
                "tour_name":      {"type": "string", "example": "Melbourne & Sydney Discovery"},
                "year":           {"type": "integer", "example": 2026},
                "departure_date": {"type": "string", "format": "date", "example": "20/04/2026"},
                "return_date":    {"type": "string", "format": "date", "example": "28/04/2026"},
                "total_days":     {"type": "integer", "example": 9},
                "destination":    {"type": "string", "example": "Australia"},
            }
        },

        # ── 乘客信息 ──────────────────────────────────────────────────
        "pax_details": {
            "type": "object",
            "required": ["total_pax", "room_config"],
            "properties": {
                "total_pax": {"type": "integer", "example": 22},
                "room_config": {
                    "type": "object",
                    "properties": {
                        "SGL": {"type": "integer", "default": 0},
                        "TWN": {"type": "integer", "default": 0},
                        "DBL": {"type": "integer", "default": 0},
                        "TRPL": {"type": "integer", "default": 0},
                    }
                },
                "upgrade_notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["Upgrade 1 night to 5-star hotel on Day 3"]
                },
                "guide_name":   {"type": "string"},
                "guide_phone":  {"type": "string"},
            }
        },

        # ── 航班信息 ──────────────────────────────────────────────────
        "flights": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["flight_number", "origin_iata", "dest_iata",
                             "departure_datetime", "arrival_datetime", "day_number"],
                "properties": {
                    "flight_number":       {"type": "string",  "example": "HU7092"},
                    "airline":             {"type": "string",  "example": "Hainan Airlines"},
                    "origin_iata":         {"type": "string",  "example": "KMG"},
                    "dest_iata":           {"type": "string",  "example": "HAK"},
                    "origin_city":         {"type": "string",  "example": "Kunming"},
                    "dest_city":           {"type": "string",  "example": "Haikou"},
                    "departure_datetime":  {"type": "string",  "example": "20/04/2026 12:00"},
                    "arrival_datetime":    {"type": "string",  "example": "20/04/2026 13:50"},
                    "day_number":          {"type": "integer", "example": 1},
                    "overnight_flight":    {"type": "boolean", "default": False},
                    "arrives_next_day":    {"type": "boolean", "default": False},
                }
            }
        },

        # ── 每日行程 ──────────────────────────────────────────────────
        "daily_itinerary": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["day_number", "date", "activities"],
                "properties": {
                    "day_number": {"type": "integer"},
                    "date":       {"type": "string", "format": "date", "example": "20/04/2026"},
                    "day_title":  {"type": "string", "example": "Arrival in Melbourne"},
                    "hotel":      {"type": "string", "example": "Novotel Melbourne Preston"},
                    "meals": {
                        "type": "object",
                        "properties": {
                            "breakfast": {"type": ["string", "null"]},
                            "lunch":     {"type": ["string", "null"]},
                            "dinner":    {"type": ["string", "null"]},
                        }
                    },
                    "activities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["time", "category", "description_en"],
                            "properties": {
                                "time":           {"type": "string",  "example": "09:00"},
                                "category": {
                                    "type": "string",
                                    "enum": ["Transfer", "Sightseeing", "Meal", "Hotel Check-in",
                                             "Hotel Check-out", "Flight", "Shopping", "Activity", "Other"]
                                },
                                "description_en": {"type": "string"},
                                "description_zh": {"type": "string"},
                                "supplier_ref":   {"type": ["string", "null"],
                                                   "description": "Links to supplier id in suppliers[]"},
                                "duration_mins":  {"type": ["integer", "null"]},
                            }
                        }
                    }
                }
            }
        },

        # ── 供应商列表 ────────────────────────────────────────────────
        "suppliers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["supplier_id", "name_en", "category", "status"],
                "properties": {
                    "supplier_id":  {"type": "string",  "example": "SUP-001"},
                    "name_en":      {"type": "string",  "example": "Novotel Melbourne Preston"},
                    "name_zh":      {"type": "string",  "example": "墨尔本普雷斯顿诺富特酒店"},
                    "category": {
                        "type": "string",
                        "enum": ["Hotel", "Restaurant", "Transport", "Attraction", "Guide", "Other"]
                    },
                    "address":      {"type": ["string", "null"]},
                    "phone":        {"type": ["string", "null"]},
                    "email":        {"type": ["string", "null"]},
                    "contact_name": {"type": ["string", "null"]},
                    "status": {
                        "type": "string",
                        "enum": ["confirmed", "missing", "needs_review"],
                        "description": "'missing' triggers UI highlight for manual completion"
                    },
                    "day_references": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Which day numbers this supplier appears on"
                    }
                }
            }
        },

        # ── 解析元数据 ────────────────────────────────────────────────
        "parse_metadata": {
            "type": "object",
            "properties": {
                "source_filename":   {"type": "string"},
                "parsed_at":         {"type": "string", "format": "datetime"},
                "parser_version":    {"type": "string"},
                "missing_suppliers": {"type": "integer", "description": "Count needing manual review"},
                "warnings":          {"type": "array", "items": {"type": "string"}},
            }
        }
    }
}
