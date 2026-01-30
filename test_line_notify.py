"""
LINE通知機能のテストスクリプト

このスクリプトを実行すると、現在のTodoをチェックしてLINE通知をテスト送信します。
"""

from line_notifier import send_todo_notifications, send_line_message
from google_sheets_handler import GoogleSheetsHandler
import json
import os

def main():
    print("=== LINE通知機能 テスト ===\n")
    
    # 設定を読み込み
    try:
        if os.getenv('SPREADSHEET_ID'):
            # 環境変数から読み込み（Render用）
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
        
        print("✓ 設定ファイルを読み込みました")
    except Exception as e:
        print(f"✗ 設定ファイルの読み込みに失敗しました: {str(e)}")
        return
    
    # LINE Messaging API の設定確認
    channel_access_token = config.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    user_id = config.get('LINE_USER_ID', '')
    
    if not channel_access_token:
        print("\n⚠ LINE Messaging API チャネルアクセストークンが設定されていません")
        print("config.json に 'LINE_CHANNEL_ACCESS_TOKEN' を追加するか、")
        print("環境変数 'LINE_CHANNEL_ACCESS_TOKEN' を設定してください。")
        return
    
    if not user_id:
        print("\n⚠ LINE ユーザーIDが設定されていません")
        print("config.json に 'LINE_USER_ID' を追加するか、")
        print("環境変数 'LINE_USER_ID' を設定してください。")
        return
    
    print(f"✓ チャネルアクセストークンが設定されています（最初の10文字: {channel_access_token[:10]}...）")
    print(f"✓ ユーザーIDが設定されています（最初の10文字: {user_id[:10]}...）\n")
    
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
    
    # テストメニュー
    print("=== テストメニュー ===")
    print("1. 簡単なテストメッセージを送信")
    print("2. 期日が近いTodoをチェックして通知を送信（3日前、1日前、当日）")
    print("3. 当日のTodoのみ通知を送信")
    print("4. すべての未完了Todoを通知（テスト用）")
    print()
    
    choice = input("選択してください (1-4): ").strip()
    
    if choice == "1":
        # 簡単なテストメッセージ
        test_message = "📋 Todoリストアプリからのテスト通知です。\n\nこのメッセージが表示されれば、LINE通知機能は正常に動作しています。"
        print("\nテストメッセージを送信します...")
        success = send_line_message(channel_access_token, user_id, test_message)
        if success:
            print("✓ テストメッセージを送信しました！")
        else:
            print("✗ テストメッセージの送信に失敗しました")
    
    elif choice == "2":
        # 通常の通知（3日前、1日前、当日）
        print("\n期日が近いTodoをチェックして通知を送信します...")
        results = send_todo_notifications(
            todos=todos,
            channel_access_token=channel_access_token,
            user_id=user_id,
            days_before_list=[3, 1, 0]
        )
        
        print("\n=== 送信結果 ===")
        for timing, result in results.items():
            if result is True:
                print(f"✓ {timing}: 通知を送信しました")
            elif result is False:
                print(f"✗ {timing}: 通知送信に失敗しました")
            else:
                print(f"- {timing}: 通知対象のTodoがありませんでした")
    
    elif choice == "3":
        # 当日のTodoのみ
        print("\n当日のTodoをチェックして通知を送信します...")
        results = send_todo_notifications(
            todos=todos,
            channel_access_token=channel_access_token,
            user_id=user_id,
            days_before_list=[0]
        )
        
        if results.get("当日") is True:
            print("✓ 当日のTodoの通知を送信しました")
        elif results.get("当日") is False:
            print("✗ 通知送信に失敗しました")
        else:
            print("- 当日が期日のTodoはありませんでした")
    
    elif choice == "4":
        # すべての未完了Todoを通知（テスト用）
        print("\nすべての未完了Todoを通知します（テスト用）...")
        uncompleted_todos = [t for t in todos if t.get('ステータス', '未完了') == '未完了']
        
        if not uncompleted_todos:
            print("- 未完了のTodoがありません")
        else:
            # 重要度の表示用
            priority_emoji = {
                '高': '🔴',
                '中': '🟡',
                '低': '🟢'
            }
            
            message = "📋 すべての未完了Todo（テスト通知）\n\n"
            for todo in uncompleted_todos:
                priority = todo.get('重要度', '中')
                emoji = priority_emoji.get(priority, '🟡')
                message += f"{emoji} {todo.get('タイトル', 'タイトルなし')}\n"
                message += f"   期日: {todo.get('期日', '')}\n"
                message += f"   重要度: {priority}\n\n"
            
            success = send_line_message(channel_access_token, user_id, message)
            if success:
                print(f"✓ {len(uncompleted_todos)}件のTodoを通知しました")
            else:
                print("✗ 通知送信に失敗しました")
    
    else:
        print("無効な選択です")
        return
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()

