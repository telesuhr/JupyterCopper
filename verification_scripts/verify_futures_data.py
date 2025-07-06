#!/usr/bin/env python3
"""
LME銅36限月先物データの検証・可視化スクリプト
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from datetime import datetime
import numpy as np
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

def fetch_and_verify_data():
    """データベースからデータを取得して検証"""
    try:
        conn = psycopg2.connect(**db_config)
        
        query = """
        SELECT 
            trade_date,
            contract_month,
            ric,
            close_price,
            high_price,
            low_price,
            open_price,
            volume
        FROM lme_copper_futures
        WHERE close_price IS NOT NULL
        ORDER BY trade_date, contract_month
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # データ型変換
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        numeric_cols = ['close_price', 'high_price', 'low_price', 'open_price', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        
        return df
    
    except Exception as e:
        print(f"Database error: {e}")
        return None

def create_verification_charts(df):
    """検証用チャートを作成"""
    plt.style.use('default')
    
    # 図1: データ完全性チェック
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 15))
    
    # 1. 限月別レコード数
    records_by_month = df.groupby('contract_month').size()
    ax1.bar(records_by_month.index, records_by_month.values, 
            color='skyblue', edgecolor='navy', alpha=0.7)
    ax1.set_title('Records Count by Contract Month', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Contract Month')
    ax1.set_ylabel('Number of Records')
    ax1.grid(True, alpha=0.3)
    
    # データ完全性の確認
    expected_records = df['trade_date'].nunique()
    for i, (month, count) in enumerate(records_by_month.items()):
        if i < 10:  # 最初の10限月のみ表示
            completion_rate = (count / expected_records) * 100
            ax1.text(month, count + 10, f'{completion_rate:.1f}%', 
                    ha='center', va='bottom', fontsize=8)
    
    # 2. 年別データ分布
    df['year'] = df['trade_date'].dt.year
    yearly_data = df.groupby('year').size()
    ax2.bar(yearly_data.index, yearly_data.values, 
            color='lightgreen', edgecolor='darkgreen', alpha=0.7)
    ax2.set_title('Records Count by Year', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Number of Records')
    ax2.grid(True, alpha=0.3)
    
    # 3. 価格データの連続性チェック（近月3限月）
    for month in [1, 2, 3]:
        month_data = df[df['contract_month'] == month].sort_values('trade_date')
        ax3.plot(month_data['trade_date'], month_data['close_price'], 
                 label=f'Month {month}', linewidth=1.5, alpha=0.8)
    
    ax3.set_title('Price Continuity Check - Front 3 Contracts', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Price (USD/ton)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 出来高データの妥当性チェック
    volume_by_month = df.groupby('contract_month')['volume'].sum()
    ax4.semilogy(volume_by_month.index, volume_by_month.values, 
                 marker='o', linewidth=2, markersize=6, color='red')
    ax4.set_title('Total Volume by Contract Month (Log Scale)', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Contract Month')
    ax4.set_ylabel('Total Volume (Log Scale)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('futures_data_verification.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 図2: 先物カーブの妥当性チェック
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # 最新の先物カーブ
    latest_date = df['trade_date'].max()
    latest_curve = df[df['trade_date'] == latest_date].sort_values('contract_month')
    
    ax1.plot(latest_curve['contract_month'], latest_curve['close_price'], 
             marker='o', linewidth=2, markersize=6, color='blue')
    ax1.set_title(f'Latest Futures Curve ({latest_date.strftime("%Y-%m-%d")})', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Contract Month')
    ax1.set_ylabel('Price (USD/ton)')
    ax1.grid(True, alpha=0.3)
    
    # 期間構造の時系列変化
    monthly_data = df.groupby([df['trade_date'].dt.to_period('M'), 'contract_month'])['close_price'].last().unstack()
    
    # 1限月と12限月の価格差
    if 1 in monthly_data.columns and 12 in monthly_data.columns:
        spread = monthly_data[12] - monthly_data[1]
        spread = spread.dropna()
        
        ax2.plot(spread.index.to_timestamp(), spread.values, 
                 linewidth=2, color='purple', alpha=0.8)
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax2.fill_between(spread.index.to_timestamp(), spread.values, 0, 
                         where=(spread.values > 0), alpha=0.3, color='green', label='Contango')
        ax2.fill_between(spread.index.to_timestamp(), spread.values, 0, 
                         where=(spread.values < 0), alpha=0.3, color='red', label='Backwardation')
        
        ax2.set_title('Term Structure: 12M - 1M Spread', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Price Spread (USD/ton)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('futures_curve_verification.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_data_summary(df):
    """データサマリーを出力"""
    print("=" * 80)
    print("              LME COPPER FUTURES DATA VERIFICATION")
    print("=" * 80)
    
    print(f"\n【DATA COMPLETENESS】")
    print(f"Total Records: {len(df):,}")
    print(f"Date Range: {df['trade_date'].min().strftime('%Y-%m-%d')} to {df['trade_date'].max().strftime('%Y-%m-%d')}")
    print(f"Trading Days: {df['trade_date'].nunique():,}")
    print(f"Contract Months: {sorted(df['contract_month'].unique())}")
    
    # データ完全性チェック
    expected_total = df['trade_date'].nunique() * len(df['contract_month'].unique())
    actual_total = len(df)
    completeness = (actual_total / expected_total) * 100
    print(f"Data Completeness: {completeness:.1f}% ({actual_total:,} / {expected_total:,})")
    
    print(f"\n【PRICE DATA VALIDATION】")
    print(f"Price Range: ${df['close_price'].min():.2f} - ${df['close_price'].max():.2f}")
    print(f"Average Price: ${df['close_price'].mean():.2f}")
    
    # 価格の妥当性チェック
    price_outliers = df[(df['close_price'] < 1000) | (df['close_price'] > 20000)]
    print(f"Price Outliers (< $1,000 or > $20,000): {len(price_outliers)}")
    
    # 高値-安値の妥当性
    df['daily_range'] = df['high_price'] - df['low_price']
    df['range_pct'] = (df['daily_range'] / df['close_price']) * 100
    unusual_ranges = df[df['range_pct'] > 10]  # 10%以上の日次レンジ
    print(f"Unusual Daily Ranges (> 10%): {len(unusual_ranges)}")
    
    print(f"\n【VOLUME DATA VALIDATION】")
    print(f"Volume Range: {df['volume'].min():.0f} - {df['volume'].max():.0f}")
    print(f"Zero Volume Records: {len(df[df['volume'] == 0])}")
    print(f"Average Daily Volume: {df.groupby('trade_date')['volume'].sum().mean():.0f}")
    
    print(f"\n【CONTRACT MONTH ANALYSIS】")
    volume_by_month = df.groupby('contract_month')['volume'].sum()
    print(f"Most Active Contracts:")
    for month in volume_by_month.head().index:
        pct = (volume_by_month[month] / volume_by_month.sum()) * 100
        print(f"  Month {month:2d}: {volume_by_month[month]:8.0f} ({pct:5.1f}%)")
    
    print(f"\n【MISSING DATA ANALYSIS】")
    missing_analysis = df.groupby('contract_month').apply(
        lambda x: {
            'total_days': df['trade_date'].nunique(),
            'actual_records': len(x),
            'missing_records': df['trade_date'].nunique() - len(x),
            'completion_rate': len(x) / df['trade_date'].nunique() * 100
        }
    )
    
    print(f"Contract Months with Missing Data:")
    for month, stats in missing_analysis.items():
        if stats['completion_rate'] < 95:
            print(f"  Month {month:2d}: {stats['completion_rate']:5.1f}% complete "
                  f"({stats['missing_records']} missing)")
    
    print(f"\n【TEMPORAL CONSISTENCY】")
    # 日付の連続性チェック
    all_dates = pd.date_range(start=df['trade_date'].min(), 
                             end=df['trade_date'].max(), 
                             freq='D')
    business_days = pd.bdate_range(start=df['trade_date'].min(), 
                                  end=df['trade_date'].max())
    
    actual_dates = set(df['trade_date'].dt.date)
    missing_business_days = set(business_days.date) - actual_dates
    
    print(f"Total Calendar Days: {len(all_dates)}")
    print(f"Business Days: {len(business_days)}")
    print(f"Actual Trading Days: {df['trade_date'].nunique()}")
    print(f"Missing Business Days: {len(missing_business_days)}")
    
    if len(missing_business_days) > 0 and len(missing_business_days) < 20:
        print(f"Missing Dates: {sorted(list(missing_business_days))}")
    
    print(f"\n【RIC VALIDATION】")
    expected_rics = [f'CMCUc{i}' for i in range(1, 37)]
    actual_rics = set(df['ric'].unique())
    missing_rics = set(expected_rics) - actual_rics
    unexpected_rics = actual_rics - set(expected_rics)
    
    print(f"Expected RICs: {len(expected_rics)}")
    print(f"Actual RICs: {len(actual_rics)}")
    if missing_rics:
        print(f"Missing RICs: {sorted(missing_rics)}")
    if unexpected_rics:
        print(f"Unexpected RICs: {sorted(unexpected_rics)}")
    
    print("\n" + "=" * 80)
    if completeness > 95 and len(price_outliers) == 0 and len(missing_rics) == 0:
        print("✅ DATA VERIFICATION PASSED - Data appears complete and accurate")
    else:
        print("⚠️  DATA VERIFICATION ISSUES DETECTED - Please review the analysis above")
    print("=" * 80)

def main():
    """メイン実行関数"""
    print("Starting LME Copper Futures Data Verification...")
    
    # データ取得
    df = fetch_and_verify_data()
    if df is None:
        print("Failed to fetch data from database")
        return
    
    # データサマリー出力
    print_data_summary(df)
    
    # 可視化作成
    create_verification_charts(df)
    
    print("\nVerification completed successfully!")
    print("Charts saved as 'futures_data_verification.png' and 'futures_curve_verification.png'")

if __name__ == "__main__":
    main()