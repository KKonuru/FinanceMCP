import yfinance as yf
import mcp.types as types
import pandas as pd

tools = [
    types.Tool(
                name="get-stock-price-data",
                description=(
                    "Fetches the current stock price and related data for a given ticker"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["ticker"],
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol to fetch data for",
                        },
                    },
                }
            ),
    types.Tool(
                name="get-stock-price-period",
                description=(
                    "Fetches the stock price for a given ticker and timeframe"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["ticker"],
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol to fetch data for",
                        },
                        "timeframe": {
                            "type": "string",
                            "default": "1d",
                            "description": (
                                """Timeframe for the stock price, default is '1d'. 
                                Options for are _d,_m,_y for daily, monthly, and yearly data respectively.
                                Example: '1d' for daily, '1m' for monthly, '1y' for yearly.
                                Can also be ytd or max for year to date or maximum data.
                                """
                            ),
                        },
                    },
                }
            ),
        types.Tool(
                name="get-options-dates",
                description=(
                    "Fetches the available options dates for a given ticker. The results can be used to fetch the options chain"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["ticker"],
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol to fetch options dates for",
                        },
                    },
                }
            ),
        types.Tool(
            name="get-options-chain",
            description=(
                "Fetches the options chain for a given ticker and its option type, expiration date, and number of strikes"
            ),
            inputSchema={
                "type": "object",
                "required": ["ticker"],
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol to fetch options chain for",
                    },
                    "options_type": {
                        "type": "string",
                        "default": "call",
                        "description": (
                            "Type of options to fetch, e.g., 'call' or 'put'. Default is 'call'"
                        ),
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": (
                            "Expiration date for the options in 'YYYY-MM-DD' format"
                        ),
                    },
                    "number_strikes": {
                        "type": "integer",
                        "default": 5,
                        "description": (
                            "Number of strikes to fetch for expiration date, default is 5"
                        ),
                    },
                },
            }
        ),
        types.Tool(
            name="get-dividend-history",
            description=(
                "Fetches the dividend history for a given ticker"
            ),
            inputSchema={
                "type": "object",
                "required": ["ticker"],
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol to fetch dividend history for",
                    },
                    "years_back": {
                        "type": "integer",
                        "default": 5,
                        "description": (
                            "Number of years back to fetch dividend history, default is 5"
                        ),
                    },
                },
            }
        ),
        types.Tool(
            name="get-earnings-calendar",
            description=(
                "Fetches the earnings calendar for a given ticker"
            ),
            inputSchema={
                "type": "object",
                "required": ["ticker"],
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol to fetch earnings calendar for",
                    },
                },
            }
        )
]
async def tool_call_router(name: str,args:dict) -> list[types.ContentBlock]:
    for tool in tools:
        if tool.name == name:
            return await globals()[tool.name.replace("-", "_")](None, args)
    raise ValueError(f"Tool {name} not found")

async def get_stock_price_data(app,args: dict) -> list[types.ContentBlock]:
    """Fetches the current stock price and related data for a given ticker.
    Args:
        args (dict): Dictionary containing 'ticker'.
            - ticker (str): Stock ticker symbol to fetch data for.
    Returns:
        list[types.ContentBlock]: List of content blocks with stock data.
    """
    ctx = app.request_context
    if "ticker" not in args:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    ticker = args["ticker"].upper()
    
    try:
        stock_data = yf.Ticker(ticker).info
        if not stock_data:
            raise ValueError(f"No data found for ticker: {ticker}")
        
        price = stock_data.get("currentPrice", "N/A")
        market = stock_data.get("market", "N/A")
        market_cap = stock_data.get("marketCap", "N/A")
        volume = stock_data.get("volume", "N/A")
        sector = stock_data.get("sector", "N/A")
        
        response_msg = (
            f"Current price for {ticker}: ${price}\n"
            f"Market Cap: ${market_cap}\n"
            f"Volume: {volume}"
        )
        
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="stock_price_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching data for {ticker}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="stock_price_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]
    
async def get_stock_price_period(app,args:dict) -> list[type.ContentBlock]:
    """Fetches the stock price for a given ticker and timeframe.
    Args:
        args (dict): Dictionary containing 'ticker' and 'timeframe'.
            - ticker (str): Stock ticker symbol to fetch data for.
            - timeframe (str): Timeframe for the stock price, default is "1d".
    Returns:
        list[types.ContentBlock]: List of content blocks with stock price data.
    """
    ctx = app.request_context
    ticker = args.get("ticker", "").upper()
    timeframe = args.get("timeframe", "1d")
    
    if not ticker:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    
    try:
        stock_data = yf.Ticker(ticker).history(period=timeframe)
        if stock_data.empty:
            raise ValueError(f"No data found for ticker: {ticker} with timeframe: {timeframe}")
        stock_data_json = stock_data.to_json(orient="records")
        latest_price = stock_data["Close"].iloc[-1]
        response_msg = (
            f"Latest price for {ticker} ({timeframe}): ${latest_price}\n"
            f"Data: {stock_data_json}"
        )
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="stock_price_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching data for {ticker} with timeframe {timeframe}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="stock_price_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]
async def get_options_dates(app, args: dict) -> list[types.ContentBlock]:
    """Fetches the available options dates for a given ticker.
    Args:
        args (dict): Dictionary containing 'ticker'.
            - ticker (str): Stock ticker symbol to fetch options dates for.
    Returns:
        list[types.ContentBlock]: List of content blocks with options dates.
    """
    ctx = app.request_context
    ticker = args.get("ticker", "").upper()
    
    if not ticker:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    
    try:
        options_dates = yf.Ticker(ticker).options
        if not options_dates:
            raise ValueError(f"No options dates found for ticker: {ticker}")
        
        response_msg = f"Available options dates for {ticker}: {', '.join(options_dates)}"
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="options_dates_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching options dates for {ticker}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="options_dates_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]
    
async def get_options_chain(app, args: dict) -> list[types.ContentBlock]:
    """Fetches the options chain for a given ticker.
    Args:
        args (dict): Dictionary containing 'ticker'.
            - ticker (str): Stock ticker symbol to fetch options chain for.
            - options_type (str): Type of options to fetch, e.g., "call" or "put".
            - expiration_date (str): Expiration date for the options in 'YYYY-MM-DD' format.
            - number_strikes (int): Number of strikes to fetch for expiration date.
    Returns:
        list[types.ContentBlock]: List of content blocks with options chain data.
    """
    ctx = app.request_context
    ticker = args.get("ticker", "").upper()
    options_type = args.get("options_type", "call").lower()
    expiration_date = args.get("expiration_date", None)
    number_strikes = args.get("number_strikes", 5)
    if not ticker:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    
    try:
        options_dates = yf.Ticker(ticker).options
        if not options_dates:
            raise ValueError(f"No options chain found for ticker: {ticker}")
        if not expiration_date or expiration_date not in options_dates:
            return [types.TextContent(type="text", text=f"Expiration date {expiration_date} not found for {ticker}. Available dates: {', '.join(options_dates)}")]

        options_chain = yf.Ticker(ticker).option_chain(expiration_date)
        if options_type == "call":
            options_data = options_chain.calls
        elif options_type == "put":
            options_data = options_chain.puts
        options_data_json = options_data.head(number_strikes).to_json(orient="records")
        response_msg = (
            f"Options chain for {ticker} on {expiration_date} ({options_type}):\n"
            f"{options_data_json}"
        )
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="options_chain_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching options chain for {ticker}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="options_chain_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]
async def get_dividend_history(app, args: dict) -> list[types.ContentBlock]:
    """Fetches the dividend history for a given ticker.
    Args:
        args (dict): Dictionary containing 'ticker' and 'years_back'.
            - ticker (str): Stock ticker symbol to fetch dividend history for.
            - years_back (int): Number of years back to fetch dividend history, default is 5.
    Returns:
        list[types.ContentBlock]: List of content blocks with dividend history data.
    """
    ctx = app.request_context
    ticker = args.get("ticker", "").upper()
    years_back = args.get("years_back", 5)
    
    if not ticker:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    
    try:
        dat = yf.Ticker(ticker)
        dividends = dat.dividends
        if dividends.empty:
            raise ValueError(f"No dividend history found for ticker: {ticker}")
        
        # Filter dividends based on years_back
        recent_dividends = dividends[dividends.index.year >= (pd.Timestamp.now().year - years_back)]
        if recent_dividends.empty:
            raise ValueError(f"No dividends found for the last {years_back} years for ticker: {ticker}")
        recent_dividends = recent_dividends.reset_index()
        recent_dividends["Date"] = recent_dividends["Date"].dt.strftime("%Y-%m-%d")
        
        response_msg = f"Dividend history for {ticker} over the last {years_back} years:\n{recent_dividends.to_json(orient='records')}"
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="dividend_history_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching dividend history for {ticker}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="dividend_history_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]

async def get_earnings_calendar(app, args: dict) -> list[types.ContentBlock]:
    """Fetches the earnings calendar for a given ticker.
    Args:
        args (dict): Dictionary containing 'ticker'.
            - ticker (str): Stock ticker symbol to fetch earnings calendar for.
    Returns:
        list[types.ContentBlock]: List of content blocks with earnings calendar data.
    """
    ctx = app.request_context
    ticker = args.get("ticker", "").upper()
    
    if not ticker:
        return [types.TextContent(type="text", text="Ticker symbol is required.")]
    
    try:
        earnings_calendar = yf.Ticker(ticker).earnings_dates
        if earnings_calendar.empty:
            raise ValueError(f"No earnings calendar found for ticker: {ticker}")
        earnings_calendar = earnings_calendar.reset_index()
        earnings_calendar["Earnings Date"] = earnings_calendar["Earnings Date"].dt.strftime("%Y-%m-%d")
        response_msg = f"Earnings calendar for {ticker}:\n{earnings_calendar.to_json(orient='records')}"
        await ctx.session.send_log_message(
            level="info",
            data=response_msg,
            logger="earnings_calendar_fetcher",
            related_request_id=ctx.request_id,
        )
        
        return [types.TextContent(type="text", text=response_msg)]
    
    except Exception as e:
        error_msg = f"Error fetching earnings calendar for {ticker}: {str(e)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_msg,
            logger="earnings_calendar_fetcher",
            related_request_id=ctx.request_id,
        )
        return [types.TextContent(type="text", text=error_msg)]

