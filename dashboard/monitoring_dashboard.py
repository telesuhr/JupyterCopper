#!/usr/bin/env python3
"""
LME銅先物データ監視ダッシュボード
データ収集状況、予測精度、システム健全性を監視するWebダッシュボード
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="LME銅先物監視ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MonitoringDashboard:
    """監視ダッシュボードクラス"""
    
    def __init__(self):
        """初期化"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'lme_copper_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    @st.cache_data(ttl=300)  # 5分間キャッシュ
    def get_data_collection_status(_self) -> pd.DataFrame:
        """データ収集状況の取得"""
        try:
            conn = psycopg2.connect(**_self.db_config)
            
            query = """
            SELECT 
                collection_date,
                start_time,
                end_time,
                duration_seconds,
                success,
                records_collected,
                contracts_processed,
                errors,
                warnings
            FROM data_collection_log
            WHERE collection_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY collection_date DESC;
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"データ収集状況の取得エラー: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_latest_futures_data(_self) -> pd.DataFrame:
        """最新の先物データ取得"""
        try:
            conn = psycopg2.connect(**_self.db_config)
            
            query = """
            SELECT 
                contract_month,
                close_price,
                volume,
                trade_date
            FROM lme_copper_futures
            WHERE trade_date = (
                SELECT MAX(trade_date) 
                FROM lme_copper_futures 
                WHERE close_price IS NOT NULL
            )
            AND close_price IS NOT NULL
            ORDER BY contract_month;
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"先物データの取得エラー: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_prediction_performance(_self) -> pd.DataFrame:
        """予測パフォーマンスの取得"""
        try:
            conn = psycopg2.connect(**_self.db_config)
            
            query = """
            SELECT 
                evaluation_date,
                model_name,
                days_ahead,
                mae,
                rmse,
                mape,
                directional_accuracy,
                total_predictions
            FROM prediction_performance
            WHERE evaluation_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY evaluation_date DESC, model_name, days_ahead;
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"予測パフォーマンスの取得エラー: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_recent_predictions(_self, days_back: int = 7) -> pd.DataFrame:
        """最近の予測結果取得"""
        try:
            conn = psycopg2.connect(**_self.db_config)
            
            query = """
            SELECT 
                prediction_date,
                target_date,
                days_ahead,
                model_name,
                predicted_price,
                actual_price,
                prediction_error
            FROM daily_predictions
            WHERE prediction_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY prediction_date DESC, target_date, model_name;
            """
            
            df = pd.read_sql_query(query, conn, params=(days_back,))
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"予測結果の取得エラー: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_price_history(_self, contract_month: int = 3, days_back: int = 90) -> pd.DataFrame:
        """価格履歴の取得"""
        try:
            conn = psycopg2.connect(**_self.db_config)
            
            query = """
            SELECT 
                trade_date,
                close_price,
                volume,
                high_price,
                low_price
            FROM lme_copper_futures
            WHERE contract_month = %s
                AND trade_date >= CURRENT_DATE - INTERVAL '%s days'
                AND close_price IS NOT NULL
            ORDER BY trade_date;
            """
            
            df = pd.read_sql_query(query, conn, params=(contract_month, days_back))
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"価格履歴の取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def render_system_status(self):
        """システム状況の表示"""
        st.header("🔧 システム状況")
        
        # データ収集状況
        collection_data = self.get_data_collection_status()
        
        if not collection_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            # 最新の収集結果
            latest_collection = collection_data.iloc[0]
            
            with col1:
                success_rate = (collection_data['success'].sum() / len(collection_data)) * 100
                st.metric(
                    "データ収集成功率 (30日)",
                    f"{success_rate:.1f}%",
                    delta=None,
                    delta_color="normal"
                )
            
            with col2:
                avg_records = collection_data['records_collected'].mean()
                st.metric(
                    "平均収集レコード数",
                    f"{avg_records:.0f}",
                    delta=None
                )
            
            with col3:
                avg_duration = collection_data['duration_seconds'].mean()
                st.metric(
                    "平均処理時間",
                    f"{avg_duration:.1f}秒",
                    delta=None
                )
            
            with col4:
                latest_date = latest_collection['collection_date']
                days_since = (datetime.now().date() - latest_date).days
                st.metric(
                    "最新データ収集",
                    f"{days_since}日前",
                    delta=f"-{days_since}" if days_since > 1 else "最新",
                    delta_color="inverse" if days_since > 1 else "normal"
                )
            
            # 収集履歴チャート
            st.subheader("データ収集履歴")
            
            fig = go.Figure()
            
            # 成功/失敗の可視化
            success_df = collection_data[collection_data['success'] == True]
            failure_df = collection_data[collection_data['success'] == False]
            
            if not success_df.empty:
                fig.add_trace(go.Scatter(
                    x=success_df['collection_date'],
                    y=success_df['records_collected'],
                    mode='markers+lines',
                    name='成功',
                    marker=dict(color='green', size=8),
                    line=dict(color='green')
                ))
            
            if not failure_df.empty:
                fig.add_trace(go.Scatter(
                    x=failure_df['collection_date'],
                    y=[0] * len(failure_df),
                    mode='markers',
                    name='失敗',
                    marker=dict(color='red', size=10, symbol='x')
                ))
            
            fig.update_layout(
                title="日次データ収集結果",
                xaxis_title="日付",
                yaxis_title="収集レコード数",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_futures_curve(self):
        """先物カーブの表示"""
        st.header("📈 先物カーブ")
        
        futures_data = self.get_latest_futures_data()
        
        if not futures_data.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 先物カーブチャート
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=futures_data['contract_month'],
                    y=futures_data['close_price'],
                    mode='markers+lines',
                    name='終値',
                    marker=dict(size=8),
                    line=dict(width=3)
                ))
                
                fig.update_layout(
                    title=f"LME銅先物カーブ ({futures_data['trade_date'].iloc[0]})",
                    xaxis_title="限月",
                    yaxis_title="価格 (USD/t)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 先物カーブ統計
                st.subheader("カーブ統計")
                
                # コンタンゴ/バックワーデーション
                m1_price = futures_data[futures_data['contract_month'] == 1]['close_price'].iloc[0]
                m3_price = futures_data[futures_data['contract_month'] == 3]['close_price'].iloc[0]
                m12_price = futures_data[futures_data['contract_month'] == 12]['close_price'].iloc[0]
                
                spread_1m_3m = m1_price - m3_price
                spread_3m_12m = m3_price - m12_price
                
                st.metric("1M-3Mスプレッド", f"{spread_1m_3m:.2f}")
                st.metric("3M-12Mスプレッド", f"{spread_3m_12m:.2f}")
                
                if spread_1m_3m > 0:
                    st.success("🔴 バックワーデーション")
                else:
                    st.info("🔵 コンタンゴ")
                
                # ボラティリティ代理指標
                price_range = futures_data['close_price'].max() - futures_data['close_price'].min()
                avg_price = futures_data['close_price'].mean()
                curve_volatility = (price_range / avg_price) * 100
                
                st.metric("カーブボラティリティ", f"{curve_volatility:.2f}%")
    
    def render_prediction_performance(self):
        """予測パフォーマンスの表示"""
        st.header("🎯 予測パフォーマンス")
        
        performance_data = self.get_prediction_performance()
        predictions_data = self.get_recent_predictions()
        
        if not performance_data.empty:
            # 最新のパフォーマンス指標
            latest_performance = performance_data[
                performance_data['evaluation_date'] == performance_data['evaluation_date'].max()
            ]
            
            if not latest_performance.empty:
                st.subheader("モデル別精度 (最新)")
                
                # モデル別精度表示
                models = latest_performance['model_name'].unique()
                cols = st.columns(len(models))
                
                for i, model in enumerate(models):
                    model_data = latest_performance[latest_performance['model_name'] == model]
                    
                    with cols[i]:
                        st.write(f"**{model.upper()}**")
                        
                        if not model_data.empty:
                            avg_mae = model_data['mae'].mean()
                            avg_mape = model_data['mape'].mean()
                            avg_directional = model_data['directional_accuracy'].mean() * 100
                            
                            st.metric("MAE", f"{avg_mae:.2f}")
                            st.metric("MAPE", f"{avg_mape:.1f}%")
                            st.metric("方向性精度", f"{avg_directional:.1f}%")
            
            # パフォーマンス推移チャート
            st.subheader("予測精度推移")
            
            # 日数別のパフォーマンス
            day_1_data = performance_data[performance_data['days_ahead'] == 1]
            
            if not day_1_data.empty:
                fig = go.Figure()
                
                for model in day_1_data['model_name'].unique():
                    model_data = day_1_data[day_1_data['model_name'] == model]
                    
                    fig.add_trace(go.Scatter(
                        x=model_data['evaluation_date'],
                        y=model_data['mape'],
                        mode='lines+markers',
                        name=f'{model} MAPE',
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title="1日先予測のMAPE推移",
                    xaxis_title="日付",
                    yaxis_title="MAPE (%)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 最近の予測vs実績
        if not predictions_data.empty:
            st.subheader("予測 vs 実績")
            
            # 実績がある予測のみフィルタ
            completed_predictions = predictions_data[predictions_data['actual_price'].notna()]
            
            if not completed_predictions.empty:
                fig = go.Figure()
                
                # 散布図: 予測 vs 実績
                fig.add_trace(go.Scatter(
                    x=completed_predictions['predicted_price'],
                    y=completed_predictions['actual_price'],
                    mode='markers',
                    text=completed_predictions['model_name'],
                    name='予測vs実績',
                    marker=dict(
                        size=8,
                        color=completed_predictions['prediction_error'],
                        colorscale='RdYlGn_r',
                        showscale=True,
                        colorbar=dict(title="予測誤差")
                    )
                ))
                
                # 理想線 (y=x)
                min_price = min(completed_predictions['predicted_price'].min(), 
                              completed_predictions['actual_price'].min())
                max_price = max(completed_predictions['predicted_price'].max(), 
                              completed_predictions['actual_price'].max())
                
                fig.add_trace(go.Scatter(
                    x=[min_price, max_price],
                    y=[min_price, max_price],
                    mode='lines',
                    name='理想線',
                    line=dict(dash='dash', color='gray')
                ))
                
                fig.update_layout(
                    title="予測精度散布図",
                    xaxis_title="予測価格",
                    yaxis_title="実際価格",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def render_price_analysis(self):
        """価格分析の表示"""
        st.header("💰 価格分析")
        
        # サイドバーで契約月選択
        contract_month = st.sidebar.selectbox(
            "分析対象契約月",
            options=[1, 2, 3, 6, 12, 24],
            index=2,  # デフォルトは3M
            help="分析する先物契約の月数を選択"
        )
        
        price_data = self.get_price_history(contract_month=contract_month)
        
        if not price_data.empty:
            price_data['trade_date'] = pd.to_datetime(price_data['trade_date'])
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 価格チャート
                fig = make_subplots(
                    rows=2, cols=1,
                    row_heights=[0.7, 0.3],
                    vertical_spacing=0.1,
                    subplot_titles=['価格推移', '出来高']
                )
                
                # ローソク足チャート
                fig.add_trace(
                    go.Candlestick(
                        x=price_data['trade_date'],
                        open=price_data['close_price'],  # OHLCデータが不完全な場合の代替
                        high=price_data['high_price'],
                        low=price_data['low_price'],
                        close=price_data['close_price'],
                        name='価格'
                    ),
                    row=1, col=1
                )
                
                # 出来高
                fig.add_trace(
                    go.Bar(
                        x=price_data['trade_date'],
                        y=price_data['volume'],
                        name='出来高',
                        marker_color='lightblue'
                    ),
                    row=2, col=1
                )
                
                fig.update_layout(
                    title=f"LME銅 {contract_month}M 価格・出来高推移",
                    height=600,
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 価格統計
                st.subheader(f"{contract_month}M統計")
                
                current_price = price_data['close_price'].iloc[-1]
                price_change = price_data['close_price'].iloc[-1] - price_data['close_price'].iloc[-2]
                price_change_pct = (price_change / price_data['close_price'].iloc[-2]) * 100
                
                st.metric(
                    "現在価格",
                    f"${current_price:.2f}",
                    delta=f"{price_change:+.2f} ({price_change_pct:+.1f}%)"
                )
                
                # 統計情報
                st.write("**90日統計:**")
                st.write(f"最高値: ${price_data['close_price'].max():.2f}")
                st.write(f"最安値: ${price_data['close_price'].min():.2f}")
                st.write(f"平均値: ${price_data['close_price'].mean():.2f}")
                st.write(f"標準偏差: ${price_data['close_price'].std():.2f}")
                
                # ボラティリティ
                returns = price_data['close_price'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100  # 年率ボラティリティ
                
                st.metric("年率ボラティリティ", f"{volatility:.1f}%")
    
    def render_alerts(self):
        """アラート表示"""
        st.header("⚠️ アラート")
        
        alerts = []
        
        # データ収集アラート
        collection_data = self.get_data_collection_status()
        if not collection_data.empty:
            latest_collection = collection_data.iloc[0]
            days_since = (datetime.now().date() - latest_collection['collection_date']).days
            
            if days_since > 2:
                alerts.append({
                    'level': 'error',
                    'message': f"データ収集が{days_since}日間停止しています",
                    'timestamp': latest_collection['collection_date']
                })
            
            if not latest_collection['success']:
                alerts.append({
                    'level': 'warning',
                    'message': "最新のデータ収集が失敗しています",
                    'timestamp': latest_collection['collection_date']
                })
        
        # 予測精度アラート
        performance_data = self.get_prediction_performance()
        if not performance_data.empty:
            latest_performance = performance_data[
                performance_data['evaluation_date'] == performance_data['evaluation_date'].max()
            ]
            
            poor_models = latest_performance[latest_performance['mape'] > 5.0]  # MAPE > 5%
            
            for _, model in poor_models.iterrows():
                alerts.append({
                    'level': 'warning',
                    'message': f"{model['model_name']}モデルの精度が低下しています (MAPE: {model['mape']:.1f}%)",
                    'timestamp': model['evaluation_date']
                })
        
        # アラート表示
        if alerts:
            for alert in alerts:
                if alert['level'] == 'error':
                    st.error(f"🚨 {alert['message']} ({alert['timestamp']})")
                elif alert['level'] == 'warning':
                    st.warning(f"⚠️ {alert['message']} ({alert['timestamp']})")
        else:
            st.success("✅ 現在アラートはありません")
    
    def run_dashboard(self):
        """ダッシュボード実行"""
        # タイトル
        st.title("📊 LME銅先物監視ダッシュボード")
        st.write("データ収集、予測精度、システム健全性をリアルタイムで監視")
        
        # サイドバー設定
        st.sidebar.title("⚙️ 設定")
        
        # 自動更新設定
        auto_refresh = st.sidebar.checkbox("自動更新 (5分)", value=True)
        if auto_refresh:
            st.sidebar.write("⏱️ 次回更新まで約5分")
        
        # 表示セクション選択
        sections = st.sidebar.multiselect(
            "表示セクション",
            ["システム状況", "先物カーブ", "予測パフォーマンス", "価格分析", "アラート"],
            default=["システム状況", "先物カーブ", "予測パフォーマンス", "アラート"]
        )
        
        # アラート（常に上部に表示）
        if "アラート" in sections:
            self.render_alerts()
            st.divider()
        
        # 各セクション表示
        if "システム状況" in sections:
            self.render_system_status()
            st.divider()
        
        if "先物カーブ" in sections:
            self.render_futures_curve()
            st.divider()
        
        if "予測パフォーマンス" in sections:
            self.render_prediction_performance()
            st.divider()
        
        if "価格分析" in sections:
            self.render_price_analysis()
            st.divider()
        
        # フッター
        st.sidebar.markdown("---")
        st.sidebar.write(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """メイン実行関数"""
    dashboard = MonitoringDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()