# -*- coding: utf-8 -*-
"""Instagram API with Instagram Login の薄いクライアント(標準ライブラリのみ)。

- 画像カルーセル投稿(子コンテナ作成 → カルーセルコンテナ → 公開)
- 長期トークンの延命
- アカウント情報取得

前提: プロアカウント(ビジネス/クリエイター)と、権限
instagram_business_basic / instagram_business_content_publish を持つユーザートークン。
画像は Meta 側が URL を取りに来るので、公開 URL の JPEG であること。
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.instagram.com"
VERSION = "v23.0"
API = f"{GRAPH}/{VERSION}"
CAROUSEL_MAX = 10  # API 上限は20だが、アプリ表示との互換のため10枚に抑える


class InstagramError(RuntimeError):
    pass


def _request(method, url, data=None, timeout=60):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise InstagramError(f"HTTP {e.code} {method} {url.split('?')[0]}: {detail}") from None


def get_me(token):
    url = f"{API}/me?" + urllib.parse.urlencode(
        {"fields": "user_id,username,account_type", "access_token": token})
    return _request("GET", url)


def refresh_token(token):
    """長期トークン(60日)を延命する。発行から24時間以上・未失効が条件。"""
    url = f"{GRAPH}/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": token})
    return _request("GET", url)


def publishing_limit(user_id, token):
    url = f"{API}/{user_id}/content_publishing_limit?" + urllib.parse.urlencode(
        {"fields": "quota_usage,config", "access_token": token})
    return _request("GET", url)


def _create(user_id, token, params):
    res = _request("POST", f"{API}/{user_id}/media", {**params, "access_token": token})
    if "id" not in res:
        raise InstagramError(f"コンテナ作成に id が無い: {res}")
    return res["id"]


def _wait_finished(container_id, token, timeout=300, interval=5):
    """コンテナの処理完了(FINISHED)を待つ。ERROR / EXPIRED なら例外。"""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        url = f"{API}/{container_id}?" + urllib.parse.urlencode(
            {"fields": "status_code,status", "access_token": token})
        res = _request("GET", url)
        last = res
        code = res.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise InstagramError(f"コンテナ {container_id} が {code}: {res.get('status')}")
        time.sleep(interval)
    raise InstagramError(f"コンテナ {container_id} の処理待ちがタイムアウト: {last}")


def publish_carousel(user_id, token, image_urls, caption):
    """image_urls(公開JPEGのURL、2〜10枚)をカルーセルとして公開し media id を返す。"""
    urls = list(image_urls)[:CAROUSEL_MAX]
    if len(urls) < 2:
        return publish_image(user_id, token, urls[0], caption)
    children = []
    for u in urls:
        cid = _create(user_id, token, {"image_url": u, "is_carousel_item": "true"})
        children.append(cid)
    for cid in children:
        _wait_finished(cid, token)
    parent = _create(user_id, token, {
        "media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
    _wait_finished(parent, token)
    res = _request("POST", f"{API}/{user_id}/media_publish",
                   {"creation_id": parent, "access_token": token})
    if "id" not in res:
        raise InstagramError(f"公開に id が無い: {res}")
    return res["id"]


def publish_image(user_id, token, image_url, caption):
    cid = _create(user_id, token, {"image_url": image_url, "caption": caption})
    _wait_finished(cid, token)
    res = _request("POST", f"{API}/{user_id}/media_publish",
                   {"creation_id": cid, "access_token": token})
    if "id" not in res:
        raise InstagramError(f"公開に id が無い: {res}")
    return res["id"]


def get_permalink(media_id, token):
    url = f"{API}/{media_id}?" + urllib.parse.urlencode(
        {"fields": "permalink", "access_token": token})
    try:
        return _request("GET", url).get("permalink")
    except InstagramError:
        return None
