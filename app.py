"""
TodoリストWebアプリケーション

Flaskを使用したTodoリスト管理アプリケーション
データはGoogleスプレッドシートに保存されます。
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from google_sheets_handler import GoogleSheetsHandler
import os
import json
import base64
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)  # セッション管理用


def load_config():
    """設定を環境変数またはconfig.jsonから読み込む"""
    # 環境変数から読み込み（Render用）
    if os.getenv('SPREADSHEET_ID'):
        credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if credentials_json:
            # 環境変数からJSON文字列を読み込む
            # Base64エンコードされたJSONをデコード（試行）
            try:
                credentials_data = base64.b64decode(credentials_json).decode('utf-8')
            except Exception:
                # Base64エンコードされていない場合はそのまま使用
                credentials_data = credentials_json
            
            # 一時ファイルに保存
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            temp_file.write(credentials_data)
            temp_file.close()
            
            return {
                'GOOGLE_CREDENTIALS_PATH': temp_file.name,
                'SPREADSHEET_ID': os.getenv('SPREADSHEET_ID')
            }
    
    # config.jsonから読み込み（ローカル開発用）
    config_path = os.path.join(
        os.path.dirname(__file__),
        "config.json"
    )
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {config_path}\n"
            "config.jsonを作成するか、環境変数を設定してください。"
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Googleスプレッドシートハンドラー初期化
try:
    config = load_config()
    sheets_handler = GoogleSheetsHandler(
        credentials_path=config['GOOGLE_CREDENTIALS_PATH'],
        spreadsheet_id=config['SPREADSHEET_ID']
    )
    print("✓ Googleスプレッドシートへの接続に成功しました")
except Exception as e:
    import traceback
    print(f"初期化エラー: {str(e)}")
    print("詳細:")
    traceback.print_exc()
    sheets_handler = None


@app.route('/')
def index():
    """Todo一覧表示"""
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return render_template('index.html', todos=[])
    
    try:
        # get_all_records()でTodo取得（expected_headersでヘッダーを明示的に指定）
        expected_headers = ["ID", "タイトル", "内容", "期日", "作成日時", "更新日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        return render_template('index.html', todos=todos)
    except Exception as e:
        flash(f'データの取得に失敗しました: {str(e)}', 'error')
        return render_template('index.html', todos=[])


@app.route('/add', methods=['GET', 'POST'])
def add_todo():
    """Todo登録"""
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        
        if not title or not content or not due_date:
            flash('すべての項目を入力してください', 'error')
            return render_template('add.html')
        
        try:
            todo_id = sheets_handler.create_todo(title, content, due_date)
            flash('Todoを登録しました', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'登録に失敗しました: {str(e)}', 'error')
            return render_template('add.html')
    
    return render_template('add.html')


@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    """Todo編集"""
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return redirect(url_for('index'))
    
    # idを使って行番号を特定
    def find_row_by_id(todo_id):
        """IDから行番号を取得"""
        all_values = sheets_handler.worksheet.get_all_values()
        for idx, row in enumerate(all_values[1:], start=2):  # ヘッダーを除く、行番号は2から
            if row and row[0] and str(row[0]) == str(todo_id):
                return idx
        return None
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        
        if not title or not content or not due_date:
            flash('すべての項目を入力してください', 'error')
            # 既存Todoを取得してフォームに表示
            expected_headers = ["ID", "タイトル", "内容", "期日", "作成日時", "更新日時"]
            todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
            todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
            if not todo:
                return redirect(url_for('index'))
            return render_template('edit.html', todo=todo)
        
        try:
            row_num = find_row_by_id(todo_id)
            if row_num is None:
                flash('Todoが見つかりません', 'error')
                return redirect(url_for('index'))
            
            # update_cell()で編集内容を反映
            # タイトル（B列=2）、内容（C列=3）、期日（D列=4）
            sheets_handler.worksheet.update_cell(row_num, 2, title)  # タイトル
            sheets_handler.worksheet.update_cell(row_num, 3, content)  # 内容
            sheets_handler.worksheet.update_cell(row_num, 4, due_date)  # 期日
            
            flash('Todoを更新しました', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'更新に失敗しました: {str(e)}', 'error')
            # 既存Todoを取得してフォームに表示
            expected_headers = ["ID", "タイトル", "内容", "期日", "作成日時", "更新日時"]
            todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
            todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
            if not todo:
                return redirect(url_for('index'))
            return render_template('edit.html', todo=todo)
    
    # GET：既存Todoをフォームに表示
    try:
        expected_headers = ["ID", "タイトル", "内容", "期日", "作成日時", "更新日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
        if not todo:
            flash('Todoが見つかりません', 'error')
            return redirect(url_for('index'))
        
        return render_template('edit.html', todo=todo)
    except Exception as e:
        flash(f'データの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """Todo削除"""
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return redirect(url_for('index'))
    
    try:
        success = sheets_handler.delete_todo(todo_id)
        if success:
            flash('Todoを削除しました', 'success')
        else:
            flash('Todoが見つかりません', 'error')
    except Exception as e:
        flash(f'削除に失敗しました: {str(e)}', 'error')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

