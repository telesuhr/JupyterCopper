#!/usr/bin/env python3
"""
LME銅先物分析システム - 本番運用スクリプト
データ収集、予測、監視の統合実行システム
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from typing import List, Dict
import schedule
import logging

# ログ設定
def setup_logging():
    """ログ設定の初期化"""
    log_dir = '/Users/Yusuke/claude-code/RefinitivDB/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = os.path.join(log_dir, f'production_system_{datetime.now().strftime("%Y%m")}.log')
    
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

class ProductionSystemManager:
    """本番システム管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.base_dir = '/Users/Yusuke/claude-code/RefinitivDB'
        self.python_cmd = sys.executable
        
        # 各コンポーネントのパス
        self.components = {
            'data_collector': os.path.join(self.base_dir, 'data_collectors/lme_copper_futures_collector.py'),
            'scheduler': os.path.join(self.base_dir, 'automation/daily_data_scheduler.py'),
            'predictor': os.path.join(self.base_dir, 'prediction/daily_prediction_system.py'),
            'dashboard': os.path.join(self.base_dir, 'dashboard/monitoring_dashboard.py')
        }
    
    def run_component(self, component: str, args: List[str] = None) -> Dict:
        """コンポーネントの実行"""
        if component not in self.components:
            return {'success': False, 'error': f'Unknown component: {component}'}
        
        script_path = self.components[component]
        if not os.path.exists(script_path):
            return {'success': False, 'error': f'Script not found: {script_path}'}
        
        try:
            cmd = [self.python_cmd, script_path]
            if args:
                cmd.extend(args)
            
            logger.info(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1時間タイムアウト
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Process timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_data_collection(self) -> bool:
        """データ収集の実行"""
        logger.info("Starting data collection...")
        
        result = self.run_component('scheduler', ['collect'])
        
        if result['success']:
            logger.info("Data collection completed successfully")
            return True
        else:
            logger.error(f"Data collection failed: {result.get('error', 'Unknown error')}")
            if result.get('stderr'):
                logger.error(f"Error output: {result['stderr']}")
            return False
    
    def run_prediction(self) -> bool:
        """予測システムの実行"""
        logger.info("Starting prediction system...")
        
        result = self.run_component('predictor', ['predict'])
        
        if result['success']:
            logger.info("Prediction system completed successfully")
            return True
        else:
            logger.error(f"Prediction system failed: {result.get('error', 'Unknown error')}")
            if result.get('stderr'):
                logger.error(f"Error output: {result['stderr']}")
            return False
    
    def run_validation(self) -> bool:
        """データ検証の実行"""
        logger.info("Starting data validation...")
        
        result = self.run_component('scheduler', ['validate'])
        
        if result['success']:
            logger.info("Data validation completed successfully")
            return True
        else:
            logger.error(f"Data validation failed: {result.get('error', 'Unknown error')}")
            return False
    
    def run_backup(self) -> bool:
        """バックアップの実行"""
        logger.info("Starting database backup...")
        
        result = self.run_component('scheduler', ['backup'])
        
        if result['success']:
            logger.info("Database backup completed successfully")
            return True
        else:
            logger.error(f"Database backup failed: {result.get('error', 'Unknown error')}")
            return False
    
    def start_dashboard(self) -> bool:
        """ダッシュボードの起動"""
        logger.info("Starting monitoring dashboard...")
        
        try:
            # Streamlitダッシュボードを別プロセスで起動
            cmd = [
                'streamlit', 'run', 
                self.components['dashboard'],
                '--server.port=8501',
                '--server.address=localhost'
            ]
            
            subprocess.Popen(cmd)
            logger.info("Dashboard started at http://localhost:8501")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dashboard: {str(e)}")
            return False
    
    def run_full_pipeline(self) -> Dict:
        """完全なパイプラインの実行"""
        logger.info("Starting full production pipeline...")
        
        results = {
            'data_collection': False,
            'prediction': False,
            'validation': False,
            'overall_success': False
        }
        
        # 1. データ収集
        results['data_collection'] = self.run_data_collection()
        
        # 2. データ収集が成功した場合のみ予測実行
        if results['data_collection']:
            results['prediction'] = self.run_prediction()
        
        # 3. データ検証（常に実行）
        results['validation'] = self.run_validation()
        
        # 全体的な成功判定
        results['overall_success'] = results['data_collection'] and results['prediction']
        
        if results['overall_success']:
            logger.info("Full pipeline completed successfully")
        else:
            logger.warning("Pipeline completed with some failures")
        
        return results
    
    def setup_production_schedule(self):
        """本番スケジュールの設定"""
        # 平日午前7時にフルパイプライン実行
        schedule.every().monday.at("07:00").do(self.run_full_pipeline)
        schedule.every().tuesday.at("07:00").do(self.run_full_pipeline)
        schedule.every().wednesday.at("07:00").do(self.run_full_pipeline)
        schedule.every().thursday.at("07:00").do(self.run_full_pipeline)
        schedule.every().friday.at("07:00").do(self.run_full_pipeline)
        
        # 毎日午前2時にバックアップ
        schedule.every().day.at("02:00").do(self.run_backup)
        
        # 平日午後1時に追加の予測更新
        schedule.every().monday.at("13:00").do(self.run_prediction)
        schedule.every().tuesday.at("13:00").do(self.run_prediction)
        schedule.every().wednesday.at("13:00").do(self.run_prediction)
        schedule.every().thursday.at("13:00").do(self.run_prediction)
        schedule.every().friday.at("13:00").do(self.run_prediction)
        
        logger.info("Production schedule configured:")
        logger.info("  Full pipeline: Weekdays at 07:00")
        logger.info("  Predictions: Weekdays at 13:00")
        logger.info("  Backup: Daily at 02:00")
    
    def run_scheduler(self):
        """スケジューラーの実行"""
        logger.info("Starting production scheduler...")
        
        self.setup_production_schedule()
        
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
    parser = argparse.ArgumentParser(description='LME銅先物分析システム - 本番運用')
    
    parser.add_argument('command', choices=[
        'collect', 'predict', 'validate', 'backup', 'pipeline', 
        'dashboard', 'schedule', 'status'
    ], help='実行するコマンド')
    
    parser.add_argument('--force', action='store_true', 
                       help='エラーがあっても続行')
    
    args = parser.parse_args()
    
    manager = ProductionSystemManager()
    
    if args.command == 'collect':
        # データ収集のみ
        success = manager.run_data_collection()
        sys.exit(0 if success else 1)
        
    elif args.command == 'predict':
        # 予測のみ
        success = manager.run_prediction()
        sys.exit(0 if success else 1)
        
    elif args.command == 'validate':
        # データ検証のみ
        success = manager.run_validation()
        sys.exit(0 if success else 1)
        
    elif args.command == 'backup':
        # バックアップのみ
        success = manager.run_backup()
        sys.exit(0 if success else 1)
        
    elif args.command == 'pipeline':
        # フルパイプライン実行
        results = manager.run_full_pipeline()
        print("Pipeline Results:")
        for component, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {component}: {status}")
        
        sys.exit(0 if results['overall_success'] else 1)
        
    elif args.command == 'dashboard':
        # ダッシュボード起動
        success = manager.start_dashboard()
        if success:
            print("Dashboard started at http://localhost:8501")
            print("Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nDashboard stopped")
        else:
            sys.exit(1)
            
    elif args.command == 'schedule':
        # スケジューラー実行
        manager.run_scheduler()
        
    elif args.command == 'status':
        # システム状況確認
        print("LME銅先物分析システム - 状況確認")
        print("=" * 50)
        
        # 各コンポーネントファイルの存在確認
        for name, path in manager.components.items():
            exists = "✓" if os.path.exists(path) else "✗"
            print(f"{name}: {exists} {path}")
        
        # ログディレクトリ確認
        log_dir = '/Users/Yusuke/claude-code/RefinitivDB/logs'
        log_exists = "✓" if os.path.exists(log_dir) else "✗"
        print(f"Logs: {log_exists} {log_dir}")
        
        # モデルディレクトリ確認
        model_dir = '/Users/Yusuke/claude-code/RefinitivDB/models'
        model_exists = "✓" if os.path.exists(model_dir) else "✗"
        print(f"Models: {model_exists} {model_dir}")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()