"""
Document ingestion pipeline.

Loads raw .txt files from the documents/ folder, splits them into
substantive text units, and attaches source metadata to each unit.

Each unit is a dict with: text, source, location, url, doc_type, filename.
Units are the input to chunk.py.
"""

import re
from pathlib import Path

DOCUMENTS_DIR = Path("documents")

# Per-file metadata matching the sources table in planning.md
SOURCE_META: dict[str, dict] = {
    "1_yelp_broward_dining.txt": {
        "source": "Yelp",
        "location": "Broward Dining Hall",
        "url": "https://www.yelp.com/biz/fresh-food-company-broward-dining-gainesville",
        "doc_type": "review",
    },
    "2_restarauntji_gator_corner.txt": {
        "source": "Restaurantji",
        "location": "Gator Corner Dining Center",
        "url": "https://www.restaurantji.com/fl/gainesville/gator-corner-dining-center-/",
        "doc_type": "review",
    },
    "3_spoonuniversity_cravings_campus.txt": {
        "source": "Spoon University",
        "location": "Cravings Campus Kitchen",
        "url": "https://spoonuniversity.com/school/ufl/reviewing-the-new-dining-hall/",
        "doc_type": "article",
    },
    "4_alligator_broward_renovated.txt": {
        "source": "The Alligator",
        "location": "Broward Dining Hall",
        "url": "https://www.alligator.org/article/2024/08/the-eatery-at-broward-hall-first-look",
        "doc_type": "article",
    },
    "5_alligator_broward_old.txt": {
        "source": "The Alligator",
        "location": "Norman Tent Dining (Broward Renovation)",
        "url": "https://www.alligator.org/article/2024/01/broward-tent",
        "doc_type": "article",
    },
    "6_alligator_uf_vegan.txt": {
        "source": "The Alligator",
        "location": "UF Dining Halls (Vegan Options)",
        "url": "https://www.alligator.org/article/2024/01/uf-vegan-experience",
        "doc_type": "article",
    },
    "7_alligator_mealplans_atlernative.txt": {
        "source": "The Alligator",
        "location": "UF Dining / Bite Club",
        "url": "https://www.alligator.org/article/2024/09/what-to-know-about-a-new-student-meal-plan-alternative",
        "doc_type": "article",
    },
    "8_niche_uf_campuslife.txt": {
        "source": "Niche",
        "location": "UF Campus Dining",
        "url": "https://www.niche.com/colleges/university-of-florida/campus-life/",
        "doc_type": "review",
    },
    "9_wanderlog_reitz_union.txt": {
        "source": "Wanderlog",
        "location": "Reitz Union Food Court",
        "url": "https://wanderlog.com/place/details/11039454/reitz-union",
        "doc_type": "review",
    },
    "10_reddit_campus_dining.txt": {
        "source": "Reddit r/ufl",
        "location": "UF Campus Dining",
        "url": "https://www.reddit.com/r/ufl/comments/1szl19w/new_uf_meal_plans_breakdown/",
        "doc_type": "reddit",
    },
    "11_reddit_food_budegting.txt": {
        "source": "Reddit r/ufl",
        "location": "UF Campus Dining",
        "url": "https://www.reddit.com/r/ufl/comments/q4af5g/how_much_money_do_you_spend_on_food/",
        "doc_type": "reddit",
    },
    "12_reddit_late_night.txt": {
        "source": "Reddit r/ufl",
        "location": "Gainesville Late-Night Dining",
        "url": "https://www.reddit.com/r/ufl/comments/jh2ikl/good_food_after_midnight/",
        "doc_type": "reddit",
    },
}

# Compiled patterns that identify noise paragraphs (metadata, headers, bios, UI chrome)
_NOISE_PATTERNS = [
    # Review rating fields
    re.compile(r"^(Atmosphere|Food|Service|Vegetarian options|Dietary restrictions|Wheelchair)", re.I),
    # Article footers
    re.compile(r"^(Recommended dishes|Contact |Follow her|Follow him)", re.I),
    re.compile(r"(reporter|editor|writer) for the (Avenue|Alligator)", re.I),
    re.compile(r"does not reflect the views", re.I),
    re.compile(r"Student Contributor,", re.I),
    # Site domain names appearing in bios/attributions
    re.compile(r"(alligator\.org|spoonuniversity\.com|wanderlog\.com|restaurantji\.com)", re.I),
    # Reddit thread chrome
    re.compile(r"^(Sort by|Comments Section|Rating stars)", re.I),
    re.compile(r"•\s+\d+[ymdwh]", re.I),  # "• 1mo ago" timestamps
    re.compile(r"^u/\w"),  # "u/username" links
    re.compile(r"^(OP\s*•|\[deleted\]|OP$)", re.I),
    re.compile(r"^(Undergraduate|Junior|Senior|Alumni|Graduate|Public Health|Levin College)", re.I),
    # Review platform metadata lines ("August 2025 on Google")
    re.compile(r"on (Google|Facebook|Foursquare|Yelp)\s*$", re.M),
    # Niche / aggregate site headers and poll chrome
    re.compile(
        r"^(Men in Fraternities|Women in Sororities|Campus Food|grade [A-F]|Meal Plan Available|"
        r"Average Meal Plan|STUDENT POLL|Based on \d|Midsize City|Gainesville, FL$|"
        r"Places to visit|Student union|Know before you go|Mentioned on articles|"
        r"Why you should go|About$|Address$|Website$|Phone$|Reviews$)",
        re.I,
    ),
    # Phone numbers
    re.compile(r"^\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}$"),
    re.compile(r"^Get Directions"),
    # Opening-hours lines like "9:00 AM–9:00 PM"
    re.compile(r"^\d+:\d{2}\s*(AM|PM)", re.I),
    # Aggregate rating headers like "Fresh Food Company/Broward Dining\n2.2 (19 reviews)"
    re.compile(r"\(\d+\s+reviews?\)", re.I),
    # Niche page title repeated twice at the top
    re.compile(r"^University of Florida Campus Life", re.I),
    # Wanderlog place metadata: "Address\n[street]"
    re.compile(r"^Address\n", re.I),
]


def _is_noise(paragraph: str) -> bool:
    """Return True if the paragraph should be discarded as metadata or UI chrome."""
    stripped = paragraph.strip()

    if len(stripped) < 40:
        return True

    # Paragraphs where the majority of lines contain a '%' sign are poll data (Niche)
    lines = stripped.splitlines()
    if len(lines) >= 3 and sum(1 for line in lines if "%" in line) >= len(lines) * 0.5:
        return True

    for pattern in _NOISE_PATTERNS:
        if pattern.search(stripped):
            return True

    return False


# Line-level noise patterns used by the Reddit preprocessor
_REDDIT_LINE_NOISE = [
    re.compile(r"^u/\S"),                    # "u/username avatar" lines
    re.compile(r"^\s*•\s*$"),                # standalone bullet lines
    re.compile(r"^\d+[ymdwh]\s+ago", re.I), # "6y ago", "1mo ago"
    re.compile(r"^• Edited", re.I),
    re.compile(r"^\d+$"),                    # upvote counts
    re.compile(r"^OP\s*•", re.I),
    re.compile(
        r"^(Undergraduate|Junior|Senior|Alumni|Graduate|Public Health|Levin College)",
        re.I,
    ),
]


def _preprocess_reddit(text: str) -> str:
    """
    Strip Reddit thread chrome (usernames, upvote counts, timestamps, bullets)
    line-by-line so comment bodies end up as clean standalone paragraphs.

    Reddit raw text joins comment body + upvote count + next username with
    single newlines, no blank line between them.  After stripping those metadata
    lines the remaining blank lines correctly isolate each comment body.
    """
    lines = text.splitlines()
    result: list[str] = []
    skip_next_username = False

    for line in lines:
        stripped = line.strip()

        # The line immediately after "u/username avatar" is the bare username —
        # catch it with skip_next_username so we don't need to guess username formats.
        if skip_next_username:
            skip_next_username = False
            if re.match(r"^[A-Za-z0-9_]+$", stripped):
                continue  # bare username line

        if any(p.match(stripped) for p in _REDDIT_LINE_NOISE):
            if re.match(r"^u/\S", stripped):
                skip_next_username = True
            continue

        result.append(line)

    return "\n".join(result)


def _clean(text: str) -> str:
    """Collapse intra-line whitespace; leave paragraph structure intact."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(lines).strip()


def _extract_units(text: str, meta: dict) -> list[dict]:
    """
    Split a document on blank lines, filter noise, and return substantive units.
    Each unit carries the document's source metadata.
    """
    raw_paragraphs = re.split(r"\n{2,}", text)
    units = []
    for paragraph in raw_paragraphs:
        cleaned = _clean(paragraph)
        if cleaned and not _is_noise(cleaned):
            units.append({"text": cleaned, **meta})
    return units


def ingest_documents(documents_dir: str = "documents") -> list[dict]:
    """
    Load all .txt source documents, parse them into units, and return the list.
    Prints a per-file count so you can verify extraction quality.
    """
    all_units: list[dict] = []
    docs_path = Path(documents_dir)

    for filename, meta in SOURCE_META.items():
        filepath = docs_path / filename
        if not filepath.exists():
            print(f"  [skip] {filename} not found")
            continue

        text = filepath.read_text(encoding="utf-8")
        if meta["doc_type"] == "reddit":
            text = _preprocess_reddit(text)
        units = _extract_units(text, {**meta, "filename": filename})
        all_units.extend(units)
        print(f"  {filename}: {len(units)} units")

    return all_units


if __name__ == "__main__":
    import json

    print("Ingesting documents...")
    units = ingest_documents()
    print(f"\nTotal units extracted: {len(units)}")

    with open("units_debug.json", "w", encoding="utf-8") as f:
        json.dump(units, f, indent=2, ensure_ascii=False)
    print("Saved to units_debug.json — inspect this to verify extraction quality.")