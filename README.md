# TradeStrategyComparer 📊


A sophisticated Python Flask web application for simulating and comparing trading execution strategies, specifically focused on SOL/USDC trading using real-time Jupiter API data.

## 🌟 Features

- **Dual Trading Strategy Comparison**
  - **TWAP Bot**: Time-Weighted Average Price execution at fixed intervals
  - **Smart Bot**: Intelligent execution only when slippage is below threshold

- **Bidirectional Trading Support**
  - SOL → USDC conversion
  - USDC → SOL conversion
  - Dynamic strategy adaptation

- **Real-Time Performance Analytics**
  - Live dashboard with Chart.js visualizations
  - Comprehensive slippage analysis
  - Trade execution efficiency metrics
  - Success rate tracking

- **Professional Data Management**
  - CSV export functionality
  - Historical trade logging
  - Time series performance data
  - Statistical summaries


### Usage

1. **Configure Trading Parameters**
   - Set trade amount (default: 1.0)
   - Choose trading direction (SOL↔USDC)
   - Set slippage threshold for Smart Bot (default: 0.2%)
   - Configure simulation duration (default: 60 minutes)

2. **Start Simulation**
   - Both bots run in parallel
   - TWAP Bot executes every 5 minutes
   - Smart Bot executes when conditions are favorable

3. **Monitor Performance**
   - Real-time dashboard updates every 2 seconds
   - Live charts show cumulative performance
   - Track trade statistics as they happen

4. **Analyze Results**
   - View detailed performance charts
   - Compare strategy effectiveness
   - Download trade data as CSV
   - Review execution insights


## 🏗️ Architecture

### Core Components

- **Flask Backend**: RESTful API with real-time endpoints
- **Jupiter API Integration**: Live SOL/USDC market data
- **Trading Bots**: Object-oriented strategy implementations
- **Data Logger**: CSV persistence with in-memory caching
- **Chart Generator**: Matplotlib visualizations with dark theme
- **Bootstrap Frontend**: Responsive UI with live updates

  
### Trading Strategies

#### TWAP Bot
- Executes trades at fixed 5-minute intervals
- Provides consistent market exposure
- Ideal for dollar-cost averaging approach

#### Smart Bot
- Only executes when slippage < 0.2% (configurable)
- Waits for favorable market conditions
- Optimizes for execution efficiency

  
## 📊 Performance Metrics

- **Cumulative Performance**: Total input/output comparison
- **Slippage Analysis**: Average and per-trade slippage tracking
- **Execution Efficiency**: Success rates and timing analysis
- **Price Tracking**: Real-time price monitoring and logging

  ## 🛠️ Technical Stack

- **Backend**: Flask, Gunicorn, Python 3.11
- **Frontend**: Bootstrap 5, Chart.js, Custom CSS
- **Data**: Pandas, NumPy, CSV logging
- **Visualization**: Matplotlib, Base64 encoding
- **API**: Jupiter DEX aggregator

  
## 🔧 Configuration

### Environment Variables
- `SESSION_SECRET`: Flask session management (auto-generated)
- `DATABASE_URL`: PostgreSQL connection (available but unused)

### Default Settings
- **Trade Amount**: 1.0 SOL/USDC
- **TWAP Interval**: 5 minutes
- **Smart Bot Threshold**: 0.2% slippage
- **Simulation Duration**: 60 minutes
- **Update Frequency**: 2 seconds


