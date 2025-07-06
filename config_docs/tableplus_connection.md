# TablePlus Connection Settings for LME Copper Database

## Connection Parameters

TablePlusでLME銅データベースに接続するための設定情報：

### Basic Settings
- **Connection Name**: `LME Copper Database`
- **Host**: `localhost`
- **Port**: `5432`
- **User**: `postgres`
- **Password**: `password`
- **Database**: `lme_copper_db`

### Connection String (Optional)
```
postgresql://postgres:password@localhost:5432/lme_copper_db
```

## Setup Instructions

1. **TablePlusを起動**
2. **新しい接続を作成**:
   - 左上の「+」ボタンをクリック
   - 「PostgreSQL」を選択
3. **接続情報を入力**:
   - Name: `LME Copper Database`
   - Host: `localhost`
   - Port: `5432`
   - User: `postgres`
   - Password: `password`
   - Database: `lme_copper_db`
4. **接続をテスト**: 「Test」ボタンをクリック
5. **接続を保存**: 「Save」ボタンをクリック

## Database Schema

### Table 1: `lme_copper_prices` (Original Spot/Spread Data)

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PRIMARY KEY | レコードID |
| `trade_date` | DATE | 取引日 |
| `price_type` | VARCHAR(20) | 価格タイプ (3M_OUTRIGHT, CASH_3M_SPREAD) |
| `ric` | VARCHAR(50) | Reuters Instrument Code |
| `last_price` | DECIMAL(10,4) | 最終価格 |
| `high_price` | DECIMAL(10,4) | 高値 |
| `low_price` | DECIMAL(10,4) | 安値 |
| `open_price` | DECIMAL(10,4) | 始値 |
| `volume` | BIGINT | 出来高 |
| `currency` | VARCHAR(3) | 通貨 (USD) |
| `created_at` | TIMESTAMP | 作成日時 |

### Table 2: `lme_copper_futures` (36-Month Futures Data)

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PRIMARY KEY | レコードID |
| `trade_date` | DATE | 取引日 |
| `contract_month` | INTEGER | 限月 (1-36) |
| `ric` | VARCHAR(20) | Reuters Instrument Code (CMCUc1-CMCUc36) |
| `close_price` | DECIMAL(12,4) | 終値 |
| `high_price` | DECIMAL(12,4) | 高値 |
| `low_price` | DECIMAL(12,4) | 安値 |
| `open_price` | DECIMAL(12,4) | 始値 |
| `volume` | BIGINT | 出来高 |
| `currency` | VARCHAR(3) | 通貨 (USD) |
| `created_at` | TIMESTAMP | 作成日時 |
| `updated_at` | TIMESTAMP | 更新日時 |

### Sample Queries

#### 最新の価格データを表示
```sql
SELECT 
    trade_date,
    price_type,
    last_price,
    high_price,
    low_price,
    volume
FROM lme_copper_prices 
WHERE last_price IS NOT NULL 
ORDER BY trade_date DESC, price_type 
LIMIT 10;
```

#### 月次統計を表示
```sql
SELECT 
    DATE_TRUNC('month', trade_date) as month,
    price_type,
    AVG(last_price) as avg_price,
    MIN(last_price) as min_price,
    MAX(last_price) as max_price,
    SUM(volume) as total_volume
FROM lme_copper_prices 
WHERE last_price IS NOT NULL 
GROUP BY DATE_TRUNC('month', trade_date), price_type
ORDER BY month DESC, price_type;
```

#### 価格レンジ分析
```sql
SELECT 
    price_type,
    COUNT(*) as record_count,
    AVG(last_price) as avg_price,
    STDDEV(last_price) as price_volatility,
    MIN(trade_date) as start_date,
    MAX(trade_date) as end_date
FROM lme_copper_prices 
WHERE last_price IS NOT NULL 
GROUP BY price_type;
```

#### 最新の先物カーブを表示
```sql
SELECT 
    contract_month,
    ric,
    close_price,
    volume,
    trade_date
FROM lme_copper_futures 
WHERE trade_date = (
    SELECT MAX(trade_date) 
    FROM lme_copper_futures
)
ORDER BY contract_month;
```

#### 限月別の平均価格と出来高
```sql
SELECT 
    contract_month,
    ric,
    COUNT(*) as record_count,
    AVG(close_price) as avg_price,
    SUM(volume) as total_volume,
    MIN(trade_date) as start_date,
    MAX(trade_date) as end_date
FROM lme_copper_futures 
WHERE close_price IS NOT NULL 
GROUP BY contract_month, ric
ORDER BY contract_month;
```

## Data Summary

### Table 1: `lme_copper_prices`
- **総レコード数**: 1,516
- **データ期間**: 2022-07-06 to 2025-07-04
- **価格タイプ**:
  - 3M_OUTRIGHT: 758レコード
  - CASH_3M_SPREAD: 758レコード

### Table 2: `lme_copper_futures` 
- **総レコード数**: 45,407
- **データ期間**: 2020-07-06 to 2025-07-04（5年分）
- **限月数**: 36限月 (CMCUc1 - CMCUc36)
- **各限月**: 約1,260レコード（5年分）
- **価格レンジ**: $6,114 - $11,299/トン
- **年別平均価格**:
  - 2020年: $6,864/トン
  - 2021年: $9,166/トン
  - 2022年: $8,715/トン
  - 2023年: $8,591/トン
  - 2024年: $9,442/トン
  - 2025年: $9,512/トン

## Notes

- データは重複防止のため、UNIQUE制約 `(trade_date, price_type, ric)` が設定されています
- 価格データが存在しないレコードは除外してクエリすることを推奨します (`WHERE last_price IS NOT NULL`)
- スプレッドデータの正負は市場構造（コンタンゴ/バックワーデーション）を示します