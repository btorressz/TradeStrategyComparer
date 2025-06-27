import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import logging
import os
import io
import base64
from datetime import datetime
from typing import Dict, Any, List

class ChartGenerator:
    """Generate performance comparison charts"""
    
    def __init__(self, data_logger):
        self.data_logger = data_logger
        plt.style.use('dark_background')  # Dark theme to match UI
        
    def generate_cumulative_performance_chart(self) -> str:
        """Generate cumulative performance comparison chart"""
        try:
            time_series = self.data_logger.get_time_series_data()
            
            if not time_series['timestamps']:
                return self._create_empty_chart("No data available for cumulative performance")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            timestamps = [datetime.fromisoformat(ts) for ts in time_series['timestamps']]
            
            ax.plot(timestamps, time_series['twap_cumulative'], 
                   label='TWAP Bot', linewidth=2, color='#00ff88')
            ax.plot(timestamps, time_series['smart_cumulative'], 
                   label='Smart Bot', linewidth=2, color='#ff6b6b')
            
            ax.set_title('Cumulative Output Comparison', fontsize=16, fontweight='bold')
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Cumulative Output Received', fontsize=12)
            ax.legend(fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logging.error(f"Error generating cumulative performance chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def generate_slippage_comparison_chart(self) -> str:
        """Generate slippage comparison chart"""
        try:
            df = self.data_logger.get_trades_dataframe()
            
            if df.empty:
                return self._create_empty_chart("No data available for slippage comparison")
            
            successful_df = df[df['success'] == True]
            
            if successful_df.empty:
                return self._create_empty_chart("No successful trades for slippage comparison")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Slippage over time
            twap_df = successful_df[successful_df['bot_type'] == 'TWAPBot']
            smart_df = successful_df[successful_df['bot_type'] == 'SmartBot']
            
            if not twap_df.empty:
                ax1.scatter(twap_df['timestamp'], twap_df['slippage_percent'], 
                           alpha=0.7, label='TWAP Bot', color='#00ff88', s=50)
            
            if not smart_df.empty:
                ax1.scatter(smart_df['timestamp'], smart_df['slippage_percent'], 
                           alpha=0.7, label='Smart Bot', color='#ff6b6b', s=50)
            
            ax1.set_title('Slippage Over Time', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Time', fontsize=12)
            ax1.set_ylabel('Slippage (%)', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Average slippage comparison
            if not twap_df.empty and not smart_df.empty:
                avg_slippage = [twap_df['slippage_percent'].mean(), smart_df['slippage_percent'].mean()]
                bot_names = ['TWAP Bot', 'Smart Bot']
                colors = ['#00ff88', '#ff6b6b']
                
                bars = ax2.bar(bot_names, avg_slippage, color=colors, alpha=0.8)
                ax2.set_title('Average Slippage Comparison', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Average Slippage (%)', fontsize=12)
                
                # Add value labels on bars
                for bar, value in zip(bars, avg_slippage):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{value:.3f}%', ha='center', va='bottom', fontsize=11)
            
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logging.error(f"Error generating slippage comparison chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def generate_execution_efficiency_chart(self) -> str:
        """Generate execution efficiency comparison chart"""
        try:
            stats = self.data_logger.get_summary_stats()
            
            if not stats or stats['total_trades'] == 0:
                return self._create_empty_chart("No data available for execution efficiency")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Trade count comparison
            twap_trades = stats['twap_stats']['total_trades']
            smart_trades = stats['smart_stats']['total_trades']
            
            if twap_trades > 0 or smart_trades > 0:
                trade_counts = [twap_trades, smart_trades]
                bot_names = ['TWAP Bot', 'Smart Bot']
                colors = ['#00ff88', '#ff6b6b']
                
                bars1 = ax1.bar(bot_names, trade_counts, color=colors, alpha=0.8)
                ax1.set_title('Total Trades Executed', fontsize=14, fontweight='bold')
                ax1.set_ylabel('Number of Trades', fontsize=12)
                
                # Add value labels
                for bar, value in zip(bars1, trade_counts):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            str(value), ha='center', va='bottom', fontsize=11)
            
            # Output per trade efficiency
            twap_efficiency = stats['twap_stats']['total_output'] / twap_trades if twap_trades > 0 else 0
            smart_efficiency = stats['smart_stats']['total_output'] / smart_trades if smart_trades > 0 else 0
            
            if twap_efficiency > 0 or smart_efficiency > 0:
                efficiencies = [twap_efficiency, smart_efficiency]
                
                bars2 = ax2.bar(bot_names, efficiencies, color=colors, alpha=0.8)
                ax2.set_title('Average Output per Trade', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Output per Trade', fontsize=12)
                
                # Add value labels
                for bar, value in zip(bars2, efficiencies):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                            f'{value:.4f}', ha='center', va='bottom', fontsize=11)
            
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logging.error(f"Error generating execution efficiency chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def generate_price_tracking_chart(self) -> str:
        """Generate price tracking chart"""
        try:
            df = self.data_logger.get_trades_dataframe()
            
            if df.empty:
                return self._create_empty_chart("No data available for price tracking")
            
            successful_df = df[df['success'] == True]
            
            if successful_df.empty:
                return self._create_empty_chart("No successful trades for price tracking")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Sort by timestamp
            successful_df = successful_df.sort_values('timestamp')
            
            twap_df = successful_df[successful_df['bot_type'] == 'TWAPBot']
            smart_df = successful_df[successful_df['bot_type'] == 'SmartBot']
            
            if not twap_df.empty:
                ax.plot(twap_df['timestamp'], twap_df['price'], 
                       'o-', label='TWAP Bot Prices', color='#00ff88', markersize=6, linewidth=2)
            
            if not smart_df.empty:
                ax.plot(smart_df['timestamp'], smart_df['price'], 
                       's-', label='Smart Bot Prices', color='#ff6b6b', markersize=6, linewidth=2)
            
            ax.set_title('Price Tracking', fontsize=16, fontweight='bold')
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Price', fontsize=12)
            ax.legend(fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format price axis
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.4f}'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logging.error(f"Error generating price tracking chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def generate_all_charts(self) -> Dict[str, str]:
        """Generate all performance charts"""
        return {
            'cumulative_performance': self.generate_cumulative_performance_chart(),
            'slippage_comparison': self.generate_slippage_comparison_chart(),
            'execution_efficiency': self.generate_execution_efficiency_chart(),
            'price_tracking': self.generate_price_tracking_chart()
        }
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)  # Free memory
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logging.error(f"Error converting figure to base64: {e}")
            plt.close(fig)
            return self._create_empty_chart(f"Error rendering chart: {str(e)}")
    
    def _create_empty_chart(self, message: str) -> str:
        """Create an empty chart with a message"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, message, ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='#cccccc')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logging.error(f"Error creating empty chart: {e}")
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
