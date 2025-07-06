# LME銅先物分析システム - 詳細使用マニュアル

## 目次

1. [システム概要](#システム概要)
2. [初期セットアップ](#初期セットアップ)
3. [基本操作](#基本操作)
4. [ダッシュボード操作](#ダッシュボード操作)
5. [データ収集](#データ収集)
6. [予測システム](#予測システム)
7. [監視・アラート](#監視アラート)
8. [バックアップ・復旧](#バックアップ復旧)
9. [トラブルシューティング](#トラブルシューティング)
10. [高度な使用方法](#高度な使用方法)
11. [分析ノートブック](#分析ノートブック)
12. [Cash/3Mスプレッド分析](#cash3mスプレッド分析)
13. [隣月間スプレッド分析](#隣月間スプレッド分析)

---

## システム概要

### アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EIKON API     │───▶│  データ収集     │───▶│  PostgreSQL     │
│  (Refinitiv)    │    │   スケジューラー │    │   データベース   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Webダッシュボード│◀───│   予測システム   │◀───│  機械学習モデル  │
│  (Streamlit)    │    │ (マルチモデル)   │    │ (RF/XGB/ARIMA)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 主要コンポーネント

| コンポーネント | ファイル | 機能 |
|---------------|---------|------|
| **データ収集** | `automation/daily_data_scheduler.py` | EIKON APIからの日次データ取得 |
| **予測システム** | `prediction/daily_prediction_system.py` | マルチモデル価格予測 |
| **ダッシュボード** | `dashboard/monitoring_dashboard.py` | リアルタイム監視・可視化 |
| **統合管理** | `run_production_system.py` | システム全体の制御 |

---

## 初期セットアップ

### 1. 前提条件

```bash
# Python 3.8+ が必要
python --version

# 必要なライブラリのインストール
pip install -r requirements.txt

# PostgreSQLが起動していることを確認
pg_ctl status
```

### 2. 環境変数設定

`.env` ファイルを作成：

```bash
# データベース設定
DB_HOST=localhost
DB_NAME=lme_copper_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

# Refinitiv EIKON API（必須）
EIKON_APP_KEY=your_eikon_api_key

# スケジュール設定（オプション）
COLLECTION_TIME=07:00
BACKUP_TIME=02:00

# メールアラート設定（オプション）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=alert_recipient@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 3. データベース初期化

```bash
# PostgreSQLにデータベース作成
createdb lme_copper_db

# テーブルは自動作成されます（初回実行時）
```

### 4. システム状況確認

```bash
# システムコンポーネントの確認
python run_production_system.py status
```

**期待される出力:**
```
LME銅先物分析システム - 状況確認
==================================================
data_collector: ✓ /path/to/lme_copper_futures_collector.py
scheduler: ✓ /path/to/daily_data_scheduler.py
predictor: ✓ /path/to/daily_prediction_system.py
dashboard: ✓ /path/to/monitoring_dashboard.py
Logs: ✓ /path/to/logs
Models: ✓ /path/to/models
```

---

## 基本操作

### コマンド一覧

| コマンド | 説明 | 実行時間目安 |
|---------|------|-------------|
| `status` | システム状況確認 | 即座 |
| `collect` | データ収集のみ実行 | 5-10分 |
| `predict` | 予測のみ実行 | 2-5分 |
| `validate` | データ検証のみ実行 | 1-2分 |
| `backup` | バックアップのみ実行 | 3-5分 |
| `pipeline` | フルパイプライン実行 | 10-20分 |
| `dashboard` | ダッシュボード起動 | 即座 |
| `schedule` | 24/7スケジューラー起動 | 常駐 |

### 基本的な実行例

#### 1. 初回データ収集

```bash
# 過去のデータを収集（初回セットアップ時）
python run_production_system.py collect

# 実行ログの確認
tail -f logs/daily_scheduler_$(date +%Y%m).log
```

#### 2. 予測実行

```bash
# 訓練済みモデルによる予測実行
python run_production_system.py predict

# 予測結果の確認
python run_production_system.py dashboard
```

#### 3. フルパイプライン実行

```bash
# データ収集 → 予測 → 検証の完全実行
python run_production_system.py pipeline
```

**出力例:**
```
Pipeline Results:
  data_collection: ✓
  prediction: ✓
  validation: ✓
  overall_success: ✓
```

---

## ダッシュボード操作

### 1. ダッシュボード起動

```bash
# ダッシュボードを起動
python run_production_system.py dashboard

# ブラウザで以下にアクセス
# http://localhost:8501
```

### 2. ダッシュボード画面構成

#### メイン画面

```
┌─────────────────────────────────────────────────┐
│ 📊 LME銅先物監視ダッシュボード                    │
├─────────────────────────────────────────────────┤
│ ⚠️ アラート                                      │
│ ✅ 現在アラートはありません                       │
├─────────────────────────────────────────────────┤
│ 🔧 システム状況                                  │
│ ┌───────┬───────┬───────┬───────┐              │
│ │成功率 │平均   │処理   │最新   │              │
│ │95.2% │1,250  │45.3秒 │0日前  │              │
│ └───────┴───────┴───────┴───────┘              │
├─────────────────────────────────────────────────┤
│ 📈 先物カーブ                                    │
│ [価格チャート表示エリア]                         │
├─────────────────────────────────────────────────┤
│ 🎯 予測パフォーマンス                            │
│ [モデル精度表示エリア]                           │
└─────────────────────────────────────────────────┘
```

#### サイドバー設定

```
⚙️ 設定
├─ ☑️ 自動更新 (5分)
├─ 表示セクション
│  ☑️ システム状況
│  ☑️ 先物カーブ
│  ☑️ 予測パフォーマンス
│  ☑️ アラート
└─ 分析対象契約月: 3M
```

### 3. 主要画面の説明

#### システム状況画面

- **データ収集成功率**: 過去30日の収集成功率
- **平均収集レコード数**: 1回あたりの取得レコード数
- **平均処理時間**: データ収集にかかる時間
- **最新データ収集**: 最後にデータが更新された日数

#### 先物カーブ画面

- **価格カーブ**: 各限月の終値をプロット
- **スプレッド情報**: 
  - 1M-3Mスプレッド: 短期の需給状況
  - 3M-12Mスプレッド: 長期トレンド
- **市場構造**: コンタンゴ/バックワーデーション判定

#### 予測パフォーマンス画面

- **モデル別精度**: 各予測モデルのMAE、MAPE、方向性精度
- **精度推移チャート**: 時系列での予測精度変化
- **予測vs実績**: 散布図による精度可視化

#### 価格分析画面

- **ローソク足チャート**: OHLC価格データ
- **出来高チャート**: 取引量の推移
- **統計情報**: 最高値、最安値、ボラティリティ

---

## データ収集

### 1. 手動データ収集

#### 基本的な収集

```bash
# 最新3日分のデータ収集
python run_production_system.py collect
```

#### データ収集の詳細確認

```bash
# 収集プロセスのリアルタイム監視
python automation/daily_data_scheduler.py collect

# ログの詳細確認
tail -f logs/daily_scheduler_$(date +%Y%m).log
```

**正常なログ例:**
```
2024-01-15 07:00:01 - INFO - Starting daily data collection...
2024-01-15 07:00:02 - INFO - EIKON API initialized successfully
2024-01-15 07:00:03 - INFO - Database connection established
2024-01-15 07:00:05 - INFO - Processing Month_01 (CMCUc1) - Month 1
2024-01-15 07:00:08 - INFO - Successfully fetched 3 records for CMCUc1
...
2024-01-15 07:05:30 - INFO - Daily collection successful. Processed 36 contracts, collected 108 records
```

### 2. 自動データ収集設定

#### スケジューラー起動

```bash
# 24/7自動データ収集の開始
python run_production_system.py schedule

# バックグラウンド実行
nohup python run_production_system.py schedule > scheduler.log 2>&1 &
```

#### スケジュール設定の確認

デフォルトスケジュール:
- **平日 07:00**: フルデータ収集 + 予測
- **平日 13:00**: 予測のみ更新
- **毎日 02:00**: データベースバックアップ

#### スケジュール変更

`.env` ファイルで時刻変更:
```bash
COLLECTION_TIME=09:00  # 午前9時に変更
BACKUP_TIME=01:00      # 午前1時に変更
```

### 3. データ品質チェック

#### 手動検証実行

```bash
# データ品質チェックのみ実行
python run_production_system.py validate
```

#### 検証項目

1. **最新性チェック**: データが3日以上古くないか
2. **欠損データチェック**: 欠損率が10%を超えていないか
3. **異常価格チェック**: 前日比10%以上の価格変動がないか

**正常な検証結果例:**
```json
{
  "success": true,
  "checks": {
    "latest_data": {
      "latest_date": "2024-01-15",
      "days_behind": 0,
      "total_records": 15840
    },
    "missing_data": [
      {"contract_month": 1, "missing_percentage": 0.0},
      {"contract_month": 2, "missing_percentage": 2.1}
    ],
    "anomalous_prices": []
  },
  "warnings": [],
  "errors": []
}
```

---

## 予測システム

### 1. 予測実行

#### 基本的な予測

```bash
# 訓練済みモデルで予測実行
python run_production_system.py predict
```

#### 予測の詳細確認

```bash
# 予測プロセスの詳細実行
python prediction/daily_prediction_system.py predict

# 予測ログの確認
tail -f logs/daily_predictions_$(date +%Y%m).log
```

**正常な予測ログ例:**
```
2024-01-15 13:00:01 - INFO - Starting daily prediction run...
2024-01-15 13:00:02 - INFO - Prediction tables created successfully
2024-01-15 13:00:03 - INFO - Loaded random_forest model
2024-01-15 13:00:03 - INFO - Loaded xgboost model
2024-01-15 13:00:04 - INFO - Loaded arima model
2024-01-15 13:00:10 - INFO - Generated predictions for 4 models
2024-01-15 13:00:11 - INFO - Saved predictions for 4 models
2024-01-15 13:00:12 - INFO - Updated 25 predictions with actual prices
2024-01-15 13:00:13 - INFO - Daily prediction completed successfully
```

### 2. 使用モデル

#### 利用可能モデル

| モデル | ファイル | 特徴 | 予測期間 |
|-------|---------|------|----------|
| **Random Forest** | `rf_model.pkl` | アンサンブル学習、安定性 | 1-5日 |
| **XGBoost** | `xgb_model.pkl` | 勾配ブースティング、高精度 | 1-5日 |
| **ARIMA** | `arima_model.pkl` | 時系列分析、トレンド追従 | 1-5日 |
| **LSTM** | `lstm_model.h5` | 深層学習、パターン認識 | 1-5日 |
| **Prophet** | `prophet_model.pkl` | 季節性考慮、休日対応 | 1-5日 |
| **Ensemble** | - | 全モデルの平均 | 1-5日 |

#### モデル精度の目安

| 予測期間 | 目標MAPE | 目標方向性精度 |
|---------|----------|---------------|
| 1日先 | < 2.0% | > 65% |
| 2日先 | < 3.0% | > 60% |
| 3日先 | < 4.0% | > 58% |
| 5日先 | < 6.0% | > 55% |

### 3. 予測結果の確認

#### データベースでの確認

```sql
-- 最新の予測結果確認
SELECT 
    prediction_date,
    target_date,
    model_name,
    predicted_price,
    actual_price,
    prediction_error
FROM daily_predictions 
WHERE prediction_date = CURRENT_DATE
ORDER BY target_date, model_name;
```

#### ダッシュボードでの確認

1. ダッシュボード起動: `python run_production_system.py dashboard`
2. 「予測パフォーマンス」セクションで確認
3. 「予測 vs 実績」チャートで精度確認

### 4. モデル性能評価

#### 手動評価実行

```bash
# モデル性能評価のみ実行
python prediction/daily_prediction_system.py evaluate
```

#### 評価メトリクス

- **MAE (Mean Absolute Error)**: 平均絶対誤差
- **RMSE (Root Mean Square Error)**: 二乗平均平方根誤差
- **MAPE (Mean Absolute Percentage Error)**: 平均絶対パーセント誤差
- **方向性精度**: 価格上昇/下落の予測的中率

---

## 監視・アラート

### 1. アラート条件

#### システムアラート

| アラートレベル | 条件 | 対応アクション |
|---------------|------|--------------|
| **エラー** | データ収集が2日以上停止 | 即座に調査・復旧 |
| **エラー** | 予測システムが完全に停止 | システム再起動 |
| **警告** | データ収集成功率 < 90% | 原因調査 |
| **警告** | 予測精度MAPE > 5% | モデル再訓練検討 |
| **警告** | 欠損データ率 > 10% | データソース確認 |

#### 価格アラート

| 条件 | アラート内容 |
|------|-------------|
| 前日比 > 5% | 急激な価格変動検出 |
| スプレッド異常 | カーブ形状の急変 |
| 出来高急増 | 通常の3倍以上の出来高 |

### 2. ログ監視

#### 重要ログファイル

```bash
# 各システムのログファイル
logs/
├── daily_scheduler_YYYYMM.log      # データ収集
├── daily_predictions_YYYYMM.log    # 予測システム
└── production_system_YYYYMM.log    # 統合システム
```

#### ログ監視コマンド

```bash
# リアルタイムログ監視
tail -f logs/daily_scheduler_$(date +%Y%m).log

# エラーログの検索
grep -i error logs/*.log

# 警告ログの検索
grep -i warning logs/*.log

# 成功率の確認
grep -c "completed successfully" logs/daily_scheduler_$(date +%Y%m).log
```

### 3. メールアラート設定

#### Gmail設定例

```bash
# .envファイルに追加
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=alert_recipient@gmail.com
EMAIL_PASSWORD=your_app_password  # Googleアプリパスワード
```

#### アプリパスワードの取得

1. Googleアカウント設定 → セキュリティ
2. 2段階認証を有効化
3. アプリパスワードを生成
4. 生成されたパスワードを`EMAIL_PASSWORD`に設定

---

## バックアップ・復旧

### 1. 自動バックアップ

#### バックアップスケジュール

- **実行時刻**: 毎日午前2時（設定可能）
- **保存先**: `/Users/Yusuke/claude-code/RefinitivDB/backups/`
- **ファイル名**: `lme_copper_db_backup_YYYYMMDD_HHMMSS.sql`
- **保持期間**: 7日間（古いファイルは自動削除）

#### 手動バックアップ

```bash
# 手動バックアップ実行
python run_production_system.py backup

# バックアップファイル確認
ls -la backups/lme_copper_db_backup_*.sql
```

### 2. データ復旧

#### 完全復旧

```bash
# PostgreSQLデータベースの完全復旧
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS lme_copper_db;"
psql -h localhost -U postgres -c "CREATE DATABASE lme_copper_db;"
psql -h localhost -U postgres -d lme_copper_db -f backups/lme_copper_db_backup_YYYYMMDD_HHMMSS.sql
```

#### 部分復旧（特定テーブル）

```bash
# 特定テーブルのみ復旧
pg_restore --table=daily_predictions backups/lme_copper_db_backup_YYYYMMDD_HHMMSS.sql
```

### 3. 災害復旧手順

#### 手順1: システム状況確認

```bash
# システム全体の状況確認
python run_production_system.py status

# データベース接続確認
psql -h localhost -U postgres -d lme_copper_db -c "SELECT COUNT(*) FROM lme_copper_futures;"
```

#### 手順2: データ復旧

```bash
# 最新バックアップから復旧
LATEST_BACKUP=$(ls -t backups/lme_copper_db_backup_*.sql | head -1)
psql -h localhost -U postgres -d lme_copper_db -f $LATEST_BACKUP
```

#### 手順3: システム再起動

```bash
# システム全体の再起動
python run_production_system.py pipeline

# スケジューラー再起動
nohup python run_production_system.py schedule > scheduler.log 2>&1 &
```

#### 手順4: 動作確認

```bash
# ダッシュボードで動作確認
python run_production_system.py dashboard

# データ整合性確認
python run_production_system.py validate
```

---

## トラブルシューティング

### 1. よくある問題と解決方法

#### EIKON API接続エラー

**症状:**
```
ERROR - EIKON API initialization failed: [Errno 11001] getaddrinfo failed
```

**原因と対処法:**

1. **APIキーの確認**
```bash
echo $EIKON_APP_KEY
# 空の場合は.envファイルを確認
```

2. **EIKON Terminal起動確認**
```bash
# EIKON Terminalが起動しているか確認
# またはRefinitiv Workspaceが起動しているか確認
```

3. **ネットワーク接続確認**
```bash
ping api.refinitiv.com
```

4. **API制限確認**
```bash
# 1日のAPI呼び出し回数制限を確認
# Refinitivの管理画面で使用量を確認
```

#### データベース接続エラー

**症状:**
```
ERROR - Database connection failed: could not connect to server
```

**対処法:**

1. **PostgreSQL起動確認**
```bash
# macOS (Homebrew)
brew services list | grep postgresql
brew services start postgresql@14

# Linux (systemd)
sudo systemctl status postgresql
sudo systemctl start postgresql
```

2. **接続パラメータ確認**
```bash
# .envファイルの設定確認
cat .env | grep DB_

# 手動接続テスト
psql -h localhost -U postgres -d lme_copper_db
```

3. **データベース存在確認**
```bash
# データベース一覧表示
psql -h localhost -U postgres -l

# データベース作成（存在しない場合）
createdb -h localhost -U postgres lme_copper_db
```

#### 予測精度低下

**症状:**
```
WARNING - random_forestモデルの精度が低下しています (MAPE: 8.5%)
```

**対処法:**

1. **データ品質確認**
```bash
python run_production_system.py validate
```

2. **モデル再訓練**
```bash
# 分析ノートブック9でモデル再訓練
jupyter notebook analysis_notebooks/9_timeseries_modeling_comprehensive.ipynb
```

3. **特徴量確認**
```sql
-- 最近のデータ品質確認
SELECT 
    trade_date,
    COUNT(*) as total_records,
    COUNT(close_price) as valid_prices,
    AVG(volume) as avg_volume
FROM lme_copper_futures 
WHERE trade_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY trade_date
ORDER BY trade_date;
```

#### ダッシュボードエラー

**症状:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**対処法:**

1. **必要ライブラリのインストール**
```bash
pip install streamlit plotly pandas
```

2. **手動起動確認**
```bash
streamlit run dashboard/monitoring_dashboard.py --server.port=8501
```

3. **ポート競合確認**
```bash
# ポート8501の使用状況確認
lsof -i :8501

# 別ポートで起動
streamlit run dashboard/monitoring_dashboard.py --server.port=8502
```

### 2. 性能問題の診断

#### メモリ使用量確認

```bash
# Pythonプロセスのメモリ使用量
ps aux | grep python | grep -E "(scheduler|prediction|dashboard)"

# システム全体のメモリ使用量
free -h  # Linux
vm_stat  # macOS
```

#### データベース性能確認

```sql
-- 実行中のクエリ確認
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- テーブルサイズ確認
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### ログ解析

```bash
# エラー頻度の確認
grep -c "ERROR" logs/daily_scheduler_$(date +%Y%m).log

# 処理時間の分析
grep "duration" logs/daily_scheduler_$(date +%Y%m).log | awk '{print $NF}' | sort -n

# 成功率の計算
SUCCESS=$(grep -c "completed successfully" logs/daily_scheduler_$(date +%Y%m).log)
TOTAL=$(grep -c "Starting" logs/daily_scheduler_$(date +%Y%m).log)
echo "Success rate: $(echo "scale=2; $SUCCESS / $TOTAL * 100" | bc)%"
```

---

## 高度な使用方法

### 1. カスタム設定

#### 予測対象の変更

```python
# prediction/daily_prediction_system.py の設定変更
class DailyPredictionSystem:
    def __init__(self):
        # ...
        self.target_contract = 6  # 3Mから6Mに変更
        self.prediction_horizon = 10  # 5日から10日に変更
```

#### 特徴量の追加

```python
# 新しい特徴量を追加
def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
    # 既存の特徴量 + 新規追加
    df['bollinger_upper'] = df['ma_20'] + (df['close_price'].rolling(20).std() * 2)
    df['bollinger_lower'] = df['ma_20'] - (df['close_price'].rolling(20).std() * 2)
    df['williams_r'] = talib.WILLR(df['high_price'], df['low_price'], df['close_price'])
    
    return df
```

### 2. API拡張

#### REST API化

```python
# api/prediction_api.py (新規作成)
from flask import Flask, jsonify
from prediction.daily_prediction_system import DailyPredictionSystem

app = Flask(__name__)

@app.route('/api/predictions/latest')
def get_latest_predictions():
    predictor = DailyPredictionSystem()
    # 最新予測の取得・返却
    return jsonify(predictions)

@app.route('/api/performance/<model_name>')
def get_model_performance(model_name):
    # モデル性能の取得・返却
    return jsonify(performance)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### 使用例

```bash
# API起動
python api/prediction_api.py

# APIテスト
curl http://localhost:5000/api/predictions/latest
curl http://localhost:5000/api/performance/random_forest
```

### 3. 多環境対応

#### 開発環境設定

```bash
# .env.development
DB_NAME=lme_copper_db_dev
COLLECTION_TIME=09:00
DEBUG=True

# 開発環境での実行
ENV=development python run_production_system.py pipeline
```

#### 本番環境設定

```bash
# .env.production
DB_NAME=lme_copper_db_prod
COLLECTION_TIME=07:00
DEBUG=False
EMAIL_ALERTS=True

# 本番環境での実行
ENV=production python run_production_system.py schedule
```

### 4. Docker化

#### Dockerfile例

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run_production_system.py", "schedule"]
```

#### Docker Compose例

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: lme_copper_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  lme_system:
    build: .
    depends_on:
      - postgres
    environment:
      DB_HOST: postgres
    volumes:
      - ./logs:/app/logs
      - ./backups:/app/backups

  dashboard:
    build: .
    command: streamlit run dashboard/monitoring_dashboard.py
    ports:
      - "8501:8501"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

#### 実行方法

```bash
# Docker環境の起動
docker-compose up -d

# ログ確認
docker-compose logs -f lme_system

# 停止
docker-compose down
```

### 5. 監視システム拡張

#### Prometheus + Grafana連携

```python
# monitoring/metrics.py (新規作成)
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# メトリクス定義
data_collection_success = Counter('lme_data_collection_success_total')
data_collection_duration = Histogram('lme_data_collection_duration_seconds')
prediction_accuracy = Gauge('lme_prediction_accuracy')

def track_data_collection():
    # データ収集メトリクスの更新
    data_collection_success.inc()
    
def track_prediction_accuracy(mape):
    # 予測精度メトリクスの更新
    prediction_accuracy.set(mape)

# メトリクスサーバー起動
start_http_server(9090)
```

#### Slack通知

```python
# alerts/slack_notifier.py (新規作成)
import requests
import json

def send_slack_alert(message, webhook_url):
    payload = {
        'text': f'🚨 LME System Alert: {message}',
        'channel': '#lme-alerts',
        'username': 'LME Bot'
    }
    
    response = requests.post(webhook_url, data=json.dumps(payload))
    return response.status_code == 200
```

---

## まとめ

このマニュアルに従って、LME銅先物分析システムを効果的に運用してください。

### 日常運用チェックリスト

#### 毎日
- [ ] ダッシュボードでシステム状況確認
- [ ] アラートの有無確認
- [ ] 予測精度の確認

#### 毎週
- [ ] ログファイルの確認
- [ ] バックアップファイルの確認
- [ ] システム性能の評価

#### 毎月
- [ ] モデル性能の詳細評価
- [ ] システム全体の見直し
- [ ] セキュリティアップデート

### サポート連絡先

システムに関する問題や質問は、以下まで連絡してください：

- **技術サポート**: システム管理者
- **業務サポート**: プロジェクトチーム
- **緊急時**: 24時間オンコール体制

---

## 分析ノートブック

### 1. 分析ノートブックの構成

#### 先物カーブ分析

```
analysis_notebooks/
├── 1_futures_curve_analysis.ipynb           # 先物カーブの基本分析
├── 2_futures_curve_3d_visualization.ipynb   # 3D可視化とカーブ動学
├── 3_volume_liquidity_analysis.ipynb        # 出来高・流動性分析
├── 4_correlation_cointegration_analysis.ipynb # 相関・共和分分析
├── 5_volatility_risk_metrics.ipynb          # ボラティリティ・リスク分析
└── 6_backtest_trading_strategies.ipynb      # バックテスト・取引戦略
```

#### 3Mアウトライト分析

```
analysis_notebooks/3m_outright/
├── 1_3m_outright_basic_analysis.ipynb       # 基本統計・トレンド分析
├── 2_3m_outright_technical_analysis.ipynb   # テクニカル分析
├── 3_3m_outright_volatility_analysis.ipynb  # ボラティリティ分析
├── 4_3m_outright_model_comparison.ipynb     # モデル比較・評価
└── 5_3m_outright_trading_strategies.ipynb   # 取引戦略・バックテスト
```

#### Cash/3Mスプレッド分析

```
analysis_notebooks/cash_3m_spread/
├── 1_cash_3m_spread_basic_analysis.ipynb        # 基本統計・分布分析
├── 2_cash_3m_spread_correlation_analysis.ipynb  # 相関・要因分析
├── 3_cash_3m_spread_cointegration_analysis.ipynb # 共和分・長期関係
├── 4_cash_3m_spread_seasonality_analysis.ipynb  # 季節性・周期性分析
├── 5_cash_3m_spread_volatility_analysis.ipynb   # ボラティリティ分析
├── 6_cash_3m_spread_market_regime_analysis.ipynb # 市場レジーム分析
├── 7_cash_3m_spread_timeseries_analysis.ipynb   # 時系列分析
├── 8_cash_3m_spread_modeling_comprehensive.ipynb # 包括的モデリング
├── 9_cash_3m_spread_interpretation_guide.ipynb  # 結果解釈ガイド
├── 10_spread_results_interpretation.ipynb       # 統合結果解釈
└── 11_spread_next_steps_roadmap.ipynb          # 実装ロードマップ
```

### 2. 分析ノートブックの使用方法

#### Jupyter Notebook起動

```bash
# Jupyter Notebookを起動
jupyter notebook

# 特定のノートブックを直接開く
jupyter notebook analysis_notebooks/1_futures_curve_analysis.ipynb
```

#### 分析の実行順序

1. **基本分析から開始**: 各カテゴリーの `1_*_basic_analysis.ipynb` から始める
2. **段階的な深掘り**: 番号順に実行して深い分析に進む
3. **結果の統合**: 最終的な解釈・統合ノートブックで全体把握

#### 分析結果の保存

```python
# 分析結果をファイルに保存
results.to_csv('analysis_results/futures_curve_analysis_results.csv')

# 図表を保存
fig.savefig('analysis_results/futures_curve_chart.png', dpi=300, bbox_inches='tight')
```

### 3. 各分析の特徴

#### 先物カーブ分析

- **対象**: 36ヶ月先物カーブ（M1-M36）
- **主要指標**: カーブ形状、スプレッド、流動性
- **用途**: 市場構造理解、期間構造分析

#### 3Mアウトライト分析

- **対象**: 3ヶ月先物価格（CMCUc3）
- **主要指標**: 価格動向、テクニカル指標、ボラティリティ
- **用途**: 価格予測、リスク管理

#### Cash/3Mスプレッド分析

- **対象**: Cash-3Mスプレッド
- **主要指標**: スプレッド水準、季節性、市場レジーム
- **用途**: 裁定取引、市場タイミング

---

## Cash/3Mスプレッド分析

### 1. 分析概要

Cash/3Mスプレッド分析は、LME銅のキャッシュ価格と3ヶ月先物価格の差額を分析し、市場の需給バランスと投資機会を特定するための包括的な分析です。

### 2. 分析の構成

#### Phase 1: 基本分析（ノートブック1-3）

- **基本統計・分布分析**: スプレッドの基本的な性質理解
- **相関・要因分析**: 他の市場要因との関係性
- **共和分・長期関係**: 長期的な均衡関係の分析

#### Phase 2: 深掘り分析（ノートブック4-6）

- **季節性・周期性分析**: 時期的なパターン特定
- **ボラティリティ分析**: リスク特性の把握
- **市場レジーム分析**: 市場状況による行動変化

#### Phase 3: 時系列分析（ノートブック7-8）

- **時系列分析**: ARIMAモデルによる予測
- **包括的モデリング**: 機械学習による高度な予測

#### Phase 4: 実装ガイド（ノートブック9-11）

- **結果解釈ガイド**: 実務での活用方法
- **統合結果解釈**: 全分析の統合的理解
- **実装ロードマップ**: 本格運用への道筋

### 3. 主要な発見と洞察

#### 市場構造の理解

- **Backwardation vs Contango**: 市場の需給状況判定
- **スプレッドの変動パターン**: 予測可能な周期性
- **ボラティリティクラスタリング**: リスク管理への応用

#### 投資機会の特定

- **平均回帰戦略**: スプレッドの収束性を利用
- **季節性戦略**: 時期的パターンの活用
- **ボラティリティ戦略**: 変動率の変化を捉える

### 4. 実務での活用方法

#### トレーディング戦略

```python
# スプレッド取引シグナルの例
if spread > upper_threshold:
    # ロングキャッシュ、ショート3M
    signal = "BUY_SPREAD"
elif spread < lower_threshold:
    # ショートキャッシュ、ロング3M
    signal = "SELL_SPREAD"
else:
    signal = "HOLD"
```

#### リスク管理

```python
# VaRベースのリスク管理
var_95 = np.percentile(spread_returns, 5)
position_size = risk_budget / abs(var_95)
```

### 5. 次のステップ

1. **リアルタイム監視**: スプレッドの動的監視システム
2. **自動取引**: シグナルに基づく自動執行
3. **パフォーマンス評価**: 戦略の継続的改善

---

## 隣月間スプレッド分析

### 1. 分析概要

隣月間スプレッド分析は、LME銅先物の隣接する限月間のスプレッド（M1-M2、M2-M3、M3-M4）を分析し、期間構造の歪みと裁定機会を特定するための新しい分析プロジェクトです。

### 2. 分析対象

#### 主要スプレッド

- **M1-M2スプレッド**: 第1限月 - 第2限月
- **M2-M3スプレッド**: 第2限月 - 第3限月
- **M3-M4スプレッド**: 第3限月 - 第4限月

#### 分析期間

- **データ期間**: 2020年1月〜現在
- **分析頻度**: 日次データ
- **更新頻度**: リアルタイム

### 3. 分析の特徴

#### 短期構造の特徴

- **ロールオーバー効果**: 限月切り替え時の価格変動
- **流動性プレミアム**: 限月による流動性の差
- **キャリー効果**: 期間構造による理論価格差

#### 裁定機会の特定

- **カレンダースプレッド**: 限月間の価格差異常
- **バタフライスプレッド**: 3限月の相対価格関係
- **タイムスプレッド**: 時間価値の歪み

### 4. 実装予定

#### Phase 1: データ準備と基本分析

- データベースからの隣月間スプレッド計算
- 基本統計と分布分析
- 視覚化とトレンド分析

#### Phase 2: 高度分析

- 相関分析と共和分テスト
- ボラティリティ分析
- 市場レジーム分析

#### Phase 3: モデリングと予測

- 機械学習モデルの構築
- 予測精度の評価
- シグナル生成システム

#### Phase 4: バックテストと実装

- 取引戦略のバックテスト
- リスク管理システム
- 実装ガイドライン

### 5. 期待される成果

#### 戦略的価値

- **新しい収益源**: 隣月間スプレッドの裁定機会
- **リスク分散**: 既存戦略との相関が低い新戦略
- **市場効率性**: 期間構造の歪み是正への貢献

#### 技術的価値

- **モデル高度化**: 多次元スプレッド分析技術
- **自動化**: リアルタイム監視・執行システム
- **知見蓄積**: LME市場構造の深い理解

---

**注意**: 本番環境では適切なセキュリティ設定（認証、暗号化、アクセス制御）を必ず実装してください。