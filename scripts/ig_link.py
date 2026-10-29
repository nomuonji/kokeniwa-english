# -*- coding: utf-8 -*-
"""Threads アカウントに Instagram を紐づける / 止める / 状態を見る。

トークンの扱いは Threads と同じ:
  - トークンは引数・環境変数・Actions Secret に置かず、標準入力で渡してローカルで実行する
  - 保存先は状態 Gist(threads_state.json)の accounts.<name>.instagram だけ
  - 以後の延命(60日)は自動投稿のたびに Gist 上で行う

使い方(ローカル。リポジトリのルートで):

  紐づけ(1行に「Threadsアカウント名 トークン」。複数行で一度に複数アカウント):
    printf 'uscpa %s\\nreading %s\\n' "$IG_USCPA" "$IG_READING" | python scripts/ig_link.py link

    - GH_GIST_TOKEN と GIST_ID が環境にあれば Gist を直接更新する
    - 無ければ、Gist に貼り付ける instagram ブロック(JSON)を表示するだけ
      (build_seed_state.py と同じく、表示内容にトークンが含まれるので扱いに注意)

  状態 / 一時停止 / 再開(トークン不要。Actions の「Instagram 連携」からも実行できる):
    python scripts/ig_link.py status
    python scripts/ig_link.py disable uscpa
    python scripts/ig_link.py enable uscpa
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gist_state
import instagram_client as ic

NOW = dt.datetime.now(dt.timezone.utc)


def _summary(name, acc):
    ig = acc.get("instagram")
    head = f"{name:<12} Threads @{acc.get('username', '?'):<30}"
    if not ig:
        return f"{head} Instagram: 未連携"
    state = "ON " if ig.get("enabled") else "OFF"
    err = f"\n{'':<14}最終エラー: {ig['last_error'][:160]}" if ig.get("last_error") else ""
    return (f"{head} Instagram: {state} @{ig.get('username')}  期限 {ig.get('expires_at') or '?'}"
            f"  最終投稿 {ig.get('last_posted_at') or '-'}{err}")


def _build_block(token):
    """トークンを検証し、Gist に入れる instagram ブロックを作る。"""
    me = ic.get_me(token)
    if me.get("account_type") not in (None, "BUSINESS", "MEDIA_CREATOR", "CREATOR"):
        raise SystemExit(f"@{me.get('username')} はプロアカウントではありません(account_type={me.get('account_type')})")
    block = {"user_id": str(me["user_id"]), "username": me.get("username", ""), "token": token,
             "expires_at": None, "enabled": True, "last_error": None, "linked_at": NOW.isoformat()}
    try:  # 発行24時間以内は延命できない。その場合は最初の自動投稿時に延命される
        res = ic.refresh_token(token)
        block["token"] = res["access_token"]
        block["expires_at"] = (NOW + dt.timedelta(seconds=int(res.get("expires_in", 60 * 86400)))).isoformat()
    except ic.InstagramError as e:
        print(f"  (延命は次回の自動投稿時に: {str(e)[:120]})", file=sys.stderr)
    return block


def cmd_link():
    pairs = []
    for ln in sys.stdin:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split()
        if len(parts) != 2:
            raise SystemExit("標準入力は1行に「Threadsアカウント名 トークン」の形で渡してください")
        pairs.append(parts)
    if not pairs:
        raise SystemExit("標準入力が空です")

    can_write = os.environ.get("GH_GIST_TOKEN") and os.environ.get("GIST_ID")
    state = gist_state.load_state() if can_write or os.environ.get("LOCAL_STATE_FILE") else None
    accounts = (state or {}).get("accounts", {})
    blocks = {}
    for name, token in pairs:
        if state is not None and name not in accounts:
            raise SystemExit(f"'{name}' は状態にありません。候補: {', '.join(accounts)}")
        block = _build_block(token)
        taken = [n for n, a in accounts.items()
                 if n != name and (a.get("instagram") or {}).get("user_id") == block["user_id"]]
        taken += [n for n, b in blocks.items() if b["user_id"] == block["user_id"]]
        if taken:
            raise SystemExit(f"@{block['username']} は既に {taken} に紐づいています(1対1運用のため中止)")
        blocks[name] = block
        print(f"OK: {name} → Instagram @{block['username']} (user_id {block['user_id']})", file=sys.stderr)

    if state is None:
        print("\n# Gist の threads_state.json で、各アカウントに次の \"instagram\" を追加してください:",
              file=sys.stderr)
        print(json.dumps({n: {"instagram": b} for n, b in blocks.items()}, ensure_ascii=False, indent=2))
        return
    for name, block in blocks.items():
        old = accounts[name].get("instagram") or {}
        accounts[name]["instagram"] = {**old, **block}
    gist_state.save_state(state)
    print("Gist を更新しました", file=sys.stderr)
    for name in blocks:
        print(_summary(name, accounts[name]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", nargs="?", default=os.environ.get("ACTION", "status"),
                    choices=["link", "status", "enable", "disable"])
    ap.add_argument("account", nargs="?", default=os.environ.get("ACCOUNT", ""))
    args = ap.parse_args()

    if args.action == "link":
        return cmd_link()

    state = gist_state.load_state()
    accounts = state.get("accounts", {})
    if args.action == "status":
        for n, acc in accounts.items():
            print(_summary(n, acc))
        return
    name = args.account.strip()
    acc = accounts.get(name)
    if not acc:
        raise SystemExit(f"'{name}' は状態にありません。候補: {', '.join(accounts)}")
    if not acc.get("instagram"):
        raise SystemExit(f"{name} は Instagram 未連携です(先に link)")
    acc["instagram"]["enabled"] = args.action == "enable"
    gist_state.save_state(state)
    print(_summary(name, acc))


if __name__ == "__main__":
    main()
