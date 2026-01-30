"""
LINE通知機能のテストスクリプト

このスクリプトを実行すると、実際の通知と同じ形式でLINEに送信します。
期日が近いTodoをチェックして、実際の通知形式で送信します。
"""

from line_notifier import send_todo_notifications, send_line_message, format_notification_message, check_upcoming_todos
from google_sheets_handler import GoogleSheetsHandler
import json
import os

def main():
    print("=== LINE通知 テスト（実際の通知形式） ===\n")
    
    # 設定を読み込み
    try:
        if os.getenv('SPREADSHEET_ID'):
            # 環境変数から読み込み
            config = {
                'GOOGLE_CREDENTIALS_PATH': os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json'),
                'SPREADSHEET_ID': os.getenv('SPREADSHEET_ID'),
                'LINE_CHANNEL_ACCESS_TOKEN': os.getenv('LINE_CHANNEL_ACCESS_TOKEN', ''),
                'LINE_USER_ID': os.getenv('LINE_USER_ID', '')
            }
        else:
            # config.jsonから読み込み
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        channel_access_token = config.get('LINE_CHANNEL_ACCESS_TOKEN', '')
        user_id = config.get('LINE_USER_ID', '')
        
        if not channel_access_token:
            print("⚠ LINE Messaging API チャネルアクセストークンが設定されていません")
            print("\nconfig.json に 'LINE_CHANNEL_ACCESS_TOKEN' を追加してください。")
            print("または環境変数 'LINE_CHANNEL_ACCESS_TOKEN' を設定してください。")
            return
        
        if not user_id:
            print("⚠ LINE ユーザーIDが設定されていません")
            print("\nconfig.json に 'LINE_USER_ID' を追加してください。")
            print("または環境変数 'LINE_USER_ID' を設定してください。")
            return
        
        print(f"✓ チャネルアクセストークンが設定されています（長さ: {len(channel_access_token)}文字）")
        print(f"✓ ユーザーIDが設定されています（長さ: {len(user_id)}文字）\n")
    except Exception as e:
        print(f"✗ 設定の読み込みに失敗しました: {str(e)}")
        return
    
    # スプレッドシートからTodoを取得
    try:
        handler = GoogleSheetsHandler(
            credentials_path=config['GOOGLE_CREDENTIALS_PATH'],
            spreadsheet_id=config['SPREADSHEET_ID']
        )
        print("✓ Googleスプレッドシートに接続しました\n")
    except Exception as e:
        print(f"✗ スプレッドシートへの接続に失敗しました: {str(e)}")
        return
    
    # Todoを取得
    try:
        expected_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
        todos = handler.worksheet.get_all_records(expected_headers=expected_headers)
        print(f"✓ Todoを取得しました（{len(todos)}件）\n")
    except Exception as e:
        print(f"✗ Todoの取得に失敗しました: {str(e)}")
        return
    
    # 実際の通知形式で送信（当日のTodoをチェック）
    print("期日が近いTodoをチェックして、実際の通知形式で送信します...\n")
    
    # 当日、1日前、3日前のTodoをチェック
    for days_before in [0, 1, 3]:
        upcoming_todos = check_upcoming_todos(todos, days_before)
        
        if upcoming_todos:
            message = format_notification_message(upcoming_todos, days_before)
            if message:
                print(f"【{days_before}日前の通知】")
                print(f"通知対象: {len(upcoming_todos)}件のTodo")
                print(f"メッセージ内容:\n{message}")
                
                success = send_line_message(channel_access_token, user_id, message)
                
                if success:
                    print("✓ 通知を送信しました！\n")
                else:
                    print("✗ 通知送信に失敗しました\n")
            else:
                print(f"- {days_before}日前: 通知対象のTodoがありません\n")
        else:
            print(f"- {days_before}日前: 通知対象のTodoがありません\n")
    
    # 通知対象がない場合のテスト送信
    all_checked = False
    for days_before in [0, 1, 3]:
        upcoming_todos = check_upcoming_todos(todos, days_before)
        if upcoming_todos:
            all_checked = True
            break
    
    if not all_checked:
        print("通知対象のTodoがないため、テスト用の通知を送信します...\n")
        # すべての未完了Todoを表示（テスト用）
        uncompleted_todos = [t for t in todos if t.get('ステータス', '未完了') == '未完了']
        
        if uncompleted_todos:
            # 重要度の表示用
            priority_emoji = {
                '高': '🔴',
                '中': '🟡',
                '低': '🟢'
            }
            
            message = "📋 Todo一覧（テスト通知）\n\n"
            for todo in uncompleted_todos[:5]:  # 最大5件まで
                priority = todo.get('重要度', '中')
                emoji = priority_emoji.get(priority, '🟡')
                message += f"{emoji} {todo.get('タイトル', 'タイトルなし')}\n"
                message += f"   期日: {todo.get('期日', '')}\n"
                message += f"   重要度: {priority}\n\n"
            
            print(f"メッセージ内容:\n{message}")
            success = send_line_message(channel_access_token, user_id, message)
            
            if success:
                print("✓ テスト通知を送信しました！")
                print("LINEアプリで通知を確認してください。")
            else:
                print("✗ テスト通知の送信に失敗しました")
        else:
            print("未完了のTodoがありません。")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()

