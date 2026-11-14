# Zenn 記事リポジトリ

Zenn CLI で管理する技術記事。`push` すると Zenn に反映される（GitHub 連携）。

## 構成
- articles/ 記事本体（`<slug>.md`、英小文字・数字・ハイフン）
- images/<slug>/ 記事ごとの画像。本文からは `/images/<slug>/xxx.png` で参照
- books/ 本（現在は空）
- notes/ 調査メモ・ネタ帳（Zenn には公開されない。必要になったら作る）

## 記事のルール
- frontmatter は次の形式:
  ```
  ---
  title: "..."
  emoji: "🤖"
  type: "tech"
  topics: ["a", "b"]   # 小文字
  published: false     # 公開時のみ true
  ---
  ```
- 下書きは `published: false`。`true` にするのは私が指示したときだけ
- 見出しは `##` から始める（`#` は使わない）
- 既存記事の書き方に合わせる:
  - 「はじめに」で動機を書く
  - たとえ話（身近な例）を使って概念を説明する
  - 「〜です／ます」調
- 事実を捏造しない。バージョン・日付・仕様は公式ドキュメントで確認できるものだけ書く
- コードは動作確認したものだけ載せる。未確認なら「イメージ」と明記する
- 画像は `images/<slug>/` に置く（記事と同じ slug）

## コマンド
- プレビュー: `npx zenn preview`
- 新規作成: `npx zenn new:article --slug <slug>`

## Git
- コミットメッセージ: `feat: 〜記事を公開` / `fix: 〜` の形式（既存の履歴に合わせる）
- `git push` は、公開内容を提示して私の承認を得てから実行する
