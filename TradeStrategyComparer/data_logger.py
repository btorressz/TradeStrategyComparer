import csv
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import json

class DataLogger:
    """Logger for trading data and statistics"""
    
    def __init__(self):
        self.trades_data = []
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.log_file = f"data/trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_headers = [
            'timestamp', 'bot_type', 'trade_direction', 'input_amount', 'input_symbol',
            'output_received', 'output_symbol', 'expected_output', 'slippage_percent', 'price', 'success'
        ]
        
        # Initialize CSV file
        self._init_csv_file()
        
    def _init_csv_file(self):
        """Initialize CSV file with headers"""
        try:
            with open(self.log_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
            logging.info(f"Initialized CSV log file: {self.log_file}")
        except Exception as e:
            logging.error(f"Error initializing CSV file: {e}")
    
    def log_trade(self, trade_data: Dict[str, Any]):
        """Log a single trade to memory and CSV"""
        try:
            # Add to memory
            self.trades_data.append(trade_data.copy())
            
            # Write to CSV
            with open(self.log_file, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                
                # Prepare row data
                row_data = {
                    'timestamp': trade_data['timestamp'].isoformat(),
                    'bot_type': trade_data['bot_type'],
                    'trade_direction': trade_data.get('trade_direction', 'SOL_TO_USDC'),
                    'input_amount': trade_data.get('input_amount', 0),
                    'input_symbol': trade_data.get('input_symbol', 'SOL'),
                    'output_received': trade_data.get('output_received', 0),
                    'output_symbol': trade_data.get('output_symbol', 'USDC'),
                    'expected_output': trade_data.get('expected_output', 0),
                    'slippage_percent': trade_data.get('slippage_percent', 0),
                    'price': trade_data.get('price', 0),
                    'success': trade_data.get('success', False)
                }
                
                writer.writerow(row_data)
            
            logging.debug(f"Logged trade: {trade_data['bot_type']} - {trade_data.get('input_amount', 0)} {trade_data.get('input_symbol', 'INPUT')}")
            
        except Exception as e:
            logging.error(f"Error logging trade: {e}")
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """Get all trades as pandas DataFrame"""
        try:
            if not self.trades_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(self.trades_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
            
        except Exception as e:
            logging.error(f"Error creating trades DataFrame: {e}")
            return pd.DataFrame()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        try:
            df = self.get_trades_dataframe()
            
            if df.empty:
                return {
                    'total_trades': 0,
                    'twap_trades': 0,
                    'smart_trades': 0,
                    'total_input_traded': 0,
                    'total_output_received': 0,
                    'average_slippage': 0,
                    'success_rate': 0,
                    'twap_stats': {
                        'total_trades': 0,
                        'total_input': 0,
                        'total_output': 0,
                        'avg_slippage': 0,
                        'avg_price': 0
                    },
                    'smart_stats': {
                        'total_trades': 0,
                        'total_input': 0,
                        'total_output': 0,
                        'avg_slippage': 0,
                        'avg_price': 0
                    }
                }
            
            # Filter successful trades
            successful_df = df[df['success'] == True]
            
            # Calculate statistics by bot type
            twap_df = successful_df[successful_df['bot_type'] == 'TWAPBot']
            smart_df = successful_df[successful_df['bot_type'] == 'SmartBot']
            
            stats = {
                'total_trades': len(df),
                'successful_trades': len(successful_df),
                'twap_trades': len(twap_df),
                'smart_trades': len(smart_df),
                'total_input_traded': float(successful_df['input_amount'].sum()),
                'total_output_received': float(successful_df['output_received'].sum()),
                'average_slippage': float(successful_df['slippage_percent'].mean()) if len(successful_df) > 0 else 0,
                'success_rate': float(len(successful_df) / len(df) * 100) if len(df) > 0 else 0,
                'twap_stats': {
                    'total_trades': len(twap_df),
                    'total_input': float(twap_df['input_amount'].sum()) if len(twap_df) > 0 else 0,
                    'total_output': float(twap_df['output_received'].sum()) if len(twap_df) > 0 else 0,
                    'avg_slippage': float(twap_df['slippage_percent'].mean()) if len(twap_df) > 0 else 0,
                    'avg_price': float(twap_df['price'].mean()) if len(twap_df) > 0 else 0
                },
                'smart_stats': {
                    'total_trades': len(smart_df),
                    'total_input': float(smart_df['input_amount'].sum()) if len(smart_df) > 0 else 0,
                    'total_output': float(smart_df['output_received'].sum()) if len(smart_df) > 0 else 0,
                    'avg_slippage': float(smart_df['slippage_percent'].mean()) if len(smart_df) > 0 else 0,
                    'avg_price': float(smart_df['price'].mean()) if len(smart_df) > 0 else 0
                }
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"Error calculating summary stats: {e}")
            return {}
    
    def get_time_series_data(self) -> Dict[str, List]:
        """Get time series data for charting"""
        try:
            df = self.get_trades_dataframe()
            
            if df.empty:
                return {'timestamps': [], 'twap_cumulative': [], 'smart_cumulative': []}
            
            # Filter successful trades
            successful_df = df[df['success'] == True]
            
            # Sort by timestamp
            successful_df = successful_df.sort_values('timestamp')
            
            # Calculate cumulative output by bot type
            twap_df = successful_df[successful_df['bot_type'] == 'TWAPBot'].copy()
            smart_df = successful_df[successful_df['bot_type'] == 'SmartBot'].copy()
            
            # Create time series
            all_timestamps = successful_df['timestamp'].unique()
            all_timestamps = sorted(all_timestamps)
            
            twap_cumulative = []
            smart_cumulative = []
            twap_total = 0
            smart_total = 0
            
            for timestamp in all_timestamps:
                # Add TWAP trades up to this timestamp
                twap_trades = twap_df[twap_df['timestamp'] <= timestamp]
                if not twap_trades.empty:
                    twap_total = twap_trades['output_received'].sum()
                
                # Add Smart trades up to this timestamp
                smart_trades = smart_df[smart_df['timestamp'] <= timestamp]
                if not smart_trades.empty:
                    smart_total = smart_trades['output_received'].sum()
                
                twap_cumulative.append(float(twap_total))
                smart_cumulative.append(float(smart_total))
            
            return {
                'timestamps': [ts.isoformat() for ts in all_timestamps],
                'twap_cumulative': twap_cumulative,
                'smart_cumulative': smart_cumulative
            }
            
        except Exception as e:
            logging.error(f"Error getting time series data: {e}")
            return {'timestamps': [], 'twap_cumulative': [], 'smart_cumulative': []}
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export all data to CSV file"""
        try:
            if filename is None:
                filename = f"data/trading_simulation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            df = self.get_trades_dataframe()
            
            if not df.empty:
                df.to_csv(filename, index=False)
                logging.info(f"Exported {len(df)} trades to {filename}")
            else:
                # Create empty CSV with headers
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                    writer.writeheader()
                logging.info(f"Created empty CSV file: {filename}")
            
            return filename
            
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            raise
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent trades"""
        try:
            if not self.trades_data:
                return []
            
            # Sort by timestamp (most recent first)
            sorted_trades = sorted(self.trades_data, 
                                 key=lambda x: x['timestamp'], 
                                 reverse=True)
            
            return sorted_trades[:limit]
            
        except Exception as e:
            logging.error(f"Error getting recent trades: {e}")
            return []
