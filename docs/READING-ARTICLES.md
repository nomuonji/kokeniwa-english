# Kokeniwa Reading Garden — 教材追加ガイド

`/reading/articles/` は、ブログとは別系統の英語リーディング・精読教材です。

## 基本方針

- 内容そのものが読み物として面白いことを最優先する。
- 英文を主役にし、日本語は学習補助として使う。
- 精読機能は常時組み込む。ON/OFFスイッチやフローティング教材UIは追加しない。
- 各文には「訳」ボタンを置き、その直下に日本語訳を差し込む。
- 構造データがある英文は、意味・文法上の塊ごとに控えめに装飾し、タップで役割と解説を表示する。
- 段落ごとに「ここで覚える」として、重要語・表現・構文・ニュアンスを必要なものだけ出す。
- 記事末尾の学習ガイドで、語彙・表現・構文・ニュアンス・言い換え・背景・理解チェック・アウトプットを整理する。
- ブログ記事とは別コンテンツとして扱う。

## 追加方法

`content/reading/<slug>.json` を1ファイル追加すると、ビルド時に一覧と個別ページへ自動追加されます。

最低限必要なトップレベル項目:

```json
{
  "slug": "example-topic",
  "title": "English Title",
  "title_ja": "日本語タイトル",
  "date": "2026-09-12",
  "topic": "Culture & Society",
  "level": "B1–B2",
  "minutes": 7,
  "description": "日本語の短い説明",
  "orientation_ja": "読むときに意識するポイント",
  "paragraphs": [],
  "guide": {}
}
```

`slug` はファイル名と一致させます。

## paragraphs

各段落は `sentences` と任意の `notes` を持ちます。

```json
{
  "sentences": [
    {
      "en": "A natural English sentence.",
      "ja": "自然な日本語訳。"
    }
  ],
  "notes": [
    {
      "type": "phrase",
      "quote": "a useful expression",
      "explanation_ja": "本文の文脈に即した簡潔な解説"
    }
  ]
}
```

`notes.type` は原則として以下を使用します。

- `word`: 重要語
- `phrase`: 表現
- `grammar`: 文法・構文
- `nuance`: 語感・談話上の働き

精読ポイントを増やしすぎないこと。本文を読む流れを壊さない密度を優先します。

## 文構造チャンク

構造表示は本文JSONと分離し、任意の伴走ファイルとして追加します。

`content/reading/structure/<slug>.json`

```json
{
  "sentences": {
    "Knowing the destination can make it easier to notice the road.": [
      {
        "text": "Knowing the destination",
        "role": "subject",
        "label_ja": "主語（動名詞句）",
        "note_ja": "Knowing から始まる動名詞句全体が文の主語です。"
      },
      {
        "text": "can make",
        "role": "predicate",
        "label_ja": "述語",
        "note_ja": "make O C の骨格を作る動詞です。"
      },
      {
        "text": "it",
        "role": "object",
        "label_ja": "形式目的語",
        "note_ja": "後ろの to不定詞を受ける形式目的語です。"
      },
      {
        "text": "easier",
        "role": "complement",
        "label_ja": "目的格補語",
        "note_ja": "it がどうなるかを説明します。"
      },
      {
        "text": "to notice the road.",
        "role": "infinitive",
        "label_ja": "真の内容",
        "note_ja": "実際の内容を to不定詞で示しています。"
      }
    ]
  }
}
```

推奨 `role`:

- `subject`: 主語。苔色。
- `predicate`: 述部。藍色。
- `object`: 目的語。
- `complement`: 補語。
- `clause`: 条件節・that節・疑問詞節など。
- `relative`: 関係詞節、関係詞省略の節。
- `infinitive`: to不定詞。
- `participle`: 分詞・分詞句。
- `modifier`: 副詞句、前置詞句、比較句などの修飾。
- `connector`: but / yet / so / and など論理のつなぎ。

色は細かな文法用語を暗記するためではなく、**骨格と枝葉の境界を瞬時に認識するため**に使います。主語・述部を最優先で切り、次に目的語・補語、その後に節や修飾を分けてください。

構造ファイルは任意です。存在しない記事も従来どおり読めます。存在する場合、ビルド時に以下を検査します。

- 対象英文が本文に実在すること。
- 各チャンクに `text / role / label_ja / note_ja` があること。
- チャンクを半角スペースで連結した結果が元の英文と完全一致すること。

この検査により、本文を編集したのに古い構造解析だけ残る事故を防ぎます。

## guide

推奨フィールド:

```json
{
  "summary_ja": "記事の要旨",
  "vocabulary": [],
  "phrases": [],
  "grammar": [],
  "nuance": [],
  "paraphrases": [],
  "background": [],
  "comprehension": [
    {"q": "Question in English?", "a": "Answer in English."}
  ],
  "output": []
}
```

すべてを無理に埋める必要はありません。ただし、語彙・表現・構文・ニュアンスのうち本文で学習価値が高いものは十分に拾います。

## テーマ選定

教材は「英語を勉強するためだけの文章」にしないこと。まず読みたい話題を作ります。

向いている例:

- 日常の心理や行動の不思議
- 映画・音楽・インターネット文化
- 食・都市・旅行・仕事・テクノロジー
- 歴史上の小さな逸話
- 科学や社会の意外な事実
- 賛否が分かれるが、安全に読める身近な問い

1記事では1つの明確な問いに絞り、読後に「人に話したくなる」情報や視点を残します。

## SEO方針

主な検索対象は英語圏ではなく、日本語話者の英語学習者です。英語本文を不自然に検索キーワードへ寄せません。

カテゴリ・一覧・meta title / description では、需要調査を踏まえて次の検索意図を自然にカバーします。

- 英語 リーディング
- 英語 長文 読解
- 英語 精読
- 英語 多読

個別記事は、記事テーマ固有の日本語検索意図も取れそうな場合に `title_ja` と `description` へ自然に反映します。公開前に Keywords Operator で需要とSERPを確認し、検索需要が薄い場合でも教材として面白ければ公開を優先します。

## 品質チェック

追加後は以下を実行します。

```bash
python -m compileall -q site
python site/build_site.py
```

ビルド時に以下を検査します。

- 必須フィールド
- `slug` とファイル名の一致
- 各段落に1文以上あること
- 各文に `en` と `ja` があること
- 構造チャンクと元英文の一致
- 内部リンク切れ

## UI上の不変条件

今後の変更でも以下を維持します。

1. 訳は別パネルではなく、対象英文のすぐ下に差し込む。
2. 文構造も別画面へ飛ばさず、対象文のすぐ下で確認できるようにする。
3. 精読情報を読むためにモード切替を要求しない。
4. フローティングパネルを教材の主導線にしない。
5. Kokeniwa の既存CSS変数・ライト/ダークテーマ・苔庭の世界観に合わせる。
6. 色だけに意味を依存させず、タップ時に日本語ラベルを必ず表示する。
7. モバイルでも本文の可読性を最優先する。
