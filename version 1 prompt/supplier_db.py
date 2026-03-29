"""
Supplier Database (supplier_db.py)
------------------------------------
In production, replace SUPPLIER_DB with a real DB lookup (PostgreSQL / SQLite).
Keys are normalised lowercase for fuzzy matching.
"""

from difflib import SequenceMatcher

# ── Static Supplier Records ────────────────────────────────────────────────────
SUPPLIER_DB: dict[str, dict] = {

    # Hotels
    "novotel melbourne preston": {
        "name_en":      "Novotel Melbourne Preston",
        "name_zh":      "墨尔本普雷斯顿诺富特酒店",
        "category":     "Hotel",
        "address":      "4 215 Bell St, Preston VIC 3072, Australia",
        "phone":        "(03) 9485 1000",
        "email":        "H3630@accor.com",
        "contact_name": "Reservations Team",
    },
    "novotel sydney on darling harbour": {
        "name_en":      "Novotel Sydney on Darling Harbour",
        "name_zh":      "悉尼达令港诺富特酒店",
        "category":     "Hotel",
        "address":      "100 Murray St, Pyrmont NSW 2009, Australia",
        "phone":        "(02) 9934 0000",
        "email":        "H1181@accor.com",
        "contact_name": "Reservations Team",
    },
    "crown melbourne": {
        "name_en":      "Crown Melbourne",
        "name_zh":      "墨尔本皇冠酒店",
        "category":     "Hotel",
        "address":      "8 Whiteman St, Southbank VIC 3006, Australia",
        "phone":        "(03) 9292 8888",
        "email":        "hotels@crownmelbourne.com.au",
        "contact_name": "Groups & Events",
    },
    "mercure sydney": {
        "name_en":      "Mercure Sydney",
        "name_zh":      "悉尼美居酒店",
        "category":     "Hotel",
        "address":      "818-820 George St, Sydney NSW 2000, Australia",
        "phone":        "(02) 9217 6666",
        "email":        "H3354@accor.com",
        "contact_name": "Reservations Team",
    },

    # Restaurants
    "sydney fish market": {
        "name_en":      "Sydney Fish Market",
        "name_zh":      "悉尼鱼市场",
        "category":     "Restaurant",
        "address":      "Bank St & Pyrmont Bridge Rd, Pyrmont NSW 2009",
        "phone":        "(02) 9004 1100",
        "email":        "info@sydneyfishmarket.com.au",
        "contact_name": "Group Bookings",
    },
    "melbourne central food court": {
        "name_en":      "Melbourne Central Food Court",
        "name_zh":      "墨尔本中央购物中心美食广场",
        "category":     "Restaurant",
        "address":      "300 Lonsdale St, Melbourne VIC 3000",
        "phone":        "(03) 9922 1100",
        "email":        None,
        "contact_name": None,
    },

    # Transport
    "skybus melbourne": {
        "name_en":      "SkyBus Melbourne",
        "name_zh":      "墨尔本天空巴士",
        "category":     "Transport",
        "address":      "Melbourne Airport T2, Melbourne VIC 3045",
        "phone":        "1300 759 287",
        "email":        "groups@skybus.com.au",
        "contact_name": "Group Reservations",
    },

    # Attractions
    "great ocean road tour": {
        "name_en":      "Great Ocean Road Experience",
        "name_zh":      "大洋路一日游",
        "category":     "Attraction",
        "address":      "Departs Melbourne CBD",
        "phone":        "(03) 9650 6600",
        "email":        "bookings@greatoceanroad.org",
        "contact_name": "Tour Operations",
    },
    "phillip island nature parks": {
        "name_en":      "Phillip Island Nature Parks",
        "name_zh":      "菲利普岛自然公园（小企鹅巡游）",
        "category":     "Attraction",
        "address":      "1019 Ventnor Rd, Summerlands VIC 3922",
        "phone":        "(03) 5951 2800",
        "email":        "bookings@penguins.org.au",
        "contact_name": "Group Bookings",
    },
    "sydney opera house": {
        "name_en":      "Sydney Opera House",
        "name_zh":      "悉尼歌剧院",
        "category":     "Attraction",
        "address":      "Bennelong Point, Sydney NSW 2000",
        "phone":        "(02) 9250 7111",
        "email":        "visitorservices@sydneyoperahouse.com",
        "contact_name": "Visitor Services",
    },
}

# ── Lookup Functions ───────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    return text.lower().strip()


def exact_lookup(name: str) -> dict | None:
    """Exact (normalised) match."""
    return SUPPLIER_DB.get(normalise(name))


def fuzzy_lookup(name: str, threshold: float = 0.72) -> dict | None:
    """
    Fuzzy match using SequenceMatcher.
    Returns the best match above threshold, or None.
    threshold=0.72 balances recall vs. false positives for hotel/restaurant names.
    """
    key = normalise(name)
    best_score = 0.0
    best_match = None

    for db_key, record in SUPPLIER_DB.items():
        score = SequenceMatcher(None, key, db_key).ratio()
        if score > best_score:
            best_score = score
            best_match = record

    if best_score >= threshold:
        return best_match
    return None


def lookup_supplier(name: str) -> tuple[dict | None, str]:
    """
    Master lookup: tries exact → fuzzy → returns status.
    Returns (record_or_None, status)
    status: 'confirmed' | 'fuzzy_match' | 'missing'
    """
    record = exact_lookup(name)
    if record:
        return record, "confirmed"

    record = fuzzy_lookup(name)
    if record:
        return record, "fuzzy_match"

    return None, "missing"
