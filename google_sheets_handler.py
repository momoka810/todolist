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
    
    # ヘッダー定義（拡張版）
    new_headers = ["ID", "タイトル", "内容", "期日", "重要度", "ステータス", "作成日時", "更新日時", "完了日時"]
    
    # ヘッダーが存在しない場合は設定
    all_values = worksheet.get_all_values()
    if not all_values or len(all_values) == 0 or (len(all_values) > 0 and len(all_values[0]) > 0 and all_values[0][0] != "ID"):
        worksheet.clear()
        worksheet.append_row(new_headers)
        # ヘッダー行を太字にする
        try:
            worksheet.format(f"A1:I1", {
                "textFormat": {
                    "bold": True
                }
            })
        except:
            pass  # フォーマット設定が失敗しても続行
    else:
        # 既存ヘッダーを確認して、新カラムを追加する必要があるかチェック
        existing_headers = all_values[0] if all_values else []
        
        # 旧形式（6カラム）から新形式（9カラム）への移行
        if len(existing_headers) == 6 and existing_headers == ["ID", "タイトル", "内容", "期日", "作成日時", "更新日時"]:
            # ヘッダー行を更新
            worksheet.update("A1:I1", [new_headers])
            
            # 既存データにデフォルト値を追加
            if len(all_values) > 1:  # データ行がある場合
                for row_idx in range(2, len(all_values) + 1):  # 2行目から
                    row = all_values[row_idx - 1]
                    if len(row) >= 4 and row[0]:  # IDが存在する行のみ
                        # 既存の値を保持
                        existing_id = row[0]
                        existing_title = row[1] if len(row) > 1 else ""
                        existing_content = row[2] if len(row) > 2 else ""
                        existing_due_date = row[3] if len(row) > 3 else ""
                        existing_created_at = row[4] if len(row) > 4 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        existing_updated_at = row[5] if len(row) > 5 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 新形式で行全体を更新
                        worksheet.update(f"A{row_idx}:I{row_idx}", [[
                            existing_id,
                            existing_title,
                            existing_content,
                            existing_due_date,
                            "中",  # 重要度（デフォルト）
                            "未完了",  # ステータス（デフォルト）
                            existing_created_at,  # 作成日時
                            existing_updated_at,  # 更新日時
                            ""  # 完了日時（空）
                        ]])
            
            # ヘッダー行を太字にする
            try:
                worksheet.format("A1:I1", {
                    "textFormat": {
                        "bold": True
                    }
                })
            except:
                pass
        elif len(existing_headers) < 9:
            # ヘッダーが不完全な場合、更新
            worksheet.update("A1:I1", [new_headers])
            try:
                worksheet.format("A1:I1", {
                    "textFormat": {
                        "bold": True
                    }
                })
            except:
                pass
    
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
    
    def create_todo(self, title: str, content: str, due_date: str, priority: str = "中") -> int:
        """
        Todoを作成
        
        Args:
            title: タイトル
            content: 内容
            due_date: 期日（YYYY-MM-DD形式）
            priority: 重要度（高/中/低、デフォルト: 中）
            
        Returns:
            作成されたTodoのID
        """
        todo_id = self._get_next_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 重要度の検証
        if priority not in ["高", "中", "低"]:
            priority = "中"
        
        self.worksheet.append_row([
            str(todo_id),
            title,
            content,
            due_date,
            priority,  # 重要度
            "未完了",  # ステータス
            now,  # 作成日時
            now,  # 更新日時
            ""  # 完了日時（空）
        ])
        
        return todo_id
    
    def update_todo(
        self,
        todo_id: int,
        title: str,
        content: str,
        due_date: str,
        priority: str = None,
        status: str = None
    ) -> bool:
        """
        Todoを更新
        
        Args:
            todo_id: TodoのID
            title: タイトル
            content: 内容
            due_date: 期日（YYYY-MM-DD形式）
            priority: 重要度（高/中/低、Noneの場合は既存値を保持）
            status: ステータス（未完了/完了、Noneの場合は既存値を保持）
            
        Returns:
            更新成功時True、Todoが見つからない場合False
        """
        all_values = self.worksheet.get_all_values()
        
        for idx, row in enumerate(all_values[1:], start=2):  # ヘッダーを除く、行番号は2から
            if row and row[0].isdigit() and int(row[0]) == todo_id:
                # 既存の値を取得（互換性のため）
                created_at = row[6] if len(row) > 6 else (row[4] if len(row) > 4 else datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 重要度とステータスの処理
                if priority is None:
                    priority = row[4] if len(row) > 4 and row[4] in ["高", "中", "低"] else "中"
                else:
                    if priority not in ["高", "中", "低"]:
                        priority = "中"
                
                if status is None:
                    status = row[5] if len(row) > 5 and row[5] in ["未完了", "完了"] else "未完了"
                
                # 完了日時の処理
                completed_at = ""
                if status == "完了":
                    # 既存の完了日時がある場合は保持、ない場合は現在時刻を設定
                    completed_at = row[8] if len(row) > 8 and row[8] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # 未完了の場合は空にする
                    completed_at = ""
                
                # 行を更新（9カラム）
                self.worksheet.update(f"A{idx}:I{idx}", [[
                    str(todo_id),
                    title,
                    content,
                    due_date,
                    priority,  # 重要度
                    status,  # ステータス
                    created_at,  # 作成日時
                    updated_at,  # 更新日時
                    completed_at  # 完了日時
                ]])
                
                return True
        
        return False
    
    def complete_todo(self, todo_id: int, completed: bool = True) -> bool:
        """
        Todoの完了ステータスを更新
        
        Args:
            todo_id: TodoのID
            completed: Trueで完了、Falseで未完了に戻す
            
        Returns:
            更新成功時True、Todoが見つからない場合False
        """
        all_values = self.worksheet.get_all_values()
        
        for idx, row in enumerate(all_values[1:], start=2):  # ヘッダーを除く、行番号は2から
            if row and row[0].isdigit() and int(row[0]) == todo_id:
                # 既存の値を取得（カラム位置を確認）
                title = row[1] if len(row) > 1 else ""
                content = row[2] if len(row) > 2 else ""
                due_date = row[3] if len(row) > 3 else ""
                
                # 重要度の取得（カラム位置を確認）
                if len(row) > 4 and row[4] in ["高", "中", "低"]:
                    priority = row[4]
                else:
                    priority = "中"
                
                # 作成日時と更新日時の取得（カラム位置を確認）
                if len(row) >= 9:
                    # 新形式（9カラム）
                    created_at = row[6] if len(row) > 6 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif len(row) >= 6:
                    # 旧形式（6カラム）
                    created_at = row[4] if len(row) > 4 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # ステータスと完了日時を設定
                if completed:
                    status = "完了"
                    completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    status = "未完了"
                    completed_at = ""
                
                # 行を更新（9カラム）
                self.worksheet.update(f"A{idx}:I{idx}", [[
                    str(todo_id),
                    title,
                    content,
                    due_date,
                    priority,
                    status,
                    created_at,
                    updated_at,
                    completed_at
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

