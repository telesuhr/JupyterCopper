# LME Copper Analysis - Complete Trading Analysis Suite

## 🏆 プロジェクト概要

**LME Copper Analysis**は、LME（ロンドン金属取引所）銅の包括的な市場分析プラットフォームです。**Cash/3Mスプレッド分析**と**3Mアウトライト価格分析**の両方をカバーし、データ取得から高度な機械学習モデリング、実践的なトレーディング戦略まで、銅市場分析の全工程を提供します。

## 🚀 主要機能

### 📈 データ取得・処理
- **Refinitiv EIKON API**: リアルタイム・ヒストリカルデータ取得
- **PostgreSQL統合**: 大容量データの効率的管理
- **自動データ更新**: スケジューラーによる定期更新
- **データ品質管理**: 欠損値処理・異常値検出

### 📊 包括的分析
- **基本統計分析**: 価格動向・分布・相関分析
- **時系列分析**: ARIMA・GARCH・定常性検定
- **機械学習**: Random Forest・XGBoost・LSTM・Prophet
- **リスク分析**: VaR・ドローダウン・ボラティリティ予測

### 💼 実践的応用
- **トレーディングシグナル**: 自動売買シグナル生成
- **リスク管理**: ポジションサイジング・ストップロス設定
- **戦略バックテスト**: 過去データでの戦略検証
- **パフォーマンス評価**: シャープレシオ・最大ドローダウン

## 📁 プロジェクト構造

```
LME-Copper-Analysis/
├── 📊 data_collection/           # データ取得システム
│   ├── eikon_collector.py        # Refinitiv EIKON データ収集
│   ├── database_setup.py         # PostgreSQL セットアップ
│   ├── automated_scheduler.py    # 自動データ更新
│   └── data_quality_monitor.py   # データ品質監視
├── 📈 analysis_notebooks/        # 分析ノートブック
│   ├── cash_3m_spread/          # Cash/3Mスプレッド分析 (12ノートブック)
│   │   ├── 1_spread_curve_dynamics.ipynb
│   │   ├── 2_spread_volatility_liquidity.ipynb
│   │   ├── 3_spread_correlation_cointegration.ipynb
│   │   ├── 4_spread_volatility_risk.ipynb
│   │   ├── 5_spread_term_structure_volatility.ipynb
│   │   ├── 6_cash_3m_spread_visualization.ipynb
│   │   ├── 7_cash_3m_spread_timeseries_analysis.ipynb
│   │   ├── 8_cash_3m_spread_modeling_comprehensive.ipynb
│   │   ├── 9_cash_3m_spread_interpretation_guide.ipynb
│   │   ├── 10_spread_results_interpretation.ipynb
│   │   ├── 11_spread_next_steps_roadmap.ipynb
│   │   └── README.md
│   └── outright_3m/             # 3Mアウトライト価格分析 (5ノートブック)
│       ├── 6_lme_3m_outright_visualization.ipynb
│       ├── 7_lme_3m_timeseries_analysis.ipynb
│       ├── 8_timeseries_interpretation_guide.ipynb
│       ├── 9_timeseries_modeling_comprehensive.ipynb
│       ├── 10_modeling_results_interpretation.ipynb
│       └── README.md
├── 🔧 src/                      # ソースコード
│   ├── data_utils.py            # データ処理ユーティリティ
│   ├── models.py                # 予測モデル
│   ├── trading_signals.py       # シグナル生成
│   ├── risk_management.py       # リスク管理
│   └── backtesting.py           # バックテスト
├── 💾 data/                     # データフォルダ
│   ├── raw/                     # 生データ
│   ├── processed/               # 処理済みデータ
│   └── sample/                  # サンプルデータ
├── ⚙️ config/                   # 設定ファイル
│   ├── database_config.json     # DB設定
│   ├── eikon_config.json        # API設定
│   └── model_params.json        # モデルパラメータ
├── 🖼️ images/                   # 生成グラフ・画像
├── 📚 docs/                     # ドキュメント
├── 🧪 tests/                    # テストコード
├── requirements.txt             # 依存関係
├── .env.example                 # 環境変数例
├── .gitignore                   # Git除外設定
└── README.md                    # このファイル
```

## 🛠️ セットアップ

### 1. リポジトリクローン
```bash
git clone https://github.com/telesuhr/LME-Copper-Analysis.git
cd LME-Copper-Analysis
```

### 2. 仮想環境作成
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集してAPI KEY等を設定
```

### 5. データベースセットアップ
```bash
python data_collection/database_setup.py
```

## 📊 使用方法

### 🔄 データ取得
```bash
# ヒストリカルデータ取得
python data_collection/eikon_collector.py --start-date 2020-01-01 --end-date 2024-12-31

# 自動データ更新開始
python data_collection/automated_scheduler.py
```

### 📈 分析実行
```bash
# Jupyter Notebook起動
jupyter notebook analysis_notebooks/

# Cash/3Mスプレッド分析 (cash_3m_spread/)
# 1: スプレッドカーブダイナミクス
# 2: ボラティリティ・流動性分析  
# 3: 相関・共和分分析
# 4: ボラティリティリスク
# 5: ターム構造分析
# 6: 包括的可視化
# 7: 時系列分析 (ARIMA/GARCH)
# 8: 機械学習モデリング
# 9: 実践的解釈ガイド
# 10-11: 結果解釈・ロードマップ

# 3Mアウトライト分析 (outright_3m/)
# 6: LME 3M価格可視化
# 7: 時系列分析
# 8: 解釈ガイド  
# 9: 包括的モデリング
# 10: 結果解釈
```

### 💼 トレーディングシステム
```bash
# リアルタイムシグナル生成
python src/trading_signals.py --live

# バックテスト実行
python src/backtesting.py --strategy mean_reversion --start-date 2023-01-01
```

## 🎯 包括的分析アプローチ

### 📊 Cash/3Mスプレッド分析
**焦点**: 市場構造・需給バランス・裁定機会
- **定義**: Cash価格 - 3M先物価格
- **バックワーデーション（正値）**: 現物 > 先物（需給タイト）
- **コンタンゴ（負値）**: 現物 < 先物（供給過多）
- **活用**: スプレッド取引・市場構造分析・リスク管理

### 📈 3Mアウトライト価格分析
**焦点**: 絶対価格レベル・トレンド予測・方向性戦略
- **対象**: LME銅3ヶ月先物（CMCU3）
- **分析**: 価格トレンド・ボラティリティ・技術指標
- **予測**: 機械学習・時系列モデルによる価格予測
- **活用**: 方向性取引・ヘッジ戦略・ポートフォリオ管理

### 🔄 両分析の相乗効果
- **統合戦略**: スプレッド + アウトライトのコンビネーション
- **リスク分散**: 異なるリスクファクターへの対応
- **機会最大化**: 市場構造と価格動向の両面活用

## 🤖 機械学習モデル

### 実装モデル
- **Random Forest**: 非線形関係・特徴量重要度
- **XGBoost**: 勾配ブースティング・高精度予測
- **LSTM**: 深層学習・長期依存関係
- **Prophet**: 季節性・トレンド自動検出
- **ARIMA-GARCH**: 時系列・ボラティリティ

### 特徴量エンジニアリング
- **価格特徴量**: ラグ・移動平均・技術指標
- **ボラティリティ**: 実現ボラティリティ・GARCH
- **時間特徴量**: 曜日・月・季節サイクル
- **市場構造**: バックワーデーション・レジーム

## 📊 サンプル結果

### 価格分析
![Spread Visualization](images/cash_3m_spread_analysis.png)

### 予測モデル
![ML Performance](images/ml_model_comparison.png)

### リスク分析
![Risk Analysis](images/risk_metrics_dashboard.png)

## 💡 実践的活用

### 1. 市場分析
- 銅市場の構造変化検出
- 需給バランス判定
- 季節性パターン活用

### 2. トレーディング戦略
- 平均回帰戦略
- トレンドフォロー戦略
- ブレイクアウト戦略
- ボラティリティ戦略

### 3. リスク管理
- 動的ポジションサイジング
- ボラティリティベースストップロス
- ポートフォリオVaR管理

## 🔧 技術スタック

### データ・分析
- **Python**: 3.8+
- **pandas**: データ処理
- **numpy**: 数値計算
- **scipy**: 統計分析
- **statsmodels**: 時系列分析

### 機械学習
- **scikit-learn**: 基本ML
- **xgboost**: 勾配ブースティング
- **tensorflow**: 深層学習
- **prophet**: 時系列予測

### データベース・API
- **PostgreSQL**: データ管理
- **Refinitiv EIKON**: データ取得
- **SQLAlchemy**: ORM
- **schedule**: タスクスケジューラ

### 可視化
- **matplotlib**: 基本グラフ
- **seaborn**: 統計グラフ
- **plotly**: インタラクティブ

## 📈 パフォーマンス例

### 予測精度（テストデータ）
- **Random Forest**: MAE 12.3, R² 0.68
- **XGBoost**: MAE 11.8, R² 0.72
- **LSTM**: MAE 13.1, R² 0.64
- **Ensemble**: MAE 11.2, R² 0.75

### トレーディング成績（バックテスト）
- **平均回帰戦略**: 年率リターン 15.2%, シャープレシオ 1.34
- **トレンドフォロー**: 年率リターン 18.7%, 最大DD 12.1%

## ⚠️ 重要な注意事項

### データ使用
- Refinitiv EIKONライセンスが必要
- 商用利用は適切なライセンス確認要
- データ配布・再販は禁止

### 投資判断
- 教育・研究目的のプロジェクト
- 実際の投資は自己責任
- 過去のパフォーマンスは将来を保証しない
- 取引コスト・流動性リスクを考慮要

### 技術的制約
- バックテストは理想的条件を仮定
- リアルタイム実行時の遅延あり
- モデルの過学習リスク

## 🤝 コントリビューション

### 歓迎する貢献
- 新しい分析手法・モデルの追加
- データ品質向上
- ドキュメント改善
- バグ修正・パフォーマンス改善

### 貢献手順
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📜 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

**注意**: Refinitiv データの使用は別途ライセンスが必要です。

## 📞 サポート・お問い合わせ

- **GitHub Issues**: [報告・質問](https://github.com/telesuhr/LME-Copper-Analysis/issues)
- **Discussions**: [技術的な議論](https://github.com/telesuhr/LME-Copper-Analysis/discussions)
- **Documentation**: [詳細ドキュメント](docs/)

## 🏅 クレジット

### データ提供
- **Refinitiv EIKON**: 市場データ提供
- **LME**: ロンドン金属取引所データ

### 技術基盤
- Python エコシステム
- オープンソースライブラリ開発者
- 金融分析コミュニティ

---

**🔥 Built for professional copper market analysis with ❤️**

*"Turning market data into trading intelligence"*