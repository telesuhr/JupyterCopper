# LME Copper Historical Data Collector

Refinitiv EIKON Data APIを使用してLME銅の3MアウトライトとCash/3Mスプレッドの過去3年分のデータを取得し、PostgreSQLデータベースに格納するプログラムです。

## 前提条件

1. **Refinitiv EIKON Workspace**が起動している
2. **PostgreSQL**がインストールされている
3. **Python 3.8+**がインストールされている

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを編集してデータベース設定を調整してください：

```env
# EIKON API設定
EIKON_APP_KEY=1475940198b04fdab9265b7892546cc2ead9eda6

# PostgreSQL設定
DB_HOST=localhost
DB_NAME=lme_copper_db
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432
```

### 3. データベースの作成

```bash
python setup_database.py
```

## 使用方法

### データ収集の実行

```bash
python lme_copper_data_collector.py
```

## 取得するデータ

- **LME銅 3Mアウトライト** (RIC: CMCU3=LME)
- **LME銅 Cash/3Mスプレッド** (RIC: CMCU0-CMCU3=LME)

### データフィールド

- 最終価格 (CF_LAST)
- 高値 (CF_HIGH)
- 安値 (CF_LOW)
- 始値 (CF_OPEN)
- 出来高 (CF_VOLUME)

## データベース構造

```sql
CREATE TABLE lme_copper_prices (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    price_type VARCHAR(20) NOT NULL,
    ric VARCHAR(50) NOT NULL,
    last_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    open_price DECIMAL(10,4),
    volume BIGINT,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, price_type, ric)
);
```

## ログ

実行ログは `lme_copper_collector.log` ファイルに記録されます。

## 注意事項

- EIKON Workspaceが起動していることを確認してください
- データの重複は自動的に処理されます（UPSERT機能）
- エラーが発生した場合は、ログファイルを確認してください