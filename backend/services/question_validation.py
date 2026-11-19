"""
Pure validation rules for question rows (no database, no SQLAlchemy).

Used by the importer (import_questions.py) and the bulk-validation script in Step 2.
Because it needs nothing but the Python standard library, it is easy to test.
"""
import re

SUBJECTS = [
    "Quantitative Aptitude",
    "General Intelligence & Reasoning",
    "English Language",
    "General Awareness",
]

# Old CSV labels -> the official label used in the database.
SUBJECT_RENAMES = {
    "Reasoning": "General Intelligence & Reasoning",
    "English": "English Language",
}

DIFFICULTIES = ["Easy", "Medium", "Hard"]
ANSWERS = ["A", "B", "C", "D"]
EXAM_TIERS = ["CGL", "CHSL", "MTS", "CPO", "GD", "JE"]
STATUSES = ["draft", "reviewed"]


def normalise_subject(subject):
    subject = (subject or "").strip()
    return SUBJECT_RENAMES.get(subject, subject)


def normalise_text(text):
    """Lower-case, collapse spaces, drop punctuation at the ends. Used to detect duplicates."""
    return re.sub(r"\s+", " ", (text or "").strip().lower()).strip(" .?!")


def duplicate_key(question, options):
    """Two rows with the same question text AND the same set of options are duplicates."""
    return (
        normalise_text(question),
        tuple(sorted(normalise_text(o) for o in options)),
    )


def parse_tiers(value):
    """'CGL;CHSL' or 'CGL, CHSL' -> ['CGL', 'CHSL']. Empty -> []."""
    parts = re.split(r"[;,|]", value or "")
    return [p.strip().upper() for p in parts if p.strip()]


def validate_row(row):
    """
    Checks ONE csv row (a dict). Returns (clean_row, errors).
    clean_row is None when there are errors.
    """
    errors = []

    raw_id = (row.get("question_id") or "").strip()
    question_id = None
    if not raw_id.isdigit() or int(raw_id) <= 0:
        errors.append(f"question_id '{raw_id}' is not a positive whole number")
    else:
        question_id = int(raw_id)

    subject = normalise_subject(row.get("subject"))
    if subject not in SUBJECTS:
        errors.append(f"subject '{subject}' is not one of {SUBJECTS}")

    topic = (row.get("topic") or "").strip()
    if not topic:
        errors.append("topic is empty")

    difficulty = (row.get("difficulty") or "").strip().capitalize()
    if difficulty not in DIFFICULTIES:
        errors.append(f"difficulty '{difficulty}' must be Easy, Medium or Hard")

    question = (row.get("question") or "").strip()
    if not question:
        errors.append("question text is empty")

    options = [(row.get(f"option_{letter}") or "").strip() for letter in "abcd"]
    if not all(options):
        errors.append("all four options (option_a..option_d) must be filled in")
    elif len({normalise_text(o) for o in options}) != 4:
        errors.append("the four options must all be different")

    answer = (row.get("correct_answer") or "").strip().upper()
    if answer not in ANSWERS:
        errors.append(f"correct_answer '{answer}' must be A, B, C or D")

    tiers = parse_tiers(row.get("exam_tiers"))
    bad_tiers = [t for t in tiers if t not in EXAM_TIERS]
    if bad_tiers:
        errors.append(f"unknown exam tier(s) {bad_tiers}; allowed: {EXAM_TIERS}")

    if errors:
        return None, errors

    return {
        "id": question_id,
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "question": question,
        "option_a": options[0],
        "option_b": options[1],
        "option_c": options[2],
        "option_d": options[3],
        "correct_answer": answer,
        "explanation": (row.get("explanation") or "").strip() or None,
        "is_diagnostic": (row.get("diagnostic") or "").strip().lower() == "yes",
        "tiers": tiers,
    }, []


def validate_rows(rows, existing_keys=None, existing_ids=None):
    """
    Checks a whole file. Returns (good, rejected, unchanged).

    good:      clean rows that are NEW and valid (see validate_row)
    rejected:  [{"line", "question_id", "errors": [...]}] - refused, with reasons
    unchanged: ids already in the database with the same content (safe re-import: skipped)

    existing_keys: {duplicate_key: id} for questions already in the database
    existing_ids:  set of ids already in the database
    """
    existing_keys = dict(existing_keys or {})
    existing_ids = set(existing_ids or [])
    file_ids = set()
    file_keys = {}
    good, rejected, unchanged = [], [], []

    for index, row in enumerate(rows):
        line = index + 2    # line 1 of the csv file is the header
        clean, errors = validate_row(row)
        key = None

        if clean is not None:
            key = duplicate_key(
                clean["question"],
                [clean["option_a"], clean["option_b"], clean["option_c"], clean["option_d"]],
            )
            qid = clean["id"]

            if qid in file_ids:
                errors.append(f"question_id {qid} appears twice in the file")
            elif qid in existing_ids:
                if existing_keys.get(key) == qid:
                    unchanged.append(qid)
                    file_ids.add(qid)
                    continue
                errors.append(f"question_id {qid} is already in the database with different content (not overwritten)")
            else:
                owner = existing_keys.get(key) or file_keys.get(key)
                if owner is not None:
                    errors.append(f"duplicate of question {owner} (same text and options)")

        if errors:
            rejected.append({
                "line": line,
                "question_id": (row.get("question_id") or "").strip(),
                "errors": errors,
            })
            continue

        file_ids.add(clean["id"])
        file_keys[key] = clean["id"]
        good.append(clean)

    return good, rejected, unchanged


def format_report(good, rejected, unchanged=()):
    lines = [
        "Question import report",
        "======================",
        f"Accepted rows : {len(good)}",
        f"Rejected rows : {len(rejected)}",
    ]
    lines.append(f"Unchanged     : {len(unchanged)} (already in the database, skipped)")
    for item in rejected:
        lines.append(f"  line {item['line']} (id {item['question_id'] or '?'}):")
        for error in item["errors"]:
            lines.append(f"      - {error}")
    return "\n".join(lines)
