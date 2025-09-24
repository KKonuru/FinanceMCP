# Model context protocol
This repository contains a implementation using low level server of the Model Context Protocol (MCP) to create a server that provides market data, market analysis, options analysis, trading strategy tools, and prediction tools.

The server uses yfinance to get market data and perform analysis. The streamable HTTP transport is used as it is can handle streaming data and supports both stateless and stateful modes, flexibility, and reliability. Compared to the Server Sent Events (SSE) transport, streamable HTTP performs all communication through one endpoint /sse. It also uses a session id mechanism to track request-response interactions. I implemented a Redis based memory store to store the event ids and session ids for reliability.


# Usage
To use MCP Clients such as Claude Desktop with the MCP server use the config format:
{
  "mcpServers": {
    "remote-example": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://remote.mcp.server/sse"
      ]
    }
  }
}
# Tools
## Market Data Tools
- [x] get_stock_price_data(ticker)
- [x] get_stock_price_period(ticker, timeframe="1d")
- [x] get_options_dates(ticker)
- [x] get_options_chain(ticker,options_type,expiration_date, number_strikes)
- [x] get_dividend_history(symbol, years_back=5)
- [x] get_earnings_calendar(symbol)
## Market Analysis Tools
- [x] calculate_all_volatility(symbol, period=30)
- [x] get_technical_indicators(symbol, indicators=["RSI", "MACD", "BB"])
- [x] calculate_correlations(symbols_list, period=252)
- [x] get_risk_metrics(symbol, benchmark="SPY")
## Options Analysis Tools
- [ ] calculate_greeks(symbol, strike, expiration, option_type)
- [x] get_implied_volatility(symbol, strike, expiration,option_type)
- [ ] find_arbitrage_opportunities(symbol, expiration_date)
- [ ] calculate_option_payoff(strategy_dict)
- [ ] get_put_call_ratio(symbol)
## Trading Strategy Tools
- [ ] backtest_strategy(strategy_params, symbol, start_date, end_date)
- [ ] find_pairs_trading_opportunities(sector="financial")
- [ ] calculate_sharpe_ratio(returns_series)
- [ ] detect_mean_reversion_signals(symbol, lookback=20)
- [ ] find_statistical_arbitrage(symbol_pair, zscore_threshold=2)
## Prediction Tools
- [ ] predict_price_movement(symbol, horizon_days=5, model="lstm")
- [ ] calculate_probability_of_profit(option_position)
- [ ] get_analyst_consensus(symbol)
- [ ] predict_volatility(symbol, days_ahead=30)
- [ ] generate_monte_carlo_simulation(symbol, scenarios=10000)

# Reliability
Each message in SSE stream is marked with a unique event id and all request-response interaction is represented with a unique session id. A response's event id and session id is stored in a event store such as:
- [x] InMemoryEventStore()
- [x] RedisEventStore()

# Acknowledgements
The project uses the low level streamable http example to create the structure of the mcp server using the streamable http. The example is from the [Python SDK](https://github.com/modelcontextprotocol/python-sdk).
