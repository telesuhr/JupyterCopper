# LME銅先物データ分析プロジェクト

## プロジェクト概要
このプロジェクトは、Refinitiv EIKON Data APIを使用してLME（ロンドン金属取引所）銅先物データを収集し、PostgreSQLデータベースに格納、包括的な分析を実行します。

## フォルダ構成

```
RefinitivDB/
├── README.md                     # このファイル
├── analysis_notebooks/           # 分析用Jupyterノートブック
│   ├── 1_futures_curve_dynamics.ipynb               # 先物カーブ動力学分析
│   ├── 2_volume_liquidity.ipynb                     # 出来高・流動性分析
│   ├── 3_correlation_cointegration.ipynb            # 相関・共和分分析
│   ├── 4_volatility_risk.ipynb                      # ボラティリティ・リスク分析
│   ├── lme_copper_analysis.ipynb                    # 基本価格分析
│   └── lme_copper_futures_analysis.ipynb            # 先物データ検証
├── data_collectors/              # データ収集スクリプト
│   ├── lme_copper_data_collector.py                  # 3M・スプレッドデータ収集
│   ├── lme_copper_futures_collector.py               # 36限月先物データ収集
│   ├── setup_database.py                            # データベースセットアップ
│   ├── debug_data_fields.py                         # フィールド確認スクリプト
│   ├── quick_visualization.py                       # クイック可視化
│   └── test_copper_futures_rics.py                  # RICコード検証
├── verification_scripts/         # データ検証スクリプト
│   └── verify_futures_data.py                       # データ品質検証
├── generated_images/             # 生成された分析チャート
├── logs/                         # ログファイル
├── config_docs/                  # 設定・ドキュメント
│   ├── requirements.txt                             # Python依存関係
│   └── tableplus_connection.md                      # TablePlus接続設定
└── venv/                         # Python仮想環境
```

## 主要機能

### 1. データ収集
- **3Mアウトライト・スプレッドデータ**: 過去3年分
- **36限月先物データ**: 過去5年分（CMCUc1-CMCUc36）
- **データ項目**: 4本値（OHLC）、出来高、建玉

### 2. 分析ノートブック
- **先物カーブ動力学**: 3D可視化、コンタンゴ・バックワーデーション分析
- **出来高・流動性**: 流動性分布、時間パターン、マーケットマイクロ構造
- **相関・共和分**: 統計的関係、ペア取引機会、平均回帰
- **ボラティリティ・リスク**: VaR、GARCH、極値事象、リスク指標

### 3. データ検証
- データ完全性チェック（99.9%達成）
- 価格連続性検証
- 出来高妥当性確認

## セットアップ

### 1. 環境準備
```bash
cd /Users/Yusuke/claude-code/RefinitivDB
source venv/bin/activate
pip install -r config_docs/requirements.txt
```

### 2. データベース設定
```bash
# PostgreSQL起動（初回のみ）
brew services start postgresql@14

# データベースセットアップ
python data_collectors/setup_database.py
```

### 3. データ収集実行
```bash
# 3Mアウトライト・スプレッドデータ
python data_collectors/lme_copper_data_collector.py

# 36限月先物データ
python data_collectors/lme_copper_futures_collector.py
```

### 4. データ検証
```bash
python verification_scripts/verify_futures_data.py
```

## 分析実行方法

### Jupyterノートブック起動
```bash
jupyter lab analysis_notebooks/
```

### 推奨実行順序
1. `lme_copper_futures_analysis.ipynb` - データ検証
2. `1_futures_curve_dynamics.ipynb` - カーブ分析
3. `2_volume_liquidity.ipynb` - 流動性分析
4. `3_correlation_cointegration.ipynb` - 統計分析
5. `4_volatility_risk.ipynb` - リスク分析

## データベース構造

### テーブル: lme_copper_data
- 3Mアウトライト（CMCU3）
- Cash/3Mスプレッド（CMCU0-3）

### テーブル: lme_copper_futures
- 36限月先物（CMCUc1-CMCUc36）
- 4本値、出来高、建玉データ

## トレーディング活用

### 1. カレンダースプレッド取引
- 平均回帰戦略
- Z-score > 2でのシグナル生成
- 半減期10-30日のポジション保有

### 2. リスク管理
- ポートフォリオVaR 1-2%
- GARCH予測による動的ヘッジ
- ストレス期間監視

### 3. 流動性考慮
- 前3-6限月での活発取引
- 高ボラティリティ期間回避
- 効率性指標による取引コスト最適化

## 技術仕様

- **言語**: Python 3.8+
- **データソース**: Refinitiv EIKON Data API
- **データベース**: PostgreSQL 14
- **分析**: pandas, numpy, matplotlib, seaborn, plotly
- **統計**: statsmodels, arch (GARCH)
- **可視化**: Jupyter Lab

## 注意事項

- EIKON Workspaceが起動している必要があります
- 大量データ処理のため十分なメモリを確保してください
- 市場時間外でのデータ収集を推奨します

## 更新履歴

- 2025-07-05: プロジェクト初期作成
- データ収集・分析パイプライン構築完了
- 4つの包括的分析ノートブック作成