"""
TodoリストWebアプリケーション

Flaskを使用したTodoリスト管理アプリケーション
データはGoogleスプレッドシートに保存されます。
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from google_sheets_handler import GoogleSheetsHandler
from line_notifier import send_todo_notifications
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import json
import base64
import tempfile
from datetime import datetime

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
            
            config = {
                'GOOGLE_CREDENTIALS_PATH': temp_file.name,
                'SPREADSHEET_ID': os.getenv('SPREADSHEET_ID')
            }
            # LINE Messaging API の設定も環境変数から取得
            channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
            user_id = os.getenv('LINE_USER_ID', '')
            if channel_access_token:
                config['LINE_CHANNEL_ACCESS_TOKEN'] = channel_access_token
            if user_id:
                config['LINE_USER_ID'] = user_id
            return config
    
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
sheets_handler = None
config = None
try:
    config = load_config()
    print(f"設定読み込み成功: SPREADSHEET_ID={config.get('SPREADSHEET_ID', 'N/A')[:20]}...")
    sheets_handler = GoogleSheetsHandler(
        credentials_path=config['GOOGLE_CREDENTIALS_PATH'],
        spreadsheet_id=config['SPREADSHEET_ID']
    )
    print("✓ Googleスプレッドシートへの接続に成功しました")
except FileNotFoundError as e:
    import traceback
    print(f"設定ファイルエラー: {str(e)}")
    print("環境変数 SPREADSHEET_ID と GOOGLE_CREDENTIALS_JSON が設定されているか確認してください。")
    traceback.print_exc()
    sheets_handler = None
except Exception as e:
    import traceback
    print(f"初期化エラー: {str(e)}")
    print("詳細:")
    traceback.print_exc()
    sheets_handler = None


# LINE通知スケジューラー初期化
def check_and_send_notifications():
    """期日が近づいたTodoをチェックしてLINE通知を送信"""
    if not sheets_handler or not config:
        return
    
    channel_access_token = config.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    user_id = config.get('LINE_USER_ID', '')
    
    if not channel_access_token or not user_id:
        return
    
    try:
        # Todoを取得
        expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        
        # 通知を送信（3日前、1日前、当日）
        results = send_todo_notifications(
            todos=todos,
            channel_access_token=channel_access_token,
            user_id=user_id,
            days_before_list=[3, 1, 0]
        )
        
        # 結果をログに出力
        for timing, result in results.items():
            if result is True:
                print(f"✓ {timing}の通知を送信しました")
            elif result is False:
                print(f"✗ {timing}の通知送信に失敗しました")
    except Exception as e:
        print(f"通知チェックエラー: {str(e)}")


# スケジューラーを設定（毎日午前9時に実行）
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_and_send_notifications,
    trigger=CronTrigger(hour=9, minute=0),  # 毎日午前9時
    id='daily_todo_notification',
    name='Daily Todo Notification',
    replace_existing=True
)

# gunicornで起動する場合もスケジューラーを開始
# Renderではgunicorn経由で起動するため、ここでスケジューラーを開始
if not scheduler.running:
    try:
        scheduler.start()
        print("✓ LINE通知スケジューラーを開始しました（毎日午前9時に実行）")
    except Exception as e:
        print(f"⚠ スケジューラーの開始に失敗しました: {str(e)}")
        print("   LINE通知機能は無効になります")


@app.route('/')
def index():
    """Todo一覧表示"""
    # sheets_handlerがNoneの場合でもテンプレートを返す（エラーメッセージを表示）
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return render_template('index.html', todos=[], sort_by='default', filter_status='all'), 200
    
    try:
        # 並び替えパラメータを取得
        sort_by = request.args.get('sort', 'default')
        filter_status = request.args.get('status', 'all')
        
        # get_all_records()でTodo取得（expected_headersでヘッダーを明示的に指定）
        expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        
        # デフォルト値の設定（既存データの互換性のため）
        for todo in todos:
            if '重要度' not in todo or not todo['重要度']:
                todo['重要度'] = '中'
            if 'ステータス' not in todo or not todo['ステータス']:
                todo['ステータス'] = '未完了'
        
        # ステータスフィルター
        if filter_status != 'all':
            todos = [t for t in todos if t.get('ステータス', '未完了') == filter_status]
        
        # 並び替え
        if sort_by == 'priority':
            # 重要度順（高→中→低）
            priority_order = {'高': 1, '中': 2, '低': 3}
            todos.sort(key=lambda x: priority_order.get(x.get('重要度', '中'), 2))
        elif sort_by == 'due_date':
            # 期日順（近い順）
            todos.sort(key=lambda x: x.get('期日', '9999-12-31'))
        elif sort_by == 'priority_due':
            # 重要度→期日（重要度優先、同重要度は期日順）
            priority_order = {'高': 1, '中': 2, '低': 3}
            todos.sort(key=lambda x: (priority_order.get(x.get('重要度', '中'), 2), x.get('期日', '9999-12-31')))
        
        return render_template('index.html', todos=todos, sort_by=sort_by, filter_status=filter_status)
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
        
        # 重要度を取得（デフォルト: 中）
        priority = request.form.get('priority', '中').strip()
        if priority not in ['高', '中', '低']:
            priority = '中'
        
        try:
            todo_id = sheets_handler.create_todo(title, content, due_date, priority)
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
            expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
            todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
            todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
            if not todo:
                return redirect(url_for('index'))
            return render_template('edit.html', todo=todo)
        
        # 重要度とステータスを取得
        priority = request.form.get('priority', '中').strip()
        if priority not in ['高', '中', '低']:
            priority = '中'
        status = request.form.get('status', '未完了').strip()
        if status not in ['未完了', '完了']:
            status = '未完了'
        
        try:
            # update_todo()で編集内容を反映
            success = sheets_handler.update_todo(
                todo_id=todo_id,
                title=title,
                content=content,
                due_date=due_date,
                priority=priority,
                status=status
            )
            if success:
                flash('Todoを更新しました', 'success')
                return redirect(url_for('index'))
            else:
                flash('Todoが見つかりません', 'error')
                return redirect(url_for('index'))
        except Exception as e:
            flash(f'更新に失敗しました: {str(e)}', 'error')
            # 既存Todoを取得してフォームに表示
            expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
            todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
            todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
            if not todo:
                return redirect(url_for('index'))
            return render_template('edit.html', todo=todo)
    
    # GET：既存Todoをフォームに表示
    try:
        expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
        if not todo:
            flash('Todoが見つかりません', 'error')
            return redirect(url_for('index'))
        
        # デフォルト値の設定
        if '重要度' not in todo or not todo['重要度']:
            todo['重要度'] = '中'
        if 'ステータス' not in todo or not todo['ステータス']:
            todo['ステータス'] = '未完了'
        
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


@app.route('/complete/<int:todo_id>', methods=['POST'])
def complete_todo(todo_id):
    """Todo完了/未完了切り替え"""
    if not sheets_handler:
        flash('Googleスプレッドシートの接続に失敗しました。設定を確認してください。', 'error')
        return redirect(url_for('index'))
    
    try:
        # 現在のステータスを取得
        expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
        todos = sheets_handler.worksheet.get_all_records(expected_headers=expected_headers)
        todo = next((t for t in todos if str(t.get('ID', '')) == str(todo_id)), None)
        
        if not todo:
            flash('Todoが見つかりません', 'error')
            return redirect(url_for('index'))
        
        # 現在のステータスを反転
        current_status = todo.get('ステータス', '未完了')
        completed = (current_status != '完了')
        
        success = sheets_handler.complete_todo(todo_id, completed)
        if success:
            if completed:
                flash('Todoを完了しました', 'success')
            else:
                flash('Todoを未完了に戻しました', 'success')
        else:
            flash('Todoが見つかりません', 'error')
    except Exception as e:
        flash(f'更新に失敗しました: {str(e)}', 'error')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    # スケジューラーを開始
    try:
        scheduler.start()
        print("✓ LINE通知スケジューラーを開始しました（毎日午前9時に実行）")
    except Exception as e:
        print(f"⚠ スケジューラーの開始に失敗しました: {str(e)}")
        print("   LINE通知機能は無効になります")
    
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

