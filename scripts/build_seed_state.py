# -*- coding: utf-8 -*-
"""Gist に貼り付ける初期状態 JSON を生成する(ローカルで一度だけ実行)。

トークンは引数ではなく標準入力(1行1トークン: uscpa, legal, reading の順)で渡す。
user_id は Threads API から自動取得する。出力は標準出力。

使い方(PowerShell):
    Get-Content tokens.txt | python scripts/build_seed_state.py > seed_state.json
使い方(bash):
    printf '%s\n%s\n%s\n' "$T1" "$T2" "$T3" | python scripts/build_seed_state.py > seed_state.json

生成後、seed_state.json の中身を「シークレット Gist」に threads_state.json として貼り、
ローカルの seed_state.json は削除すること(トークンを含むため)。
"""
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import threads_client as tc

ORDER = [
    ("uscpa", "uscpa"),
    ("legal", "legal"),
    ("reading", "reading"),
]


def main():
    tokens = [ln.strip() for ln in sys.stdin if ln.strip()]
    if len(tokens) != 3:
        sys.exit(f"3 行のトークンが必要です(uscpa, legal, reading の順)。受領: {len(tokens)}")
    accounts = {}
    for (name, content), token in zip(ORDER, tokens):
        me = tc.get_me(token)
        accounts[name] = {
            "content": content,
            "token": token,
            "user_id": me["id"],
            "username": me.get("username", ""),
            "expires_at": None,  # 初回実行時にリフレッシュして確定
            "cursor": 0,
        }
        print(f"# {name}: @{me.get('username')} ({me['id']})", file=sys.stderr)
    print(json.dumps({"accounts": accounts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
