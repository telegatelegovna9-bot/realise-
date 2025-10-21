import aiohttp
import pandas as pd
from monitor.logger import log

BINANCE_FAPI = "https://fapi.binance.com/fapi/v1"

async def get_all_futures_tickers():
    try:
        url = f"{BINANCE_FAPI}/ticker/24hr"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    log(f"Ошибка получения тикеров: HTTP {resp.status}, Ответ: {await resp.text()}", level="error")
                    return []
                data = await resp.json()
                if not data or not isinstance(data, list):
                    log(f"Ошибка: данные тикеров не являются списком или пусты: {data}", level="error")
                    return []
            
            from monitor.settings import load_config
            config = load_config()
            volume_filter = config.get('volume_filter', 5_000_000.0)
            tickers = []
            failed_reasons = {'volume': 0, 'usdt': 0}

            for item in data:
                if not isinstance(item, dict):
                    continue
                symbol = item.get('symbol', '')
                quote_volume = float(item.get('quoteVolume', 0))

                if not symbol.endswith('USDT'):
                    failed_reasons['usdt'] += 1
                    continue
                if quote_volume < volume_filter:
                    failed_reasons['volume'] += 1
                    continue

                tickers.append(symbol)

            log(f"Всего тикеров: {len(data)}, после фильтра по объёму ({volume_filter}): {len(tickers)}", level="info")
            log(f"Причины исключения тикеров: {failed_reasons}", level="info")
            return tickers
    except Exception as e:
        log(f"Ошибка получения тикеров: {str(e)}", level="error")
        return []

async def validate_symbol(symbol):
    """Проверяет, существует ли символ на Binance Futures."""
    try:
        url = f"{BINANCE_FAPI}/exchangeInfo"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    log(f"Ошибка проверки символа {symbol}: HTTP {resp.status}, Ответ: {await resp.text()}", level="error")
                    return False
                data = await resp.json()
                symbols = [s['symbol'] for s in data.get('symbols', [])]
                return symbol in symbols
    except Exception as e:
        log(f"Ошибка проверки символа {symbol}: {str(e)}", level="error")
        return False

async def fetch_ohlcv_binance(symbol, timeframe='1m', limit=200):
    if not await validate_symbol(symbol):
        log(f"Символ {symbol} не найден в exchangeInfo", level="warning")
        return pd.DataFrame()

    interval_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h'}
    interval = interval_map.get(timeframe, '1m')
    url = f"{BINANCE_FAPI}/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    response_text = await resp.text()
                    log(f"Ошибка получения OHLCV для {symbol}: HTTP {resp.status}, Ответ: {response_text}, URL: {url}, Params: {params}", level="error")
                    return pd.DataFrame()
                data = await resp.json()
                if not data:
                    response_text = await resp.text()
                    log(f"{symbol} - данные OHLCV пусты. HTTP {resp.status}, Ответ: {response_text}, URL: {url}, Params: {params}", level="warning")
                    return pd.DataFrame()
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                                'close_time', 'quote_asset_volume', 'num_trades',
                                                'taker_buy_base', 'taker_buy_quote', 'ignore'])
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                log(f"Получено {len(df)} свечей для {symbol}", level="info")
                return df
    except Exception as e:
        log(f"Ошибка получения OHLCV для {symbol}: {str(e)}, URL: {url}, Params: {params}", level="error")
        return pd.DataFrame()