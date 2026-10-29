# Instagram 自動投稿 セットアップ手順

Threads の自動投稿(`threads-autopost.yml`)と**同じ回・同じ中身**を、Instagram にも
カルーセル画像で投稿する仕組み。Threads アカウントと Instagram アカウントは **1対1**。

```
Threads 自動投稿(1日3回)
   └─ scripts/auto_post.py
        ├─ Threads へ投稿(これまで通り)
        └─ 連携済みなら Instagram へ
             ├─ scripts/ig_cards.py      … シリーズ別パステル×ステッカー風の 1080x1350 JPEG を生成
             ├─ scripts/ig_media_host.py … 画像を ig-media タグのコミットに一時配置(公開URL)
             └─ scripts/instagram_client.py … カルーセルを作成・公開
```

- 単語系(USCPA / 法律 / こつこつ): 表紙(今回の語の一覧) → 1語1枚(意味・例文) → 締め
- 英文解釈: 問題 → 正解と全文訳 → 解説 → 締め
- キャプションは Threads 本文＋「スワイプで〜」＋サイト誘導(プロフィールのリンク)＋ハッシュタグ
- Instagram は Threads の投稿に**成功したときだけ**投稿する。Instagram が失敗しても
  Threads の進捗は保存され、ワークフローは失敗表示(メール通知)になる
- 未連携のアカウントには何も起きない(画像ライブラリも読み込まない)
- トークンは Threads と同じく **Gist(`threads_state.json`)にだけ** 保存する。
  Actions の Secret や環境変数には置かない(Secret は既存の `GH_GIST_TOKEN` と `GIST_ID` だけ)

## 1. Instagram 側の準備(アカウントごと)

1. Instagram アカウントを作り、**プロアカウント(クリエイター or ビジネス)** に切り替える
2. プロフィールのリンクに、対応するサイトのページを入れる
   (例: USCPA → `https://en.kokeniwa.net/vocab/uscpa/`)。投稿文中のURLはリンクにならないため

## 2. トークンを発行する(アカウントごと)

Threads と同じ Meta 開発者アプリを使える。

1. https://developers.facebook.com/apps/ → 対象アプリ →「製品を追加」→ **Instagram** →
   「Instagramログインによる API 設定」
2. 権限 `instagram_business_basic` と `instagram_business_content_publish` を有効にする
3. 「アクセストークンを生成」で、投稿したい Instagram アカウントを追加・ログインする
   (アプリが開発モードなら、そのアカウントを Instagram テスターに追加して承認しておく)
4. 表示された**長期アクセストークン**をコピー

## 3. Threads アカウントに紐づける(ローカルで実行)

Threads の `build_seed_state.py` と同じく、トークンは標準入力で渡してローカルで処理する。

```
# リポジトリのルートで。1行に「Threadsアカウント名 トークン」(複数行で複数アカウント)
printf 'uscpa %s\nreading %s\n' "$IG_USCPA" "$IG_READING" | python scripts/ig_link.py link
```

- 環境に `GH_GIST_TOKEN`(gist スコープの PAT)と `GIST_ID` があれば、Gist を直接更新する
- 無ければ、Gist に貼る `"instagram"` ブロック(JSON)を表示する。
  Gist の `threads_state.json` を開き、該当アカウントの中にそのまま追加して保存する
  (表示内容にはトークンが含まれる。貼り終えたら端末の履歴やメモから消すこと)
- Threads アカウント名は `uscpa` / `legal` / `reading` / `kotsukotsu`
- 同じ Instagram を2つの Threads アカウントに紐づけようとすると中止する(1対1運用)

トークン(60日)は投稿時に期限10日前から自動延命する。連携から24時間以内は延命できないため、
初回は「延命は次回に持ち越し」と出るが問題ない。

## 4. 動作確認

- 見た目だけ確認: Actions →「Threads 自動投稿」→ Run workflow(dry_run=1)。
  実行結果の Artifacts「instagram-slides」に全アカウント分の画像が入る(未連携でも生成)
- 状態確認: Actions「Instagram 連携」を action=`status` で実行(またはローカルで
  `python scripts/ig_link.py status`)。連携先・期限・最終投稿・最終エラーが出る
- 一時停止: action=`disable`(再開は `enable`)。トークンは不要

## 補足

- 画像の置き場はタグ `ig-media`。毎回「今回の画像だけ」のコミットで上書きされる
  (リポジトリは肥大化しない)。ブランチではないので Cloudflare Pages のプレビューは走らない
- Instagram の API 投稿上限は 24時間あたり 50〜100件(カルーセルは1件扱い)。1日3回なら十分
- カードのデザイン: シリーズごとにパステル色(USCPA=ミント / 法律=ピーチ / こつこつ=レモン /
  英文解釈=ラベンダー)と水玉の背景、縁取り＋影のステッカー風カード、マスキングテープ、
  蛍光ペン風の意味、マスコットの苔玉「こけまる」。色・文言は `scripts/ig_cards.py` の
  `SERIES` と `TEXT`、キャプションとタグは `scripts/ig_post.py`
- フォントは丸ゴシック M PLUS Rounded 1c(OFL)。ワークフローが実行時に google/fonts から
  `fonts/` へ取得する(リポジトリには入れない)。取れなければ Noto Sans CJK で代用
- ローカルで見た目を確認:
  `python scripts/ig_cards.py --fetch-fonts uscpa --cursor 0 --out out/ig`
  (`training:news` / `reading --id 1` なども可)
