#!/usr/bin/env python3
"""
LME Copper Futures (1-36 Months) Historical Data Collector
EIKON Data API経由でLME銅の1-36限月先物の4本値・出来高データを取得し、PostgreSQLに格納する
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import eikon as ek
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lme_copper_futures_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LMECopperFuturesCollector:
    """LME銅先物データ収集クラス"""
    
    def __init__(self):
        """初期化"""
        self.eikon_app_key = os.getenv('EIKON_APP_KEY', '1475940198b04fdab9265b7892546cc2ead9eda6')
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'lme_copper_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # LME銅先物のRIC（1-36限月）
        self.futures_rics = {f'Month_{i:02d}': f'CMCUc{i}' for i in range(1, 37)}
        
        # データフィールド（調査結果に基づく - OPINTは利用不可のためVOLUMEまで）
        self.fields = ['CLOSE', 'HIGH', 'LOW', 'OPEN', 'VOLUME']
        
        self.conn = None
        
    def initialize_eikon(self) -> bool:
        """EIKON APIの初期化"""
        try:
            ek.set_app_key(self.eikon_app_key)
            logger.info("EIKON API initialized successfully")
            return True
        except Exception as e:
            logger.error(f"EIKON API initialization failed: {str(e)}")
            return False
    
    def connect_database(self) -> bool:
        """PostgreSQLデータベースに接続"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def create_futures_table(self) -> bool:
        """先物データ用テーブルの作成"""
        try:
            with self.conn.cursor() as cursor:
                # 先物データテーブル作成SQL
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS lme_copper_futures (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL,
                    contract_month INTEGER NOT NULL,
                    ric VARCHAR(20) NOT NULL,
                    close_price DECIMAL(12,4),
                    high_price DECIMAL(12,4),
                    low_price DECIMAL(12,4),
                    open_price DECIMAL(12,4),
                    volume BIGINT,
                    open_interest BIGINT,
                    currency VARCHAR(3) DEFAULT 'USD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, contract_month, ric)
                );
                """
                
                cursor.execute(create_table_sql)
                
                # インデックス作成
                index_sql = """
                CREATE INDEX IF NOT EXISTS idx_futures_date ON lme_copper_futures(trade_date);
                CREATE INDEX IF NOT EXISTS idx_futures_month ON lme_copper_futures(contract_month);
                CREATE INDEX IF NOT EXISTS idx_futures_ric ON lme_copper_futures(ric);
                CREATE INDEX IF NOT EXISTS idx_futures_date_month ON lme_copper_futures(trade_date, contract_month);
                """
                
                cursor.execute(index_sql)
                
                # 更新時刻自動更新のトリガー作成
                trigger_sql = """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_lme_copper_futures_updated_at ON lme_copper_futures;
                CREATE TRIGGER update_lme_copper_futures_updated_at
                    BEFORE UPDATE ON lme_copper_futures
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                """
                
                cursor.execute(trigger_sql)
                self.conn.commit()
                
                logger.info("Futures table created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Futures table creation failed: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_futures_data(self, ric: str, month: int, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """指定期間の先物データを取得"""
        try:
            logger.info(f"Fetching data for {ric} (Month {month}) from {start_date} to {end_date}")
            
            # EIKON APIでデータ取得
            data = ek.get_timeseries(
                ric,
                fields=self.fields,
                start_date=start_date,
                end_date=end_date,
                interval='daily'
            )
            
            if data is None or data.empty:
                logger.warning(f"No data returned for {ric}")
                return None
            
            # データフレームの整形
            data = data.reset_index()
            data['contract_month'] = month
            data['ric'] = ric
            
            logger.info(f"Successfully fetched {len(data)} records for {ric}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ric}: {str(e)}")
            return None
    
    def save_futures_data(self, data: pd.DataFrame) -> bool:
        """先物データをデータベースに保存"""
        try:
            with self.conn.cursor() as cursor:
                for _, row in data.iterrows():
                    insert_sql = """
                    INSERT INTO lme_copper_futures 
                    (trade_date, contract_month, ric, close_price, high_price, low_price, open_price, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_date, contract_month, ric) 
                    DO UPDATE SET 
                        close_price = EXCLUDED.close_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        open_price = EXCLUDED.open_price,
                        volume = EXCLUDED.volume,
                        updated_at = CURRENT_TIMESTAMP;
                    """
                    
                    cursor.execute(insert_sql, (
                        row['Date'].date() if pd.notna(row['Date']) else None,
                        int(row['contract_month']),
                        row['ric'],
                        float(row['CLOSE']) if pd.notna(row['CLOSE']) else None,
                        float(row['HIGH']) if pd.notna(row['HIGH']) else None,
                        float(row['LOW']) if pd.notna(row['LOW']) else None,
                        float(row['OPEN']) if pd.notna(row['OPEN']) else None,
                        int(row['VOLUME']) if pd.notna(row['VOLUME']) else None
                    ))
                
                self.conn.commit()
                logger.info(f"Successfully saved {len(data)} records")
                return True
                
        except Exception as e:
            logger.error(f"Error saving data to database: {str(e)}")
            self.conn.rollback()
            return False
    
    def collect_all_futures_data(self, days_back: int = 365) -> bool:
        """全先物限月のデータ収集"""
        try:
            # データ取得期間設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Collecting futures data from {start_date_str} to {end_date_str}")
            logger.info(f"Processing {len(self.futures_rics)} futures contracts")
            
            success_count = 0
            total_records = 0
            
            for month_name, ric in self.futures_rics.items():
                month_num = int(month_name.split('_')[1])
                logger.info(f"Processing {month_name} ({ric}) - Month {month_num}")
                
                # データ取得
                data = self.get_futures_data(ric, month_num, start_date_str, end_date_str)
                
                if data is not None and not data.empty:
                    # データベースに保存
                    if self.save_futures_data(data):
                        success_count += 1
                        total_records += len(data)
                        logger.info(f"Successfully processed {month_name} - {len(data)} records")
                    else:
                        logger.error(f"Failed to save {month_name} data")
                else:
                    logger.warning(f"No data available for {month_name}")
            
            logger.info(f"Data collection completed. Successfully processed {success_count}/{len(self.futures_rics)} contracts")
            logger.info(f"Total records collected: {total_records}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in collect_all_futures_data: {str(e)}")
            return False
    
    def get_futures_summary(self) -> Dict:
        """データベース内の先物データサマリーを取得"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 基本統計
                summary_sql = """
                SELECT 
                    contract_month,
                    ric,
                    COUNT(*) as record_count,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date,
                    AVG(close_price) as avg_price,
                    MAX(close_price) as max_price,
                    MIN(close_price) as min_price,
                    SUM(volume) as total_volume
                FROM lme_copper_futures 
                WHERE close_price IS NOT NULL
                GROUP BY contract_month, ric
                ORDER BY contract_month;
                """
                
                cursor.execute(summary_sql)
                results = cursor.fetchall()
                
                summary = {}
                for row in results:
                    summary[f"Month_{row['contract_month']:02d}"] = {
                        'ric': row['ric'],
                        'record_count': row['record_count'],
                        'earliest_date': row['earliest_date'],
                        'latest_date': row['latest_date'],
                        'avg_price': float(row['avg_price']) if row['avg_price'] else 0,
                        'max_price': float(row['max_price']) if row['max_price'] else 0,
                        'min_price': float(row['min_price']) if row['min_price'] else 0,
                        'total_volume': int(row['total_volume']) if row['total_volume'] else 0
                    }
                
                # 最新のフューチャーカーブ
                curve_sql = """
                SELECT 
                    contract_month,
                    ric,
                    close_price,
                    volume,
                    trade_date
                FROM lme_copper_futures 
                WHERE trade_date = (
                    SELECT MAX(trade_date) 
                    FROM lme_copper_futures 
                    WHERE close_price IS NOT NULL
                )
                AND close_price IS NOT NULL
                ORDER BY contract_month;
                """
                
                cursor.execute(curve_sql)
                curve_results = cursor.fetchall()
                
                latest_curve = {}
                for row in curve_results:
                    latest_curve[row['contract_month']] = {
                        'ric': row['ric'],
                        'price': float(row['close_price']),
                        'volume': int(row['volume']) if row['volume'] else 0,
                        'date': row['trade_date']
                    }
                
                return {'summary': summary, 'latest_curve': latest_curve}
                
        except Exception as e:
            logger.error(f"Error getting futures summary: {str(e)}")
            return {}
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """メイン実行関数"""
    collector = LMECopperFuturesCollector()
    
    try:
        # EIKON API初期化
        if not collector.initialize_eikon():
            logger.error("Failed to initialize EIKON API")
            return False
        
        # データベース接続
        if not collector.connect_database():
            logger.error("Failed to connect to database")
            return False
        
        # 先物テーブル作成
        if not collector.create_futures_table():
            logger.error("Failed to create futures table")
            return False
        
        # データ収集（過去5年分）
        if collector.collect_all_futures_data(days_back=1825):
            logger.info("Futures data collection completed successfully")
            
            # データサマリー表示
            summary_data = collector.get_futures_summary()
            if summary_data.get('summary'):
                logger.info("Futures Data Summary:")
                for month, info in summary_data['summary'].items():
                    logger.info(f"  {month}: {info['record_count']} records "
                              f"(${info['avg_price']:.2f} avg, Vol: {info['total_volume']})")
            
            # 最新のフューチャーカーブ
            if summary_data.get('latest_curve'):
                logger.info("Latest Futures Curve:")
                for month, data in summary_data['latest_curve'].items():
                    logger.info(f"  Month {month:2d}: ${data['price']:8.2f} (Vol: {data['volume']:6d})")
            
            return True
        else:
            logger.error("Futures data collection failed")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        return False
    
    finally:
        collector.close_connection()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)