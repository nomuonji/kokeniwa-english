# -*- coding: utf-8 -*-
"""3つの英語DBを Anki インポート用 CSV(カンマ区切り・HTMLタグなし)へ変換する。

出力: anki/uscpa_anki.csv / anki/legal_anki.csv / anki/reading_anki.csv
- 区切りはカンマ。複数行フィールドは引用符で囲み、実際の改行で表現(<br>等は使わない)。
- 先頭に Anki のディレクティブ(デッキ/ノートタイプ/タグ列)を付与。HTMLは無効。
- Excel/スプレッドシートでもそのまま開ける。

  語彙(uscpa/legal): 表=単語 / 裏=意味+例文 / タグ=科目
  読解(reading):     表=英文+設問(+選択肢) / 裏=正解+訳+解説 / タグ=カテゴリ・難易度

使い方:
    python scripts/build_anki.py            # 3ファイルすべて生成
    python scripts/build_anki.py uscpa      # 指定のみ

注意: Anki はフィールドを HTML として表示するため、改行を「見た目の改行」で
表示したい場合は、そのノートタイプの Styling に次の1行を足す(HTMLタグではない):
    .card { white-space: pre-wrap; }
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "anki"
DIFF_LABEL = {1: "B2", 2: "C1", 3: "C2"}


def para(*parts):
    """空でないブロックを空行で区切って連結(プレーンテキスト)。"""
    return "\n\n".join(p for p in parts if p)


def header(deck, notetype, tags_col):
    return [
        "#separator:comma",
        "#html:false",
        f"#deck:{deck}",
        f"#notetype:{notetype}",
        f"#tags column:{tags_col}",
    ]


def write_csv(path, header_lines, rows):
    OUT.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for h in header_lines:
            f.write(h + "\n")
        # 改行やカンマを含むフィールドは自動で引用符付けされる(QUOTE_MINIMAL)
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        w.writerows(rows)
    return len(rows)


# ---- 語彙(USCPA / 法律) ----
VOCAB = {
    "uscpa": {"file": "uscpa_words.csv", "deck": "USCPA英単語", "out": "uscpa_anki.csv"},
    "legal": {"file": "legal_words.csv", "deck": "法律英単語", "out": "legal_anki.csv"},
}


def build_vocab(key):
    cfg = VOCAB[key]
    rows = []
    with (DATA / cfg["file"]).open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("status") == "rejected":
                continue
            front = r["term"]
            example = "\n".join(p for p in [r.get("example_en", ""), r.get("example_ja", "")] if p)
            back = para(r["meaning_ja"], example)
            tags = " ".join(t for t in [key, r.get("subject", "")] if t)
            rows.append([front, back, tags])
    path = OUT / cfg["out"]
    n = write_csv(path, header(cfg["deck"], "Basic", 3), rows)
    print(f"{key}: {n} notes -> {path.relative_to(ROOT)}")


# ---- 読解 ----
def build_reading():
    with (DATA / "reading_problems.jsonl").open(encoding="utf-8") as f:
        items = [json.loads(l) for l in f if l.strip()]
    rows = []
    for it in sorted(items, key=lambda x: x["id"]):
        if it.get("status") == "rejected":
            continue
        question = f"Q. {it['question_ja']}"
        if it["format"] == "quiz":
            choices = "\n".join(f"{chr(65 + i)}) {c}" for i, c in enumerate(it["choices"]))
            question = question + "\n" + choices
        front = para(it["sentence_en"], question)
        if it["format"] == "quiz":
            ans = f"正解: {chr(65 + it['answer_index'])}) {it['choices'][it['answer_index']]}"
            head = para(ans, f"訳: {it['translation_ja']}")
        else:
            head = f"【訳例】{it['translation_ja']}"
        back = para(head, f"【解説】{it['explanation_ja']}")
        tags = " ".join([
            "reading",
            str(it["category"]).replace(" ", "_"),
            DIFF_LABEL.get(it["difficulty"], "?"),
        ])
        rows.append([front, back, tags])
    path = OUT / "reading_anki.csv"
    n = write_csv(path, header("英文解釈", "Basic", 3), rows)
    print(f"reading: {n} notes -> {path.relative_to(ROOT)}")


def main():
    which = sys.argv[1:] or ["uscpa", "legal", "reading"]
    for key in which:
        if key in VOCAB:
            build_vocab(key)
        elif key == "reading":
            build_reading()
        else:
            print(f"未知のDB: {key}")


if __name__ == "__main__":
    main()
