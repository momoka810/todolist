"""
LINE Messaging API連携モジュール

期日が近づいたTodoをLINE Messaging APIで通知します。
"""

from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from typing import List, Dict
from datetime import datetime, timedelta
import os


def send_line_message(channel_access_token: str, user_id: str, message: str) -> bool:
    """
    LINE Messaging APIでメッセージを送信
    
    Args:
        channel_access_token: LINE Messaging API チャネルアクセストークン
        user_id: 送信先ユーザーID
        message: 送信するメッセージ
    
    Returns:
        送信成功時True、失敗時False
    """
    if not channel_access_token:
        print("LINE Messaging API チャネルアクセストークンが設定されていません")
        return False
    
    if not user_id:
        print("LINE ユーザーIDが設定されていません")
        return False
    
    if not message:
        print("メッセージ本文が空です")
        return False
    
    try:
        line_bot_api = LineBotApi(channel_access_token)
        response = line_bot_api.push_message(
            to=user_id,
            messages=[TextSendMessage(text=message)]
        )
        print(f"✓ LINE通知を送信しました: {message[:50]}...")
        if hasattr(response, "request_id"):
            print(f"   request_id: {response.request_id}")
        return True
    except LineBotApiError as e:
        print(f"✗ LINE通知送信エラー: {e}")
        print(f"   ステータスコード: {e.status_code}")
        print(f"   エラー詳細: {e.error.message if hasattr(e, 'error') else 'N/A'}")
        return False
    except Exception as e:
        print(f"✗ LINE通知送信エラー: {str(e)}")
        print(f"   エラータイプ: {type(e).__name__}")
        return False


def check_upcoming_todos(todos: List[Dict], days_before: int = 3) -> List[Dict]:
    """
    期日が近づいているTodoを取得
    
    Args:
        todos: Todoのリスト
        days_before: 何日前から通知するか（デフォルト: 3日前）
    
    Returns:
        通知対象のTodoリスト
    """
    today = datetime.now().date()
    target_date = today + timedelta(days=days_before)
    
    upcoming_todos = []
    
    for todo in todos:
        # ステータスが「未完了」のもののみ
        if todo.get('ステータス', '未完了') != '未完了':
            continue
        
        # 期日を取得
        due_date_str = todo.get('期日', '')
        if not due_date_str:
            continue
        
        try:
            # 期日を日付型に変換
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            # 期日が指定日数以内の場合
            if due_date <= target_date and due_date >= today:
                upcoming_todos.append(todo)
        except ValueError:
            # 日付形式が正しくない場合はスキップ
            continue
    
    return upcoming_todos


def format_notification_message(todos: List[Dict], days_before: int) -> str:
    """
    通知メッセージをフォーマット
    
    Args:
        todos: 通知対象のTodoリスト
        days_before: 何日前の通知か
    
    Returns:
        フォーマットされたメッセージ
    """
    if not todos:
        return ""
    
    if days_before == 0:
        date_text = "今日"
    elif days_before == 1:
        date_text = "明日"
    else:
        date_text = f"{days_before}日後"
    
    # 重要度の表示用
    priority_emoji = {
        '高': '🔴',
        '中': '🟡',
        '低': '🟢'
    }
    
    message = f"📋 Todo期日通知（{date_text}）\n\n"
    
    for todo in todos:
        priority = todo.get('重要度', '中')
        emoji = priority_emoji.get(priority, '🟡')
        message += f"{emoji} {todo.get('タイトル', 'タイトルなし')}\n"
        message += f"   期日: {todo.get('期日', '')}\n"
        message += f"   重要度: {priority}\n\n"
    
    return message


def send_todo_notifications(
    todos: List[Dict],
    channel_access_token: str,
    user_id: str,
    days_before_list: List[int] = [3, 1, 0]
) -> Dict[str, bool]:
    """
    Todoの期日通知を送信
    
    Args:
        todos: Todoのリスト
        channel_access_token: LINE Messaging API チャネルアクセストークン
        user_id: 送信先ユーザーID
        days_before_list: 通知する日数リスト（デフォルト: [3, 1, 0] = 3日前、1日前、当日）
    
    Returns:
        各通知タイミングの送信結果（辞書形式）
    """
    results = {}
    
    if not channel_access_token:
        print("LINE Messaging API チャネルアクセストークンが設定されていません")
        return results
    
    if not user_id:
        print("LINE ユーザーIDが設定されていません")
        return results
    
    for days_before in days_before_list:
        upcoming_todos = check_upcoming_todos(todos, days_before)
        
        if upcoming_todos:
            message = format_notification_message(upcoming_todos, days_before)
            if message:
                success = send_line_message(channel_access_token, user_id, message)
                results[f"{days_before}日前" if days_before > 0 else "当日"] = success
        else:
            results[f"{days_before}日前" if days_before > 0 else "当日"] = None
    
    return results

