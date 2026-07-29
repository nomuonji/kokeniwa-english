# -*- coding: utf-8 -*-
"""英文解釈問題DB(data/reading_problems.jsonl)の検証・投稿整形スクリプト。

使い方:
    python scripts/format_reading_post.py --validate      # 全行の機械検証
    python scripts/format_reading_post.py                 # 未使用で最も古い1問をツリー投稿形式で出力
    python scripts/format_reading_post.py --id 13         # 指定idを出力
    python scripts/format_reading_post.py --mark-used 13  # used_at に今日の日付を記録
    python scripts/format_reading_post.py --stats         # カテゴリ・難易度・状態の集計
"""
import argparse
import datetime
import io
import json
import sys
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reading_problems.jsonl"

REQUIRED_FIELDS = [
    "id", "category", "point", "difficulty", "format", "sentence_en",
    "question_ja", "choices", "answer_index", "translation_ja",
    "explanation_ja", "status", "used_at",
]
DIFF_LABEL = {1: "B2", 2: "C1", 3: "C2"}
HASHTAGS = "#英文解釈"  # Threadsは1投稿=タグ1個のみ有効
X_LIMIT = 280  # X の重み付き文字数上限(全角2・半角1)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def weighted_len(text: str) -> int:
    """X の文字数カウント近似: 東アジア全角文字=2、それ以外=1。"""
    total = 0
    for ch in text:
        total += 2 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 1
    return total


def load_items():
    items = []
    with DB_PATH.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            items.append((lineno, json.loads(line)))
    return items


def validate():
    errors = []
    items = load_items()
    seen_ids = set()
    for lineno, it in items:
        for field in REQUIRED_FIELDS:
            if field not in it:
                errors.append(f"line {lineno}: フィールド欠落 {field}")
        iid = it.get("id")
        if iid in seen_ids:
            errors.append(f"line {lineno}: id重複 {iid}")
        seen_ids.add(iid)
        if it.get("difficulty") not in (1, 2, 3):
            errors.append(f"id {iid}: difficultyは1/2/3のみ")
        fmt = it.get("format")
        if fmt == "quiz":
            if not it.get("choices"):
                errors.append(f"id {iid}: quizなのにchoicesが空")
            elif not isinstance(it.get("answer_index"), int) or not (
                0 <= it["answer_index"] < len(it["choices"])
            ):
                errors.append(f"id {iid}: answer_indexがchoicesの範囲外")
        elif fmt == "translation":
            if it.get("choices"):
                errors.append(f"id {iid}: translationなのにchoicesあり")
            if it.get("answer_index") is not None:
                errors.append(f"id {iid}: translationのanswer_indexはnull")
        else:
            errors.append(f"id {iid}: formatはquiz/translationのみ")
        if it.get("status") not in ("draft", "verified", "rejected"):
            errors.append(f"id {iid}: statusはdraft/verified/rejectedのみ")
        for field in ("sentence_en", "translation_ja", "explanation_ja"):
            if not str(it.get(field, "")).strip():
                errors.append(f"id {iid}: {field}が空")
    # id連番チェック(1始まり・欠番なし)
    ids = sorted(seen_ids)
    if ids != list(range(1, len(ids) + 1)):
        errors.append(f"idが1からの連番でない: {ids[:5]}...{ids[-3:]}")
    if errors:
        print(f"NG: {len(errors)}件の問題")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK: 全{len(items)}問、機械検証パス(必須フィールド・id連番・quiz整合)")
    return 0


def build_posts(it, limit=X_LIMIT, length_fn=weighted_len):
    """1問 → ツリー投稿(出題ポスト+解説リプライ)のリストを返す。

    limit/length_fn を渡すと結合判定の基準を差し替えられる。
    Threads(500字・素の文字数)向けには build_posts(it, 500, len) を使う。
    """
    # 難易度は投稿に載せない（体感と合っていないという指摘のため。サイト表示も廃止済み）
    head = f"【英文解釈 No.{it['id']}|{it['category']}】"
    q = [head, "", it["sentence_en"], "", f"Q. {it['question_ja']}"]
    if it["format"] == "quiz":
        for i, c in enumerate(it["choices"]):
            q.append(f"{chr(65 + i)}) {c}")
    q += ["", "↓答えと解説はリプ欄に", HASHTAGS]
    post1 = "\n".join(q)

    if it["format"] == "quiz":
        ans = f"正解: {chr(65 + it['answer_index'])}) {it['choices'][it['answer_index']]}"
        post2 = "\n".join([ans, "", f"訳: {it['translation_ja']}"])
    else:
        post2 = f"【訳例】\n{it['translation_ja']}"
    post3 = f"【解説】\n{it['explanation_ja']}"

    # 正解+解説が1ポストに収まるなら統合(ツリーを短く)
    merged = post2 + "\n\n" + post3
    if length_fn(merged) <= limit:
        return [post1, merged]
    return [post1, post2, post3]


def show(it):
    posts = build_posts(it)
    labels = ["① 出題ポスト"] + [f"{'②③④'[i]} リプライ{i + 1}" for i in range(len(posts) - 1)]
    for label, p in zip(labels, posts):
        n = weighted_len(p)
        warn = "  ⚠ 280超(要分割 or Premium)" if n > X_LIMIT else ""
        print(f"----- {label} ({n}/{X_LIMIT}){warn} -----")
        print(p)
        print()


def pick_next(items):
    """未使用(used_at空)で最もidが小さいものを返す。全て使用済みなら最も古いもの。"""
    unused = [it for _, it in items if not it["used_at"] and it["status"] != "rejected"]
    if unused:
        return min(unused, key=lambda x: x["id"])
    pool = [it for _, it in items if it["status"] != "rejected"]
    return min(pool, key=lambda x: x["used_at"])


def mark_used(target_id):
    lines = DB_PATH.read_text(encoding="utf-8").splitlines()
    out, found = [], False
    for line in lines:
        if line.strip():
            it = json.loads(line)
            if it["id"] == target_id:
                it["used_at"] = datetime.date.today().isoformat()
                line = json.dumps(it, ensure_ascii=False)
                found = True
        out.append(line)
    if not found:
        print(f"id {target_id} が見つかりません")
        return 1
    DB_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"id {target_id} の used_at を {datetime.date.today().isoformat()} に更新")
    return 0


def stats(items):
    from collections import Counter
    cats = Counter(it["category"] for _, it in items)
    diffs = Counter(it["difficulty"] for _, it in items)
    fmts = Counter(it["format"] for _, it in items)
    sts = Counter(it["status"] for _, it in items)
    used = sum(1 for _, it in items if it["used_at"])
    print(f"総数: {len(items)}問(使用済み {used})")
    print("カテゴリ:", ", ".join(f"{k} {v}" for k, v in cats.most_common()))
    print("難易度:", ", ".join(f"{DIFF_LABEL[k]} {v}" for k, v in sorted(diffs.items())))
    print("形式:", ", ".join(f"{k} {v}" for k, v in fmts.items()))
    print("状態:", ", ".join(f"{k} {v}" for k, v in sts.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="指定idの問題を整形して表示")
    ap.add_argument("--validate", action="store_true", help="DB全体を機械検証")
    ap.add_argument("--mark-used", type=int, metavar="ID", help="used_atに今日の日付を記録")
    ap.add_argument("--stats", action="store_true", help="集計を表示")
    args = ap.parse_args()

    if args.validate:
        sys.exit(validate())
    if args.mark_used is not None:
        sys.exit(mark_used(args.mark_used))

    items = load_items()
    if args.stats:
        stats(items)
        return
    if args.id is not None:
        match = [it for _, it in items if it["id"] == args.id]
        if not match:
            print(f"id {args.id} が見つかりません")
            sys.exit(1)
        show(match[0])
    else:
        show(pick_next(items))


if __name__ == "__main__":
    main()
