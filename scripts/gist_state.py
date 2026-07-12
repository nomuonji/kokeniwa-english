# -*- coding: utf-8 -*-
"""GitHub Gist を状態ストアとして読み書きする(標準ライブラリのみ)。

Gist 内の 1 ファイル(既定 threads_state.json)に、全アカウントの
トークン・user_id・expires_at・投稿カーソルを JSON で保持する。
環境変数トークンを避け、更新のたびに Gist を上書きする運用のため。

必要な環境変数:
    GH_GIST_TOKEN : gist スコープ付きの GitHub Personal Access Token
    GIST_ID       : 対象 Gist の ID
    GIST_FILENAME : (任意) 既定 "threads_state.json"
"""
import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"
DEFAULT_FILENAME = "threads_state.json"


def _env(name, required=True, default=None):
    val = os.environ.get(name, default)
    if required and not val:
        raise RuntimeError(f"環境変数 {name} が未設定です")
    return val


def _request(method, url, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API {e.code} {method} {url}: {detail}") from None


def load_state():
    local = os.environ.get("LOCAL_STATE_FILE")
    if local:  # ローカル検証用: Gist の代わりにファイルを読む
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    token = _env("GH_GIST_TOKEN")
    gist_id = _env("GIST_ID")
    filename = _env("GIST_FILENAME", required=False, default=DEFAULT_FILENAME)
    gist = _request("GET", f"{API}/gists/{gist_id}", token)
    files = gist.get("files", {})
    if filename not in files:
        raise RuntimeError(f"Gist に {filename} が見つかりません。存在: {list(files)}")
    content = files[filename]["content"]
    return json.loads(content)


def save_state(state):
    local = os.environ.get("LOCAL_STATE_FILE")
    if local:
        with open(local, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return
    token = _env("GH_GIST_TOKEN")
    gist_id = _env("GIST_ID")
    filename = _env("GIST_FILENAME", required=False, default=DEFAULT_FILENAME)
    payload = {
        "files": {filename: {"content": json.dumps(state, ensure_ascii=False, indent=2)}}
    }
    _request("PATCH", f"{API}/gists/{gist_id}", token, payload)
