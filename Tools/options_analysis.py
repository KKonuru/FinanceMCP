import yfinance as yf
import mcp.types as types
import pandas as pd

tools = [

]

async def calculate_greeks(app,args:dict) -> list[types.ContentBlock]:
    """Calculates the Greeks for a given option using the Black-Scholes model.
    Args:
        args (dict): A dictionary containing the following keys:
            - symbol (str): The stock symbol.
            - strike (float): The option strike price.
            - expiration (str): The option expiration date in 'YYYY-MM-DD' format.
            - option_type (str): 'call' or 'put'.
    Returns:
        list[types.ContentBlock]: A list containing a single TextContent block with the Greeks.
    """
    ctx = app.context
    symbol = args.get("symbol")
    strike = args.get("strike")
    expiration = args.get("expiration")
    option_type = args.get("option_type", "call").lower()
    try:
        ticker = yf.Ticker(symbol)
        if expiration not in ticker.options:
            return [types.TextContent(type="text", text=f"Expiration date {expiration} not found for {symbol}. Available dates: {ticker.options}")]
        options_chain = ticker.option_chain(expiration)
        if option_type == "call":
            options = options_chain.calls
        elif option_type == "put":
            options = options_chain.puts
        else:
            return [types.TextContent(type="text", text="option_type must be 'call' or 'put'.")]
        option = options[options['strike'] == strike]
        if option.empty:
            return [types.TextContent(type="text", text=f"No {option_type} option found for {symbol} with strike {strike} and expiration {expiration}.")]
        
        ticker.option_chain(ticker.options[0]).calls
    except Exception as e:
        error_msg = (
            f"Error calculating Greeks for {symbol} with strike {strike} and expiration {expiration}: {e}"
        )
        ctx.logger.error(
            f"Error in calculate_greeks for symbol={symbol}, strike={strike}, expiration={expiration}: {e}"
        )
        return [types.TextContent(type="text", text=error_msg)]
    return [types.TextContent(type="text", text="Greeks calculation not implemented yet.")]

async def get_implied_volatility(app, args:dict) -> list[types.ContentBlock]:
    """Calculates the implied volatility for a given option.
    Args:
        args (dict): A dictionary containing the following
            - symbol (str): The stock symbol.
            - strike (float): The option strike price.
            - expiration (str): The option expiration date in 'YYYY-MM-DD' format.
            - option_type (str): 'call' or 'put'.
    Returns:
        list[types.ContentBlock]: A list containing a single TextContent block with the implied volatility.
    """
    ctx = app.context
    symbol = args.get("symbol")
    strike = args.get("strike")
    expiration = args.get("expiration")
    option_type = args.get("option_type", "call").lower()
    try:
        ticker = yf.Ticker(symbol)
        if expiration not in ticker.options:
            return [types.TextContent(type="text", text=f"Expiration date {expiration} not found for {symbol}. Available dates: {ticker.options}")]
        options_chain = ticker.option_chain(expiration)
        if option_type == "call":
            options = options_chain.calls
        elif option_type == "put":
            options = options_chain.puts
        else:
            return [types.TextContent(type="text", text="option_type must be 'call' or 'put'.")]
        option = options[options['strike'] == strike]
        if option.empty:
            return [types.TextContent(type="text", text=f"No {option_type} option found for {symbol} with strike {strike} and expiration {expiration}.")]
        
        implied_vol = option['impliedVolatility'].values[0]
        response_msg = f"The implied volatility for the {option_type} option of {symbol} with strike {strike} expiring on {expiration} is {implied_vol:.2%}."
    except Exception as e:
        error_msg = (
            f"Error calculating implied volatility for {symbol} with strike {strike} and expiration {expiration}: {e}"
        )
        ctx.logger.error(
            f"Error in get_implied_volatility for symbol={symbol}, strike={strike}, expiration={expiration}: {e}"
        )
        return [types.TextContent(type="text", text=error_msg)]