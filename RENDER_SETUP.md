# Render環境変数設定ガイド

Renderで「Googleスプレッドシートの接続に失敗しました」エラーが出る場合の対処法です。

## 環境変数の設定方法

### 1. Renderダッシュボードで環境変数を設定

1. Renderダッシュボードでサービスを選択
2. 「Environment」タブをクリック
3. 以下の2つの環境変数を追加：

### 2. SPREADSHEET_ID の設定

- **Key**: `SPREADSHEET_ID`
- **Value**: スプレッドシートID（URLから取得）
  - 例: `1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4`

### 3. GOOGLE_CREDENTIALS_JSON の設定（重要）

- **Key**: `GOOGLE_CREDENTIALS_JSON`
- **Value**: `credentials.json` ファイルの内容を**そのまま**貼り付け

#### credentials.jsonの内容を取得する方法

ローカルで以下のコマンドを実行：

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/6-3-2_Todolist①"
cat credentials.json
```

表示されたJSON全体をコピーして、Renderの環境変数 `GOOGLE_CREDENTIALS_JSON` の値として貼り付けます。

#### 注意点

1. **改行を含めて全体をコピー**してください
2. **Base64エンコードは不要**です（JSON文字列をそのまま使用）
3. **ダブルクォート（"）を含めて**コピーしてください
4. 例：
   ```json
   {
     "type": "service_account",
     "project_id": "...",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "...",
     ...
   }
   ```

## 環境変数設定の確認

Renderの「Logs」タブで以下のメッセージが表示されれば成功です：

```
設定読み込み成功: SPREADSHEET_ID=1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4...
✓ Googleスプレッドシートへの接続に成功しました
```

## よくあるエラーと対処法

### エラー: "設定ファイルが見つかりません"
- **原因**: 環境変数が設定されていない
- **対処**: `SPREADSHEET_ID` と `GOOGLE_CREDENTIALS_JSON` の両方を設定

### エラー: "認証情報ファイルの読み込みに失敗しました"
- **原因**: `GOOGLE_CREDENTIALS_JSON` の形式が正しくない
- **対処**: 
  - JSON全体をコピーしているか確認
  - 改行が含まれているか確認
  - 特殊文字がエスケープされているか確認

### エラー: "スプレッドシートが見つかりません"
- **原因**: スプレッドシートIDが間違っている、またはアクセス権限がない
- **対処**:
  - スプレッドシートIDが正しいか確認
  - サービスアカウントのメールアドレスにスプレッドシートの共有権限を付与

### エラー: "API not enabled"
- **原因**: Google Sheets APIが有効になっていない
- **対処**: Google Cloud ConsoleでGoogle Sheets APIとGoogle Drive APIを有効化

## デプロイ後の確認

1. Renderの「Logs」タブでエラーログを確認
2. 環境変数が正しく設定されているか確認
3. スプレッドシートの共有設定を確認

