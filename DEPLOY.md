# Render デプロイ手順

このアプリケーションをRenderで公開する手順です。

## 1. リポジトリの準備

1. GitHubにリポジトリを作成
2. このプロジェクトをプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

## 2. Renderでサービスを作成

1. [Render](https://render.com)にログイン
2. 「New +」→「Web Service」を選択
3. GitHubリポジトリを接続
4. リポジトリを選択

## 3. 環境変数の設定

Renderのダッシュボードで以下の環境変数を設定：

### SPREADSHEET_ID
- **値**: あなたのGoogleスプレッドシートID
- **例**: `1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4`

### GOOGLE_CREDENTIALS_JSON
- **値**: サービスアカウントの認証情報JSON（Base64エンコード推奨）
- **取得方法**:
  1. `credentials.json`ファイルを開く
  2. ファイル全体の内容をコピー
  3. Base64エンコード（オプション）:
     ```bash
     base64 -i credentials.json
     ```
  4. エンコードされた文字列を環境変数に設定

**注意**: Base64エンコードしない場合は、JSON文字列をそのまま設定できます。

## 4. ビルド設定

Renderのダッシュボードで以下を設定：

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Python Version**: `3.11.0`（または利用可能なバージョン）

## 5. デプロイ

「Create Web Service」をクリックしてデプロイを開始します。

## 6. デプロイ後の確認

デプロイが完了したら、提供されたURL（例: `https://your-app.onrender.com`）にアクセスして動作を確認してください。

## トラブルシューティング

### エラー: "初期化エラー"
- 環境変数が正しく設定されているか確認
- `GOOGLE_CREDENTIALS_JSON`が正しい形式か確認
- スプレッドシートIDが正しいか確認

### エラー: "Permission denied"
- サービスアカウントのメールアドレスにスプレッドシートの共有権限が付与されているか確認

### エラー: "API not enabled"
- Google Cloud ConsoleでGoogle Sheets APIとGoogle Drive APIが有効になっているか確認

## セキュリティ注意事項

- `credentials.json`や`config.json`はGitにコミットしないでください（`.gitignore`に追加済み）
- 環境変数はRenderのダッシュボードで管理してください
- 本番環境では`debug=False`に設定してください（現在は`debug=True`）

