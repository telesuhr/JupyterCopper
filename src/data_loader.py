"""
LME Copper Data Loading Utility Module

This module provides standardized data loading functions for LME Copper analysis.
All notebooks should use this module instead of generating dummy data.

Author: LME Analysis Team
Date: 2025-07-06
"""

import pandas as pd
import psycopg2
import logging
from typing import Optional, Dict, Any, List, Tuple
import json
import os
from datetime import datetime, timedelta
import warnings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass

class DataValidationError(Exception):
    """Custom exception for data validation issues"""
    pass

class LMEDataLoader:
    """
    標準化されたLME銅データローダー
    
    このクラスは全てのノートブックで使用される標準的なデータアクセス機能を提供します。
    ダミーデータは生成せず、実際のデータベースからのデータ取得に特化しています。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        データローダーの初期化
        
        Args:
            config_path: 設定ファイルのパス (オプション)
        """
        self.connection = None
        self.config = self._load_config(config_path)
        self.table_priority = [
            'lme_copper_prices',
            'lme_copper_futures', 
            'lme_copper_spread_analysis'
        ]
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # デフォルト設定
        return {
            "database": {
                "host": "localhost",
                "database": "lme_copper_db", 
                "user": "Yusuke",
                "port": 5432
            }
        }
    
    def get_database_connection(self) -> psycopg2.extensions.connection:
        """
        データベース接続を取得
        
        Returns:
            psycopg2.extensions.connection: データベース接続
            
        Raises:
            DatabaseConnectionError: 接続に失敗した場合
        """
        if self.connection is None or self.connection.closed:
            try:
                db_config = self.config["database"]
                self.connection = psycopg2.connect(
                    host=db_config["host"],
                    database=db_config["database"],
                    user=db_config["user"],
                    port=db_config.get("port", 5432)
                )
                logger.info(f"データベース接続成功: {db_config['database']}")
            except Exception as e:
                error_msg = f"データベース接続エラー: {str(e)}"
                logger.error(error_msg)
                raise DatabaseConnectionError(error_msg)
        
        return self.connection
    
    def _check_table_exists(self, table_name: str) -> bool:
        """テーブルの存在確認"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
            """
            cursor.execute(query, (table_name,))
            exists = cursor.fetchone()[0]
            cursor.close()
            
            logger.info(f"テーブル '{table_name}' 存在確認: {'有' if exists else '無'}")
            return exists
            
        except Exception as e:
            logger.error(f"テーブル存在確認エラー: {str(e)}")
            return False
    
    def _get_table_info(self, table_name: str) -> Dict[str, Any]:
        """テーブル情報の取得"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # カラム情報取得
            query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
            """
            cursor.execute(query, (table_name,))
            columns = cursor.fetchall()
            
            # レコード数取得
            count_query = f"SELECT COUNT(*) FROM {table_name};"
            cursor.execute(count_query)
            record_count = cursor.fetchone()[0]
            
            # 日付範囲取得（可能な場合）
            date_range = None
            date_columns = [col[0] for col in columns if 'date' in col[0].lower()]
            if date_columns:
                date_col = date_columns[0]
                range_query = f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name};"
                cursor.execute(range_query)
                date_range = cursor.fetchone()
            
            cursor.close()
            
            return {
                'table_name': table_name,
                'columns': columns,
                'record_count': record_count,
                'date_range': date_range
            }
            
        except Exception as e:
            logger.error(f"テーブル情報取得エラー ({table_name}): {str(e)}")
            return {}
    
    def load_cash_3m_spread_data(self, 
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                include_volume: bool = True) -> pd.DataFrame:
        """
        Cash/3Mスプレッドデータの標準化された取得
        
        Args:
            start_date: 開始日 (YYYY-MM-DD形式)
            end_date: 終了日 (YYYY-MM-DD形式)
            include_volume: 出来高データを含めるか
            
        Returns:
            pd.DataFrame: Cash/3Mスプレッドデータ
            
        Raises:
            DataValidationError: データが取得できない場合
        """
        logger.info("Cash/3Mスプレッドデータの取得を開始")
        
        # 方法1: 直接スプレッドデータ取得 (CMCU0-3)
        spread_data = self._try_direct_spread_data(start_date, end_date, include_volume)
        if not spread_data.empty:
            logger.info(f"直接スプレッドデータ取得成功: {len(spread_data)} レコード")
            return spread_data
        
        # 方法2: Cash及び3M先物から計算
        calculated_spread = self._calculate_spread_from_components(start_date, end_date, include_volume)
        if not calculated_spread.empty:
            logger.info(f"計算スプレッドデータ取得成功: {len(calculated_spread)} レコード")
            return calculated_spread
        
        # 方法3: 包括的テーブル検索
        comprehensive_data = self._comprehensive_spread_search(start_date, end_date, include_volume)
        if not comprehensive_data.empty:
            logger.info(f"包括的検索スプレッドデータ取得成功: {len(comprehensive_data)} レコード")
            return comprehensive_data
        
        # 全ての方法が失敗した場合
        error_msg = self._generate_data_error_message("Cash/3Mスプレッドデータ", start_date, end_date)
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    
    def _try_direct_spread_data(self, 
                               start_date: Optional[str], 
                               end_date: Optional[str], 
                               include_volume: bool) -> pd.DataFrame:
        """直接スプレッドデータ取得 (CMCU0-3)"""
        try:
            conn = self.get_database_connection()
            
            # 各テーブルでCMCU0-3データを検索
            for table_name in self.table_priority:
                if not self._check_table_exists(table_name):
                    continue
                
                # テーブル構造に応じたクエリ構築
                query = self._build_spread_query(table_name, 'CMCU0-3', start_date, end_date, include_volume)
                
                if query:
                    df = pd.read_sql_query(query, conn)
                    if not df.empty:
                        df = self._validate_and_clean_data(df, 'spread')
                        logger.info(f"直接スプレッドデータ取得成功 ({table_name}): {len(df)} レコード")
                        return df
            
            logger.warning("直接スプレッドデータ (CMCU0-3) が見つかりません")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"直接スプレッドデータ取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_spread_from_components(self, 
                                        start_date: Optional[str], 
                                        end_date: Optional[str], 
                                        include_volume: bool) -> pd.DataFrame:
        """CashとFutureデータからスプレッドを計算"""
        try:
            # CashデータとFutureデータを取得
            cash_data = self._get_price_data('CMCU0', start_date, end_date, include_volume)
            future_data = self._get_price_data('CMCU3', start_date, end_date, include_volume)
            
            if cash_data.empty or future_data.empty:
                logger.warning("CashまたはFutureデータが不足しています")
                return pd.DataFrame()
            
            # 日付でマージ
            merged_data = pd.merge(
                cash_data, 
                future_data, 
                on='trade_date', 
                suffixes=('_cash', '_future'),
                how='inner'
            )
            
            if merged_data.empty:
                logger.warning("CashとFutureデータのマージに失敗")
                return pd.DataFrame()
            
            # スプレッド計算
            spread_data = pd.DataFrame({
                'trade_date': merged_data['trade_date'],
                'spread_value': merged_data['close_price_cash'] - merged_data['close_price_future'],
                'cash_price': merged_data['close_price_cash'],
                'future_price': merged_data['close_price_future']
            })
            
            if include_volume:
                spread_data['volume'] = merged_data.get('volume_cash', 0) + merged_data.get('volume_future', 0)
            
            spread_data = self._validate_and_clean_data(spread_data, 'spread')
            logger.info(f"スプレッド計算成功: {len(spread_data)} レコード")
            return spread_data
            
        except Exception as e:
            logger.error(f"スプレッド計算エラー: {str(e)}")
            return pd.DataFrame()
    
    def _comprehensive_spread_search(self, 
                                   start_date: Optional[str], 
                                   end_date: Optional[str], 
                                   include_volume: bool) -> pd.DataFrame:
        """包括的スプレッドデータ検索"""
        try:
            conn = self.get_database_connection()
            
            # 各テーブルでスプレッド関連データを検索
            for table_name in self.table_priority:
                if not self._check_table_exists(table_name):
                    continue
                
                # テーブル情報取得
                table_info = self._get_table_info(table_name)
                if not table_info:
                    continue
                
                # スプレッドカラムの検索
                columns = [col[0] for col in table_info['columns']]
                spread_columns = [col for col in columns if 'spread' in col.lower()]
                
                if spread_columns:
                    # スプレッドデータのクエリ
                    query = self._build_comprehensive_spread_query(
                        table_name, spread_columns, start_date, end_date, include_volume
                    )
                    
                    if query:
                        df = pd.read_sql_query(query, conn)
                        if not df.empty:
                            df = self._validate_and_clean_data(df, 'spread')
                            logger.info(f"包括的スプレッドデータ取得成功 ({table_name}): {len(df)} レコード")
                            return df
            
            logger.warning("包括的検索でもスプレッドデータが見つかりません")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"包括的スプレッドデータ検索エラー: {str(e)}")
            return pd.DataFrame()
    
    def load_3m_outright_price_data(self, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None,
                                   include_volume: bool = True) -> pd.DataFrame:
        """
        3M先物価格データの標準化された取得
        
        Args:
            start_date: 開始日 (YYYY-MM-DD形式)
            end_date: 終了日 (YYYY-MM-DD形式)
            include_volume: 出来高データを含めるか
            
        Returns:
            pd.DataFrame: 3M先物価格データ
            
        Raises:
            DataValidationError: データが取得できない場合
        """
        logger.info("3M先物価格データの取得を開始")
        
        # CMCU3データを取得
        price_data = self._get_price_data('CMCU3', start_date, end_date, include_volume)
        
        if not price_data.empty:
            logger.info(f"3M先物価格データ取得成功: {len(price_data)} レコード")
            return price_data
        
        # 全ての方法が失敗した場合
        error_msg = self._generate_data_error_message("3M先物価格データ", start_date, end_date)
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    
    def _get_price_data(self, 
                       ric_code: str, 
                       start_date: Optional[str], 
                       end_date: Optional[str], 
                       include_volume: bool) -> pd.DataFrame:
        """指定されたRICの価格データを取得"""
        try:
            conn = self.get_database_connection()
            
            for table_name in self.table_priority:
                if not self._check_table_exists(table_name):
                    continue
                
                query = self._build_price_query(table_name, ric_code, start_date, end_date, include_volume)
                
                if query:
                    df = pd.read_sql_query(query, conn)
                    if not df.empty:
                        df = self._validate_and_clean_data(df, 'price')
                        logger.info(f"価格データ取得成功 ({table_name}, {ric_code}): {len(df)} レコード")
                        return df
            
            logger.warning(f"価格データが見つかりません: {ric_code}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"価格データ取得エラー ({ric_code}): {str(e)}")
            return pd.DataFrame()
    
    def _build_spread_query(self, 
                           table_name: str, 
                           ric_code: str, 
                           start_date: Optional[str], 
                           end_date: Optional[str], 
                           include_volume: bool) -> Optional[str]:
        """スプレッドデータ用クエリの構築"""
        try:
            table_info = self._get_table_info(table_name)
            if not table_info:
                return None
            
            columns = [col[0] for col in table_info['columns']]
            
            # 基本的なカラムの特定
            date_col = self._find_date_column(columns)
            price_col = self._find_price_column(columns)
            ric_col = self._find_ric_column(columns)
            
            if not all([date_col, price_col, ric_col]):
                return None
            
            # SELECT句
            select_columns = [date_col, price_col]
            if include_volume:
                volume_col = self._find_volume_column(columns)
                if volume_col:
                    select_columns.append(volume_col)
            
            # クエリ構築
            query = f"""
            SELECT {', '.join(select_columns)}
            FROM {table_name}
            WHERE {ric_col} = '{ric_code}'
            """
            
            # 日付フィルタ
            if start_date:
                query += f" AND {date_col} >= '{start_date}'"
            if end_date:
                query += f" AND {date_col} <= '{end_date}'"
            
            query += f" ORDER BY {date_col};"
            
            return query
            
        except Exception as e:
            logger.error(f"スプレッドクエリ構築エラー: {str(e)}")
            return None
    
    def _build_price_query(self, 
                          table_name: str, 
                          ric_code: str, 
                          start_date: Optional[str], 
                          end_date: Optional[str], 
                          include_volume: bool) -> Optional[str]:
        """価格データ用クエリの構築"""
        try:
            table_info = self._get_table_info(table_name)
            if not table_info:
                return None
            
            columns = [col[0] for col in table_info['columns']]
            
            # 基本的なカラムの特定
            date_col = self._find_date_column(columns)
            price_col = self._find_price_column(columns)
            ric_col = self._find_ric_column(columns)
            
            if not all([date_col, price_col, ric_col]):
                return None
            
            # SELECT句
            select_columns = [
                f"{date_col} as trade_date",
                f"{price_col} as close_price"
            ]
            
            if include_volume:
                volume_col = self._find_volume_column(columns)
                if volume_col:
                    select_columns.append(f"{volume_col} as volume")
            
            # クエリ構築
            query = f"""
            SELECT {', '.join(select_columns)}
            FROM {table_name}
            WHERE {ric_col} = '{ric_code}'
            """
            
            # 日付フィルタ
            if start_date:
                query += f" AND {date_col} >= '{start_date}'"
            if end_date:
                query += f" AND {date_col} <= '{end_date}'"
            
            query += f" ORDER BY {date_col};"
            
            return query
            
        except Exception as e:
            logger.error(f"価格クエリ構築エラー: {str(e)}")
            return None
    
    def _build_comprehensive_spread_query(self, 
                                        table_name: str, 
                                        spread_columns: List[str], 
                                        start_date: Optional[str], 
                                        end_date: Optional[str], 
                                        include_volume: bool) -> Optional[str]:
        """包括的スプレッドデータ用クエリの構築"""
        try:
            table_info = self._get_table_info(table_name)
            if not table_info:
                return None
            
            columns = [col[0] for col in table_info['columns']]
            
            # 基本的なカラムの特定
            date_col = self._find_date_column(columns)
            
            if not date_col:
                return None
            
            # SELECT句
            select_columns = [f"{date_col} as trade_date"]
            
            # スプレッドカラムを追加
            for spread_col in spread_columns:
                select_columns.append(f"{spread_col} as spread_value")
                break  # 最初のスプレッドカラムのみ使用
            
            if include_volume:
                volume_col = self._find_volume_column(columns)
                if volume_col:
                    select_columns.append(f"{volume_col} as volume")
            
            # クエリ構築
            query = f"""
            SELECT {', '.join(select_columns)}
            FROM {table_name}
            WHERE {spread_columns[0]} IS NOT NULL
            """
            
            # 日付フィルタ
            if start_date:
                query += f" AND {date_col} >= '{start_date}'"
            if end_date:
                query += f" AND {date_col} <= '{end_date}'"
            
            query += f" ORDER BY {date_col};"
            
            return query
            
        except Exception as e:
            logger.error(f"包括的スプレッドクエリ構築エラー: {str(e)}")
            return None
    
    def _find_date_column(self, columns: List[str]) -> Optional[str]:
        """日付カラムの特定"""
        date_patterns = ['trade_date', 'date', 'timestamp', 'created_date']
        for pattern in date_patterns:
            for col in columns:
                if pattern in col.lower():
                    return col
        return None
    
    def _find_price_column(self, columns: List[str]) -> Optional[str]:
        """価格カラムの特定"""
        price_patterns = ['last_price', 'close_price', 'price', 'value', 'close']
        for pattern in price_patterns:
            for col in columns:
                if pattern in col.lower():
                    return col
        return None
    
    def _find_ric_column(self, columns: List[str]) -> Optional[str]:
        """RICカラムの特定"""
        ric_patterns = ['ric_code', 'ric', 'symbol', 'instrument']
        for pattern in ric_patterns:
            for col in columns:
                if pattern in col.lower():
                    return col
        return None
    
    def _find_volume_column(self, columns: List[str]) -> Optional[str]:
        """出来高カラムの特定"""
        volume_patterns = ['volume', 'vol', 'quantity', 'size']
        for pattern in volume_patterns:
            for col in columns:
                if pattern in col.lower():
                    return col
        return None
    
    def _validate_and_clean_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """データの検証とクリーニング"""
        try:
            if df.empty:
                return df
            
            # 日付カラムの処理
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date')
            
            # 数値カラムの処理
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                # 異常値の除去（3σ範囲外）
                if len(df) > 10:  # 十分なデータがある場合のみ
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        df = df[abs(df[col] - mean) <= 3 * std]
            
            # 重複の除去
            if 'trade_date' in df.columns:
                df = df.drop_duplicates(subset=['trade_date'])
            
            # 欠損値の処理
            df = df.dropna(subset=[col for col in df.columns if 'price' in col.lower() or 'value' in col.lower()])
            
            logger.info(f"データ検証・クリーニング完了: {len(df)} レコード")
            return df
            
        except Exception as e:
            logger.error(f"データ検証エラー: {str(e)}")
            return df
    
    def _generate_data_error_message(self, 
                                   data_type: str, 
                                   start_date: Optional[str], 
                                   end_date: Optional[str]) -> str:
        """データ取得エラーメッセージの生成"""
        error_msg = f"""
        🚨 {data_type}の取得に失敗しました

        【検索条件】
        - 期間: {start_date or '指定なし'} ～ {end_date or '指定なし'}
        - 検索テーブル: {', '.join(self.table_priority)}

        【トラブルシューティング】
        1. データベース接続を確認してください
        2. 以下のコマンドでテーブルの存在を確認してください:
           psql -h localhost -U Yusuke -d lme_copper_db -c "\\dt"
        
        3. データの存在を確認してください:
           SELECT table_name, COUNT(*) FROM information_schema.tables 
           WHERE table_name IN ('lme_copper_prices', 'lme_copper_futures', 'lme_copper_spread_analysis') 
           GROUP BY table_name;
        
        4. データが存在する場合は、RICコードを確認してください:
           SELECT DISTINCT ric FROM lme_copper_prices LIMIT 10;

        【注意】
        ダミーデータは生成されません。実際のデータベースの修正が必要です。
        """
        return error_msg
    
    def get_available_data_summary(self) -> Dict[str, Any]:
        """利用可能なデータの要約を取得"""
        try:
            conn = self.get_database_connection()
            summary = {
                'database_connected': True,
                'tables': {}
            }
            
            for table_name in self.table_priority:
                if self._check_table_exists(table_name):
                    table_info = self._get_table_info(table_name)
                    summary['tables'][table_name] = table_info
            
            logger.info("データ要約取得成功")
            return summary
            
        except Exception as e:
            logger.error(f"データ要約取得エラー: {str(e)}")
            return {
                'database_connected': False,
                'error': str(e),
                'tables': {}
            }
    
    def close_connection(self):
        """データベース接続のクローズ"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("データベース接続をクローズしました")

# 便利関数
def create_data_loader(config_path: Optional[str] = None) -> LMEDataLoader:
    """データローダーのファクトリ関数"""
    return LMEDataLoader(config_path)

def load_cash_3m_spread(start_date: Optional[str] = None, 
                       end_date: Optional[str] = None,
                       include_volume: bool = True) -> pd.DataFrame:
    """簡単なCash/3Mスプレッドデータ取得"""
    loader = create_data_loader()
    try:
        return loader.load_cash_3m_spread_data(start_date, end_date, include_volume)
    finally:
        loader.close_connection()

def load_3m_outright_price(start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          include_volume: bool = True) -> pd.DataFrame:
    """簡単な3M先物価格データ取得"""
    loader = create_data_loader()
    try:
        return loader.load_3m_outright_price_data(start_date, end_date, include_volume)
    finally:
        loader.close_connection()

def get_data_summary() -> Dict[str, Any]:
    """利用可能なデータの要約"""
    loader = create_data_loader()
    try:
        return loader.get_available_data_summary()
    finally:
        loader.close_connection()

if __name__ == "__main__":
    # テスト実行
    print("=== LME Data Loader テスト ===")
    
    # データ要約の取得
    summary = get_data_summary()
    print("利用可能なデータ:")
    for table_name, info in summary.get('tables', {}).items():
        print(f"  {table_name}: {info.get('record_count', 0)} レコード")
    
    # Cash/3Mスプレッドデータのテスト
    try:
        spread_data = load_cash_3m_spread()
        print(f"\nCash/3Mスプレッドデータ: {len(spread_data)} レコード")
        if not spread_data.empty:
            print(spread_data.head())
    except Exception as e:
        print(f"Cash/3Mスプレッドデータエラー: {e}")
    
    # 3M先物価格データのテスト
    try:
        price_data = load_3m_outright_price()
        print(f"\n3M先物価格データ: {len(price_data)} レコード")
        if not price_data.empty:
            print(price_data.head())
    except Exception as e:
        print(f"3M先物価格データエラー: {e}")