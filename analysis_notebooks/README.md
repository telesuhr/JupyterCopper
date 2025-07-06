# LME銅先物分析 ノートブック集

## 📁 フォルダ構造

```
analysis_notebooks/
├── README.md                                    # このファイル
├── 1_futures_curve_dynamics.ipynb             # 先物カーブ動態分析
├── 2_volume_liquidity.ipynb                   # 出来高・流動性分析
├── 3_correlation_cointegration.ipynb          # 相関・共和分分析
├── 4_volatility_risk.ipynb                    # ボラティリティ・リスク分析
├── 5_term_structure_volatility.ipynb          # タームストラクチャー・ボラティリティ分析
├── 6_lme_3m_outright_visualization.ipynb      # 3Mアウトライト可視化分析
├── 7_lme_3m_timeseries_analysis.ipynb         # 3Mアウトライト時系列分析
├── 8_timeseries_interpretation_guide.ipynb    # 時系列解釈ガイド
├── 9_timeseries_modeling_comprehensive.ipynb  # 包括的モデリング
├── 10_modeling_results_interpretation.ipynb   # モデリング結果解釈
├── 11_next_steps_roadmap.ipynb                # 今後のロードマップ
├── cash_3m_spread/                            # Cash/3Mスプレッド分析
│   ├── 1_cash_3m_spread_visualization.ipynb      # 可視化分析
│   ├── 2_cash_3m_spread_timeseries_analysis.ipynb # 時系列分析
│   ├── 3_cash_3m_spread_modeling_comprehensive.ipynb # 包括的モデリング
│   └── 4_cash_3m_spread_interpretation_guide.ipynb   # 結果解釈ガイド
└── outright_3m/                               # 3Mアウトライト分析（バックアップ）
    ├── 6_lme_3m_outright_visualization.ipynb     # 可視化分析
    ├── 7_lme_3m_timeseries_analysis.ipynb        # 時系列分析
    ├── 8_timeseries_interpretation_guide.ipynb   # 時系列解釈ガイド
    ├── 9_timeseries_modeling_comprehensive.ipynb # 包括的モデリング
    └── 10_modeling_results_interpretation.ipynb  # モデリング結果解釈
```

## 🎯 分析対象

### 📈 **3Mアウトライト分析** (`outright_3m/`)
LME銅3M先物（CMCU3）の価格分析

- **対象データ**: 3M先物の終値、高値、安値、出来高
- **分析期間**: 2022年7月〜2025年7月（約3年間）
- **価格範囲**: $6,955 - $11,105 per tonne
- **用途**: 価格予測、トレンド分析、投資戦略

### 📊 **Cash/3Mスプレッド分析** (`cash_3m_spread/`)
現物と3M先物の価格差分析

- **対象データ**: Cash価格 - 3M先物価格
- **解釈**: 正値=バックワーデーション、負値=コンタンゴ
- **市場意味**: 需給バランス、在庫状況の指標
- **用途**: スプレッド取引、市場構造分析

## 📋 実行順序

### 🚀 **初心者向け**
1. `outright_3m/6_lme_3m_outright_visualization.ipynb` - 基本的な価格可視化
2. `cash_3m_spread/1_cash_3m_spread_visualization.ipynb` - スプレッド可視化
3. 結果の比較・解釈

### 📚 **学習目的**
1. `outright_3m/7_lme_3m_timeseries_analysis.ipynb` - 時系列分析基礎
2. `outright_3m/8_timeseries_interpretation_guide.ipynb` - 結果解釈
3. `cash_3m_spread/2_cash_3m_spread_timeseries_analysis.ipynb` - スプレッド時系列
4. `cash_3m_spread/4_cash_3m_spread_interpretation_guide.ipynb` - 解釈ガイド

### 🔬 **高度な分析**
1. `outright_3m/9_timeseries_modeling_comprehensive.ipynb` - 包括的モデリング
2. `cash_3m_spread/3_cash_3m_spread_modeling_comprehensive.ipynb` - スプレッドモデリング
3. `outright_3m/10_modeling_results_interpretation.ipynb` - 結果解釈
4. `11_next_steps_roadmap.ipynb` - 今後の展開

## 🔧 技術要件

### 必須ライブラリ
```bash
pip install pandas numpy matplotlib seaborn sqlalchemy psycopg2-binary
pip install scikit-learn xgboost statsmodels arch-py
pip install plotly mplfinance python-dotenv
```

### オプションライブラリ
```bash
pip install tensorflow prophet  # LSTM, Prophet用
pip install streamlit          # ダッシュボード用
```

### データベース
- PostgreSQL 14+
- データベース名: `lme_copper_db`
- 必要テーブル: `lme_copper_prices`, `lme_copper_futures`

## 📊 主要分析手法

### 統計分析
- **記述統計**: 平均、標準偏差、分位点
- **定常性検定**: ADF検定、KPSS検定
- **自己相関分析**: ACF、PACF
- **正規性検定**: Jarque-Bera検定

### 時系列モデル
- **ARIMA**: 自己回帰移動平均モデル
- **GARCH**: 条件付き分散不均一性モデル
- **Prophet**: Facebook時系列予測ライブラリ

### 機械学習
- **Random Forest**: アンサンブル学習
- **XGBoost**: 勾配ブースティング
- **LSTM**: 長短期記憶ネットワーク
- **アンサンブル**: 複数モデル組み合わせ

### テクニカル分析
- **移動平均**: 5日、20日、50日、200日
- **ボリンジャーバンド**: ±2σ
- **RSI**: 14日間
- **MACD**: 12-26-9設定
- **ATR**: 14日間

## 🎯 主要評価指標

### 予測精度
- **MAE**: 平均絶対誤差
- **RMSE**: 二乗平均平方根誤差  
- **MAPE**: 平均絶対パーセント誤差
- **方向性精度**: 上昇/下降の的中率

### リスク指標
- **VaR**: バリューアットリスク
- **最大ドローダウン**: 最高値からの最大下落
- **シャープレシオ**: リスク調整リターン
- **勝率**: 利益取引の割合

## 💡 実用例

### トレーディング戦略
1. **平均回帰戦略**: ±2σからの回帰取引
2. **トレンドフォロー**: 移動平均クロス戦略
3. **スプレッド取引**: 異常値での裁定取引
4. **ボラティリティブレイク**: ATR拡大での順張り

### リスク管理
- **ポジションサイズ**: ATRベース
- **ストップロス**: ATRの1.5-2倍
- **利食い目標**: ATRの2-3倍
- **VaR制約**: ポートフォリオリスク管理

## 🚨 注意事項

### データの制限
- 過去データに基づく分析（将来の保証なし）
- 市場構造変化時は再分析が必要
- バックテストと実取引の乖離

### 実装時の考慮点
- 取引コスト（スプレッド、手数料）
- 流動性リスク
- スリッページ
- 規制要件

## 🔄 更新・保守

### 定期更新項目
- **日次**: データ更新、予測実行
- **週次**: パフォーマンス評価
- **月次**: モデル再訓練
- **四半期**: 戦略見直し

### 改善ポイント
- 特徴量エンジニアリング
- ハイパーパラメータ調整
- アンサンブル手法改良
- リアルタイム対応

---

**免責事項**: このノートブック集は教育・研究目的で作成されています。実際の投資判断は自己責任で行ってください。