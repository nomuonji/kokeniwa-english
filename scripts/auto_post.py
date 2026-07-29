# -*- coding: utf-8 -*-
"""Threads 複数アカウント自動投稿のオーケストレーター(GitHub Actions から実行)。

処理の流れ(各アカウント):
  1. (前回投稿があり未リプライなら)サイト誘導リプライを前回ツリーの末尾へぶら下げる
  2. 期限が近ければトークンをリフレッシュ
  3. カーソル位置のコンテンツを1件投稿(読解はツリー投稿)
  4. 次回の誘導用に last_post を保存し、カーソルを1つ進める
状態(トークン・カーソル・last_post)は Gist に保存。

コンテンツ種別(acc["content"]):
  uscpa / legal : 語彙CSVを5語ずつ(format_vocab_post)
  reading       : 英文解釈を親+解説のツリー(format_reading_post)
  training      : 一般英単語を6語ずつ、5カテゴリをローテーション(format_training_post)

環境変数:
  GH_GIST_TOKEN, GIST_ID  : Gist アクセス(gist_state.py が使用)
  PAGES_BASE              : (任意)誘導リンクのドメイン(format_referral.py が使用)
  DRY_RUN=1               : 実投稿せず内容を表示するだけ
  ACCOUNTS="uscpa,legal"  : (任意)対象アカウントを限定
  REFRESH_BEFORE_DAYS=10  : (任意)期限が何日以内でリフレッシュするか
"""
import datetime as dt
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gist_state
import threads_client as tc
import format_training_post as ftp
from format_referral import build_referral
from format_vocab_post import build_post as build_vocab_post, load_rows, chunk_rows
import format_reading_post as reading

THREADS_LIMIT = 500  # Threads の1投稿あたり文字数上限

NOW = dt.datetime.now(dt.timezone.utc)
DRY_RUN = os.environ.get("DRY_RUN") == "1"
REFRESH_BEFORE = dt.timedelta(days=int(os.environ.get("REFRESH_BEFORE_DAYS", "10")))


# ---- コンテンツ抽出(各アカウントのカーソルを進めつつ、今回の投稿分を返す) ----

def training_pick(acc):
    """training アカウント: ローテーションで次カテゴリの6語チャンクを返す。

    acc に rotation / rot_index / cursors(カテゴリ別・語インデックス) を持つ。
    未設定なら既定値で初期化する。
    """
    rotation = acc.get("rotation") or list(ftp.ROTATION)
    acc["rotation"] = rotation
    rot = int(acc.get("rot_index", 0)) % len(rotation)
    cat = rotation[rot]
    words = ftp.load_words(cat)
    cursors = acc.setdefault("cursors", {})
    cur = int(cursors.get(cat, 0)) % len(words)
    rows = ftp.pick_chunk(words, cur)
    # 前進
    cursors[cat] = (cur + ftp.WORDS_PER_POST) % len(words)
    acc["rot_index"] = (rot + 1) % len(rotation)
    text = ftp.build_post(cat, rows)
    meta = {"slug": ftp.TRAINING[cat]["slug"], "first_id": rows[0]["id"],
            "total": len(words), "words": [r["word"] for r in rows]}
    return {"posts": [text], "kind": "training", "meta": meta,
            "label": f"training:{cat} cursor={cur}/{len(words)}"}


def vocab_pick(content_key, acc):
    rows_all = load_rows(content_key)
    chunks = chunk_rows(rows_all)  # 5語ずつ
    total = len(chunks)
    cur = int(acc.get("cursor", 0)) % total
    rows = chunks[cur]
    acc["cursor"] = (cur + 1) % total
    text = build_vocab_post(content_key, rows)
    meta = {"set": content_key, "first_id": rows[0]["id"], "total": len(rows_all),
            "words": [r["term"] for r in rows]}
    return {"posts": [text], "kind": "vocab", "meta": meta,
            "label": f"{content_key} cursor={cur}/{total}"}


def reading_pick(acc):
    items = [it for _, it in reading.load_items() if it.get("status") != "rejected"]
    items.sort(key=lambda x: x["id"])
    total = len(items)
    cur = int(acc.get("cursor", 0)) % total
    it = items[cur]
    acc["cursor"] = (cur + 1) % total
    posts = reading.build_posts(it, limit=THREADS_LIMIT, length_fn=len)  # 親+解説
    meta = {"id": it["id"], "total": total}
    return {"posts": posts, "kind": "reading", "meta": meta,
            "label": f"reading cursor={cur}/{total} id={it['id']}"}


def build_current(acc):
    content_key = acc["content"]
    if content_key == "training":
        return training_pick(acc)
    if content_key in ("uscpa", "legal"):
        return vocab_pick(content_key, acc)
    if content_key == "reading":
        return reading_pick(acc)
    raise ValueError(f"未知のコンテンツ種別: {content_key}")


# ---- トークン延命 ----

def maybe_refresh(name, acc):
    if DRY_RUN:  # 副作用を避けるためリフレッシュしない
        return False
    exp = acc.get("expires_at")
    need = True
    if exp:
        try:
            expires = dt.datetime.fromisoformat(exp)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=dt.timezone.utc)
            need = (expires - NOW) <= REFRESH_BEFORE
        except ValueError:
            need = True
    if not need:
        return False
    try:
        res = tc.refresh_token(acc["token"])
        acc["token"] = res["access_token"]
        secs = int(res.get("expires_in", 60 * 24 * 3600))
        acc["expires_at"] = (NOW + dt.timedelta(seconds=secs)).isoformat()
        print(f"[{name}] トークンをリフレッシュ(新期限 {acc['expires_at']})")
        return True
    except tc.ThreadsError as e:
        print(f"[{name}] リフレッシュskip: {e}")
        return False


# ---- 遅延サイト誘導リプライ(前回投稿へ) ----

def do_referral(name, acc):
    """前回投稿(last_post)が未リプライなら、そのツリーの末尾に誘導リプライをぶら下げる。

    ベストエフォート: 失敗しても本投稿は続行し、無限リトライを避けるため
    以後は replied=True にして諦める(親削除=media_not_found 等を想定)。
    """
    lp = acc.get("last_post")
    if not lp or lp.get("replied"):
        return False
    text = build_referral(lp["kind"], lp["meta"])
    if DRY_RUN:
        print(f"[{name}] (DRY_RUN 誘導リプライ)\n  " + text.replace("\n", "\n  "))
        return False
    # ツリーの末尾へぶら下げる(読解は親+解説の複数投稿。先頭に付けると
    # 解説より前に誘導が挟まって読む順序が崩れる)。tail_id が無い古い状態は root_id で代替。
    parent_id = lp.get("tail_id") or lp["root_id"]
    try:
        rid = tc.post_text(acc["user_id"], acc["token"], text, reply_to_id=parent_id)
        lp["replied"] = True
        lp["reply_id"] = rid
        print(f"[{name}] 誘導リプライ完了 reply_id={rid}")
    except tc.ThreadsError as e:
        lp["replied"] = True  # 諦めて次へ(親が消えている等)
        print(f"[{name}] 誘導リプライskip: {e}")
    return True


# ---- 1アカウントの処理 ----

def post_account(name, acc):
    cur = build_current(acc)
    label = f"[{name}] {cur['label']}"
    if DRY_RUN:
        print(f"{label} (DRY_RUN 投稿せず)")
        for i, p in enumerate(cur["posts"]):
            print(f"  --- part {i + 1} ---")
            print("  " + p.replace("\n", "\n  "))
    else:
        ids = tc.post_thread(acc["user_id"], acc["token"], cur["posts"])
        print(f"{label} 投稿完了 media_ids={ids}")
        # 次回の誘導用に記録。root_id=親(先頭)、tail_id=ツリー末尾(誘導リプライのぶら下げ先)
        acc["last_post"] = {
            "kind": cur["kind"], "meta": cur["meta"],
            "root_id": ids[0], "tail_id": ids[-1], "replied": False,
            "posted_at": NOW.isoformat(),
        }


def main():
    state = gist_state.load_state()
    accounts = state.get("accounts", {})
    only = os.environ.get("ACCOUNTS")
    targets = [a.strip() for a in only.split(",")] if only else list(accounts)

    changed = False
    errors = []
    for name in targets:
        acc = accounts.get(name)
        if not acc:
            print(f"[{name}] 状態に存在しないためskip")
            continue
        try:
            if do_referral(name, acc):
                changed = True
            if maybe_refresh(name, acc):
                changed = True
            post_account(name, acc)
            changed = True
        except Exception as e:  # 1アカウントの失敗で他を止めない
            errors.append(name)
            print(f"[{name}] 失敗: {e}")
            traceback.print_exc()

    if changed and not DRY_RUN:
        gist_state.save_state(state)
        print("状態を Gist へ保存しました")
    elif DRY_RUN:
        print("DRY_RUN のため Gist は更新しません")

    if errors:
        print(f"失敗したアカウント: {errors}")
        sys.exit(1)


if __name__ == "__main__":
    main()
