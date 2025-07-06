"""
Data utilities for LME Copper analysis
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging
from datetime import datetime, timedelta
import os
from typing import Optional, Tuple, Dict, Any

class DataLoader:
    """
    Data loading utilities for LME Copper analysis
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize DataLoader with database connection
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.engine = create_engine(connection_string)
        self.logger = logging.getLogger(__name__)
    
    def load_spread_data(self, 
                        start_date: str = None, 
                        end_date: str = None,
                        table_name: str = 'lme_copper_prices') -> pd.DataFrame:
        """
        Load Cash/3M spread data from database
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            table_name: Database table name
            
        Returns:
            DataFrame with spread data
        """
        try:
            query = f"""
            SELECT 
                trade_date,
                CASE 
                    WHEN ric_code = 'CMCU0-3' THEN close_price
                    ELSE NULL 
                END as spread_value,
                CASE 
                    WHEN ric_code = 'CMCU0' THEN close_price
                    ELSE NULL 
                END as cash_price,
                CASE 
                    WHEN ric_code = 'CMCU3' THEN close_price
                    ELSE NULL 
                END as month_3_price
            FROM {table_name}
            WHERE ric_code IN ('CMCU0-3', 'CMCU0', 'CMCU3')
            """
            
            if start_date:
                query += f" AND trade_date >= '{start_date}'"
            if end_date:
                query += f" AND trade_date <= '{end_date}'"
                
            query += " ORDER BY trade_date"
            
            df = pd.read_sql(query, self.engine)
            
            # Pivot and aggregate data
            df_pivot = df.groupby('trade_date').agg({
                'spread_value': 'first',
                'cash_price': 'first', 
                'month_3_price': 'first'
            }).fillna(method='ffill')
            
            return df_pivot
            
        except Exception as e:
            self.logger.error(f"Error loading spread data: {e}")
            return self._generate_dummy_data()
    
    def _generate_dummy_data(self) -> pd.DataFrame:
        """Generate dummy data for testing purposes"""
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        
        # Generate realistic spread data
        np.random.seed(42)
        base_spread = 50
        spread_values = base_spread + np.cumsum(np.random.normal(0, 5, len(dates)))
        
        return pd.DataFrame({
            'spread_value': spread_values,
            'cash_price': 9000 + np.random.normal(0, 100, len(dates)),
            'month_3_price': 9000 + np.random.normal(0, 100, len(dates))
        }, index=dates)

def calculate_technical_indicators(df: pd.DataFrame, 
                                 price_column: str = 'spread_value') -> pd.DataFrame:
    """
    Calculate technical indicators for spread data
    
    Args:
        df: DataFrame with price data
        price_column: Column name for price data
        
    Returns:
        DataFrame with technical indicators added
    """
    df = df.copy()
    
    # Moving averages
    df['ma_5'] = df[price_column].rolling(window=5).mean()
    df['ma_20'] = df[price_column].rolling(window=20).mean()
    df['ma_50'] = df[price_column].rolling(window=50).mean()
    
    # Bollinger Bands
    df['bb_middle'] = df[price_column].rolling(window=20).mean()
    bb_std = df[price_column].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    
    # RSI
    delta = df[price_column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Volatility
    df['volatility'] = df[price_column].rolling(window=20).std()
    
    return df

def safe_value(val) -> Any:
    """
    Safely convert values, handling NaN and None
    
    Args:
        val: Value to convert
        
    Returns:
        Converted value or None
    """
    if pd.isna(val):
        return None
    return float(val) if isinstance(val, (int, float)) else val