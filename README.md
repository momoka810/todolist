# TodoリストWebアプリケーション

Googleスプレッドシートを使用したTodoリスト管理アプリケーションです。

## 機能

- Todoの登録（タイトル・内容・期日）
- Todoの編集
- Todoの一覧表示
- Todoの削除
- データはGoogleスプレッドシートに保存

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Googleスプレッドシートの設定

1. Google Cloud Consoleでプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. サービスアカウントを作成
4. サービスアカウントの認証情報JSONファイルをダウンロード
5. ダウンロードしたJSONファイルを`credentials.json`として保存

### 3. スプレッドシートの準備

1. Googleスプレッドシートを新規作成
2. スプレッドシートのIDを取得（URLから取得可能）
   - 例: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
3. サービスアカウントのメールアドレスにスプレッドシートの共有権限を付与

### 4. 設定ファイルの作成

`config.json.example`をコピーして`config.json`を作成し、以下の情報を設定：

```json
{
    "GOOGLE_CREDENTIALS_PATH": "credentials.json",
    "SPREADSHEET_ID": "your-spreadsheet-id-here",
    "WORKSHEET_NAME": "Todos"
}
```

- `GOOGLE_CREDENTIALS_PATH`: サービスアカウントの認証情報JSONファイルのパス
- `SPREADSHEET_ID`: GoogleスプレッドシートのID
- `WORKSHEET_NAME`: ワークシート名（デフォルト: "Todos"）

## 実行方法

```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセスしてください。

## ファイル構成

```
6-3-2_Todolist①/
├── app.py                    # Flaskアプリケーションのメインファイル
├── google_sheets_handler.py  # Googleスプレッドシート操作モジュール
├── config.json               # 設定ファイル
├── credentials.json          # Googleサービスアカウント認証情報
├── requirements.txt          # 依存パッケージ
├── templates/                # HTMLテンプレート
│   ├── base.html
│   ├── index.html
│   ├── add.html
│   └── edit.html
└── static/                   # 静的ファイル
    └── style.css
```

## 注意事項

- `credentials.json`は機密情報のため、Gitにコミットしないでください
- `.gitignore`に`credentials.json`と`config.json`を追加することを推奨します

