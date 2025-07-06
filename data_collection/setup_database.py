#!/usr/bin/env python3
"""
PostgreSQLデータベースセットアップスクリプト
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """データベースを作成"""
    try:
        # PostgreSQLに接続（デフォルトのpostgresデータベースに接続）
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='password',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # データベースが存在するかチェック
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='lme_copper_db'")
        exists = cursor.fetchone()
        
        if not exists:
            # データベース作成
            cursor.execute("CREATE DATABASE lme_copper_db")
            logger.info("Database 'lme_copper_db' created successfully")
        else:
            logger.info("Database 'lme_copper_db' already exists")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    if create_database():
        logger.info("Database setup completed successfully")
        return True
    else:
        logger.error("Database setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)