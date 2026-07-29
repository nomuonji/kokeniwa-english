# -*- coding: utf-8 -*-
"""サイト誘導リプライの本文を組み立てる(kokeniwa-english 用)。

本投稿の約1サイクル後(次回実行時)に、前回投稿へぶら下げる誘導リプライを作る。
構成は「今日の単語おぼえてる？(自己テスト)」＋「無料の単語帳/学習サイトへ誘導」。
毎回同じ定型文だと bot 判定されやすいので、書き出し(hook)と締め(cta)を
複数候補からランダムに選び、単語の並びと合わせて投稿ごとに文面を変える。

リンク先は該当カード/問題へのディープリンク(サイト側が該当箇所へスクロール&強調):
  - 一般英単語(training) : /training/{slug}/#w{先頭id}
  - 専門英単語(vocab)    : /vocab/{set}/#w{先頭id}
  - 英文解釈(reading)    : /reading/{id}/

将来 独自ドメインへ移行する際は PAGES_BASE(または環境変数 PAGES_BASE)のみ変更。
"""
import os
import random

PAGES_BASE = os.environ.get("PAGES_BASE", "https://en.kokeniwa.net").rstrip("/")

# --- 単語系(training / vocab)。{n}=語数, {total}=総語数, {url}=一覧ページ ---
WORD_HOOKS = [
    "今日の単語、もう覚えた？🤔",
    "この{n}語、意味をパッと言える？",
    "復習タイム！意味を思い出せるかチェック✍️",
    "サッと自己テスト👀 意味わかる？",
    "寝る前にもう一度、今日の単語👇",
    "昨日の{n}語、まだ言える？🧠",
]
WORD_CTAS = [
    "意味の確認＆全{total}語の単語帳はこちら👇\n{url}",
    "答え合わせは無料の単語帳で👇\n{url}",
    "全{total}語まとめて復習できます（無料）👇\n{url}",
    "続きは無料フラッシュカードで👇\n{url}",
]

# --- 英文解釈(reading)。{total}=総問題数, {url}=この問題のページ ---
#
# 誘導リプライはツリーの末尾（訳・解説のあと）にぶら下がる。
# 読み手はすでに答えを見た状態なので、「答え合わせしよう」ではなく
# 「あとで解き直す／他の問題も解く」導線として書く。
# サイトに載せているのは英文・設問・正解・全文訳まで（詳しい解説はKindle版のみ）なので、
# 「解説はサイトで」とは書かないこと。
READING_HOOKS = [
    "この一文、時間をおいてもう一度読むと定着します。",
    "「読めたつもり」を潰すには、日をあけて解き直すのが確実です。",
    "同じ構造でまたつまずかないように、復習用のページを置いています。",
    "解説を読んだ直後より、明日もう一度読んだときのほうが力になります。",
    "この形の英文、まだまだあります。",
    "構造が見えると、読み返しが減って読むのが速くなります。",
]
READING_CTAS = [
    "▼この問題を解き直す（英文・設問・全文訳／無料）\n{url}\n\n"
    "同じ形式の問題を全{total}問、無料で公開しています。",
    "▼この問題のページ（無料）\n{url}\n\n"
    "倒置・省略・比較など21カテゴリ、全{total}問。苦手なところから解けます。",
    "▼あとで解き直す用にどうぞ（無料）\n{url}\n\n"
    "全{total}問。1問1分、通勤中にひとつずつ。",
    "▼問題ページはこちら（無料・登録不要）\n{url}\n\n"
    "全{total}問をカテゴリ別に公開中。過去の問題もすべて残しています。",
]


def _word_referral(url, words, total):
    hook = random.choice(WORD_HOOKS).format(n=len(words), total=total)
    cta = random.choice(WORD_CTAS).format(total=total, url=url)
    body = "\n".join(words)
    return f"{hook}\n\n{body}\n\n{cta}"


def build_referral(kind, meta):
    """kind と meta から誘導リプライ本文を返す。

    meta:
      training : {"slug","first_id","total","words":[...]}
      vocab    : {"set","first_id","total","words":[...]}
      reading  : {"id","total"}
    """
    if kind == "training":
        url = f"{PAGES_BASE}/training/{meta['slug']}/#w{meta['first_id']}"
        return _word_referral(url, meta["words"], meta["total"])
    if kind == "vocab":
        url = f"{PAGES_BASE}/vocab/{meta['set']}/#w{meta['first_id']}"
        return _word_referral(url, meta["words"], meta["total"])
    if kind == "reading":
        url = f"{PAGES_BASE}/reading/{meta['id']}/"
        hook = random.choice(READING_HOOKS)
        cta = random.choice(READING_CTAS).format(total=meta["total"], url=url)
        return f"{hook}\n\n{cta}"
    raise ValueError(f"未知の誘導種別: {kind}")
