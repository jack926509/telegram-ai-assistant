from telegram import Update
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
import ipaddress
import socket
import asyncio
from urllib.parse import urlparse
import aiohttp
from utils.openai_helper import OpenAIHelper
from utils.retry import retry_async, is_retryable_http_error, run_in_thread_with_retry

ai_helper = OpenAIHelper()

BLOCKED_HOSTS = {'localhost', 'localhost.localdomain'}


async def is_safe_url(url):
    """檢查 URL 是否安全可抓取 (基本 SSRF 防護)"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False, "僅支援 http/https 網址"

        hostname = parsed.hostname
        if not hostname:
            return False, "網址缺少主機名稱"

        normalized_host = hostname.lower()
        if normalized_host in BLOCKED_HOSTS or normalized_host.endswith('.local'):
            return False, "不允許存取本機或內網位址"

        try:
            host_ip = ipaddress.ip_address(hostname)
            if (
                host_ip.is_private
                or host_ip.is_loopback
                or host_ip.is_link_local
                or host_ip.is_multicast
                or host_ip.is_reserved
                or host_ip.is_unspecified
            ):
                return False, "不允許存取內網或保留位址"
        except ValueError:
            pass

        # 解析 DNS 並阻擋解析到私有/本機網段
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        for info in infos:
            ip_text = info[4][0]
            resolved_ip = ipaddress.ip_address(ip_text)
            if (
                resolved_ip.is_private
                or resolved_ip.is_loopback
                or resolved_ip.is_link_local
                or resolved_ip.is_multicast
                or resolved_ip.is_reserved
                or resolved_ip.is_unspecified
            ):
                return False, "不允許存取內網或保留位址"

        return True, ""
    except socket.gaierror:
        return False, "無法解析網址主機"
    except Exception:
        return False, "網址格式不正確"

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
        results = await search_duckduckgo(query)
        
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

    is_safe, reason = await is_safe_url(url)
    if not is_safe:
        await update.message.reply_text(f"網址不可用: {reason}")
        return
    
    await update.message.reply_text("📄 正在分析網頁內容...")
    
    try:
        # 抓取網頁內容
        content = await fetch_web_content(url)
        
        if not content:
            await update.message.reply_text("無法讀取網頁內容。")
            return
        
        # 使用 AI 總結
        summary = await run_in_thread_with_retry(
            ai_helper.summarize_web_content,
            content
        )
        
        response = (
            f"📄 網頁摘要\n"
            f"🔗 {url}\n\n"
            f"{summary}"
        )
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"總結網頁時發生錯誤: {str(e)}")

async def search_duckduckgo(query, num_results=5):
    """使用 DuckDuckGo 搜尋"""
    try:
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=10)

        async def _request():
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.post(url, data=params) as response:
                    response.raise_for_status()
                    return await response.text()

        text = await retry_async(
            _request,
            should_retry=is_retryable_http_error
        )
        soup = BeautifulSoup(text, 'html.parser')
        
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

async def fetch_web_content(url):
    """抓取網頁內容"""
    try:
        is_safe, _ = await is_safe_url(url)
        if not is_safe:
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        timeout = aiohttp.ClientTimeout(total=15)

        async def _request():
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()

        content_bytes = await retry_async(
            _request,
            should_retry=is_retryable_http_error
        )

        soup = BeautifulSoup(content_bytes, 'html.parser')
        
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
        results = await search_duckduckgo(query, num_results=3)
        
        if not results:
            await update.message.reply_text("沒有找到相關結果。")
            return
        
        # 總結前幾個結果
        summaries = []
        for result in results[:2]:
            content = await fetch_web_content(result['url'])
            if content:
                summary = await run_in_thread_with_retry(
                    ai_helper.summarize_web_content,
                    content,
                    200
                )
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
