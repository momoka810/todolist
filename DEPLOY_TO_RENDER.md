# Renderへのデプロイ手順

このドキュメントでは、TodoリストアプリケーションをRenderにデプロイする手順を説明します。

## 前提条件

- GitHubアカウント
- Renderアカウント（無料プランで可）
- Google Cloud Consoleでサービスアカウントを作成済み
- LINE Messaging APIのチャネルアクセストークンとユーザーIDを取得済み

## ステップ1: GitHubにプッシュ

### 1.1 Gitリポジトリの初期化（まだの場合）

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/6-3-2_Todolist①"
git init
git add .
git commit -m "Initial commit: Todoリストアプリケーション"
```

### 1.2 GitHubリポジトリの作成

1. GitHubにログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例: `todolist-app`）
4. 「Create repository」をクリック

### 1.3 ローカルリポジトリをGitHubにプッシュ

```bash
git remote add origin https://github.com/YOUR_USERNAME/todolist-app.git
git branch -M main
git push -u origin main
```

**注意**: `YOUR_USERNAME` をあなたのGitHubユーザー名に置き換えてください。

## ステップ2: RenderでWebサービスを作成

### 2.1 Renderダッシュボードにアクセス

1. [Render](https://render.com) にログイン
2. ダッシュボードで「New +」→「Web Service」をクリック

### 2.2 GitHubリポジトリを接続

1. 「Connect GitHub」をクリック
2. GitHubアカウントを認証
3. 作成したリポジトリ（`todolist-app`）を選択

### 2.3 サービス設定

以下の設定を入力：

- **Name**: `todolist-app`（任意）
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Plan**: `Free`（無料プラン）

## ステップ3: 環境変数の設定

Renderダッシュボードで「Environment」タブを開き、以下の環境変数を追加します。

### 3.1 SPREADSHEET_ID

- **Key**: `SPREADSHEET_ID`
- **Value**: スプレッドシートID
  - 例: `1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4`

### 3.2 GOOGLE_CREDENTIALS_JSON

- **Key**: `GOOGLE_CREDENTIALS_JSON`
- **Value**: `credentials.json` ファイルの内容を**そのまま**貼り付け

#### credentials.jsonの内容を取得

ローカルで以下のコマンドを実行：

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/6-3-2_Todolist①"
cat credentials.json
```

表示されたJSON全体をコピーして、Renderの環境変数 `GOOGLE_CREDENTIALS_JSON` の値として貼り付けます。

**重要**: 
- 改行を含めて全体をコピーしてください
- Base64エンコードは不要です（JSON文字列をそのまま使用）
- ダブルクォート（"）を含めてコピーしてください

### 3.3 LINE_CHANNEL_ACCESS_TOKEN

- **Key**: `LINE_CHANNEL_ACCESS_TOKEN`
- **Value**: LINE Messaging APIのチャネルアクセストークン
  - 例: `U0DRtI0EPfRWhm1uoLiDOKFJbn242Em7m/wkD7RNPMWgpQYT5Ya6B8lDhELLKbQaqm5U+tyyCT/ge5abg9e35CeACh9W+61TLpTr09YM9hFhYOSwvDPwkMYofS2ejXtecSm3OOeo2JtWNqjqlpKehAdB04t89/1O/w1cDnyilFU=`

### 3.4 LINE_USER_ID

- **Key**: `LINE_USER_ID`
- **Value**: LINE Messaging APIのユーザーID
  - 例: `U5a37e08d86fc32e778042157a58eacd8`

## ステップ4: デプロイの実行

1. 環境変数をすべて設定したら、「Save Changes」をクリック
2. 「Manual Deploy」→「Deploy latest commit」をクリック
3. デプロイが完了するまで待機（数分かかります）

## ステップ5: デプロイの確認

### 5.1 ログの確認

Renderの「Logs」タブで以下のメッセージが表示されれば成功です：

```
設定読み込み成功: SPREADSHEET_ID=1TQUJbvMdHISeVxXvG1MgIdhVrQgXsEsoHK2iy1Sw4c4...
✓ Googleスプレッドシートへの接続に成功しました
✓ LINE通知スケジューラーを開始しました（毎日午前9時に実行）
```

### 5.2 アプリケーションの動作確認

1. Renderの「Settings」タブで「URL」を確認
2. ブラウザでそのURLにアクセス
3. Todoの登録・編集・一覧表示が正常に動作するか確認

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

### エラー: "Address already in use"

- **原因**: ポートが既に使用されている（ローカル環境のみ）
- **対処**: Renderでは発生しません（gunicornが自動でポートを設定）

## 自動通知について

Renderにデプロイすると、自動通知スケジューラーが毎日午前9時に実行されます。

**注意**: 
- 無料プランの場合、15分間アクセスがないとスリープします
- スリープ中は通知が送信されません
- 定期的にアクセスがあるか、有料プランを使用することを推奨します

## 更新方法

コードを更新した場合：

1. ローカルで変更をコミット
2. GitHubにプッシュ
3. Renderが自動的にデプロイを開始（数分で完了）

```bash
git add .
git commit -m "Update: 機能追加"
git push origin main
```

## 参考リンク

- [Render公式ドキュメント](https://render.com/docs)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [LINE Messaging API](https://developers.line.biz/ja/docs/messaging-api/)

