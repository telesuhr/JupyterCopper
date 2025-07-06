# LME銅先物分析システム - 本番運用ガイド

## 概要

このシステムは、LME銅先物データの自動収集、予測、監視を行う統合システムです。
ロードマップに基づいて実装された本番運用システムとして使用できます。

## システム構成

```
RefinitivDB/
├── automation/           # 自動化システム
│   └── daily_data_scheduler.py
├── prediction/          # 予測システム
│   └── daily_prediction_system.py
├── dashboard/           # 監視ダッシュボード
│   └── monitoring_dashboard.py
├── models/              # 訓練済みモデル保存
├── logs/                # システムログ
├── backups/             # データベースバックアップ
└── run_production_system.py  # メイン実行スクリプト
```

## 主要機能

### 1. 自動データ収集システム (`automation/daily_data_scheduler.py`)
- **機能**: 毎日定時にLME銅先物データを収集
- **スケジュール**: 平日午前7時（設定可能）
- **監視**: データ品質チェック、異常検知
- **アラート**: 収集失敗時のメール通知
- **バックアップ**: 日次データベースバックアップ

### 2. 日次予測システム (`prediction/daily_prediction_system.py`)
- **モデル**: Random Forest, XGBoost, ARIMA, LSTM, Prophet
- **予測期間**: 5営業日先まで
- **対象**: 3Mアウトライト（設定可能）
- **評価**: MAE, RMSE, MAPE, 方向性精度
- **アンサンブル**: 複数モデルの組み合わせ予測

### 3. 監視ダッシュボード (`dashboard/monitoring_dashboard.py`)
- **Webベース**: Streamlit使用のリアルタイム監視
- **表示項目**: 
  - システム状況（データ収集成功率、処理時間）
  - 先物カーブ（コンタンゴ/バックワーデーション分析）
  - 予測パフォーマンス（モデル別精度推移）
  - 価格分析（ローソク足、出来高、ボラティリティ）
  - アラート（システム異常、精度低下警告）

## 使用方法

### 基本コマンド

```bash
# システム状況確認
python run_production_system.py status

# 単発実行
python run_production_system.py collect    # データ収集のみ
python run_production_system.py predict    # 予測のみ
python run_production_system.py validate   # データ検証のみ
python run_production_system.py backup     # バックアップのみ

# フルパイプライン実行
python run_production_system.py pipeline

# ダッシュボード起動
python run_production_system.py dashboard

# 本番スケジューラー起動
python run_production_system.py schedule
```

### 本番運用スケジュール

```
平日 07:00: フルパイプライン実行（データ収集 → 予測）
平日 13:00: 追加予測更新
毎日 02:00: データベースバックアップ
```

### ダッシュボードアクセス

```bash
python run_production_system.py dashboard
```
→ http://localhost:8501 でアクセス

## 設定

### 環境変数 (`.env`)

```bash
# データベース設定
DB_HOST=localhost
DB_NAME=lme_copper_db
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432

# Refinitiv EIKON API
EIKON_APP_KEY=your_api_key

# アラート設定（オプション）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=alert_recipient@gmail.com
EMAIL_PASSWORD=your_app_password

# スケジュール設定
COLLECTION_TIME=07:00
BACKUP_TIME=02:00
```

### データベース設定

システムは以下のテーブルを自動作成します：

1. `lme_copper_futures` - 先物価格データ
2. `daily_predictions` - 日次予測結果
3. `prediction_performance` - モデルパフォーマンス履歴
4. `data_collection_log` - データ収集ログ

## システム監視

### アラート条件

1. **データ収集**: 2日以上データ更新なし
2. **予測精度**: MAPE > 5%の継続
3. **システム**: プロセス停止、エラー率増加

### ログファイル

```
logs/
├── daily_scheduler_YYYYMM.log      # データ収集ログ
├── daily_predictions_YYYYMM.log    # 予測システムログ
└── production_system_YYYYMM.log    # メインシステムログ
```

### パフォーマンス指標

- **データ収集成功率**: 95%以上を目標
- **予測精度**: 1日先予測でMAPE < 3%
- **方向性精度**: 60%以上
- **システム稼働率**: 99%以上

## トラブルシューティング

### よくある問題

1. **EIKON API接続エラー**
   ```bash
   # APIキー確認
   echo $EIKON_APP_KEY
   
   # 手動データ収集テスト
   python data_collectors/lme_copper_futures_collector.py
   ```

2. **データベース接続エラー**
   ```bash
   # PostgreSQL起動確認
   pg_ctl status
   
   # 接続テスト
   psql -h localhost -U postgres -d lme_copper_db
   ```

3. **予測精度低下**
   ```bash
   # モデル再訓練が必要
   # 分析ノートブック9を参照
   jupyter notebook analysis_notebooks/9_timeseries_modeling_comprehensive.ipynb
   ```

4. **ダッシュボードエラー**
   ```bash
   # Streamlit再インストール
   pip install streamlit plotly
   
   # 手動起動
   streamlit run dashboard/monitoring_dashboard.py
   ```

## 保守・運用

### 日次チェック項目

- [ ] ダッシュボードでシステム状況確認
- [ ] データ収集成功確認
- [ ] 予測結果の妥当性確認
- [ ] アラート有無確認

### 週次チェック項目

- [ ] ログファイルの確認とクリーンアップ
- [ ] データベースバックアップの確認
- [ ] 予測精度の週次評価
- [ ] システムリソース使用量確認

### 月次チェック項目

- [ ] モデル性能の月次評価
- [ ] システム全体の性能評価
- [ ] バックアップファイルの整理
- [ ] セキュリティアップデート適用

## 拡張・改良

現在の実装は基盤として、以下の拡張が可能です：

1. **マルチアセット対応** - 他の商品・通貨への拡張
2. **高度なAIモデル** - Transformer、強化学習の導入
3. **リアルタイム処理** - ストリーミングデータ対応
4. **アラート拡充** - Slack、Teams連携
5. **API化** - REST API提供
6. **スケーリング** - Docker、Kubernetes対応

## サポート

システムに関する問題や改善提案は、プロジェクトチーム、またはシステム管理者にご連絡ください。

---

**注意**: 本番環境では適切なセキュリティ設定（認証、暗号化、アクセス制御）を必ず実装してください。