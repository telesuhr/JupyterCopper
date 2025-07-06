#!/usr/bin/env python3
"""
LME銅36限月先物のRIC構造調査とデータ確認
"""

import eikon as ek
import pandas as pd
from datetime import datetime, timedelta

# EIKON API初期化
ek.set_app_key('1475940198b04fdab9265b7892546cc2ead9eda6')

def test_copper_futures_rics():
    """LME銅先物のRIC構造をテスト"""
    
    # LME銅先物のRIC構造をテスト
    print("=== LME Copper Futures RIC Structure Test ===")
    
    # 基本的なRIC構造をテスト
    test_rics = [
        'CMCUc1',   # 1限月
        'CMCUc2',   # 2限月
        'CMCUc3',   # 3限月
        'CMCUc6',   # 6限月
        'CMCUc12',  # 12限月
        'CMCUc24',  # 24限月
        'CMCUc36'   # 36限月
    ]
    
    # 過去30日のデータで各RICをテスト
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Testing period: {start_date} to {end_date}")
    print()
    
    valid_rics = []
    
    for ric in test_rics:
        print(f"Testing RIC: {ric}")
        try:
            # デフォルトフィールドでデータ取得
            data = ek.get_timeseries(ric, start_date=start_date, end_date=end_date)
            
            if data is not None and not data.empty:
                print(f"  ✓ Valid RIC: {len(data)} records")
                print(f"  Columns: {list(data.columns)}")
                print(f"  Latest price: {data.iloc[-1]['CLOSE']}")
                valid_rics.append(ric)
                
                # 最初の数行を表示
                print(f"  Sample data:")
                print(data.head(2).to_string(index=True))
            else:
                print(f"  ✗ No data returned")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print("-" * 50)
    
    print(f"\nValid RICs found: {len(valid_rics)}")
    print(f"Valid RICs: {valid_rics}")
    
    return valid_rics

def test_futures_curve_data():
    """先物カーブデータの取得テスト"""
    print("\n=== Futures Curve Data Test ===")
    
    # 1-36限月のRICを生成
    futures_rics = [f'CMCUc{i}' for i in range(1, 37)]
    
    print(f"Testing {len(futures_rics)} futures contracts...")
    
    # 最新の1日分のデータで各限月をテスト
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    curve_data = {}
    
    for i, ric in enumerate(futures_rics[:10], 1):  # 最初の10限月のみテスト
        print(f"Testing {ric} (Month {i})...")
        try:
            data = ek.get_timeseries(ric, start_date=start_date, end_date=end_date)
            
            if data is not None and not data.empty:
                latest_price = data.iloc[-1]['CLOSE']
                latest_volume = data.iloc[-1]['VOLUME'] if 'VOLUME' in data.columns else 0
                curve_data[i] = {
                    'ric': ric,
                    'price': latest_price,
                    'volume': latest_volume,
                    'records': len(data)
                }
                print(f"  ✓ Price: ${latest_price:.2f}, Volume: {latest_volume}")
            else:
                print(f"  ✗ No data")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    if curve_data:
        print(f"\n=== Futures Curve Summary ===")
        for month, data in curve_data.items():
            print(f"Month {month:2d}: {data['ric']:8s} - ${data['price']:8.2f} (Vol: {data['volume']:6.0f})")
    
    return curve_data

def test_open_interest_data():
    """建玉データの取得テスト"""
    print("\n=== Open Interest Data Test ===")
    
    # 建玉データ用のフィールドをテスト
    test_fields = [
        'OPEN_INT',      # 建玉
        'OPEN_INTEREST', # 建玉（別名）
        'OI',            # 建玉（略語）
        'VOLUME',        # 出来高
        'CLOSE',         # 終値
        'HIGH',          # 高値
        'LOW',           # 安値
        'OPEN'           # 始値
    ]
    
    ric = 'CMCUc3'  # 3限月でテスト
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Testing fields for {ric}...")
    
    # 各フィールドを個別にテスト
    available_fields = []
    
    for field in test_fields:
        try:
            data = ek.get_timeseries(ric, fields=[field], start_date=start_date, end_date=end_date)
            
            if data is not None and not data.empty and not data[field].isna().all():
                latest_value = data.iloc[-1][field]
                available_fields.append(field)
                print(f"  ✓ {field:15s}: {latest_value}")
            else:
                print(f"  ✗ {field:15s}: No data or all NaN")
                
        except Exception as e:
            print(f"  ✗ {field:15s}: Error - {e}")
    
    print(f"\nAvailable fields: {available_fields}")
    
    # すべての利用可能フィールドでデータ取得
    if available_fields:
        try:
            print(f"\nTesting combined fields: {available_fields}")
            combined_data = ek.get_timeseries(ric, fields=available_fields, 
                                            start_date=start_date, end_date=end_date)
            
            if combined_data is not None and not combined_data.empty:
                print(f"Combined data shape: {combined_data.shape}")
                print("Latest values:")
                print(combined_data.iloc[-1].to_string())
                
                return available_fields, combined_data
                
        except Exception as e:
            print(f"Error with combined fields: {e}")
    
    return available_fields, None

def main():
    """メイン実行関数"""
    print("LME Copper Futures RIC Investigation")
    print("=" * 50)
    
    # RIC構造テスト
    valid_rics = test_copper_futures_rics()
    
    # 先物カーブデータテスト
    curve_data = test_futures_curve_data()
    
    # 建玉データテスト
    available_fields, sample_data = test_open_interest_data()
    
    print("\n" + "=" * 50)
    print("INVESTIGATION SUMMARY")
    print("=" * 50)
    print(f"Valid RICs tested: {len(valid_rics)}")
    print(f"Available data fields: {available_fields}")
    
    if curve_data:
        print(f"Futures curve data points: {len(curve_data)}")
    
    if sample_data is not None:
        print(f"Sample data columns: {list(sample_data.columns)}")
        print(f"Sample data period: {sample_data.index[0]} to {sample_data.index[-1]}")

if __name__ == "__main__":
    main()