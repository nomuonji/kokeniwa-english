# -*- coding: utf-8 -*-
"""Threads アカウントに Instagram を紐づける / 止める / 状態を見る(Gist の状態を更新)。

ワークフロー「Instagram 連携」(instagram-link.yml)から実行する想定。
トークンはワークフロー入力(ログに残る)ではなく、一時的な Secret IG_LINK_TOKEN で渡す。

環境変数:
  ACTION      : link / enable / disable / status
  ACCOUNT     : Threads 側のアカウント名(Gist の accounts のキー。例: uscpa)
  IG_TOKEN    : (link のとき)Instagram の長期ユーザートークン
  GH_GIST_TOKEN, GIST_ID : Gist アクセス
"""
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gist_state
import instagram_client as ic

NOW = dt.datetime.now(dt.timezone.utc)


def _summary(name, acc):
    ig = acc.get("instagram")
    if not ig:
        return f"{name:<12} Threads @{acc.get('username', '?'):<28} Instagram: 未連携"
    state = "ON " if ig.get("enabled") else "OFF"
    last = ig.get("last_posted_at") or "-"
    err = f"  最終エラー: {ig['last_error'][:120]}" if ig.get("last_error") else ""
    return (f"{name:<12} Threads @{acc.get('username', '?'):<28} Instagram: {state} @{ig.get('username')}"
            f"  期限 {ig.get('expires_at') or '?'}  最終投稿 {last}{err}")


def main():
    action = os.environ.get("ACTION", "status").strip()
    name = os.environ.get("ACCOUNT", "").strip()
    state = gist_state.load_state()
    accounts = state.get("accounts", {})

    if action == "status":
        for n, acc in accounts.items():
            print(_summary(n, acc))
        return

    if name not in accounts:
        sys.exit(f"アカウント '{name}' が状態にありません。候補: {', '.join(accounts)}")
    acc = accounts[name]

    if action == "link":
        token = os.environ.get("IG_TOKEN", "").strip()
        if not token:
            sys.exit("Secret IG_LINK_TOKEN が空です。Instagram のトークンを設定してから実行してください。")
        me = ic.get_me(token)
        if me.get("account_type") not in (None, "BUSINESS", "MEDIA_CREATOR", "CREATOR"):
            sys.exit(f"プロアカウントではありません(account_type={me.get('account_type')})。")
        others = [n for n, a in accounts.items()
                  if n != name and (a.get("instagram") or {}).get("user_id") == me["user_id"]]
        if others:
            sys.exit(f"@{me.get('username')} は既に {others} に紐づいています(1対1運用のため中止)。")
        ig = acc.get("instagram") or {}
        ig.update({"user_id": str(me["user_id"]), "username": me.get("username", ""),
                   "token": token, "expires_at": None, "enabled": True, "last_error": None,
                   "linked_at": NOW.isoformat()})
        try:  # 発行24時間以内は延命できないので失敗しても続行(次回投稿時に再試行)
            res = ic.refresh_token(token)
            ig["token"] = res["access_token"]
            ig["expires_at"] = (NOW + dt.timedelta(seconds=int(res.get("expires_in", 60 * 86400)))).isoformat()
        except ic.InstagramError as e:
            print(f"(延命は次回に持ち越し: {e})")
        try:
            lim = ic.publishing_limit(ig["user_id"], ig["token"])
            print(f"投稿枠: {lim}")
        except ic.InstagramError as e:
            print(f"(投稿枠の確認に失敗: {e})")
        acc["instagram"] = ig
        print(f"連携しました: {name} (Threads @{acc.get('username')}) → Instagram @{ig['username']}")
    elif action in ("enable", "disable"):
        if not acc.get("instagram"):
            sys.exit(f"{name} は Instagram 未連携です。先に link を実行してください。")
        acc["instagram"]["enabled"] = action == "enable"
        print(f"{name}: Instagram 投稿を {'ON' if action == 'enable' else 'OFF'} にしました")
    else:
        sys.exit(f"未知の ACTION: {action}")

    gist_state.save_state(state)
    print(_summary(name, acc))


if __name__ == "__main__":
    main()
