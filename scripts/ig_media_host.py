# -*- coding: utf-8 -*-
"""Instagram に渡す画像を、このリポジトリの ig-media ブランチへ置いて公開URLを返す。

Instagram の投稿APIは画像を「公開URL」で受け取り、Meta 側が取りに来る。
専用サーバーを持たずに済むよう、GitHub の公開リポジトリを一時置き場に使う。

- GitHub Actions の GITHUB_TOKEN(contents: write)で Git Data API を叩く
- 毎回「親なしの新しいコミット(今回の画像だけ)」を作り、ig-media を強制更新する
  → ブランチには常に直近1回分しか残らず、リポジトリが肥大化しない
- URL はコミットSHA固定の raw.githubusercontent.com(後から書き換わらない)

Instagram はコンテナ作成時に画像を取り込むので、投稿後に消えても問題ない。

環境変数: GITHUB_TOKEN, GITHUB_REPOSITORY(Actions が自動で設定)
"""
import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
BRANCH = os.environ.get("IG_MEDIA_BRANCH", "ig-media")


class HostError(RuntimeError):
    pass


def _gh(method, path, payload=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise HostError("GITHUB_TOKEN が未設定(ワークフローの env を確認)")
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 404 and method == "GET":
            return None
        raise HostError(f"GitHub API {e.code} {method} {path}: {e.read().decode(errors='replace')}") from None


def upload(paths, folder):
    """paths の画像を ig-media/{folder}/ に置き、公開URLのリストを返す。"""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise HostError("GITHUB_REPOSITORY が未設定")
    tree = []
    for p in paths:
        p = Path(p)
        blob = _gh("POST", f"/repos/{repo}/git/blobs",
                   {"content": base64.b64encode(p.read_bytes()).decode(), "encoding": "base64"})
        tree.append({"path": f"{folder}/{p.name}", "mode": "100644", "type": "blob", "sha": blob["sha"]})
    t = _gh("POST", f"/repos/{repo}/git/trees", {"tree": tree})
    commit = _gh("POST", f"/repos/{repo}/git/commits",
                 {"message": f"ig-media: {folder}", "tree": t["sha"], "parents": []})
    sha = commit["sha"]
    if _gh("GET", f"/repos/{repo}/git/ref/heads/{BRANCH}"):
        _gh("PATCH", f"/repos/{repo}/git/refs/heads/{BRANCH}", {"sha": sha, "force": True})
    else:
        _gh("POST", f"/repos/{repo}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": sha})
    return [f"https://raw.githubusercontent.com/{repo}/{sha}/{e['path']}" for e in tree]
