import yfinance as yf
import mcp.types as types
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.trend import MACD
tools = [
    types.Tool(
            name="calculate-all-volatility",
            description=(
                "Fetches the volatility measurement over multiple periods for a given stock symbol."
            ),
            inputSchema={
                "type": "object",
                "required": ["symbol"],
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock symbol to analyze (e.g., 'AAPL')",
                    },
                    "period": {
                        "type": "string",
                        "description": (
                            "The time period for the analysis (e.g., '1mo', '3mo', '1y')."
                            " Defaults to '1mo' if not provided."
                        ),
                    },
                },
            }
    ),
    types.Tool(
            name="get-technical-indicators",
            description=(
                "Fetches technical indicators like RSI, MACD, and Bollinger Bands for a given stock symbol."
            ),
            inputSchema={
                "type": "object",
                "required": ["symbol"],
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock symbol to analyze (e.g., 'AAPL')",
                    },
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "A list of technical indicators to fetch. "
                            "Supported indicators: 'RSI', 'MACD', 'BB'. "
                            "Defaults to all if not provided."
                        ),
                    },
                },
            }
    ),
    types.Tool(
            name="calculate-correlations",
            description=(
                "Calculates the correlation matrix for a list of stock symbols over a specified period."
            ),
            inputSchema={
                "type": "object",
                "required": ["symbols_list"],
                "properties": {
                    "symbols_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "A list of stock symbols to analyze (e.g., ['AAPL', 'MSFT', 'GOOGL'])."
                        ),
                    },
                    "period": {
                        "type": "string",
                        "description": (
                            "The time period for the analysis (e.g., '1mo', '3mo', '1y')."
                            " Defaults to '1y' if not provided."
                        ),
                    },
                },
            }
    ),
    types.Tool(
            name="get-risk-metrics",
            description=(
                "Calculates risk metrics like Beta, Volatility, and Sharpe Ratio for a given stock symbol compared to a benchmark index."
            ),
            inputSchema={
                "type": "object",
                "required": ["symbol"],
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock symbol to analyze (e.g., 'AAPL')",
                    },
                    "benchmark": {
                        "type": "string",
                        "description": (
                            "The benchmark index symbol (e.g., 'SPY'). Defaults to 'SPY' if not provided."
                        ),
                    },
                    "period": {
                        "type": "string",
                        "description": (
                            "The time period for the analysis (e.g., '1mo', '3mo', '1y')."
                            " Defaults to '1y' if not provided."
                        ),
                    },
                },
            }
    )
]
async def tool_call_router(name: str, args: dict) -> list[types.ContentBlock]:
    for tool in tools:
        if tool.name == name:
            return await globals()[tool.name.replace("-", "_")](None, args)
    raise ValueError(f"Tool {name} not found")
async def calculate_all_volatility(app, args:dict) -> list[types.ContentBlock]:
    """Calculates the standard deviation of returns for a given stock symbol over multiple periods.
    Args:
        args (dict): A dictionary containing the following
            - symbol (str): The stock symbol to analyze (e.g., "AAPL").
            - period (str, optional): The time period for the analysis. Defaults to "1mo".
    Returns:
        list[type.ContentBlock]: A list containing a single ContentBlock with the volatility information.
    """
    ctx = app.request_context
    symbol = args.get("sysmbol", "").upper()
    period = args.get("period","")

    if not symbol:
        return [types.ContentBlock(text="Please provide a valid stock symbol.")]

    try:
        ticker = yf.Ticker(symbol)
        response_data = {}
        periods = ["1d","5d","1mo","3mo","6mo","1y","2y","5y"]
        for period in periods:
            if period=='1d':
                history = ticker.history(period=period,interval="1m").sort_values(by="Datetime")
            elif period=='5d':
                history = ticker.history(period=period,interval='60m').sort_values(by="Datetime")
            else:
                history = ticker.history(period=period).sort_values(by="Date")
            history["returns"] = history["Close"].pct_change()*100
            response_data[period] = history.std(axis=0).iloc[-1]

        #Work in progress as values are added
        response_msg = (
            f"Standard Deviation of Returns for {symbol}:\n"
            f"1 Day (1 minute intervals): {response_data['1d']:.2f}%\n"
            f"5 Days (60 minute intervals): {response_data['5d']:.2f}%\n"
            f"1 Month: {response_data['1mo']:.2f}%\n"
            f"3 Months: {response_data['3mo']:.2f}%\n"
            f"6 Months: {response_data['6mo']:.2f}%\n"
            f"1 Year: {response_data['1y']:.2f}%\n"
            f"2 Years: {response_data['2y']:.2f}%\n"
            f"5 Years: {response_data['5y']:.2f}%\n"
        )
        
    except Exception as e:
        error_msg = f"Error fetching data fro {symbol} with period {period}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="calculate_volatility",
            related_request_id=ctx.request_id
        )
        return [types.TextContent(type="text",text=error_msg)]
    
    return [types.TextContent(type="text",text=response_msg)]

async def get_technical_indicators(app, args:dict) -> list[type.ContentBlock]:
    """
    Fetches technical indicators for a given stock symbol.
    Args:
        args (dict): A dictionary containing the following keys:
            - symbol (str): The stock symbol to analyze (e.g., "AAPL").
            - indicators (list, optional): A list of technical indicators to fetch. Defaults to ["RSI", "MACD", "BB"].
    Returns:
        list[type.ContentBlock]: A list containing a single ContentBlock with the technical indicators information.
    """
    ctx = app.request_context
    symbol = args.get("symbol", "").upper()
    indicators = args.get("indicators", ["RSI", "MACD", "BB"])

    if not symbol:
        return [types.ContentBlock(text="Please provide a valid stock symbol.")]

    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1y")
        response_data = {}

        if "RSI" in indicators:
            rsi_indicator = RSIIndicator(history['Close'], window=14)
            history['RSI'] = rsi_indicator.rsi()
            response_data["RSI"] = history['RSI'].iloc[-1]

        if "MACD" in indicators:
            macd_indicator = MACD(history['Close'])
            history['MACD'] = macd_indicator.macd()
            history['Signal Line'] = macd_indicator.macd_signal()
            response_data["MACD"] = (history['MACD'].iloc[-1], history['Signal Line'].iloc[-1])

        if "BB" in indicators:
            bb_indicator = BollingerBands(history['Close'], window=20, window_dev=2)
            history['BB_High'] = bb_indicator.bollinger_hband()
            history['BB_Low'] = bb_indicator.bollinger_lband()
            response_data["BB"] = (history['BB_High'].iloc[-1], history['BB_Low'].iloc[-1])

        response_msg = f"Technical Indicators for {symbol}:\n"
        if "RSI" in response_data:
            response_msg += f"RSI: {response_data['RSI']:.2f}\n"
        if "MACD" in response_data:
            macd, signal = response_data["MACD"]
            response_msg += f"MACD: {macd:.2f}, Signal Line: {signal:.2f}\n"
        if "BB" in response_data:
            bb_high, bb_low = response_data["BB"]
            response_msg += f"Bollinger Bands - High: {bb_high:.2f}, Low: {bb_low:.2f}\n"
    except Exception as e:
        error_msg = f"Error fetching data for {symbol}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="get_technical_indicators",
            related_request_id=ctx.request_id
        )
        return [types.TextContent(type="text", text=error_msg)]
    return [types.TextContent(type="text", text=response_msg)]

async def calculate_correlations(app, args:dict) -> list[types.ContentBlock]:
    """
    Calculates the correlation matrix for a list of stock symbols over a specified period.
    Args:
        args (dict): A dictionary containing the following keys:
            - symbols_list (list): A list of stock symbols to analyze (e.g., [
            " AAPL", "MSFT", "GOOGL"]).
            - period (str, optional): The time period for the analysis. Defaults to "1y".
    Returns:
        list[type.ContentBlock]: A list containing a single ContentBlock with the correlation matrix information.
    """
    ctx = app.request_context
    stock_symbols = args.get("symbols_list", [])
    period = args.get("period", "1y")
    try:
        if not stock_symbols or not isinstance(stock_symbols, list):
            return [types.ContentBlock(text="Please provide a valid list of stock symbols.")]

        data = {}
        for symbol in stock_symbols:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period)
            data[symbol] = history['Close']

        df = pd.DataFrame(data)
        correlation_matrix = df.corr()

        response_msg = f"Correlation Matrix for {', '.join(stock_symbols)} over {period}:\n"
        response_msg += correlation_matrix.to_string()

        return [types.TextContent(type="text", text=response_msg)]
    except Exception as e:
        error_msg = f"Error calculating correlations: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="calculate_correlations",
            related_request_id=ctx.request_id
        )
        return [types.TextContent(type="text", text=error_msg)]

async def get_risk_metrics(app, args:dict) -> list[types.ContentBlock]:
    """
    Calculates risk metrics for a given stock symbol compared to a benchmark index.
    Args:
        args (dict): A dictionary containing the following
            - symbol (str): The stock symbol to analyze (e.g., "AAPL").
            - benchmark (str, optional): The benchmark index symbol. Defaults to "SPY".
            - period (str, optional): The time period for the analysis. Defaults to "1y".
    Returns:
        list[type.ContentBlock]: A list containing a single ContentBlock with the risk metrics information.
    """
    ctx = app.request_context
    symbol = args.get("symbol", "").upper()
    benchmark = args.get("benchmark", "SPY").upper()
    period = args.get("period", "1y")

    if not symbol:
        return [types.ContentBlock(text="Please provide a valid stock symbol.")]

    try:
        ticker = yf.Ticker(symbol)
        benchmark_ticker = yf.Ticker(benchmark)

        history = ticker.history(period=period)
        benchmark_history = benchmark_ticker.history(period=period)

        history['Returns'] = history['Close'].pct_change()
        benchmark_history['Benchmark Returns'] = benchmark_history['Close'].pct_change()

        merged_data = history[['Returns']].join(benchmark_history[['Benchmark Returns']], how='inner').dropna()

        beta = merged_data['Returns'].cov(merged_data['Benchmark Returns']) / merged_data['Benchmark Returns'].var()
        volatility = history['Returns'].std() * (252 ** 0.5)  # Annualized volatility
        sharpe_ratio = (history['Returns'].mean() * 252) / (history['Returns'].std() * (252 ** 0.5))

        response_msg = (
            f"Risk Metrics for {symbol} compared to {benchmark} over {period}:\n"
            f"Beta: {beta:.2f}\n"
            f"Annualized Volatility: {volatility:.2f}\n"
            f"Sharpe Ratio: {sharpe_ratio:.2f}\n"
        )

    except Exception as e:
        error_msg = f"Error fetching data for {symbol} or {benchmark}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="get_risk_metrics",
            related_request_id=ctx.request_id
        )
        return [types.TextContent(type="text", text=error_msg)]

    return [types.TextContent(type="text", text=response_msg)]
    