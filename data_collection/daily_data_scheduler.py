#!/usr/bin/env python3
"""
LME銅先物データの日次自動収集スケジューラー
毎日決められた時間にデータ収集を実行し、ログ管理と異常検知を行う
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 親ディレクトリのdata_collectorsモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_collectors.lme_copper_futures_collector import LMECopperFuturesCollector

# ログ設定
def setup_logging():
    """ログ設定の初期化"""
    log_dir = '/Users/Yusuke/claude-code/RefinitivDB/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = os.path.join(log_dir, f'daily_scheduler_{datetime.now().strftime("%Y%m")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class DailyDataScheduler:
    """日次データ収集スケジューラー"""
    
    def __init__(self):
        """初期化"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'lme_copper_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # アラート設定
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'to_email': os.getenv('TO_EMAIL', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', '')
        }
        
        # スケジュール設定
        self.collection_time = os.getenv('COLLECTION_TIME', '07:00')  # JST午前7時
        self.backup_time = os.getenv('BACKUP_TIME', '02:00')         # JST午前2時
        
    def run_daily_collection(self) -> Dict:
        """日次データ収集の実行"""
        logger.info("Starting daily data collection...")
        
        start_time = datetime.now()
        result = {
            'success': False,
            'start_time': start_time,
            'end_time': None,
            'duration': None,
            'records_collected': 0,
            'contracts_processed': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # データコレクター初期化
            collector = LMECopperFuturesCollector()
            
            # EIKON API初期化
            if not collector.initialize_eikon():
                result['errors'].append("Failed to initialize EIKON API")
                return result
            
            # データベース接続
            if not collector.connect_database():
                result['errors'].append("Failed to connect to database")
                return result
            
            # 前日分のデータ収集（市場休日対応で3日分）
            collection_result = collector.collect_all_futures_data(days_back=3)
            
            if collection_result:
                # 収集結果の詳細取得
                summary = collector.get_futures_summary()
                if summary.get('summary'):
                    result['contracts_processed'] = len(summary['summary'])
                    result['records_collected'] = sum(
                        info['record_count'] for info in summary['summary'].values()
                    )
                
                result['success'] = True
                logger.info(f"Daily collection successful. Processed {result['contracts_processed']} contracts, "
                          f"collected {result['records_collected']} records")
            else:
                result['errors'].append("Data collection failed")
            
            collector.close_connection()
            
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
            logger.error(f"Error in daily collection: {str(e)}")
        
        finally:
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        # 結果の記録
        self.log_collection_result(result)
        
        # アラート送信（必要に応じて）
        if not result['success'] or result['errors']:
            self.send_alert(result)
        
        return result
    
    def log_collection_result(self, result: Dict):
        """収集結果をデータベースに記録"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cursor:
                # ログテーブル作成（存在しない場合）
                create_log_table_sql = """
                CREATE TABLE IF NOT EXISTS data_collection_log (
                    id SERIAL PRIMARY KEY,
                    collection_date DATE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds DECIMAL(10,2),
                    success BOOLEAN NOT NULL,
                    records_collected INTEGER DEFAULT 0,
                    contracts_processed INTEGER DEFAULT 0,
                    errors TEXT[],
                    warnings TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cursor.execute(create_log_table_sql)
                
                # ログ挿入
                insert_log_sql = """
                INSERT INTO data_collection_log 
                (collection_date, start_time, end_time, duration_seconds, success, 
                 records_collected, contracts_processed, errors, warnings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_log_sql, (
                    result['start_time'].date(),
                    result['start_time'],
                    result['end_time'],
                    result['duration'],
                    result['success'],
                    result['records_collected'],
                    result['contracts_processed'],
                    result['errors'],
                    result['warnings']
                ))
                
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging collection result: {str(e)}")
    
    def send_alert(self, result: Dict):
        """異常時のアラート送信"""
        if not self.email_config['from_email'] or not self.email_config['to_email']:
            logger.warning("Email configuration not set, skipping alert")
            return
        
        try:
            # メール作成
            msg = MimeMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']
            
            if result['success']:
                msg['Subject'] = 'LME Data Collection - Warning'
                body = f"""
データ収集は成功しましたが、警告があります：

収集時刻: {result['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
処理時間: {result['duration']:.2f}秒
収集契約数: {result['contracts_processed']}
収集レコード数: {result['records_collected']}

警告:
{chr(10).join(result['warnings'])}

エラー:
{chr(10).join(result['errors'])}
                """
            else:
                msg['Subject'] = 'LME Data Collection - ERROR'
                body = f"""
データ収集に失敗しました：

収集時刻: {result['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
処理時間: {result['duration']:.2f}秒

エラー:
{chr(10).join(result['errors'])}
                """
            
            msg.attach(MimeText(body, 'plain'))
            
            # メール送信
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['from_email'], self.email_config['email_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Alert email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
    
    def run_data_validation(self) -> Dict:
        """データ品質チェックの実行"""
        logger.info("Running data validation...")
        
        validation_result = {
            'success': True,
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # 1. 最新データの確認
                cursor.execute("""
                    SELECT MAX(trade_date) as latest_date, COUNT(*) as total_records
                    FROM lme_copper_futures
                """)
                latest_info = cursor.fetchone()
                
                if latest_info:
                    latest_date = latest_info['latest_date']
                    days_behind = (datetime.now().date() - latest_date).days
                    
                    validation_result['checks']['latest_data'] = {
                        'latest_date': latest_date,
                        'days_behind': days_behind,
                        'total_records': latest_info['total_records']
                    }
                    
                    if days_behind > 3:
                        validation_result['warnings'].append(
                            f"Data is {days_behind} days behind (latest: {latest_date})"
                        )
                
                # 2. 欠損データの確認
                cursor.execute("""
                    SELECT 
                        contract_month,
                        COUNT(*) as total_records,
                        COUNT(close_price) as valid_prices,
                        COUNT(*) - COUNT(close_price) as missing_prices
                    FROM lme_copper_futures
                    WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY contract_month
                    ORDER BY contract_month
                """)
                missing_data = cursor.fetchall()
                
                validation_result['checks']['missing_data'] = []
                for row in missing_data:
                    missing_pct = (row['missing_prices'] / row['total_records']) * 100
                    validation_result['checks']['missing_data'].append({
                        'contract_month': row['contract_month'],
                        'missing_percentage': missing_pct,
                        'missing_count': row['missing_prices']
                    })
                    
                    if missing_pct > 10:
                        validation_result['warnings'].append(
                            f"Month {row['contract_month']} has {missing_pct:.1f}% missing prices"
                        )
                
                # 3. 異常価格の確認
                cursor.execute("""
                    SELECT 
                        contract_month,
                        trade_date,
                        close_price,
                        LAG(close_price) OVER (PARTITION BY contract_month ORDER BY trade_date) as prev_price
                    FROM lme_copper_futures
                    WHERE trade_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND close_price IS NOT NULL
                """)
                price_data = cursor.fetchall()
                
                anomalous_prices = []
                for row in price_data:
                    if row['prev_price']:
                        change_pct = abs((row['close_price'] - row['prev_price']) / row['prev_price']) * 100
                        if change_pct > 10:  # 10%以上の価格変動
                            anomalous_prices.append({
                                'contract_month': row['contract_month'],
                                'date': row['trade_date'],
                                'price': row['close_price'],
                                'prev_price': row['prev_price'],
                                'change_pct': change_pct
                            })
                
                validation_result['checks']['anomalous_prices'] = anomalous_prices
                if anomalous_prices:
                    validation_result['warnings'].append(
                        f"Found {len(anomalous_prices)} anomalous price movements (>10%)"
                    )
            
            conn.close()
            
        except Exception as e:
            validation_result['success'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"Error in data validation: {str(e)}")
        
        return validation_result
    
    def run_database_backup(self):
        """データベースバックアップの実行"""
        logger.info("Starting database backup...")
        
        try:
            backup_dir = '/Users/Yusuke/claude-code/RefinitivDB/backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"lme_copper_db_backup_{timestamp}.sql"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # pg_dumpコマンド実行
            os.system(f"""
            pg_dump -h {self.db_config['host']} \
                    -p {self.db_config['port']} \
                    -U {self.db_config['user']} \
                    -d {self.db_config['database']} \
                    -f {backup_path}
            """)
            
            # 古いバックアップファイルの削除（7日以上前）
            cutoff_date = datetime.now() - timedelta(days=7)
            for filename in os.listdir(backup_dir):
                if filename.startswith('lme_copper_db_backup_'):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {filename}")
            
            logger.info(f"Database backup completed: {backup_filename}")
            
        except Exception as e:
            logger.error(f"Error in database backup: {str(e)}")
    
    def setup_schedules(self):
        """スケジュール設定"""
        # 毎日の定時データ収集
        schedule.every().day.at(self.collection_time).do(self.run_daily_collection)
        
        # 毎日のデータ検証
        schedule.every().day.at("08:00").do(self.run_data_validation)
        
        # 毎日のデータベースバックアップ
        schedule.every().day.at(self.backup_time).do(self.run_database_backup)
        
        logger.info(f"Schedules configured:")
        logger.info(f"  Data collection: daily at {self.collection_time}")
        logger.info(f"  Data validation: daily at 08:00")
        logger.info(f"  Database backup: daily at {self.backup_time}")
    
    def run_scheduler(self):
        """スケジューラーの実行"""
        logger.info("Starting LME Copper Data Scheduler...")
        
        self.setup_schedules()
        
        # 即座に初回データ検証を実行
        validation_result = self.run_data_validation()
        logger.info(f"Initial validation completed: {validation_result['success']}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")

def main():
    """メイン実行関数"""
    scheduler = DailyDataScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'collect':
            # 手動でデータ収集実行
            result = scheduler.run_daily_collection()
            print(f"Collection result: {result}")
            
        elif command == 'validate':
            # 手動でデータ検証実行
            result = scheduler.run_data_validation()
            print(f"Validation result: {result}")
            
        elif command == 'backup':
            # 手動でバックアップ実行
            scheduler.run_database_backup()
            
        else:
            print("Available commands: collect, validate, backup")
            sys.exit(1)
    else:
        # スケジューラー実行
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()