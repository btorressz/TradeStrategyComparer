import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any
import random

class BaseTradingBot:
    """Base class for trading bots"""
    
    def __init__(self, trade_amount: float, jupiter_api, data_logger, trade_direction='SOL_TO_USDC'):
        self.trade_amount = trade_amount
        self.jupiter_api = jupiter_api
        self.data_logger = data_logger
        self.trade_direction = trade_direction  # 'SOL_TO_USDC' or 'USDC_TO_SOL'
        self.running = False
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_input_traded': 0.0,
            'total_output_received': 0.0,
            'total_slippage': 0.0,
            'average_slippage': 0.0,
            'total_pnl': 0.0
        }
        
    def stop(self):
        """Stop the bot"""
        self.running = False
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current bot statistics"""
        if self.stats['total_trades'] > 0:
            self.stats['average_slippage'] = self.stats['total_slippage'] / self.stats['total_trades']
        return self.stats.copy()
    
    def execute_trade(self) -> Dict[str, Any]:
        """Execute a single trade and return trade data"""
        try:
            # Determine input/output mints based on trade direction
            if self.trade_direction == 'SOL_TO_USDC':
                input_mint = 'So11111111111111111111111111111111111111112'  # SOL
                output_mint = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC
                amount = int(self.trade_amount * 1e9)  # Convert SOL to lamports
                input_symbol = 'SOL'
                output_symbol = 'USDC'
                output_decimals = 1e6  # USDC has 6 decimals
            else:  # USDC_TO_SOL
                input_mint = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC
                output_mint = 'So11111111111111111111111111111111111111112'  # SOL
                amount = int(self.trade_amount * 1e6)  # Convert USDC to micro USDC
                input_symbol = 'USDC'
                output_symbol = 'SOL'
                output_decimals = 1e9  # SOL has 9 decimals
            
            # Get quote from Jupiter API
            quote_data = self.jupiter_api.get_quote(
                input_mint=input_mint,
                output_mint=output_mint,
                amount=amount
            )
            
            if not quote_data:
                return {'success': False, 'error': 'Failed to get quote'}
            
            # Calculate slippage
            expected_output = int(quote_data.get('outAmount', 0)) / output_decimals
            actual_output = expected_output * (1 - random.uniform(0.001, 0.01))  # Simulate slippage
            slippage = abs(expected_output - actual_output) / expected_output * 100 if expected_output > 0 else 0
            
            # Update statistics
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_input_traded'] += self.trade_amount
            self.stats['total_output_received'] += actual_output
            self.stats['total_slippage'] += slippage
            
            # Calculate price and PnL
            if self.trade_direction == 'SOL_TO_USDC':
                current_price = actual_output / self.trade_amount  # USDC per SOL
                expected_price = expected_output / self.trade_amount
            else:
                current_price = self.trade_amount / actual_output  # USDC per SOL (inverted)
                expected_price = self.trade_amount / expected_output if expected_output > 0 else 0
            
            self.stats['total_pnl'] += (current_price - expected_price) * self.trade_amount
            
            trade_data = {
                'timestamp': datetime.now(),
                'bot_type': self.__class__.__name__,
                'trade_direction': self.trade_direction,
                'input_amount': self.trade_amount,
                'input_symbol': input_symbol,
                'output_received': actual_output,
                'output_symbol': output_symbol,
                'expected_output': expected_output,
                'slippage_percent': slippage,
                'price': current_price,
                'success': True
            }
            
            # Log the trade
            self.data_logger.log_trade(trade_data)
            
            logging.info(f"{self.__class__.__name__} executed trade: {self.trade_amount} {input_symbol} -> {actual_output:.4f} {output_symbol} (slippage: {slippage:.3f}%)")
            
            return trade_data
            
        except Exception as e:
            logging.error(f"Error executing trade in {self.__class__.__name__}: {e}")
            self.stats['total_trades'] += 1
            return {'success': False, 'error': str(e)}

class TWAPBot(BaseTradingBot):
    """TWAP (Time-Weighted Average Price) Bot - executes trades at fixed intervals"""
    
    def __init__(self, trade_amount: float, interval_minutes: int, jupiter_api, data_logger, trade_direction='SOL_TO_USDC'):
        super().__init__(trade_amount, jupiter_api, data_logger, trade_direction)
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        
    def run(self):
        """Run the TWAP bot"""
        self.running = True
        input_symbol = 'SOL' if self.trade_direction == 'SOL_TO_USDC' else 'USDC'
        logging.info(f"TWAP Bot started - trading {self.trade_amount} {input_symbol} every {self.interval_minutes} minutes")
        
        while self.running:
            try:
                # Execute trade
                trade_result = self.execute_trade()
                
                if not trade_result.get('success', False):
                    logging.warning(f"TWAP Bot trade failed: {trade_result.get('error', 'Unknown error')}")
                
                # Wait for next interval
                time.sleep(self.interval_seconds)
                
            except Exception as e:
                logging.error(f"Error in TWAP Bot main loop: {e}")
                time.sleep(10)  # Wait 10 seconds before retrying
        
        logging.info("TWAP Bot stopped")

class SmartBot(BaseTradingBot):
    """Smart Bot - only executes trades when slippage is below threshold"""
    
    def __init__(self, trade_amount: float, slippage_threshold: float, jupiter_api, data_logger, trade_direction='SOL_TO_USDC'):
        super().__init__(trade_amount, jupiter_api, data_logger, trade_direction)
        self.slippage_threshold = slippage_threshold
        self.check_interval = 30  # Check every 30 seconds
        self.stats['trades_skipped'] = 0
        
    def should_execute_trade(self, quote_data: Dict[str, Any]) -> bool:
        """Determine if trade should be executed based on slippage"""
        try:
            # Estimate slippage based on quote data
            estimated_slippage = random.uniform(0.05, 0.5)  # Simulate market conditions
            
            return estimated_slippage <= self.slippage_threshold
            
        except Exception as e:
            logging.error(f"Error checking trade conditions: {e}")
            return False
    
    def run(self):
        """Run the Smart bot"""
        self.running = True
        input_symbol = 'SOL' if self.trade_direction == 'SOL_TO_USDC' else 'USDC'
        logging.info(f"Smart Bot started - trading {self.trade_amount} {input_symbol} when slippage < {self.slippage_threshold}%")
        
        while self.running:
            try:
                # Determine input/output mints based on trade direction
                if self.trade_direction == 'SOL_TO_USDC':
                    input_mint = 'So11111111111111111111111111111111111111112'  # SOL
                    output_mint = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC
                    amount = int(self.trade_amount * 1e9)  # Convert SOL to lamports
                else:  # USDC_TO_SOL
                    input_mint = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC
                    output_mint = 'So11111111111111111111111111111111111111112'  # SOL
                    amount = int(self.trade_amount * 1e6)  # Convert USDC to micro USDC
                
                # Get current quote to check conditions
                quote_data = self.jupiter_api.get_quote(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount
                )
                
                if quote_data and self.should_execute_trade(quote_data):
                    # Execute trade
                    trade_result = self.execute_trade()
                    
                    if not trade_result.get('success', False):
                        logging.warning(f"Smart Bot trade failed: {trade_result.get('error', 'Unknown error')}")
                else:
                    # Skip trade due to unfavorable conditions
                    self.stats['trades_skipped'] += 1
                    logging.debug(f"Smart Bot skipped trade - conditions not favorable")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Error in Smart Bot main loop: {e}")
                time.sleep(10)  # Wait 10 seconds before retrying
        
        logging.info("Smart Bot stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Smart Bot statistics including skipped trades"""
        stats = super().get_stats()
        stats['trades_skipped'] = self.stats.get('trades_skipped', 0)
        stats['execution_rate'] = (
            stats['successful_trades'] / (stats['successful_trades'] + stats['trades_skipped']) * 100
            if (stats['successful_trades'] + stats['trades_skipped']) > 0 else 0
        )
        return stats
