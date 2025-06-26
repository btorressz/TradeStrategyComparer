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
