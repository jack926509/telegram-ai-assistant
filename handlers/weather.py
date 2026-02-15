from telegram import Update
from telegram.ext import ContextTypes
import config
from datetime import datetime
import aiohttp
from utils.retry import retry_async, is_retryable_http_error

async def weather_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """天氣查詢處理器"""
    city = ' '.join(context.args) if context.args else '台北'
    
    await update.message.reply_text(f"🌤 正在查詢 {city} 的天氣...")
    
    try:
        # 如果有 API key,使用 OpenWeatherMap
        if config.WEATHER_API_KEY:
            weather_data = await get_weather_openweathermap(city)
        else:
            # 否則使用免費的 wttr.in
            weather_data = await get_weather_wttr(city)
        
        if weather_data:
            await update.message.reply_text(weather_data, parse_mode='Markdown')
        else:
            await update.message.reply_text("無法取得天氣資訊,請檢查城市名稱是否正確。")
    
    except Exception as e:
        await update.message.reply_text(f"查詢天氣時發生錯誤: {str(e)}")

async def get_weather_openweathermap(city):
    """使用 OpenWeatherMap API 查詢天氣"""
    try:
        # 當前天氣
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': config.WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'zh_tw'
        }

        timeout = aiohttp.ClientTimeout(total=10)

        async def _fetch_current_weather():
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(current_url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()

        data = await retry_async(
            _fetch_current_weather,
            should_retry=is_retryable_http_error
        )

        # 取得未來天氣
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

        async def _fetch_forecast():
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(forecast_url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()

        forecast_data = await retry_async(
            _fetch_forecast,
            should_retry=is_retryable_http_error
        )
        
        # 格式化當前天氣
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        wind_speed = data['wind']['speed']
        
        weather_emoji = get_weather_emoji(data['weather'][0]['id'])
        
        result = (
            f"🌍 *{city} 天氣*\n\n"
            f"{weather_emoji} {description}\n"
            f"🌡 溫度: {temp}°C (體感 {feels_like}°C)\n"
            f"💧 濕度: {humidity}%\n"
            f"💨 風速: {wind_speed} m/s\n"
        )
        
        # 加入未來預報
        if forecast_data and 'list' in forecast_data:
            result += "\n*未來預報:*\n"
            # 取每8小時的預報(約3次,代表未來1天)
            for i in range(0, min(len(forecast_data['list']), 9), 3):
                forecast = forecast_data['list'][i]
                dt = datetime.fromtimestamp(forecast['dt'])
                temp = forecast['main']['temp']
                desc = forecast['weather'][0]['description']
                emoji = get_weather_emoji(forecast['weather'][0]['id'])
                result += f"{dt.strftime('%m/%d %H:%M')} {emoji} {temp}°C {desc}\n"
        
        return result
    
    except Exception as e:
        print(f"OpenWeatherMap API 錯誤: {e}")
        return None

async def get_weather_wttr(city):
    """使用免費的 wttr.in 服務查詢天氣"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        timeout = aiohttp.ClientTimeout(total=10)

        async def _request():
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()

        data = await retry_async(
            _request,
            should_retry=is_retryable_http_error
        )
        
        current = data['current_condition'][0]
        
        temp = current['temp_C']
        feels_like = current['FeelsLikeC']
        humidity = current['humidity']
        description = current['lang_zh'][0]['value'] if current.get('lang_zh') else current['weatherDesc'][0]['value']
        wind_speed = current['windspeedKmph']
        
        result = (
            f"🌍 *{city} 天氣*\n\n"
            f"🌤 {description}\n"
            f"🌡 溫度: {temp}°C (體感 {feels_like}°C)\n"
            f"💧 濕度: {humidity}%\n"
            f"💨 風速: {wind_speed} km/h\n"
        )
        
        # 加入未來3天預報
        if 'weather' in data:
            result += "\n*未來預報:*\n"
            for day in data['weather'][:3]:
                date = day['date']
                max_temp = day['maxtempC']
                min_temp = day['mintempC']
                desc = day['hourly'][4]['lang_zh'][0]['value'] if day['hourly'][4].get('lang_zh') else day['hourly'][4]['weatherDesc'][0]['value']
                result += f"{date}: {min_temp}°C ~ {max_temp}°C {desc}\n"
        
        return result
    
    except Exception as e:
        print(f"wttr.in 錯誤: {e}")
        return None

def get_weather_emoji(weather_id):
    """根據天氣代碼回傳對應的 emoji"""
    # OpenWeatherMap 天氣代碼對應
    if weather_id < 300:
        return "⛈"  # 雷雨
    elif weather_id < 400:
        return "🌧"  # 毛毛雨
    elif weather_id < 600:
        return "🌧"  # 雨
    elif weather_id < 700:
        return "❄️"  # 雪
    elif weather_id < 800:
        return "🌫"  # 霧霾
    elif weather_id == 800:
        return "☀️"  # 晴天
    elif weather_id == 801:
        return "🌤"  # 少雲
    elif weather_id == 802:
        return "⛅"  # 多雲
    else:
        return "☁️"  # 陰天

async def forecast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """詳細天氣預報"""
    city = ' '.join(context.args) if context.args else '台北'
    
    await update.message.reply_text(f"📅 正在查詢 {city} 的未來天氣...")
    
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        timeout = aiohttp.ClientTimeout(total=10)

        async def _request():
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()

        data = await retry_async(
            _request,
            should_retry=is_retryable_http_error
        )
        
        result = f"📅 *{city} 未來天氣預報*\n\n"
        
        for day in data['weather'][:5]:
            date = day['date']
            max_temp = day['maxtempC']
            min_temp = day['mintempC']
            
            # 取得中午的天氣
            noon_weather = day['hourly'][4]
            desc = noon_weather['lang_zh'][0]['value'] if noon_weather.get('lang_zh') else noon_weather['weatherDesc'][0]['value']
            
            result += (
                f"📆 {date}\n"
                f"  🌡 {min_temp}°C ~ {max_temp}°C\n"
                f"  🌤 {desc}\n\n"
            )
        
        await update.message.reply_text(result, parse_mode='Markdown')
    
    except Exception as e:
        await update.message.reply_text(f"查詢預報時發生錯誤: {str(e)}")
