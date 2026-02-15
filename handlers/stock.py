from telegram import Update
from telegram.ext import ContextTypes
import yfinance as yf
from datetime import datetime, timedelta

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
        stock_data = get_stock_info(symbol)
        
        if stock_data:
            await update.message.reply_text(stock_data, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"無法取得 {symbol} 的資訊。\n"
                "請確認股票代碼是否正確。"
            )
    
    except Exception as e:
        await update.message.reply_text(f"查詢股價時發生錯誤: {str(e)}")

def get_stock_info(symbol):
    """取得股票資訊"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 取得即時報價
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        
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
        currency = info.get('currency', 'TWD')
        
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
        
        if info.get('volume'):
            volume = info['volume']
            if volume > 1_000_000:
                vol_str = f"{volume/1_000_000:.2f}M"
            elif volume > 1_000:
                vol_str = f"{volume/1_000:.2f}K"
            else:
                vol_str = f"{volume}"
            result += f"📊 成交量: {vol_str}\n"
        
        if info.get('dayLow') and info.get('dayHigh'):
            result += f"📏 今日區間: {info['dayLow']:.2f} - {info['dayHigh']:.2f}\n"
        
        if info.get('fiftyTwoWeekLow') and info.get('fiftyTwoWeekHigh'):
            result += f"📅 52週區間: {info['fiftyTwoWeekLow']:.2f} - {info['fiftyTwoWeekHigh']:.2f}\n"
        
        # PE 比率
        if info.get('trailingPE'):
            result += f"📈 本益比: {info['trailingPE']:.2f}\n"
        
        # 股息
        if info.get('dividendYield'):
            dividend_yield = info['dividendYield'] * 100
            result += f"💵 殖利率: {dividend_yield:.2f}%\n"
        
        return result
    
    except Exception as e:
        print(f"取得股票資訊錯誤: {e}")
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
        stock = yf.Ticker(symbol)
        
        # 取得歷史數據
        hist = stock.history(period=period)
        
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
    
    except Exception as e:
        await update.message.reply_text(f"生成圖表時發生錯誤: {str(e)}")

async def watchlist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票觀察清單 (簡化版)"""
    # 預設的熱門股票
    watchlist = ['2330.TW', 'AAPL', 'TSLA', '^TWII', '^GSPC']
    
    await update.message.reply_text("📊 正在查詢熱門股票...")
    
    result = "📊 *熱門股票*\n\n"
    
    for symbol in watchlist:
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
                result += f"{emoji} {name}: {current_price:.2f} ({change_percent:+.2f}%)\n"
        
        except:
            continue
    
    await update.message.reply_text(result, parse_mode='Markdown')
