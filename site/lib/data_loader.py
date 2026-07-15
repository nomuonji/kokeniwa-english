"""data/ 配下のJSONL/CSVを読み込み、掲載対象にフィルタして返す。"""
import csv
import json

from . import config

# scripts/format_reading_post.py の REQUIRED_FIELDS と揃えている
READING_REQUIRED_FIELDS = [
    "id", "category", "point", "difficulty", "format", "sentence_en",
    "question_ja", "choices", "answer_index", "translation_ja",
    "explanation_ja", "status", "used_at",
]


def load_reading_problems(cfg):
    """読解問題を読み込む。rejectedは常に除外、draftはconfigで制御。"""
    problems = []
    path = config.DATA_DIR / "reading_problems.jsonl"
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            missing = [k for k in READING_REQUIRED_FIELDS if k not in p]
            if missing:
                raise ValueError(f"{path.name}:{lineno} missing fields: {missing}")
            if p["category"] not in config.CATEGORY_SLUGS:
                raise ValueError(
                    f"{path.name}:{lineno} unknown category: {p['category']!r} "
                    "(site/lib/config.py の CATEGORY_SLUGS に追加してください)")
            if p["status"] == "rejected":
                continue
            if p["status"] == "draft" and not cfg.get("include_draft", True):
                continue
            problems.append(p)
    problems.sort(key=lambda p: p["id"])
    return problems


def load_vocab(set_key):
    """語彙CSVを読み込み、subject別のdictで返す。rejectedは除外。"""
    vset = config.VOCAB_SETS[set_key]
    path = config.DATA_DIR / vset["csv"]
    by_subject = {k: [] for k in vset["subjects"]}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["status"] == "rejected":
                continue
            subject = row["subject"]
            if subject not in by_subject:
                raise ValueError(
                    f"{path.name}: unknown subject {subject!r} "
                    "(site/lib/config.py の subject 定義に追加してください)")
            row["id"] = int(row["id"])
            by_subject[subject].append(row)
    for words in by_subject.values():
        words.sort(key=lambda w: w["id"])
    return by_subject
