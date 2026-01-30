# Render「Not Found」エラーの対処法（詳細版）

デプロイは成功したが「Not Found」エラーが表示される場合の対処法です。

## ステップ1: Renderのログを確認

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

エラーメッセージを確認して、以下を試してください。

## ステップ2: よくあるエラーと対処法

### エラー1: "設定ファイルが見つかりません"

**症状**: ログに「設定ファイルが見つかりません」と表示される

**原因**: 環境変数が設定されていない

**対処法**:
1. Renderダッシュボードで「Environment」タブを開く
2. 以下の環境変数がすべて設定されているか確認：
   - `SPREADSHEET_ID`
   - `GOOGLE_CREDENTIALS_JSON`
3. 設定後、「Save Changes」をクリック
4. 「Manual Deploy」→「Deploy latest commit」で再デプロイ

### エラー2: "認証情報ファイルの読み込みに失敗しました"

**症状**: ログに認証関連のエラーが表示される

**原因**: `GOOGLE_CREDENTIALS_JSON` の形式が正しくない

**対処法**:
1. ローカルで `cat credentials.json` を実行
2. 表示されたJSON全体をコピー（改行を含む）
3. Renderの環境変数 `GOOGLE_CREDENTIALS_JSON` に貼り付け
4. Base64エンコードは不要（JSON文字列をそのまま使用）
5. 再デプロイ

### エラー3: "スプレッドシートが見つかりません"

**症状**: ログに「スプレッドシートが見つかりません」と表示される

**原因**: スプレッドシートIDが間違っている、またはアクセス権限がない

**対処法**:
1. スプレッドシートIDが正しいか確認
2. Googleスプレッドシートを開く
3. 「共有」ボタンをクリック
4. サービスアカウントのメールアドレス（`credentials.json`の`client_email`）に編集権限を付与
5. 再デプロイ

### エラー4: gunicornが起動しない

**症状**: ログに「Starting gunicorn」のメッセージがない

**原因**: アプリケーションのインポートエラー

**対処法**:
1. ログでエラーメッセージを確認
2. `requirements.txt` に必要なパッケージがすべて含まれているか確認
3. 再デプロイ

### エラー5: ルーティングエラー

**症状**: アプリは起動しているが「Not Found」が表示される

**原因**: ルートパス `/` にアクセスしていない、またはルーティングに問題がある

**対処法**:
1. ブラウザで `https://todolist-1-5uja.onrender.com/` にアクセス（末尾の `/` を確認）
2. キャッシュをクリアして再アクセス
3. シークレットモードでアクセス

## ステップ3: デプロイ設定の再確認

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
3. エラーメッセージが表示される場合は、その内容を確認

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

