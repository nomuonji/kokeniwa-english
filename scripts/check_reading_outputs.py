"""Verify that reading source, site, bonus CSV, and Kindle EPUB agree."""
import csv
import html
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "reading_problems.jsonl"
ANKI = ROOT / "anki" / "reading_anki.csv"
DIST_ANKI = ROOT / "dist" / "downloads" / "reading_anki.csv"
DIST = ROOT / "dist"
EPUB = Path(r"D:\youph\Kindle\英文解釈トレーニング200問\英文解釈トレーニング200問.epub")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    items = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line]
    require(len(items) == 200, "source must contain 200 records")
    require([item["id"] for item in items] == list(range(1, 201)), "IDs must be 1..200")

    quizzes = [item for item in items if item["format"] == "quiz"]
    distribution = Counter(item["answer_index"] for item in quizzes)
    require(distribution == Counter({0: 20, 1: 20, 2: 19}),
            f"unexpected answer distribution: {distribution}")
    for item in quizzes:
        require(len(item["choices"]) == 3, f"No.{item['id']} must have three choices")
        require(0 <= item["answer_index"] < 3, f"No.{item['id']} answer out of range")

    require(ANKI.read_bytes() == DIST_ANKI.read_bytes(), "Anki source and deployed copy differ")
    with ANKI.open(encoding="utf-8", newline="") as handle:
        header = [next(handle).rstrip("\n") for _ in range(5)]
        require(header[0] == "#separator:comma", "unexpected Anki header")
        cards = list(csv.reader(handle))
    require(len(cards) == 200, "Anki CSV must contain 200 cards")

    with ZipFile(EPUB) as archive:
        require(archive.testzip() is None, "EPUB ZIP CRC failure")
        epub_text = "\n".join(
            archive.read(name).decode("utf-8")
            for name in archive.namelist()
            if name.endswith((".xhtml", ".html"))
        )

    for item, card in zip(items, cards):
        problem_id = item["id"]
        require(len(card) == 3, f"No.{problem_id} Anki field count differs")
        front, back, _tags = card
        require(item["sentence_en"] in front, f"No.{problem_id} sentence missing from Anki")
        require(item["translation_ja"] in back, f"No.{problem_id} translation missing from Anki")
        if item["format"] == "quiz":
            for index, choice in enumerate(item["choices"]):
                require(f"{chr(65 + index)}) {choice}" in front,
                        f"No.{problem_id} choice missing from Anki")
            answer = item["answer_index"]
            require(f"正解: {chr(65 + answer)}) {item['choices'][answer]}" in back,
                    f"No.{problem_id} answer missing from Anki")

        site_text = (DIST / "reading" / str(problem_id) / "index.html").read_text(encoding="utf-8")
        require(html.escape(item["sentence_en"]) in site_text,
                f"No.{problem_id} sentence missing from site")
        require(html.escape(item["translation_ja"]) in site_text,
                f"No.{problem_id} translation missing from site")
        if item["format"] == "quiz":
            require(f'data-answer="{item["answer_index"]}"' in site_text,
                    f"No.{problem_id} answer index missing from site")
            for choice in item["choices"]:
                require(html.escape(choice) in site_text,
                        f"No.{problem_id} choice missing from site")

        for field in ("sentence_en", "translation_ja", "explanation_ja"):
            require(html.escape(item[field], quote=False) in epub_text,
                    f"No.{problem_id} {field} missing from EPUB")

    require("windows dressing" not in epub_text, "old typo remains in EPUB")
    require("出版があまりに容易になったことで" not in epub_text,
            "old No.118 translation remains in EPUB")
    print("reading outputs: OK")
    print("  source/site/Anki/EPUB: 200 records synchronized")
    print(f"  quiz answers: {dict(sorted(distribution.items()))}")
    print("  EPUB ZIP integrity: OK")


if __name__ == "__main__":
    main()
