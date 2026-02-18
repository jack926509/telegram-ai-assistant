import logging

import yfinance as yf
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from utils.retry import run_in_thread_with_retry

logger = logging.getLogger(__name__)

async def stock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股價查詢處理器"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "請提供股票代碼,例如:\n"
            "/stock 2330 (台積電)\n"
            "/stock AAPL (蘋果)\n"
            "/stock ^TWII (台灣加權指數)"
        )
        return
    
    symbol = context.args[0].upper()
    
    # 台股代碼需要加上 .TW
    if symbol.isdigit() and len(symbol) == 4:
        symbol = f"{symbol}.TW"
    
    await update.message.reply_text(f"📈 正在查詢 {symbol} 的股價...")
    
    try:
        stock_data = await run_in_thread_with_retry(get_stock_info, symbol)
        
        if stock_data:
            await update.message.reply_text(stock_data, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"無法取得 {symbol} 的資訊。\n"
                "請確認股票代碼是否正確。"
            )
    
    except Exception:
        logger.exception("stock_handler failed: symbol=%s", symbol)
        await update.message.reply_text("查詢股價時發生錯誤，請稍後再試。")

def get_stock_info(symbol):
    """取得股票資訊"""
    try:
        stock = yf.Ticker(symbol)
        try:
            info = stock.info or {}
        except Exception:
            info = {}

        try:
            fast_info = dict(stock.fast_info or {})
        except Exception:
            fast_info = {}
        
        # 取得即時報價
        current_price = (
            info.get('currentPrice')
            or info.get('regularMarketPrice')
            or fast_info.get('lastPrice')
            or fast_info.get('regularMarketPrice')
        )
        previous_close = (
            info.get('previousClose')
            or info.get('regularMarketPreviousClose')
            or fast_info.get('previousClose')
        )

        if not current_price:
            # yfinance info API 偶爾失敗，改用歷史價格做 fallback
            hist = stock.history(period='5d')
            if not hist.empty:
                closes = hist['Close'].dropna()
                if len(closes) >= 1:
                    current_price = float(closes.iloc[-1])
                if len(closes) >= 2:
                    previous_close = float(closes.iloc[-2])
        
        if not current_price:
            return None
        
        # 計算漲跌
        change = current_price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        # 漲跌符號
        if change > 0:
            change_emoji = "📈"
            change_symbol = "+"
        elif change < 0:
            change_emoji = "📉"
            change_symbol = ""
        else:
            change_emoji = "➡️"
            change_symbol = ""
        
        # 基本資訊
        name = info.get('longName') or info.get('shortName') or symbol
        currency = info.get('currency') or fast_info.get('currency') or 'USD'
        
        result = (
            f"📊 *{name}* ({symbol})\n\n"
            f"💰 現價: {current_price:.2f} {currency}\n"
            f"{change_emoji} 漲跌: {change_symbol}{change:.2f} ({change_percent:+.2f}%)\n"
        )
        
        # 其他資訊
        if info.get('marketCap'):
            market_cap = info['marketCap']
            if market_cap > 1_000_000_000_000:
                cap_str = f"{market_cap/1_000_000_000_000:.2f}T"
            elif market_cap > 1_000_000_000:
                cap_str = f"{market_cap/1_000_000_000:.2f}B"
            else:
                cap_str = f"{market_cap/1_000_000:.2f}M"
            result += f"🏢 市值: {cap_str} {currency}\n"
        
        volume_value = info.get('volume') or fast_info.get('lastVolume')
        if volume_value:
            volume = volume_value
            if volume > 1_000_000:
                vol_str = f"{volume/1_000_000:.2f}M"
            elif volume > 1_000:
                vol_str = f"{volume/1_000:.2f}K"
            else:
                vol_str = f"{volume}"
            result += f"📊 成交量: {vol_str}\n"
        
        day_low = info.get('dayLow') or fast_info.get('dayLow')
        day_high = info.get('dayHigh') or fast_info.get('dayHigh')
        if day_low and day_high:
            result += f"📏 今日區間: {day_low:.2f} - {day_high:.2f}\n"
        
        year_low = info.get('fiftyTwoWeekLow') or fast_info.get('yearLow')
        year_high = info.get('fiftyTwoWeekHigh') or fast_info.get('yearHigh')
        if year_low and year_high:
            result += f"📅 52週區間: {year_low:.2f} - {year_high:.2f}\n"
        
        # PE 比率
        if info.get('trailingPE'):
            result += f"📈 本益比: {info['trailingPE']:.2f}\n"
        
        # 股息
        if info.get('dividendYield'):
            dividend_yield = info['dividendYield'] * 100
            result += f"💵 殖利率: {dividend_yield:.2f}%\n"
        
        return result
    
    except Exception:
        logger.exception("get_stock_info failed: symbol=%s", symbol)
        return None


def get_stock_history(symbol, period):
    """取得股票歷史資料"""
    stock = yf.Ticker(symbol)
    return stock.history(period=period)


def get_watchlist_item(symbol):
    """取得觀察清單單一股票資訊"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose')

        if current_price and previous_close:
            change_percent = ((current_price - previous_close) / previous_close) * 100

            if change_percent > 0:
                emoji = "📈"
            elif change_percent < 0:
                emoji = "📉"
            else:
                emoji = "➡️"

            name = info.get('shortName', symbol)
            return f"{emoji} {name}: {current_price:.2f} ({change_percent:+.2f}%)"
    except Exception:
        return None

    return None

async def stock_chart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股價走勢圖"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("請提供股票代碼")
        return
    
    symbol = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else '1mo'
    
    # 台股代碼需要加上 .TW
    if symbol.isdigit() and len(symbol) == 4:
        symbol = f"{symbol}.TW"
    
    await update.message.reply_text(f"📊 正在生成 {symbol} 的走勢圖...")
    
    try:
        # 取得歷史數據
        hist = await run_in_thread_with_retry(get_stock_history, symbol, period)
        
        if hist.empty:
            await update.message.reply_text("無法取得歷史數據")
            return
        
        # 簡單的文字圖表
        result = f"📈 *{symbol}* 走勢 ({period})\n\n"
        
        # 取最近10個交易日
        recent = hist.tail(10)
        
        max_price = recent['Close'].max()
        min_price = recent['Close'].min()
        
        for date, row in recent.iterrows():
            close = row['Close']
            # 計算相對位置 (0-20)
            if max_price != min_price:
                position = int((close - min_price) / (max_price - min_price) * 20)
            else:
                position = 10
            
            bar = "█" * position + "░" * (20 - position)
            result += f"{date.strftime('%m/%d')} {bar} {close:.2f}\n"
        
        await update.message.reply_text(result, parse_mode='Markdown')
    
    except Exception:
        logger.exception("stock_chart_handler failed: symbol=%s", symbol)
        await update.message.reply_text("生成走勢圖時發生錯誤，請稍後再試。")

async def watchlist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票觀察清單 (簡化版)"""
    # 預設的熱門股票
    watchlist = ['2330.TW', 'AAPL', 'TSLA', '^TWII', '^GSPC']
    
    await update.message.reply_text("📊 正在查詢熱門股票...")
    
    result = "📊 *熱門股票*\n\n"

    lines = await asyncio.gather(
        *(run_in_thread_with_retry(get_watchlist_item, symbol) for symbol in watchlist)
    )
    for line in lines:
        if line:
            result += f"{line}\n"
    
    await update.message.reply_text(result, parse_mode='Markdown')
