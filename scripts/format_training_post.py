# -*- coding: utf-8 -*-
"""一般英単語(旧 english-learner「こつこつ英単語」)の投稿整形。

data/training/{cat}.jsonl(id,word,meaning,example,example_ja,tag)を読み、
WORDS_PER_POST 語ずつ「単語 = 意味」で1投稿に整形する。
english-learner と同じ 6語/投稿 にして進捗(cursor=語インデックス)を引き継ぐ。

使い方:
    python scripts/format_training_post.py news            # 先頭6語を表示
    python scripts/format_training_post.py drama --cursor 12
"""
import argparse
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "training"
WORDS_PER_POST = 6
THREADS_LIMIT = 500

# cat -> サイトの slug / 見出し / ハッシュタグ(Threadsは1投稿=タグ1個のみ有効)
TRAINING = {
    "news": {"slug": "news", "file": "news.jsonl", "title": "ニュース英単語", "hashtag": "#ニュース英語"},
    "drama": {"slug": "drama", "file": "drama.jsonl", "title": "ドラマ英単語", "hashtag": "#英語ドラマ"},
    "phrasal": {"slug": "phrasal", "file": "phrasal.jsonl", "title": "句動詞", "hashtag": "#句動詞"},
    "idioms": {"slug": "idioms", "file": "idioms.jsonl", "title": "イディオム", "hashtag": "#イディオム"},
    "eiken_pre1": {"slug": "eiken-pre1", "file": "eiken_pre1.jsonl", "title": "英検準1級 英単語", "hashtag": "#英検準1級"},
}

# 既定のローテーション順(news → drama → phrasal → idioms → eiken_pre1)
ROTATION = ["news", "drama", "phrasal", "idioms", "eiken_pre1"]


def load_words(cat):
    path = DATA_DIR / TRAINING[cat]["file"]
    words = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                words.append(json.loads(line))
    return words


def pick_chunk(words, cursor, size=WORDS_PER_POST):
    """cursor(語インデックス)から size 語を、末尾を回り込みながら取り出す。"""
    n = len(words)
    return [words[(cursor + i) % n] for i in range(size)]


def build_post(cat, rows):
    cfg = TRAINING[cat]
    first, last = rows[0]["id"], rows[-1]["id"]
    head = f"【{cfg['title']} No.{first}-{last}】"
    lines = [head, ""]
    lines += [f"・{r['word']} = {r['meaning']}" for r in rows]
    lines += ["", cfg["hashtag"]]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cat", choices=list(TRAINING))
    ap.add_argument("--cursor", type=int, default=0, help="語インデックス(0始まり)")
    args = ap.parse_args()
    words = load_words(args.cat)
    rows = pick_chunk(words, args.cursor % len(words))
    post = build_post(args.cat, rows)
    n = len(post)
    warn = "  ⚠ 500超" if n > THREADS_LIMIT else ""
    print(f"----- {args.cat} cursor={args.cursor} ({n}/{THREADS_LIMIT}){warn} -----")
    print(post)


if __name__ == "__main__":
    main()
