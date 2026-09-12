# -*- coding: utf-8 -*-
"""Search Console と GA4 のデータを取得し、reports/ にレポートを書き出す。

記事の改稿・新規テーマ選定のための素材づくり。Claude(Claude Code)が
reports/latest.md を読めば、どの記事が伸びていて、どのクエリで
「表示はされているのに順位が低い＝改稿の余地がある」かが分かる。

前提(初回のみ。docs/セットアップ_解析連携.md を参照):
  - Google Cloud でサービスアカウントを作り、JSON鍵を .secrets/google-sa.json に置く
  - Search Console のプロパティにそのサービスアカウントを「制限付き」で追加
  - GA4 プロパティの「プロパティのアクセス管理」で閲覧者として追加
  - .env に GSC_SITE_URL / GA4_PROPERTY_ID を書く

依存: google-auth（`pip install google-auth`）。HTTPは標準ライブラリ。

使い方:
    python scripts/fetch_seo.py               # 直近28日
    python scripts/fetch_seo.py --days 90
    python scripts/fetch_seo.py --no-ga4      # Search Consoleだけ
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORT_DIR = ROOT / "reports"
SA_PATH_DEFAULT = ROOT / ".secrets" / "google-sa.json"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]
GSC_API = "https://searchconsole.googleapis.com/webmasters/v3"
GA4_API = "https://analyticsdata.googleapis.com/v1beta"

# Search Console はデータ確定まで2〜3日かかる。直近2日は空になるので除く。
GSC_LAG_DAYS = 3


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def get_token(sa_path):
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
    except ImportError:
        sys.exit("google-auth が入っていません: pip install google-auth requests")
    if not sa_path.is_file():
        sys.exit(f"サービスアカウントの鍵がありません: {sa_path}\n"
                 "docs/セットアップ_解析連携.md の手順1〜2を実施してください。")
    creds = service_account.Credentials.from_service_account_file(
        str(sa_path), scopes=SCOPES)
    creds.refresh(Request())
    return creds.token


def post(url, token, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code} {url}\n{detail}") from None


# --- Search Console ---------------------------------------------------------

def gsc_query(token, site_url, start, end, dimensions, limit=100, filters=None):
    payload = {
        "startDate": start, "endDate": end,
        "dimensions": dimensions, "rowLimit": limit, "dataState": "final",
    }
    if filters:
        payload["dimensionFilterGroups"] = [{"filters": filters}]
    url = f"{GSC_API}/sites/{urllib.parse.quote(site_url, safe='')}/searchAnalytics/query"
    rows = post(url, token, payload).get("rows", [])
    return [{
        # A totals query (dimensions=[]) comes back with no "keys" field.
        "keys": r.get("keys", []),
        "clicks": r["clicks"], "impressions": r["impressions"],
        "ctr": round(r["ctr"] * 100, 2), "position": round(r["position"], 1),
    } for r in rows]


# --- GA4 --------------------------------------------------------------------

def ga4_report(token, property_id, start, end, dimensions, metrics, limit=100):
    payload = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "limit": limit,
        "orderBys": [{"metric": {"metricName": metrics[0]}, "desc": True}],
    }
    url = f"{GA4_API}/properties/{property_id}:runReport"
    res = post(url, token, payload)
    out = []
    for r in res.get("rows", []):
        row = {d: v["value"] for d, v in zip(dimensions, r["dimensionValues"])}
        for m, v in zip(metrics, r["metricValues"]):
            val = v["value"]
            row[m] = round(float(val), 2) if "." in val else int(val)
        out.append(row)
    return out


# --- レポート整形 -----------------------------------------------------------

def table(headers, rows, aligns=None):
    aligns = aligns or ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(aligns) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"


def build_markdown(data):
    p = data["period"]
    md = [f"# SEOレポート {p['start']} 〜 {p['end']}（{p['days']}日間）", ""]
    md.append(f"生成: {data['generated_at']}／Search Console: {data['site_url']}")
    md.append("")

    g = data.get("gsc", {})
    if g:
        t = g["totals"]
        md.append("## サマリ（Search Console）\n")
        md.append(f"- クリック **{t['clicks']}** / 表示 **{t['impressions']}** "
                  f"/ CTR {t['ctr']}% / 平均掲載順位 {t['position']}")
        md.append("")

        md.append("## ページ別（クリック上位30）\n")
        md.append(table(["ページ", "クリック", "表示", "CTR%", "順位"],
                        [[r["keys"][0].replace(data["site_url"].rstrip("/"), ""),
                          r["clicks"], r["impressions"], r["ctr"], r["position"]]
                         for r in g["pages"][:30]]))

        md.append("## クエリ別（クリック上位30）\n")
        md.append(table(["検索クエリ", "クリック", "表示", "CTR%", "順位"],
                        [[r["keys"][0], r["clicks"], r["impressions"],
                          r["ctr"], r["position"]] for r in g["queries"][:30]]))

        md.append("## 改稿候補：表示は多いが順位が低いクエリ\n")
        md.append("表示100回以上・平均順位8位以下。あと一歩で1ページ目に入る、"
                  "または見出し/導入がクエリと噛み合っていない可能性がある。\n")
        cand = [r for r in g["queries"]
                if r["impressions"] >= 100 and r["position"] >= 8]
        cand.sort(key=lambda r: -r["impressions"])
        md.append(table(["検索クエリ", "表示", "クリック", "CTR%", "順位"],
                        [[r["keys"][0], r["impressions"], r["clicks"],
                          r["ctr"], r["position"]] for r in cand[:30]])
                  if cand else "該当なし。\n")

        md.append("## 改稿候補：順位は高いがCTRが低いページ\n")
        md.append("平均順位10位以内・CTR 2%未満。タイトルとdescriptionの"
                  "見直しで拾える見込み。\n")
        low = [r for r in g["pages"]
               if r["position"] <= 10 and r["ctr"] < 2 and r["impressions"] >= 50]
        md.append(table(["ページ", "表示", "クリック", "CTR%", "順位"],
                        [[r["keys"][0].replace(data["site_url"].rstrip("/"), ""),
                          r["impressions"], r["clicks"], r["ctr"], r["position"]]
                         for r in low[:20]])
                  if low else "該当なし。\n")

        md.append("## ブログ記事ごとの流入クエリ\n")
        for page, rows in g.get("blog_queries", {}).items():
            md.append(f"### {page}\n")
            md.append(table(["クエリ", "クリック", "表示", "CTR%", "順位"],
                            [[r["keys"][0], r["clicks"], r["impressions"],
                              r["ctr"], r["position"]] for r in rows[:10]]))

    a = data.get("ga4")
    if a:
        md.append("## アクセス（GA4）\n")
        md.append("### ページ別（表示回数上位30）\n")
        md.append(table(["ページ", "表示", "セッション", "エンゲージ率%", "平均滞在秒"],
                        [[r["pagePath"], r["screenPageViews"], r["sessions"],
                          round(r.get("engagementRate", 0) * 100, 1),
                          r.get("averageSessionDuration", 0)]
                         for r in a["pages"][:30]]))
        md.append("### 流入チャネル\n")
        md.append(table(["チャネル", "セッション", "エンゲージ率%"],
                        [[r["sessionDefaultChannelGroup"], r["sessions"],
                          round(r.get("engagementRate", 0) * 100, 1)]
                         for r in a["channels"]]))

    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=28, help="集計期間（既定28日）")
    ap.add_argument("--no-ga4", action="store_true", help="GA4を取得しない")
    ap.add_argument("--sa", default=None, help="サービスアカウント鍵のパス")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    site_url = os.environ.get("GSC_SITE_URL")
    if not site_url:
        sys.exit(".env に GSC_SITE_URL がありません"
                 "（例: GSC_SITE_URL=sc-domain:kokeniwa.net）")
    ga4_property = os.environ.get("GA4_PROPERTY_ID")
    sa_path = Path(args.sa) if args.sa else SA_PATH_DEFAULT

    end = dt.date.today() - dt.timedelta(days=GSC_LAG_DAYS)
    start = end - dt.timedelta(days=args.days - 1)
    s, e = start.isoformat(), end.isoformat()
    token = get_token(sa_path)

    print(f"Search Console: {site_url} {s}〜{e}")
    pages = gsc_query(token, site_url, s, e, ["page"], limit=200)
    queries = gsc_query(token, site_url, s, e, ["query"], limit=500)
    totals_rows = gsc_query(token, site_url, s, e, [], limit=1)
    totals = totals_rows[0] if totals_rows else {
        "clicks": 0, "impressions": 0, "ctr": 0, "position": 0}

    # ブログ記事ごとの流入クエリ（記事の改稿判断に直接効くので個別に取る）
    blog_queries = {}
    for row in pages:
        url = row["keys"][0]
        if "/blog/" not in url or row["impressions"] < 20:
            continue
        rows = gsc_query(token, site_url, s, e, ["query"], limit=20,
                         filters=[{"dimension": "page",
                                   "operator": "equals", "expression": url}])
        if rows:
            blog_queries[url] = rows

    data = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "period": {"start": s, "end": e, "days": args.days},
        "site_url": site_url,
        "gsc": {"totals": totals, "pages": pages, "queries": queries,
                "blog_queries": blog_queries},
    }

    if ga4_property and not args.no_ga4:
        print(f"GA4: property {ga4_property}")
        data["ga4"] = {
            "pages": ga4_report(
                token, ga4_property, s, e, ["pagePath"],
                ["screenPageViews", "sessions", "engagementRate",
                 "averageSessionDuration"], limit=200),
            "channels": ga4_report(
                token, ga4_property, s, e, ["sessionDefaultChannelGroup"],
                ["sessions", "engagementRate"], limit=20),
        }
    elif not ga4_property:
        print("GA4_PROPERTY_ID が未設定のため、GA4はスキップします。")

    REPORT_DIR.mkdir(exist_ok=True)
    stamp = dt.date.today().isoformat()
    (REPORT_DIR / f"seo_{stamp}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_markdown(data)
    (REPORT_DIR / f"seo_{stamp}.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "latest.md").write_text(md, encoding="utf-8")
    print(f"書き出し: reports/seo_{stamp}.md / latest.md")


if __name__ == "__main__":
    main()
