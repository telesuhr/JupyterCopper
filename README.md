# LME銅先物データ分析プロジェクト

## プロジェクト概要
このプロジェクトは、Refinitiv EIKON Data APIを使用してLME（ロンドン金属取引所）銅先物データを収集し、PostgreSQLデータベースに格納、包括的な分析を実行します。

## フォルダ構成

```
RefinitivDB/
├── README.md                     # このファイル
├── analysis_notebooks/           # 分析用Jupyterノートブック
│   ├── adjacent_month_spreads/   # 隣月間スプレッド分析
│   │   ├── 1_adjacent_spreads_basic_analysis.ipynb         # M1-M2, M2-M3, M3-M4基本分析
│   │   ├── 2_adjacent_spreads_correlation_analysis.ipynb   # 相関・共和分分析
│   │   └── 3_adjacent_spreads_volatility_modeling.ipynb    # ボラティリティ・GARCH分析
│   ├── cash_3m_spread/           # Cash-3Mスプレッド分析
│   │   ├── 1_spread_curve_dynamics.ipynb                   # スプレッドカーブ動力学
│   │   ├── 2_spread_volume_liquidity.ipynb                 # 出来高・流動性分析
│   │   ├── 3_spread_correlation_cointegration.ipynb        # 相関・共和分分析
│   │   ├── 4_spread_volatility_risk.ipynb                  # ボラティリティ・リスク分析
│   │   ├── 5_spread_term_structure_volatility.ipynb        # ターム構造ボラティリティ
│   │   ├── 6_cash_3m_spread_visualization.ipynb           # スプレッド可視化
│   │   ├── 7_cash_3m_spread_timeseries_analysis.ipynb     # 時系列分析
│   │   ├── 8_cash_3m_spread_modeling_comprehensive.ipynb  # 包括的モデリング
│   │   ├── 9_cash_3m_spread_interpretation_guide.ipynb    # 解釈ガイド
│   │   ├── 10_spread_results_interpretation.ipynb         # 結果解釈
│   │   └── 11_spread_next_steps_roadmap.ipynb             # 次ステップロードマップ
│   ├── outright_3m/              # 3Mアウトライト分析
│   │   ├── 1_futures_curve_dynamics.ipynb                 # 先物カーブ動力学分析
│   │   ├── 2_volume_liquidity.ipynb                       # 出来高・流動性分析
│   │   ├── 3_correlation_cointegration.ipynb              # 相関・共和分分析
│   │   ├── 4_volatility_risk.ipynb                        # ボラティリティ・リスク分析
│   │   ├── 5_term_structure_volatility.ipynb              # ターム構造ボラティリティ
│   │   ├── 6_lme_3m_outright_visualization.ipynb          # 3Mアウトライト可視化
│   │   ├── 7_lme_3m_timeseries_analysis.ipynb             # 時系列分析
│   │   ├── 8_timeseries_interpretation_guide.ipynb        # 時系列解釈ガイド
│   │   ├── 9_timeseries_modeling_comprehensive.ipynb      # 包括的時系列モデリング
│   │   ├── 10_modeling_results_interpretation.ipynb       # モデリング結果解釈
│   │   └── 11_next_steps_roadmap.ipynb                    # 次ステップロードマップ
│   ├── analysis_results/         # 分析結果データ
│   │   └── adjacent_spreads/     # 隣月間スプレッド結果
│   ├── lme_copper_analysis.ipynb                          # 基本価格分析（従来版）
│   └── lme_copper_futures_analysis.ipynb                  # 先物データ検証（従来版）
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

#### 隣月間スプレッド分析 (adjacent_month_spreads/)
- **基本分析**: M1-M2, M2-M3, M3-M4スプレッドの統計的特性
- **相関・共和分分析**: スプレッド間の統計的関係、平均回帰性
- **ボラティリティ・GARCH分析**: 時間変動ボラティリティ、リスク予測

#### Cash-3Mスプレッド分析 (cash_3m_spread/)
- **スプレッドカーブ動力学**: コンタンゴ・バックワーデーション分析
- **出来高・流動性**: スプレッド取引の流動性パターン
- **時系列分析**: ARIMA, GARCH, 機械学習モデル
- **トレーディング戦略**: 平均回帰、モメンタム戦略

#### 3Mアウトライト分析 (outright_3m/)
- **先物カーブ動力学**: 3D可視化、期間構造分析
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

#### 初期セットアップ・データ検証
1. `lme_copper_futures_analysis.ipynb` - データ検証・品質確認

#### 隣月間スプレッド分析
2. `adjacent_month_spreads/1_adjacent_spreads_basic_analysis.ipynb` - 基本統計
3. `adjacent_month_spreads/2_adjacent_spreads_correlation_analysis.ipynb` - 相関分析
4. `adjacent_month_spreads/3_adjacent_spreads_volatility_modeling.ipynb` - ボラティリティ分析

#### Cash-3Mスプレッド分析
5. `cash_3m_spread/1_spread_curve_dynamics.ipynb` - スプレッドカーブ
6. `cash_3m_spread/6_cash_3m_spread_visualization.ipynb` - 可視化
7. `cash_3m_spread/7_cash_3m_spread_timeseries_analysis.ipynb` - 時系列分析
8. `cash_3m_spread/8_cash_3m_spread_modeling_comprehensive.ipynb` - モデリング

#### 3Mアウトライト分析
9. `outright_3m/1_futures_curve_dynamics.ipynb` - カーブ分析
10. `outright_3m/2_volume_liquidity.ipynb` - 流動性分析
11. `outright_3m/6_lme_3m_outright_visualization.ipynb` - 可視化
12. `outright_3m/7_lme_3m_timeseries_analysis.ipynb` - 時系列分析

## データベース構造

### テーブル: lme_copper_data
- 3Mアウトライト（CMCU3）
- Cash/3Mスプレッド（CMCU0-3）

### テーブル: lme_copper_futures
- 36限月先物（CMCUc1-CMCUc36）
- 4本値、出来高、建玉データ

## トレーディング活用

### 1. 隣月間スプレッド取引
- **M1-M2, M2-M3, M3-M4**の相対価値戦略
- 平均回帰パターンの活用（Z-score > 2でのシグナル生成）
- 短期保有期間（5-15日）での機動的取引

### 2. Cash-3Mスプレッド取引
- **コンタンゴ・バックワーデーション**転換点の捕捉
- 季節性パターンの活用（月別・四半期別傾向）
- 中期保有期間（10-30日）での平均回帰戦略

### 3. 3Mアウトライト取引
- トレンドフォロー戦略（移動平均、MACD活用）
- ボラティリティブレイクアウト戦略
- リスク管理（ATRベースのポジションサイズ調整）

### 4. 統合リスク管理
- **ポートフォリオVaR 1-2%**での総合リスク制御
- GARCH予測による動的ヘッジ比率調整
- 流動性・効率性指標による取引コスト最適化

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

- **2025-07-07**: ノートブック構造大幅改善
  - 隣月間スプレッド分析フォルダ追加（3ノートブック）
  - Cash-3Mスプレッド分析フォルダ追加（11ノートブック）
  - 3Mアウトライト分析フォルダ追加（11ノートブック）
  - グラフタイトル文字化け修正（全ノートブック英語化）
  - 重複ノートブック削除・整理完了
- **2025-07-05**: プロジェクト初期作成
  - データ収集・分析パイプライン構築完了
  - 基本分析ノートブック作成