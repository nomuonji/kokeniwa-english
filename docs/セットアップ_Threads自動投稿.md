# Threads 自動投稿 セットアップ手順

3アカウントへ 1日3回、GitHub Actions で自動投稿する仕組み。
トークンは環境変数に置かず **Gist** に保存し、期限が近づくと自動リフレッシュする。

- 投稿時刻: 07:00 / 12:00 / 20:00 JST(ワークフローの cron で変更可)
- USCPA → `data/uscpa_words.csv`(1語/回)
- 法律英語 → `data/legal_words.csv`(1語/回)
- 英文読解 → `data/reading_problems.jsonl`(出題＋解説のツリー投稿)
- 進捗は Gist 内 `threads_state.json` の `cursor` で管理(id順・末尾まで行くと先頭へ循環)

---

## 全体像

```
GitHub Actions(cron 3回/日)
   └─ scripts/auto_post.py
        ├─ Gist から状態を読む            … トークン・cursor
        ├─ 期限10日以内ならトークン更新     … Gist を上書き
        ├─ 各アカウントへ1件投稿          … Threads API
        └─ cursor を進めて Gist を保存
```

必要な GitHub Secrets は **2つだけ**:

| Secret 名 | 中身 |
|---|---|
| `GIST_ID` | 状態を保存する Gist の ID |
| `GH_GIST_TOKEN` | `gist` スコープの GitHub Personal Access Token |

トークン本体(Threads の access token)は Secrets に置かず、Gist の中だけに持つ。

---

## 手順

### 1. Gist を作る(状態ストア)

1. https://gist.github.com/ を開く
2. ファイル名を `threads_state.json` にする
3. 中身に、ローカルで生成した `seed_state.json` の内容を貼り付ける
   （※このファイルは Threads トークンを含むので **Secret gist** にすること）
4. 「Create secret gist」で作成
5. URL 末尾の英数字が **Gist ID**（例: `https://gist.github.com/you/<この部分>`）

> `seed_state.json` を作り直したいときは、リポジトリのルートで:
> ```
> printf '%s\n%s\n%s\n' "USCPAトークン" "法律トークン" "読解トークン" | python scripts/build_seed_state.py > seed_state.json
> ```
> 生成後、中身を Gist に貼ったら **ローカルの seed_state.json は削除**する。

### 2. gist スコープの PAT を作る

1. https://github.com/settings/tokens → 「Generate new token (classic)」
2. スコープは **`gist` のみ**にチェック（他は不要）
3. 有効期限は「No expiration」か長め（切れると自動投稿が止まる）
4. 生成された `ghp_...` をコピー

### 3. リポジトリを用意して push

このプロジェクトはまだ git 管理外。ルートで:

```
git init
git add .
git commit -m "Threads 自動投稿の仕組みを追加"
```

> `.gitignore` で `seed_state.json` 等は除外済み。`git status` にトークンを含む
> ファイルが出ていないことを必ず確認してから commit すること。

GitHub 上で空リポジトリ（Private 推奨）を作り、リモート追加して push:

```
git remote add origin https://github.com/<あなた>/<リポジトリ>.git
git branch -M main
git push -u origin main
```

### 4. Secrets を登録

リポジトリの Settings → Secrets and variables → Actions → New repository secret:

- `GIST_ID` … 手順1の Gist ID
- `GH_GIST_TOKEN` … 手順2の PAT

### 5. 手動テスト（DRY RUN）

Actions タブ → 「Threads 自動投稿」→ Run workflow →
`dry_run` に `1` を入れて実行。実投稿せずログに投稿内容が出れば配線OK。

次に `dry_run` を `0`（空でも可）にして実行 → 各アカウントに実際に1件投稿される。
Threads アプリで確認。

### 6. 放置で自動運用

以後は cron で 1日3回自動投稿。Gist の `cursor` が進み、`expires_at` は
期限が近づくと自動更新される。**60日に一度も実行されないとトークンが失効**する
点だけ注意（毎日動くので通常は問題なし）。

---

## よくある調整

- **投稿時刻を変える**: `.github/workflows/threads-autopost.yml` の `cron`（UTC）。
  JST = UTC+9。例) 21:00 JST = `0 12 * * *`。
- **一時的に1アカウントだけ止める**: 手動実行の `accounts` に動かしたいものだけ
  指定（例 `uscpa,legal`）。定常運用で外すならワークフローに `ACCOUNTS` を固定設定。
- **投稿順を変える / 特定idから始める**: Gist の該当アカウントの `cursor`（0始まり）を編集。
- **①②アカウントの割り当てを入れ替える**: Gist で `uscpa` と `legal` の `token`/`user_id`/
  `username` を入れ替える（`content` はそのまま）。

## ローカル動作確認（任意）

Gist を使わずローカルファイルで試せる:

```
cp seed_state.json test_state.json
DRY_RUN=1 LOCAL_STATE_FILE=test_state.json python scripts/auto_post.py
```
