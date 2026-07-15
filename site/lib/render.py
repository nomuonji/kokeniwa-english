"""レンダリング補助。エスケープ・書き出し・ページ分割。"""
import html

from . import config


def esc(value):
    """HTMLエスケープ。全ての動的値はこれを通す。"""
    return html.escape(str(value), quote=True)


def write_page(path, content):
    """dist/ 配下の path（例 'reading/1/index.html'）にHTMLを書き出す。"""
    out = config.DIST_DIR / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")
    return out


def paginate(items, page_size):
    """itemsを page_size ごとのリストに分割して返す（最低1ページ）。"""
    if not items:
        return [[]]
    return [items[i:i + page_size] for i in range(0, len(items), page_size)]
