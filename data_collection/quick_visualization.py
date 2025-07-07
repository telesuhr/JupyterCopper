#!/usr/bin/env python3
"""
LME銅データの簡易可視化スクリプト
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# データベース接続設定
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'lme_copper_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

def fetch_data():
    """データベースからデータを取得"""
    try:
        conn = psycopg2.connect(**db_config)
        
        query = """
        SELECT 
            trade_date,
            price_type,
            last_price,
            high_price,
            low_price,
            volume
        FROM lme_copper_prices
        WHERE last_price IS NOT NULL
        ORDER BY trade_date, price_type
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df
    
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

def create_visualizations(df):
    """Create visualizations"""
    # Style settings
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Set font to avoid Japanese character issues
    plt.rcParams['font.family'] = 'DejaVu Sans'
    
    # データを分割
    df_3m = df[df['price_type'] == '3M_OUTRIGHT'].copy()
    df_spread = df[df['price_type'] == 'CASH_3M_SPREAD'].copy()
    
    # 図1: 価格推移の時系列チャート
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # 3Mアウトライト価格
    ax1.plot(df_3m['trade_date'], df_3m['last_price'], 
             label='LME Copper 3M Outright', color='orange', linewidth=2)
    ax1.fill_between(df_3m['trade_date'], df_3m['low_price'], df_3m['high_price'], 
                     alpha=0.3, color='orange', label='High-Low Range')
    ax1.set_title('LME Copper 3M Outright Price (Past 3 Years)', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price (USD/ton)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Cash/3Mスプレッド
    ax2.plot(df_spread['trade_date'], df_spread['last_price'], 
             label='Cash/3M Spread', color='blue', linewidth=2)
    ax2.fill_between(df_spread['trade_date'], df_spread['low_price'], df_spread['high_price'], 
                     alpha=0.3, color='blue', label='High-Low Range')
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Zero Line')
    ax2.set_title('LME Copper Cash/3M Spread (Past 3 Years)', fontsize=16, fontweight='bold')
    ax2.set_ylabel('Spread (USD/ton)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lme_copper_price_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 図2: 価格分布
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 3Mアウトライト価格分布
    ax1.hist(df_3m['last_price'], bins=50, alpha=0.7, color='orange', edgecolor='black')
    ax1.axvline(df_3m['last_price'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Mean: ${df_3m["last_price"].mean():.0f}')
    ax1.set_title('3M Outright Price Distribution', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Price (USD/ton)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # スプレッド分布
    ax2.hist(df_spread['last_price'], bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax2.axvline(df_spread['last_price'].mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: ${df_spread["last_price"].mean():.0f}')
    ax2.axvline(0, color='green', linestyle='-', linewidth=2, label='Zero Line')
    ax2.set_title('Cash/3M Spread Distribution', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Spread (USD/ton)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lme_copper_distribution_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 統計サマリーの出力
    print("=" * 60)
    print("           LME COPPER DATA ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"\nAnalysis Period:")
    print(f"Start Date: {df['trade_date'].min().strftime('%Y-%m-%d')}")
    print(f"End Date: {df['trade_date'].max().strftime('%Y-%m-%d')}")
    print(f"Total Days: {(df['trade_date'].max() - df['trade_date'].min()).days}")
    
    print(f"\n3M OUTRIGHT SUMMARY:")
    print(f"Current Price: ${df_3m.iloc[-1]['last_price']:.2f}/ton")
    print(f"3-Year Average: ${df_3m['last_price'].mean():.2f}/ton")
    print(f"Maximum Price: ${df_3m['last_price'].max():.2f}/ton")
    print(f"Minimum Price: ${df_3m['last_price'].min():.2f}/ton")
    print(f"Standard Deviation: ${df_3m['last_price'].std():.2f}/ton")
    print(f"Average Volume: {df_3m['volume'].mean():.0f}")
    
    print(f"\nCASH/3M SPREAD SUMMARY:")
    print(f"Current Spread: ${df_spread.iloc[-1]['last_price']:.2f}/ton")
    print(f"3-Year Average: ${df_spread['last_price'].mean():.2f}/ton")
    print(f"Maximum Spread: ${df_spread['last_price'].max():.2f}/ton")
    print(f"Minimum Spread: ${df_spread['last_price'].min():.2f}/ton")
    print(f"Standard Deviation: ${df_spread['last_price'].std():.2f}/ton")
    print(f"Average Volume: {df_spread['volume'].mean():.0f}")
    
    # コンタンゴ/バックワーデーション分析
    contango_days = len(df_spread[df_spread['last_price'] > 0])
    backwardation_days = len(df_spread[df_spread['last_price'] < 0])
    total_days = len(df_spread)
    
    print(f"\nMARKET STRUCTURE ANALYSIS:")
    print(f"Contango Days: {contango_days} ({contango_days/total_days*100:.1f}%)")
    print(f"Backwardation Days: {backwardation_days} ({backwardation_days/total_days*100:.1f}%)")
    
    print("=" * 60)

def main():
    """メイン実行関数"""
    print("LME Copper Data Visualization Starting...")
    
    # データ取得
    df = fetch_data()
    if df is None:
        print("Failed to fetch data from database")
        return
    
    print(f"Successfully loaded {len(df)} records")
    
    # 可視化作成
    create_visualizations(df)
    
    print("Visualization completed successfully!")
    print("Charts saved as 'lme_copper_price_analysis.png' and 'lme_copper_distribution_analysis.png'")

if __name__ == "__main__":
    main()