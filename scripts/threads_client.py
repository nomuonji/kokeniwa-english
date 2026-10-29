# -*- coding: utf-8 -*-
"""Threads Graph API の薄いクライアント(標準ライブラリのみ)。

- 単発テキスト投稿 / ツリー投稿(リプライ連結)
- 長期トークンのリフレッシュ
- アカウント情報取得

依存パッケージなし。GitHub Actions ランナーの素の Python で動く。
"""
import json
import time
import urllib.parse
import urllib.request

GRAPH = "https://graph.threads.net"
API = f"{GRAPH}/v1.0"


class ThreadsError(RuntimeError):
    pass


def _request(method, url, data=None, timeout=30):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise ThreadsError(f"HTTP {e.code} {method} {url.split('?')[0]}: {detail}") from None


def get_me(token, fields="id,username,name"):
    url = f"{API}/me?" + urllib.parse.urlencode({"fields": fields, "access_token": token})
    return _request("GET", url)


def refresh_token(token):
    """長期トークンを延命し {'access_token','expires_in',...} を返す。

    条件: トークンが発行から24時間以上経過・未失効であること。
    満たさない場合は ThreadsError。
    """
    url = f"{GRAPH}/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "th_refresh_token", "access_token": token}
    )
    return _request("GET", url)


def _create_container(user_id, token, text, reply_to_id=None):
    data = {"media_type": "TEXT", "text": text, "access_token": token}
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    res = _request("POST", f"{API}/{user_id}/threads", data)
    if "id" not in res:
        raise ThreadsError(f"コンテナ作成に id が無い: {res}")
    return res["id"]


def _publish(user_id, token, creation_id, retries=4, wait=6):
    """コンテナを公開。処理待ちのため数回リトライして media id を返す。"""
    last = None
    for attempt in range(retries):
        time.sleep(wait if attempt == 0 else wait * 2)
        try:
            res = _request(
                "POST",
                f"{API}/{user_id}/threads_publish",
                {"creation_id": creation_id, "access_token": token},
            )
            if "id" in res:
                return res["id"]
            last = res
        except ThreadsError as e:
            last = e  # メディア未処理(コード9007等)ならリトライ
    raise ThreadsError(f"公開に失敗(creation_id={creation_id}): {last}")


def post_text(user_id, token, text, reply_to_id=None):
    """単発テキスト投稿。公開された media id を返す。"""
    cid = _create_container(user_id, token, text, reply_to_id=reply_to_id)
    return _publish(user_id, token, cid)


def post_thread(user_id, token, posts):
    """posts(文字列リスト)を親→リプライの順にツリー投稿し、全 media id を返す。"""
    ids = []
    reply_to = None
    for text in posts:
        mid = post_text(user_id, token, text, reply_to_id=reply_to)
        ids.append(mid)
        reply_to = mid  # 直前の投稿にぶら下げてスレッド化
    return ids
