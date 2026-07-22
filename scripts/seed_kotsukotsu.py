# -*- coding: utf-8 -*-
"""「こつこつ英単語」(training)アカウントを Gist 状態へ一度だけ登録する。

english-learner から引き継ぐもの:
  - トークン/ユーザーID  : english-learner/.env の THREADS_USER_ID / THREADS_ACCESS_TOKEN
  - 進捗(語インデックス)  : english-learner/.state/threads_progress.json の各 index
      news / drama / phrasal はその index から継続。idioms / eiken_pre1 は 0。

既定は内容表示のみ(Gist を変更しない)。実際に書き込むには --commit を付ける。

使い方:
    # 確認(Gist は変更しない)
    python scripts/seed_kotsukotsu.py --english-learner ../english-learner
    # 実行(Gist に書き込む。kokeniwa-english/.env の GH_GIST_TOKEN/GIST_ID を使用)
    python scripts/seed_kotsukotsu.py --english-learner ../english-learner --commit
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gist_state  # noqa: E402
import format_training_post as ftp  # noqa: E402

ACCOUNT_NAME = "kotsukotsu"
# english-learner の .state index を、引き継ぐカテゴリへ対応付ける
SEED_FROM_STATE = ["news", "drama", "phrasal"]  # これらは index を継続
FRESH = ["idioms", "eiken_pre1"]                 # 未投稿 → 0 から


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def build_cursors(el_state):
    cursors = {}
    for cat in SEED_FROM_STATE:
        idx = int(el_state.get(cat, {}).get("index", 0))
        words = ftp.load_words(cat)
        cursors[cat] = idx % len(words)
    for cat in FRESH:
        cursors[cat] = 0
    return cursors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--english-learner", default="../english-learner",
                    help="english-learner プロジェクトへのパス")
    ap.add_argument("--commit", action="store_true", help="実際に Gist へ書き込む")
    args = ap.parse_args()

    el = Path(args.english_learner).resolve()
    load_dotenv(HERE.parent / ".env")  # GH_GIST_TOKEN / GIST_ID

    # english-learner の認証情報と進捗を読む
    el_env = {}
    for line in (el / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            el_env[k.strip()] = v.strip()
    user_id = el_env["THREADS_USER_ID"]
    token = el_env["THREADS_ACCESS_TOKEN"]
    expires_at = el_env.get("THREADS_TOKEN_EXPIRES_AT") or \
        (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=50)).isoformat()

    el_state = json.loads((el / ".state" / "threads_progress.json").read_text(encoding="utf-8"))
    cursors = build_cursors(el_state)

    account = {
        "content": "training",
        "user_id": user_id,
        "token": token,
        "expires_at": expires_at,
        "rotation": list(ftp.ROTATION),
        "rot_index": 0,
        "cursors": cursors,
    }

    print(f"=== {ACCOUNT_NAME} アカウント(投入内容) ===")
    preview = dict(account, token=token[:8] + "…(masked)")
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    if not args.commit:
        print("\n(--commit 未指定のため Gist は変更しません)")
        return

    state = gist_state.load_state()
    accounts = state.setdefault("accounts", {})
    if ACCOUNT_NAME in accounts:
        print(f"\n既に {ACCOUNT_NAME} が存在します。cursors/rotation のみ更新し、token は既存を尊重します。")
        accounts[ACCOUNT_NAME].update({
            "content": "training", "rotation": account["rotation"],
            "rot_index": account["rot_index"], "cursors": account["cursors"],
        })
    else:
        accounts[ACCOUNT_NAME] = account
    gist_state.save_state(state)
    print(f"\nGist に {ACCOUNT_NAME} を登録しました。")


if __name__ == "__main__":
    main()
