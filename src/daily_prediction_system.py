#!/usr/bin/env python3
"""
LME銅先物の日次予測システム
訓練済みモデルを使用して毎日の価格予測を実行し、結果をデータベースに保存
"""

import os
import sys
import logging
import pickle
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# 機械学習ライブラリ
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    from statsmodels.tsa.arima.model import ARIMA
    from prophet import Prophet
    from tensorflow.keras.models import load_model
except ImportError as e:
    print(f"Warning: Some ML libraries not available: {e}")

# 環境変数の読み込み
load_dotenv()

# ログ設定
def setup_logging():
    """ログ設定の初期化"""
    log_dir = '/Users/Yusuke/claude-code/RefinitivDB/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = os.path.join(log_dir, f'daily_predictions_{datetime.now().strftime("%Y%m")}.log')
    
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

class DailyPredictionSystem:
    """日次予測システム"""
    
    def __init__(self):
        """初期化"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'lme_copper_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # モデル保存パス
        self.model_dir = '/Users/Yusuke/claude-code/RefinitivDB/models'
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 予測対象（3Mアウトライト）
        self.target_contract = 3
        self.prediction_horizon = 5  # 5営業日先まで予測
        
        # 特徴量設定
        self.feature_columns = [
            'close_price', 'volume', 'price_change', 'volume_change',
            'ma_5', 'ma_20', 'rsi', 'volatility', 'spread_1m_3m'
        ]
        
        self.models = {}
        self.scalers = {}
        
    def create_prediction_tables(self):
        """予測結果保存用テーブルの作成"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cursor:
                # 予測結果テーブル
                create_predictions_table = """
                CREATE TABLE IF NOT EXISTS daily_predictions (
                    id SERIAL PRIMARY KEY,
                    prediction_date DATE NOT NULL,
                    target_date DATE NOT NULL,
                    contract_month INTEGER NOT NULL,
                    days_ahead INTEGER NOT NULL,
                    model_name VARCHAR(50) NOT NULL,
                    predicted_price DECIMAL(12,4),
                    actual_price DECIMAL(12,4),
                    prediction_error DECIMAL(12,4),
                    confidence_interval_lower DECIMAL(12,4),
                    confidence_interval_upper DECIMAL(12,4),
                    model_version VARCHAR(20),
                    features_used TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(prediction_date, target_date, contract_month, model_name)
                );
                """
                cursor.execute(create_predictions_table)
                
                # 予測パフォーマンステーブル
                create_performance_table = """
                CREATE TABLE IF NOT EXISTS prediction_performance (
                    id SERIAL PRIMARY KEY,
                    evaluation_date DATE NOT NULL,
                    model_name VARCHAR(50) NOT NULL,
                    contract_month INTEGER NOT NULL,
                    days_ahead INTEGER NOT NULL,
                    mae DECIMAL(12,6),
                    rmse DECIMAL(12,6),
                    mape DECIMAL(8,4),
                    directional_accuracy DECIMAL(6,4),
                    total_predictions INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(evaluation_date, model_name, contract_month, days_ahead)
                );
                """
                cursor.execute(create_performance_table)
                
                # インデックス作成
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_predictions_date ON daily_predictions(prediction_date);",
                    "CREATE INDEX IF NOT EXISTS idx_predictions_target ON daily_predictions(target_date);",
                    "CREATE INDEX IF NOT EXISTS idx_predictions_model ON daily_predictions(model_name);",
                    "CREATE INDEX IF NOT EXISTS idx_performance_date ON prediction_performance(evaluation_date);",
                    "CREATE INDEX IF NOT EXISTS idx_performance_model ON prediction_performance(model_name);"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                logger.info("Prediction tables created successfully")
                
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating prediction tables: {str(e)}")
            return False
    
    def load_models(self) -> bool:
        """保存済みモデルの読み込み"""
        try:
            model_files = {
                'random_forest': 'rf_model.pkl',
                'xgboost': 'xgb_model.pkl',
                'arima': 'arima_model.pkl',
                'lstm': 'lstm_model.h5',
                'scaler': 'feature_scaler.pkl'
            }
            
            for model_name, filename in model_files.items():
                filepath = os.path.join(self.model_dir, filename)
                
                if os.path.exists(filepath):
                    if model_name == 'lstm':
                        try:
                            self.models[model_name] = load_model(filepath)
                            logger.info(f"Loaded {model_name} model")
                        except Exception as e:
                            logger.warning(f"Could not load {model_name}: {e}")
                    elif model_name == 'scaler':
                        self.scalers['features'] = joblib.load(filepath)
                        logger.info("Loaded feature scaler")
                    else:
                        with open(filepath, 'rb') as f:
                            self.models[model_name] = pickle.load(f)
                        logger.info(f"Loaded {model_name} model")
                else:
                    logger.warning(f"Model file not found: {filepath}")
            
            return len(self.models) > 0
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def get_latest_data(self, days_back: int = 100) -> pd.DataFrame:
        """最新データの取得と特徴量作成"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # 3Mアウトライトの価格データ取得
            query = """
            SELECT 
                trade_date,
                close_price,
                volume,
                open_price,
                high_price,
                low_price
            FROM lme_copper_futures
            WHERE contract_month = %s
                AND trade_date >= CURRENT_DATE - INTERVAL '%s days'
                AND close_price IS NOT NULL
            ORDER BY trade_date;
            """
            
            df = pd.read_sql_query(query, conn, params=(self.target_contract, days_back))
            conn.close()
            
            if df.empty:
                logger.error("No data retrieved for feature engineering")
                return pd.DataFrame()
            
            # 特徴量エンジニアリング
            df = self.create_features(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting latest data: {str(e)}")
            return pd.DataFrame()
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特徴量作成"""
        try:
            df = df.copy()
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 基本的な変化率
            df['price_change'] = df['close_price'].pct_change()
            df['volume_change'] = df['volume'].pct_change()
            
            # 移動平均
            df['ma_5'] = df['close_price'].rolling(window=5).mean()
            df['ma_20'] = df['close_price'].rolling(window=20).mean()
            
            # RSI計算
            delta = df['close_price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # ボラティリティ
            df['volatility'] = df['price_change'].rolling(window=20).std()
            
            # スプレッド取得（1M-3M）
            df['spread_1m_3m'] = self.get_spread_data(df['trade_date'])
            
            # 欠損値処理
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating features: {str(e)}")
            return df
    
    def get_spread_data(self, dates: pd.Series) -> pd.Series:
        """スプレッドデータの取得"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # 1Mと3Mの価格データを取得してスプレッド計算
            query = """
            SELECT 
                m1.trade_date,
                m1.close_price - m3.close_price as spread_1m_3m
            FROM 
                (SELECT trade_date, close_price FROM lme_copper_futures WHERE contract_month = 1) m1
            JOIN 
                (SELECT trade_date, close_price FROM lme_copper_futures WHERE contract_month = 3) m3
                ON m1.trade_date = m3.trade_date
            WHERE m1.trade_date >= %s AND m1.trade_date <= %s
            ORDER BY m1.trade_date;
            """
            
            start_date = dates.min().date() if not dates.empty else datetime.now().date() - timedelta(days=100)
            end_date = dates.max().date() if not dates.empty else datetime.now().date()
            
            spread_df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            conn.close()
            
            if spread_df.empty:
                return pd.Series([0.0] * len(dates))
            
            # 日付をインデックスにして結合
            spread_df['trade_date'] = pd.to_datetime(spread_df['trade_date'])
            spread_series = spread_df.set_index('trade_date')['spread_1m_3m']
            
            # 元のデータフレームの日付と照合
            result = []
            for date in dates:
                if pd.notna(date) and date in spread_series.index:
                    result.append(spread_series[date])
                else:
                    result.append(0.0)
            
            return pd.Series(result)
            
        except Exception as e:
            logger.error(f"Error getting spread data: {str(e)}")
            return pd.Series([0.0] * len(dates))
    
    def make_predictions(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """各モデルによる予測実行"""
        predictions = {}
        
        if data.empty or len(data) < 30:
            logger.error("Insufficient data for predictions")
            return predictions
        
        try:
            # 最新データポイント
            latest_features = data[self.feature_columns].iloc[-1:].values
            
            # Random Forest予測
            if 'random_forest' in self.models:
                try:
                    rf_pred = self.models['random_forest'].predict(latest_features)[0]
                    predictions['random_forest'] = [rf_pred] * self.prediction_horizon
                except Exception as e:
                    logger.error(f"Random Forest prediction error: {e}")
            
            # XGBoost予測
            if 'xgboost' in self.models:
                try:
                    xgb_pred = self.models['xgboost'].predict(latest_features)[0]
                    predictions['xgboost'] = [xgb_pred] * self.prediction_horizon
                except Exception as e:
                    logger.error(f"XGBoost prediction error: {e}")
            
            # ARIMA予測
            if 'arima' in self.models:
                try:
                    price_series = data['close_price'].values
                    arima_forecast = self.models['arima'].forecast(steps=self.prediction_horizon)
                    predictions['arima'] = arima_forecast.tolist()
                except Exception as e:
                    logger.error(f"ARIMA prediction error: {e}")
            
            # Prophet予測
            if 'prophet' in self.models:
                try:
                    # Prophetは特別な形式のデータが必要
                    prophet_data = pd.DataFrame({
                        'ds': data['trade_date'],
                        'y': data['close_price']
                    })
                    
                    future_dates = pd.date_range(
                        start=data['trade_date'].iloc[-1] + timedelta(days=1),
                        periods=self.prediction_horizon,
                        freq='B'  # 営業日
                    )
                    
                    future_df = pd.DataFrame({'ds': future_dates})
                    prophet_forecast = self.models['prophet'].predict(future_df)
                    predictions['prophet'] = prophet_forecast['yhat'].tolist()
                except Exception as e:
                    logger.error(f"Prophet prediction error: {e}")
            
            # アンサンブル予測（利用可能なモデルの平均）
            if predictions:
                ensemble_values = []
                for i in range(self.prediction_horizon):
                    day_predictions = []
                    for model_name, pred_list in predictions.items():
                        if i < len(pred_list):
                            day_predictions.append(pred_list[i])
                    
                    if day_predictions:
                        ensemble_values.append(np.mean(day_predictions))
                
                if ensemble_values:
                    predictions['ensemble'] = ensemble_values
            
            logger.info(f"Generated predictions for {len(predictions)} models")
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return predictions
    
    def save_predictions(self, predictions: Dict[str, List[float]], prediction_date: datetime) -> bool:
        """予測結果をデータベースに保存"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            with conn.cursor() as cursor:
                for model_name, pred_list in predictions.items():
                    for days_ahead, predicted_price in enumerate(pred_list, 1):
                        target_date = prediction_date + timedelta(days=days_ahead)
                        
                        # 営業日調整（簡易版：土日をスキップ）
                        while target_date.weekday() >= 5:  # 土曜日=5, 日曜日=6
                            target_date += timedelta(days=1)
                        
                        insert_sql = """
                        INSERT INTO daily_predictions 
                        (prediction_date, target_date, contract_month, days_ahead, 
                         model_name, predicted_price, model_version, features_used)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (prediction_date, target_date, contract_month, model_name)
                        DO UPDATE SET 
                            predicted_price = EXCLUDED.predicted_price,
                            model_version = EXCLUDED.model_version,
                            features_used = EXCLUDED.features_used;
                        """
                        
                        cursor.execute(insert_sql, (
                            prediction_date.date(),
                            target_date.date(),
                            self.target_contract,
                            days_ahead,
                            model_name,
                            float(predicted_price),
                            'v1.0',
                            self.feature_columns
                        ))
                
                conn.commit()
                logger.info(f"Saved predictions for {len(predictions)} models")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving predictions: {str(e)}")
            return False
    
    def update_actual_prices(self) -> bool:
        """実際の価格でpredictionsテーブルを更新"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            with conn.cursor() as cursor:
                # 実際の価格が利用可能な予測を更新
                update_sql = """
                UPDATE daily_predictions dp
                SET 
                    actual_price = f.close_price,
                    prediction_error = ABS(dp.predicted_price - f.close_price)
                FROM lme_copper_futures f
                WHERE dp.target_date = f.trade_date
                    AND dp.contract_month = f.contract_month
                    AND dp.actual_price IS NULL
                    AND f.close_price IS NOT NULL;
                """
                
                cursor.execute(update_sql)
                rows_updated = cursor.rowcount
                
                conn.commit()
                logger.info(f"Updated {rows_updated} predictions with actual prices")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating actual prices: {str(e)}")
            return False
    
    def evaluate_model_performance(self) -> Dict:
        """モデルパフォーマンスの評価"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # 過去30日の予測精度を計算
            query = """
            SELECT 
                model_name,
                days_ahead,
                COUNT(*) as total_predictions,
                AVG(ABS(prediction_error)) as mae,
                SQRT(AVG(prediction_error * prediction_error)) as rmse,
                AVG(ABS(prediction_error / actual_price) * 100) as mape,
                AVG(
                    CASE 
                        WHEN (predicted_price > LAG(actual_price) OVER (PARTITION BY model_name ORDER BY target_date)) 
                             AND (actual_price > LAG(actual_price) OVER (PARTITION BY model_name ORDER BY target_date))
                        THEN 1
                        WHEN (predicted_price < LAG(actual_price) OVER (PARTITION BY model_name ORDER BY target_date)) 
                             AND (actual_price < LAG(actual_price) OVER (PARTITION BY model_name ORDER BY target_date))
                        THEN 1
                        ELSE 0
                    END
                ) as directional_accuracy
            FROM daily_predictions
            WHERE actual_price IS NOT NULL
                AND target_date >= CURRENT_DATE - INTERVAL '30 days'
                AND contract_month = %s
            GROUP BY model_name, days_ahead
            ORDER BY model_name, days_ahead;
            """
            
            performance_df = pd.read_sql_query(query, conn, params=(self.target_contract,))
            conn.close()
            
            # パフォーマンス結果をデータベースに保存
            self.save_performance_metrics(performance_df)
            
            # 結果を辞書形式で返す
            performance_dict = {}
            for _, row in performance_df.iterrows():
                model_name = row['model_name']
                if model_name not in performance_dict:
                    performance_dict[model_name] = {}
                
                performance_dict[model_name][f"day_{row['days_ahead']}"] = {
                    'mae': float(row['mae']) if row['mae'] else 0,
                    'rmse': float(row['rmse']) if row['rmse'] else 0,
                    'mape': float(row['mape']) if row['mape'] else 0,
                    'directional_accuracy': float(row['directional_accuracy']) if row['directional_accuracy'] else 0,
                    'total_predictions': int(row['total_predictions'])
                }
            
            return performance_dict
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {str(e)}")
            return {}
    
    def save_performance_metrics(self, performance_df: pd.DataFrame):
        """パフォーマンスメトリクスをデータベースに保存"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            with conn.cursor() as cursor:
                for _, row in performance_df.iterrows():
                    insert_sql = """
                    INSERT INTO prediction_performance 
                    (evaluation_date, model_name, contract_month, days_ahead, 
                     mae, rmse, mape, directional_accuracy, total_predictions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (evaluation_date, model_name, contract_month, days_ahead)
                    DO UPDATE SET 
                        mae = EXCLUDED.mae,
                        rmse = EXCLUDED.rmse,
                        mape = EXCLUDED.mape,
                        directional_accuracy = EXCLUDED.directional_accuracy,
                        total_predictions = EXCLUDED.total_predictions;
                    """
                    
                    cursor.execute(insert_sql, (
                        datetime.now().date(),
                        row['model_name'],
                        self.target_contract,
                        int(row['days_ahead']),
                        float(row['mae']) if row['mae'] else None,
                        float(row['rmse']) if row['rmse'] else None,
                        float(row['mape']) if row['mape'] else None,
                        float(row['directional_accuracy']) if row['directional_accuracy'] else None,
                        int(row['total_predictions'])
                    ))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving performance metrics: {str(e)}")
    
    def run_daily_prediction(self) -> Dict:
        """日次予測の実行"""
        logger.info("Starting daily prediction run...")
        
        result = {
            'success': False,
            'prediction_date': datetime.now().date(),
            'models_used': [],
            'predictions_saved': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # テーブル作成
            if not self.create_prediction_tables():
                result['errors'].append("Failed to create prediction tables")
                return result
            
            # モデル読み込み
            if not self.load_models():
                result['errors'].append("Failed to load models")
                return result
            
            # 最新データ取得
            data = self.get_latest_data()
            if data.empty:
                result['errors'].append("Failed to get latest data")
                return result
            
            # 予測実行
            predictions = self.make_predictions(data)
            if not predictions:
                result['errors'].append("Failed to generate predictions")
                return result
            
            result['models_used'] = list(predictions.keys())
            
            # 予測結果保存
            if self.save_predictions(predictions, datetime.now()):
                result['predictions_saved'] = len(predictions) * self.prediction_horizon
            
            # 実際の価格で過去の予測を更新
            self.update_actual_prices()
            
            # モデルパフォーマンス評価
            result['performance_metrics'] = self.evaluate_model_performance()
            
            result['success'] = True
            logger.info("Daily prediction completed successfully")
            
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
            logger.error(f"Error in daily prediction: {str(e)}")
        
        return result

def main():
    """メイン実行関数"""
    prediction_system = DailyPredictionSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'predict':
            # 手動で予測実行
            result = prediction_system.run_daily_prediction()
            print(f"Prediction result: {result}")
            
        elif command == 'evaluate':
            # モデルパフォーマンス評価のみ実行
            performance = prediction_system.evaluate_model_performance()
            print(f"Model performance: {performance}")
            
        elif command == 'update':
            # 実際の価格で更新のみ実行
            prediction_system.update_actual_prices()
            
        else:
            print("Available commands: predict, evaluate, update")
            sys.exit(1)
    else:
        # デフォルトは完全な予測実行
        result = prediction_system.run_daily_prediction()
        print(f"Daily prediction result: {result}")

if __name__ == "__main__":
    main()