# -*- coding: utf-8 -*-
"""語彙CSV(uscpa_words.csv / legal_words.csv)から複数語をまとめて投稿文へ整形する。

1投稿につき CHUNK 語(既定5語)を「単語 = 意味」だけでシンプルに並べる。
CSVカラム: id,subject,term,meaning_ja,example_en,example_ja,source,status,used_at

使い方:
    python scripts/format_vocab_post.py uscpa            # 先頭チャンク(1〜5語)を表示
    python scripts/format_vocab_post.py legal --index 2  # 3番目のチャンク(0始まり)
"""
import argparse
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHUNK = 5  # 1投稿あたりの語数

CONTENT = {
    # Threads は1投稿=タグ1個のみ有効なため主要タグに絞る(X転用時は複数へ)
    "uscpa": {
        "file": "uscpa_words.csv",
        "label": "USCPA英単語",
        "hashtags": "#USCPA",
    },
    "legal": {
        "file": "legal_words.csv",
        "label": "法律英単語",
        "hashtags": "#法律英語",
    },
}

THREADS_LIMIT = 500


def load_rows(content_key):
    path = DATA_DIR / CONTENT[content_key]["file"]
    with path.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("status") != "rejected"]


def chunk_rows(rows, size=CHUNK):
    return [rows[i : i + size] for i in range(0, len(rows), size)]


def build_post(content_key, rows):
    """rows(最大CHUNK件)を1投稿へ。単語=意味 のみを列挙。"""
    cfg = CONTENT[content_key]
    first, last = rows[0]["id"], rows[-1]["id"]
    subjects = {r["subject"] for r in rows}
    subj = f"｜{next(iter(subjects))}" if len(subjects) == 1 else ""
    head = f"【{cfg['label']} No.{first}-{last}{subj}】"
    lines = [head, ""]
    lines += [f"・{r['term']} = {r['meaning_ja']}" for r in rows]
    lines += ["", cfg["hashtags"]]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", choices=list(CONTENT))
    ap.add_argument("--index", type=int, default=0, help="0始まりのチャンク番号")
    args = ap.parse_args()
    chunks = chunk_rows(load_rows(args.content))
    rows = chunks[args.index % len(chunks)]
    post = build_post(args.content, rows)
    n = len(post)
    warn = "  ⚠ 500超" if n > THREADS_LIMIT else ""
    print(f"----- {args.content} chunk={args.index} ({n}/{THREADS_LIMIT}){warn} -----")
    print(post)


if __name__ == "__main__":
    main()
