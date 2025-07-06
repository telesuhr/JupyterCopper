#!/usr/bin/env python3
"""
LME Copper Historical Data Collector
Refinitiv EIKON Data API経由でLME銅の3MアウトライトとCash/3Mスプレッドの
過去3年分のデータを取得し、PostgreSQLに格納する
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
        logging.FileHandler('lme_copper_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LMECopperDataCollector:
    """LME銅データ収集クラス"""
    
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
        
        # LME銅のRIC（Reuters Instrument Code）
        self.rics = {
            '3M_OUTRIGHT': 'CMCU3',  # LME銅3Mアウトライト
            'CASH_3M_SPREAD': 'CMCU0-3'  # Cash/3Mスプレッド
        }
        
        # データフィールド
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
    
    def create_database_schema(self) -> bool:
        """データベーススキーマの作成"""
        try:
            with self.conn.cursor() as cursor:
                # テーブル作成SQL
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS lme_copper_prices (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL,
                    price_type VARCHAR(20) NOT NULL,
                    ric VARCHAR(50) NOT NULL,
                    last_price DECIMAL(10,4),
                    high_price DECIMAL(10,4),
                    low_price DECIMAL(10,4),
                    open_price DECIMAL(10,4),
                    volume BIGINT,
                    currency VARCHAR(3) DEFAULT 'USD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, price_type, ric)
                );
                """
                
                cursor.execute(create_table_sql)
                
                # インデックス作成
                index_sql = """
                CREATE INDEX IF NOT EXISTS idx_trade_date ON lme_copper_prices(trade_date);
                CREATE INDEX IF NOT EXISTS idx_price_type ON lme_copper_prices(price_type);
                CREATE INDEX IF NOT EXISTS idx_ric ON lme_copper_prices(ric);
                """
                
                cursor.execute(index_sql)
                self.conn.commit()
                
                logger.info("Database schema created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database schema creation failed: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_historical_data(self, ric: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """指定期間のヒストリカルデータを取得"""
        try:
            logger.info(f"Fetching data for {ric} from {start_date} to {end_date}")
            
            # EIKON APIでデータ取得
            try:
                data = ek.get_timeseries(
                    ric,
                    fields=self.fields,
                    start_date=start_date,
                    end_date=end_date,
                    interval='daily'
                )
            except Exception as api_error:
                logger.error(f"EIKON API error for {ric}: {str(api_error)}")
                return None
            
            if data is None or data.empty:
                logger.warning(f"No data returned for {ric}")
                return None
            
            # データフレームの整形
            data = data.reset_index()
            data['RIC'] = ric
            
            logger.info(f"Successfully fetched {len(data)} records for {ric}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ric}: {str(e)}")
            return None
    
    def save_to_database(self, data: pd.DataFrame, price_type: str, ric: str) -> bool:
        """データベースにデータを保存"""
        try:
            with self.conn.cursor() as cursor:
                for _, row in data.iterrows():
                    insert_sql = """
                    INSERT INTO lme_copper_prices 
                    (trade_date, price_type, ric, last_price, high_price, low_price, open_price, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_date, price_type, ric) 
                    DO UPDATE SET 
                        last_price = EXCLUDED.last_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        open_price = EXCLUDED.open_price,
                        volume = EXCLUDED.volume,
                        created_at = CURRENT_TIMESTAMP;
                    """
                    
                    cursor.execute(insert_sql, (
                        row['Date'].date() if pd.notna(row['Date']) else None,
                        price_type,
                        ric,
                        float(row['CLOSE']) if pd.notna(row['CLOSE']) else None,
                        float(row['HIGH']) if pd.notna(row['HIGH']) else None,
                        float(row['LOW']) if pd.notna(row['LOW']) else None,
                        float(row['OPEN']) if pd.notna(row['OPEN']) else None,
                        int(row['VOLUME']) if pd.notna(row['VOLUME']) else None
                    ))
                
                self.conn.commit()
                logger.info(f"Successfully saved {len(data)} records for {price_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving data to database: {str(e)}")
            self.conn.rollback()
            return False
    
    def collect_all_data(self) -> bool:
        """全データの収集"""
        try:
            # 過去3年の期間設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3*365)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Collecting data from {start_date_str} to {end_date_str}")
            
            success_count = 0
            
            for price_type, ric in self.rics.items():
                logger.info(f"Processing {price_type} ({ric})")
                
                # データ取得
                data = self.get_historical_data(ric, start_date_str, end_date_str)
                
                if data is not None and not data.empty:
                    # データベースに保存
                    if self.save_to_database(data, price_type, ric):
                        success_count += 1
                        logger.info(f"Successfully processed {price_type}")
                    else:
                        logger.error(f"Failed to save {price_type} data")
                else:
                    logger.error(f"No data available for {price_type}")
            
            logger.info(f"Data collection completed. Successfully processed {success_count}/{len(self.rics)} datasets")
            return success_count == len(self.rics)
            
        except Exception as e:
            logger.error(f"Error in collect_all_data: {str(e)}")
            return False
    
    def get_data_summary(self) -> Dict:
        """データベース内のデータサマリーを取得"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                summary_sql = """
                SELECT 
                    price_type,
                    ric,
                    COUNT(*) as record_count,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date,
                    AVG(last_price) as avg_price
                FROM lme_copper_prices 
                GROUP BY price_type, ric
                ORDER BY price_type;
                """
                
                cursor.execute(summary_sql)
                results = cursor.fetchall()
                
                summary = {}
                for row in results:
                    summary[row['price_type']] = {
                        'ric': row['ric'],
                        'record_count': row['record_count'],
                        'earliest_date': row['earliest_date'],
                        'latest_date': row['latest_date'],
                        'avg_price': float(row['avg_price']) if row['avg_price'] else 0
                    }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return {}
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """メイン実行関数"""
    collector = LMECopperDataCollector()
    
    try:
        # EIKON API初期化
        if not collector.initialize_eikon():
            logger.error("Failed to initialize EIKON API")
            return False
        
        # データベース接続
        if not collector.connect_database():
            logger.error("Failed to connect to database")
            return False
        
        # データベーススキーマ作成
        if not collector.create_database_schema():
            logger.error("Failed to create database schema")
            return False
        
        # データ収集
        if collector.collect_all_data():
            logger.info("Data collection completed successfully")
            
            # データサマリー表示
            summary = collector.get_data_summary()
            if summary:
                logger.info("Data Summary:")
                for price_type, info in summary.items():
                    logger.info(f"  {price_type}: {info['record_count']} records "
                              f"({info['earliest_date']} to {info['latest_date']})")
            
            return True
        else:
            logger.error("Data collection failed")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        return False
    
    finally:
        collector.close_connection()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)