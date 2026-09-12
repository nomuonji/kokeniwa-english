"""Template package shared setup."""

from templates import layout

# 長文の精読教材はブログとは別の学習導線として常設する。
_READING_ARTICLES_NAV = ("/reading/articles/", "リーディング")
if _READING_ARTICLES_NAV not in layout.NAV_ITEMS:
    reading_index = next((i for i, item in enumerate(layout.NAV_ITEMS) if item[0] == "/reading/"), 0)
    layout.NAV_ITEMS.insert(reading_index + 1, _READING_ARTICLES_NAV)
