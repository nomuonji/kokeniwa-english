# -*- coding: utf-8 -*-
"""Threads 3アカウント自動投稿のオーケストレーター(GitHub Actions から実行)。

処理の流れ:
  1. Gist から状態(トークン・カーソル等)を読む
  2. 各アカウントについて
       - 期限が近ければトークンをリフレッシュ
       - カーソル位置のコンテンツを1件投稿(読解はツリー投稿)
       - カーソルを1つ進める
  3. 状態を Gist へ書き戻す

環境変数:
  GH_GIST_TOKEN, GIST_ID           : Gist アクセス(gist_state.py が使用)
  DRY_RUN=1                        : 実投稿せず内容を表示するだけ
  ACCOUNTS="uscpa,legal"           : (任意) 対象アカウントを限定
  REFRESH_BEFORE_DAYS=10           : (任意) 期限が何日以内でリフレッシュするか
"""
import csv
import datetime as dt
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gist_state
import threads_client as tc
from format_vocab_post import build_post as build_vocab_post, load_rows, chunk_rows
import format_reading_post as reading

THREADS_LIMIT = 500  # Threads の1投稿あたり文字数上限

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NOW = dt.datetime.now(dt.timezone.utc)
DRY_RUN = os.environ.get("DRY_RUN") == "1"
REFRESH_BEFORE = dt.timedelta(days=int(os.environ.get("REFRESH_BEFORE_DAYS", "10")))


def build_items(content_key):
    """content_key に応じ、投稿単位のリストを返す。各要素は「投稿文字列のリスト」。"""
    if content_key in ("uscpa", "legal"):
        chunks = chunk_rows(load_rows(content_key))  # 5語ずつ = 1投稿
        return [[build_vocab_post(content_key, ch)] for ch in chunks]
    if content_key == "reading":
        items = [it for _, it in reading.load_items() if it.get("status") != "rejected"]
        items.sort(key=lambda x: x["id"])
        # Threads(500字・素の文字数)基準で「親+返信1」に統合
        return [reading.build_posts(it, limit=THREADS_LIMIT, length_fn=len) for it in items]
    raise ValueError(f"未知のコンテンツ種別: {content_key}")


def maybe_refresh(name, acc):
    """必要ならトークンをリフレッシュして acc を更新。変更があれば True。"""
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
        # 発行24時間未満などで失敗しても投稿は続行(次回以降に再試行)
        print(f"[{name}] リフレッシュskip: {e}")
        return False


def post_account(name, acc):
    content_key = acc["content"]
    items = build_items(content_key)
    total = len(items)
    cursor = int(acc.get("cursor", 0)) % total
    posts = items[cursor]
    label = f"[{name}/{content_key}] cursor={cursor}/{total}"

    if DRY_RUN:
        print(f"{label} (DRY_RUN 投稿せず)")
        for i, p in enumerate(posts):
            print(f"  --- part {i + 1} ---")
            print("  " + p.replace("\n", "\n  "))
    else:
        ids = tc.post_thread(acc["user_id"], acc["token"], posts)
        print(f"{label} 投稿完了 media_ids={ids}")

    acc["cursor"] = (cursor + 1) % total


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
