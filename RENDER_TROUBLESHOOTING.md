# Render「Not Found」エラーの対処法

Renderでアプリケーションにアクセスした際に「Not Found」エラーが表示される場合の対処法です。

## ステップ1: デプロイログを確認

1. Renderダッシュボードでサービスを選択
2. 「Logs」タブを開く
3. 最新のログを確認

### 正常な場合のログ例

```
設定読み込み成功: SPREADSHEET_ID=1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4...
✓ Googleスプレッドシートへの接続に成功しました
✓ LINE通知スケジューラーを開始しました（毎日午前9時に実行）
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Booting worker with pid: XXXX
```

### エラーログがある場合

エラーメッセージを確認して、以下の対処法を試してください。

## ステップ2: よくあるエラーと対処法

### エラー1: "設定ファイルが見つかりません"

**原因**: 環境変数が設定されていない

**対処法**:
1. Renderダッシュボードで「Environment」タブを開く
2. 以下の環境変数がすべて設定されているか確認：
   - `SPREADSHEET_ID`
   - `GOOGLE_CREDENTIALS_JSON`
   - `LINE_CHANNEL_ACCESS_TOKEN`（オプション）
   - `LINE_USER_ID`（オプション）
3. 設定後、「Save Changes」をクリック
4. 「Manual Deploy」→「Deploy latest commit」で再デプロイ

### エラー2: "認証情報ファイルの読み込みに失敗しました"

**原因**: `GOOGLE_CREDENTIALS_JSON` の形式が正しくない

**対処法**:
1. ローカルで `cat credentials.json` を実行
2. 表示されたJSON全体をコピー（改行を含む）
3. Renderの環境変数 `GOOGLE_CREDENTIALS_JSON` に貼り付け
4. Base64エンコードは不要（JSON文字列をそのまま使用）
5. 再デプロイ

### エラー3: "スプレッドシートが見つかりません"

**原因**: スプレッドシートIDが間違っている、またはアクセス権限がない

**対処法**:
1. スプレッドシートIDが正しいか確認
2. Googleスプレッドシートを開く
3. 「共有」ボタンをクリック
4. サービスアカウントのメールアドレス（`credentials.json`の`client_email`）に編集権限を付与
5. 再デプロイ

### エラー4: "ModuleNotFoundError" または "ImportError"

**原因**: 依存パッケージがインストールされていない

**対処法**:
1. `requirements.txt` に必要なパッケージがすべて含まれているか確認
2. ログで「pip install」のエラーを確認
3. 必要に応じて `requirements.txt` を更新
4. 再デプロイ

### エラー5: "Address already in use" またはポートエラー

**原因**: ポート設定の問題

**対処法**:
- Renderでは自動的にポートが設定されるため、通常は発生しません
- `render.yaml` の `startCommand` が `gunicorn app:app` になっているか確認

### エラー6: デプロイは成功したが「Not Found」が表示される

**原因**: アプリケーションは起動しているが、ルーティングに問題がある可能性

**対処法**:
1. ログで「Listening at:」のメッセージを確認（アプリが起動しているか）
2. ルートパス `/` にアクセスしているか確認
3. ブラウザで `https://todolist-1-5uja.onrender.com/` にアクセス（末尾の `/` を確認）
4. キャッシュをクリアして再アクセス

## ステップ3: デプロイ設定の確認

### render.yaml の確認

以下の設定が正しいか確認：

```yaml
services:
  - type: web
    name: todolist-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

### 手動設定の場合

Renderダッシュボードで以下を確認：

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment**: `Python 3`
- **Publish Directory**: 空欄（デフォルト）

## ステップ4: 再デプロイ

1. Renderダッシュボードでサービスを選択
2. 「Manual Deploy」→「Deploy latest commit」をクリック
3. デプロイが完了するまで待機（数分）
4. ログを確認してエラーがないか確認

## ステップ5: 動作確認

デプロイが成功したら：

1. ブラウザで `https://todolist-1-5uja.onrender.com/` にアクセス
2. Todo一覧が表示されるか確認
3. Todoの追加・編集が動作するか確認

## デバッグのヒント

### ログの確認方法

1. Renderダッシュボードで「Logs」タブを開く
2. 「Live」をクリックしてリアルタイムログを表示
3. エラーメッセージをコピーして検索

### 環境変数の確認

Renderダッシュボードの「Environment」タブで、すべての環境変数が設定されているか確認してください。

### ローカルでの動作確認

ローカルで動作確認してからデプロイ：

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/6-3-2_Todolist①"
python app.py
```

`http://localhost:5001` にアクセスして動作を確認。

## それでも解決しない場合

1. Renderのサポートに問い合わせ
2. ログのエラーメッセージ全文を確認
3. GitHubのリポジトリが正しく接続されているか確認
4. ブラウザの開発者ツール（F12）でネットワークエラーを確認

