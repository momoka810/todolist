"""
Googleスプレッドシート連携モジュール

TodoリストのデータをGoogleスプレッドシートで管理します。
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Optional, Dict
import os
from datetime import datetime


def connect_sheet(credentials_path: str, spreadsheet_id: str):
    """
    Googleスプレッドシートに接続する
    
    Args:
        credentials_path: サービスアカウントの認証情報JSONファイルのパス
        spreadsheet_id: スプレッドシートID
    
    Returns:
        gspread.Clientオブジェクトとワークシート（シート1枚目）のタプル
    """
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"認証情報ファイルが見つかりません: {credentials_path}\n"
            "Google Cloud Consoleでサービスアカウントを作成し、"
            "認証情報JSONファイルをダウンロードしてください。"
        )
    
    # スコープを設定
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # サービスアカウントの認証情報を読み込み
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path,
            scope
        )
    except Exception as e:
        raise Exception(
            f"認証情報ファイルの読み込みに失敗しました: {str(e)}\n"
            "サービスアカウントのJSONファイルが正しい形式か確認してください。"
        )
    
    # クライアントを作成
    client = gspread.authorize(credentials)
    
    # スプレッドシートを開く
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(
            f"スプレッドシートが見つかりません: {spreadsheet_id}\n"
            "スプレッドシートIDが正しいか、サービスアカウントにアクセス権限があるか確認してください。"
        )
    
    # シート1枚目（最初のワークシート）を取得
    worksheet = spreadsheet.sheet1
    
    # ヘッダーが存在しない場合は設定
    all_values = worksheet.get_all_values()
    if not all_values or len(all_values) == 0 or (len(all_values) > 0 and len(all_values[0]) > 0 and all_values[0][0] != "ID"):
        worksheet.clear()
        worksheet.append_row([
            "ID", "タイトル", "内容", "期日", "作成日時", "更新日時"
        ])
        # ヘッダー行を太字にする
        try:
            worksheet.format("A1:F1", {
                "textFormat": {
                    "bold": True
                }
            })
        except:
            pass  # フォーマット設定が失敗しても続行
    
    return client, worksheet


class GoogleSheetsHandler:
    """GoogleスプレッドシートでTodoデータを管理するクラス"""
    
    def __init__(
        self,
        credentials_path: str,
        spreadsheet_id: str
    ):
        """
        初期化
        
        Args:
            credentials_path: サービスアカウントの認証情報JSONファイルのパス
            spreadsheet_id: スプレッドシートID
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.worksheet = None
        self._connect()
    
    def _connect(self):
        """Googleスプレッドシートに接続"""
        self.client, self.worksheet = connect_sheet(
            self.credentials_path,
            self.spreadsheet_id
        )
    
    def _get_next_id(self) -> int:
        """次のIDを取得"""
        all_values = self.worksheet.get_all_values()
        if len(all_values) <= 1:  # ヘッダーのみ
            return 1
        
        # 既存のIDを取得して最大値を求める
        ids = []
        for row in all_values[1:]:  # ヘッダーを除く
            if row and row[0].isdigit():
                ids.append(int(row[0]))
        
        return max(ids) + 1 if ids else 1
    
    def get_all_todos(self) -> List[Dict]:
        """
        すべてのTodoを取得
        
        Returns:
            Todoのリスト（各Todoは辞書形式）
        """
        all_values = self.worksheet.get_all_values()
        if len(all_values) <= 1:  # ヘッダーのみ
            return []
        
        todos = []
        for row in all_values[1:]:  # ヘッダーを除く
            if row and row[0].isdigit():  # IDが存在する行のみ
                todos.append({
                    'id': int(row[0]),
                    'title': row[1] if len(row) > 1 else '',
                    'content': row[2] if len(row) > 2 else '',
                    'due_date': row[3] if len(row) > 3 else '',
                    'created_at': row[4] if len(row) > 4 else '',
                    'updated_at': row[5] if len(row) > 5 else ''
                })
        
        return todos
    
    def get_todo(self, todo_id: int) -> Optional[Dict]:
        """
        指定されたIDのTodoを取得
        
        Args:
            todo_id: TodoのID
            
        Returns:
            Todoの辞書、見つからない場合はNone
        """
        all_values = self.worksheet.get_all_values()
        
        for row in all_values[1:]:  # ヘッダーを除く
            if row and row[0].isdigit() and int(row[0]) == todo_id:
                return {
                    'id': int(row[0]),
                    'title': row[1] if len(row) > 1 else '',
                    'content': row[2] if len(row) > 2 else '',
                    'due_date': row[3] if len(row) > 3 else '',
                    'created_at': row[4] if len(row) > 4 else '',
                    'updated_at': row[5] if len(row) > 5 else ''
                }
        
        return None
    
    def create_todo(self, title: str, content: str, due_date: str) -> int:
        """
        Todoを作成
        
        Args:
            title: タイトル
            content: 内容
            due_date: 期日（YYYY-MM-DD形式）
            
        Returns:
            作成されたTodoのID
        """
        todo_id = self._get_next_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.worksheet.append_row([
            str(todo_id),
            title,
            content,
            due_date,
            now,
            now
        ])
        
        return todo_id
    
    def update_todo(
        self,
        todo_id: int,
        title: str,
        content: str,
        due_date: str
    ) -> bool:
        """
        Todoを更新
        
        Args:
            todo_id: TodoのID
            title: タイトル
            content: 内容
            due_date: 期日（YYYY-MM-DD形式）
            
        Returns:
            更新成功時True、Todoが見つからない場合False
        """
        all_values = self.worksheet.get_all_values()
        
        for idx, row in enumerate(all_values[1:], start=2):  # ヘッダーを除く、行番号は2から
            if row and row[0].isdigit() and int(row[0]) == todo_id:
                # 既存の作成日時を保持
                created_at = row[4] if len(row) > 4 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 行を更新
                self.worksheet.update(f"A{idx}:F{idx}", [[
                    str(todo_id),
                    title,
                    content,
                    due_date,
                    created_at,
                    updated_at
                ]])
                
                return True
        
        return False
    
    def delete_todo(self, todo_id: int) -> bool:
        """
        Todoを削除
        
        Args:
            todo_id: TodoのID
            
        Returns:
            削除成功時True、Todoが見つからない場合False
        """
        all_values = self.worksheet.get_all_values()
        
        for idx, row in enumerate(all_values[1:], start=2):  # ヘッダーを除く、行番号は2から
            if row and row[0].isdigit() and int(row[0]) == todo_id:
                # 行を削除
                self.worksheet.delete_rows(idx)
                return True
        
        return False

