from telegram import Update
from telegram.ext import ContextTypes
import requests
from bs4 import BeautifulSoup
from utils.openai_helper import OpenAIHelper

ai_helper = OpenAIHelper()

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """網頁搜尋處理器"""
    query = ' '.join(context.args) if context.args else None
    
    if not query:
        await update.message.reply_text(
            "請提供搜尋關鍵字,例如:\n"
            "/search Python 教學"
        )
        return
    
    await update.message.reply_text("🔍 正在搜尋...")
    
    try:
        # 使用 DuckDuckGo HTML 搜尋 (不需要 API key)
        results = search_duckduckgo(query)
        
        if not results:
            await update.message.reply_text("沒有找到相關結果。")
            return
        
        response = f"🔍 搜尋結果: {query}\n\n"
        
        for i, result in enumerate(results[:5], 1):
            response += (
                f"{i}. {result['title']}\n"
                f"   {result['url']}\n"
                f"   {result['snippet']}\n\n"
            )
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"搜尋時發生錯誤: {str(e)}")

async def summarize_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """總結網頁內容"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "請提供網址,例如:\n"
            "/summarize https://example.com"
        )
        return
    
    url = context.args[0]
    
    await update.message.reply_text("📄 正在分析網頁內容...")
    
    try:
        # 抓取網頁內容
        content = fetch_web_content(url)
        
        if not content:
            await update.message.reply_text("無法讀取網頁內容。")
            return
        
        # 使用 AI 總結
        summary = ai_helper.summarize_web_content(content)
        
        response = (
            f"📄 網頁摘要\n"
            f"🔗 {url}\n\n"
            f"{summary}"
        )
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"總結網頁時發生錯誤: {str(e)}")

def search_duckduckgo(query, num_results=5):
    """使用 DuckDuckGo 搜尋"""
    try:
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.find_all('div', class_='result')[:num_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')
            
            if title_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        
        return results
    
    except Exception as e:
        print(f"搜尋錯誤: {e}")
        return []

def fetch_web_content(url):
    """抓取網頁內容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 移除 script 和 style 標籤
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # 取得文字內容
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理多餘的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        return content[:5000]  # 限制長度
    
    except Exception as e:
        print(f"抓取網頁錯誤: {e}")
        return None

async def quick_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """快速搜尋並總結"""
    query = update.message.text
    
    # 移除觸發詞
    for trigger in ['搜尋', '查詢', '找', 'search']:
        query = query.replace(trigger, '').strip()
    
    if not query or len(query) < 2:
        return
    
    await update.message.reply_text("🔍 正在搜尋...")
    
    try:
        results = search_duckduckgo(query, num_results=3)
        
        if not results:
            await update.message.reply_text("沒有找到相關結果。")
            return
        
        # 總結前幾個結果
        summaries = []
        for result in results[:2]:
            content = fetch_web_content(result['url'])
            if content:
                summary = ai_helper.summarize_web_content(content, max_length=200)
                summaries.append(f"📌 {result['title']}\n{summary}")
        
        if summaries:
            response = f"🔍 關於「{query}」的資訊:\n\n"
            response += "\n\n".join(summaries)
            await update.message.reply_text(response)
        else:
            # 如果無法總結,顯示搜尋結果
            response = f"🔍 搜尋結果: {query}\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result['title']}\n   {result['url']}\n\n"
            await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"搜尋時發生錯誤: {str(e)}")
