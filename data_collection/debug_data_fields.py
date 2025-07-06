#!/usr/bin/env python3
"""
データフィールドの確認用スクリプト
"""

import eikon as ek
import pandas as pd
from datetime import datetime, timedelta

# EIKON API初期化
ek.set_app_key('1475940198b04fdab9265b7892546cc2ead9eda6')

# テストデータの取得
ric = 'CMCU3'
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"Testing RIC: {ric}")
print(f"Date range: {start_date} to {end_date}")

# デフォルトフィールドで取得
print("\n=== Default fields ===")
try:
    data = ek.get_timeseries(ric, start_date=start_date, end_date=end_date)
    print(f"Columns: {list(data.columns)}")
    print(f"Shape: {data.shape}")
    print(data.head())
except Exception as e:
    print(f"Error: {e}")

# 特定フィールドで取得
print("\n=== Specific fields ===")
fields = ['CLOSE', 'HIGH', 'LOW', 'OPEN', 'VOLUME']
try:
    data = ek.get_timeseries(ric, fields=fields, start_date=start_date, end_date=end_date)
    print(f"Columns: {list(data.columns)}")
    print(f"Shape: {data.shape}")
    print(data.head())
except Exception as e:
    print(f"Error: {e}")

# スプレッドのテスト
print("\n=== Spread data ===")
spread_ric = 'CMCU0-3'
try:
    data = ek.get_timeseries(spread_ric, start_date=start_date, end_date=end_date)
    print(f"Columns: {list(data.columns)}")
    print(f"Shape: {data.shape}")
    print(data.head())
except Exception as e:
    print(f"Error: {e}")