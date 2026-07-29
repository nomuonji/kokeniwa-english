"""サイト設定と定数。site_config.json を読み込み、カテゴリ・科目の対応表を持つ。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
SITE_DIR = ROOT / "site"
DIST_DIR = ROOT / "dist"


def load_config():
    with open(ROOT / "site_config.json", encoding="utf-8") as f:
        return json.load(f)


# 読解問題のカテゴリ名（日本語）→ URLスラッグ。
# 未知のカテゴリがデータに現れたらビルドを止める（build側でチェック）。
CATEGORY_SLUGS = {
    "構文把握": "structure",
    "省略・共通関係": "ellipsis",
    "比較": "comparison",
    "関係詞・挿入": "relatives",
    "機能語の識別": "function-words",
    "倒置・強調": "inversion",
    "仮定法・助動詞": "subjunctive",
    "長文構造把握": "long-sentences",
    "語法・多義語": "usage-polysemy",
    "名詞構文・無生物主語": "nominal-constructions",
    "否定": "negation",
    "不定詞・分詞": "infinitives-participles",
    "挿入・同格・句読点": "parenthesis-apposition",
    "指示語・照応": "reference",
    "文脈推測": "inference",
    "パラフレーズ": "paraphrase",
    "談話・論理": "discourse-logic",
    "構造の罠": "structural-traps",
    "トーン・皮肉": "tone-irony",
    "情報構造": "information-structure",
    "分詞構文": "participial-constructions",
}

# 難易度（data の difficulty 1/2/3）はサイトに表示しない。
# 体感の難しさと合っていないという指摘を受けて表示を廃止した（templates/reading.py 冒頭参照）。

# 語彙の科目（subject）メタデータ。key = データ上のsubject値
USCPA_SUBJECTS = {
    "FAR": {"slug": "far", "name": "FAR", "full": "Financial Accounting and Reporting", "ja": "財務会計"},
    "AUD": {"slug": "aud", "name": "AUD", "full": "Auditing and Attestation", "ja": "監査・証明業務"},
    "REG": {"slug": "reg", "name": "REG", "full": "Regulation", "ja": "税法・ビジネス法"},
    "BAR": {"slug": "bar", "name": "BAR", "full": "Business Analysis and Reporting", "ja": "ビジネス分析"},
    "ISC": {"slug": "isc", "name": "ISC", "full": "Information Systems and Controls", "ja": "情報システム"},
    "TCP": {"slug": "tcp", "name": "TCP", "full": "Tax Compliance and Planning", "ja": "税務コンプライアンス"},
}

LEGAL_SUBJECTS = {
    "CONTRACT": {"slug": "contract", "name": "CONTRACT", "full": "Contracts", "ja": "契約一般"},
    "CLAUSE": {"slug": "clause", "name": "CLAUSE", "full": "Contract Clauses", "ja": "契約条項"},
    "CORP": {"slug": "corp", "name": "CORP", "full": "Corporate Law", "ja": "会社法"},
    "LIT": {"slug": "lit", "name": "LIT", "full": "Litigation", "ja": "訴訟"},
    "FIN": {"slug": "fin", "name": "FIN", "full": "Finance", "ja": "金融"},
    "IP": {"slug": "ip", "name": "IP", "full": "Intellectual Property", "ja": "知的財産"},
    "EMP": {"slug": "emp", "name": "EMP", "full": "Employment Law", "ja": "労働・雇用"},
    "CRIM": {"slug": "crim", "name": "CRIM", "full": "Criminal Law", "ja": "刑事"},
    "PROP": {"slug": "prop", "name": "PROP", "full": "Property Law", "ja": "不動産・財産"},
    "GEN": {"slug": "gen", "name": "GEN", "full": "General Legal Terms", "ja": "法律一般"},
}

VOCAB_SETS = {
    "uscpa": {
        "slug": "uscpa",
        "title": "USCPA英単語",
        "csv": "uscpa_words.csv",
        "subjects": USCPA_SUBJECTS,
        "description": "USCPA（米国公認会計士）試験の頻出英単語1000語。FAR・AUD・REGなど科目別に、日本語訳と例文つきで学べます。",
        "sns_key": "uscpa",
    },
    "legal": {
        "slug": "legal",
        "title": "法律英単語",
        "csv": "legal_words.csv",
        "subjects": LEGAL_SUBJECTS,
        "description": "契約書・訴訟・会社法など実務で使う法律英単語1000語。分野別に、日本語訳と例文つきで学べます。",
        "sns_key": "legal",
    },
}

# 英単語トレーニング（旧 english-learner「こつこつ英単語」を統合）。
# 一般英語の単語帳。USCPA/法律と同じフラッシュカード一覧（英単語⇄意味を個別反転）方式。
# data/training/{file} に元データ（1行1語のJSONL: id/word/meaning/example/example_ja）。
# 表示順は dict の定義順。key = データ上のタグ名（eiken_pre1 のみタグ無し）。
TRAINING_SETS = {
    "eiken_pre1": {
        "slug": "eiken-pre1",
        "file": "eiken_pre1.jsonl",
        "title": "英検準1級 英単語",
        "short": "英検準1級",
        "icon": "🎓",
        "description": "英検準1級レベルの必須英単語1500語。カードをめくって意味を確認できます。",
    },
    "news": {
        "slug": "news",
        "file": "news.jsonl",
        "title": "ニュース英単語",
        "short": "ニュース",
        "icon": "📰",
        "description": "英字ニュースで頻出する時事英単語。政治・経済・社会の記事を読むための語彙。",
    },
    "drama": {
        "slug": "drama",
        "file": "drama.jsonl",
        "title": "ドラマ英単語",
        "short": "ドラマ",
        "icon": "🎬",
        "description": "海外ドラマや映画でよく耳にする口語英単語。生きた会話表現を身につけます。",
    },
    "phrasal": {
        "slug": "phrasal",
        "file": "phrasal.jsonl",
        "title": "句動詞",
        "short": "句動詞",
        "icon": "🔗",
        "description": "英会話に欠かせない句動詞（phrasal verbs）。get / bring / put などの組み合わせ。",
    },
    "idioms": {
        "slug": "idioms",
        "file": "idioms.jsonl",
        "title": "イディオム",
        "short": "イディオム",
        "icon": "💬",
        "description": "ネイティブがよく使う慣用表現（イディオム）。直訳では分からない決まり文句。",
    },
}
