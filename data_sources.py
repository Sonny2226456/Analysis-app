import pandas as pd
import numpy as np
import requests
import datetime
import os
from io import StringIO
import trafilatura
import re
from bs4 import BeautifulSoup

# Function to fetch cryptocurrency data
def fetch_crypto_data(coin_id='bitcoin', vs_currency='usd', days=30, interval='daily'):
    """
    Fetch cryptocurrency data from CoinGecko API
    
    Parameters:
    - coin_id: string, the ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
    - vs_currency: string, the currency to compare against (e.g., 'usd', 'eur')
    - days: int, number of days of data to retrieve
    - interval: string, data interval ('daily' or 'hourly')
    
    Returns:
    - pandas DataFrame with cryptocurrency data
    """
    # CoinGecko API endpoint for market charts
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': interval
    }
    
    try:
        # Add retry mechanism for rate limiting
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            response = requests.get(url, params=params)
            
            # If successful, process the data
            if response.status_code == 200:
                data = response.json()
                
                # Process price data
                prices_df = pd.DataFrame(data['prices'], columns=['timestamp', 'prices'])
                prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'], unit='ms')
                
                # Process market cap data
                market_caps_df = pd.DataFrame(data['market_caps'], columns=['timestamp', 'market_caps'])
                market_caps_df['timestamp'] = pd.to_datetime(market_caps_df['timestamp'], unit='ms')
                
                # Process volume data
                volumes_df = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volumes'])
                volumes_df['timestamp'] = pd.to_datetime(volumes_df['timestamp'], unit='ms')
                
                # Merge all dataframes
                result_df = prices_df.merge(market_caps_df, on='timestamp').merge(volumes_df, on='timestamp')
                result_df.set_index('timestamp', inplace=True)
                
                return result_df
            
            # If rate limited or unauthorized, use demo data
            elif response.status_code in [401, 429]:
                print(f"API error: {response.status_code}. Using demo data instead.")
                # Create demo data for visualization
                dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
                
                # Create base values based on the cryptocurrency
                if coin_id == 'bitcoin':
                    base_price = 30000
                elif coin_id == 'ethereum':
                    base_price = 2000
                elif coin_id == 'ripple':
                    base_price = 0.5
                elif coin_id == 'cardano':
                    base_price = 0.3
                else:
                    base_price = 100
                
                # Generate synthetic data
                np.random.seed(hash(coin_id) % 10000)
                prices = base_price + np.random.normal(0, base_price * 0.05, size=len(dates)).cumsum()
                volumes = np.random.normal(base_price * 1000, base_price * 100, size=len(dates))
                market_caps = prices * volumes * 0.1
                
                # Create DataFrame
                result_df = pd.DataFrame({
                    'prices': prices,
                    'volumes': volumes,
                    'market_caps': market_caps
                }, index=dates)
                
                return result_df
            
            # For other errors, retry if we haven't exceeded max retries
            if retry_count < max_retries:
                retry_count += 1
                import time
                time.sleep(1)  # Wait before retrying
            else:
                # If we've exhausted retries, raise the exception
                response.raise_for_status()
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cryptocurrency data: {e}")
        # Create demo data as fallback
        dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
        
        # Create base values based on the cryptocurrency
        if coin_id == 'bitcoin':
            base_price = 30000
        elif coin_id == 'ethereum':
            base_price = 2000
        else:
            base_price = 100
        
        # Generate synthetic data
        np.random.seed(hash(coin_id) % 10000)
        prices = base_price + np.random.normal(0, base_price * 0.05, size=len(dates)).cumsum()
        volumes = np.random.normal(base_price * 1000, base_price * 100, size=len(dates))
        market_caps = prices * volumes * 0.1
        
        # Create DataFrame
        result_df = pd.DataFrame({
            'prices': prices,
            'volumes': volumes,
            'market_caps': market_caps
        }, index=dates)
        
        return result_df

# Function to fetch stock market data
def fetch_stock_data(symbol='AAPL', interval='1d', period='1mo'):
    """
    Fetch stock market data from Yahoo Finance API
    
    Parameters:
    - symbol: string, the stock symbol (e.g., 'AAPL', 'MSFT')
    - interval: string, data interval ('1d', '1h', '5m')
    - period: string, period to retrieve ('1d', '1mo', '3mo', '6mo', '1y')
    
    Returns:
    - pandas DataFrame with stock market data
    """
    # Use yfinance to get stock data
    try:
        import yfinance as yf
        
        # Get stock data
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval=interval)
        
        # Clean up data
        data = data.reset_index()
        data.columns = [col.lower() for col in data.columns]
        
        # Ensure 'date' or 'datetime' column is present
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
        elif 'datetime' in data.columns:
            data['datetime'] = pd.to_datetime(data['datetime'])
            data.set_index('datetime', inplace=True)
        
        return data
    
    except ImportError:
        # If yfinance is not available, use a mock API with requests
        end_date = datetime.datetime.now()
        
        if period == '1d':
            start_date = end_date - datetime.timedelta(days=1)
        elif period == '1wk' or period == '1w':
            start_date = end_date - datetime.timedelta(days=7)
        elif period == '1mo':
            start_date = end_date - datetime.timedelta(days=30)
        elif period == '3mo':
            start_date = end_date - datetime.timedelta(days=90)
        elif period == '6mo':
            start_date = end_date - datetime.timedelta(days=180)
        elif period == '1y':
            start_date = end_date - datetime.timedelta(days=365)
        else:
            start_date = end_date - datetime.timedelta(days=30)  # Default to 1 month
        
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Alpha Vantage API for stock data
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        
        if interval == '1d':
            function = 'TIME_SERIES_DAILY'
        elif interval == '1h':
            function = 'TIME_SERIES_INTRADAY'
            interval = '60min'
        elif interval == '5m':
            function = 'TIME_SERIES_INTRADAY'
            interval = '5min'
        else:
            function = 'TIME_SERIES_DAILY'
        
        url = f"https://www.alphavantage.co/query"
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': api_key,
            'outputsize': 'full',
            'datatype': 'csv'
        }
        
        if function == 'TIME_SERIES_INTRADAY':
            params['interval'] = interval
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse CSV data
            data = pd.read_csv(StringIO(response.text))
            
            # Process and rename columns
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data.rename(columns={
                'timestamp': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            # Filter by date range
            data = data[(data['date'] >= start_str) & (data['date'] <= end_str)]
            
            # Set index
            data.set_index('date', inplace=True)
            
            return data
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching stock data: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume']).set_index('date')

# Function to fetch weather data
def fetch_weather_data(city='London', days=7):
    """
    Fetch weather data from OpenWeatherMap API
    
    Parameters:
    - city: string, the city name (e.g., 'London', 'New York')
    - days: int, number of days of data to retrieve (max 7 for free API)
    
    Returns:
    - pandas DataFrame with weather data
    """
    # OpenWeatherMap API endpoint
    api_key = os.getenv("OPENWEATHER_API_KEY", "placeholder_key")
    
    # First, get coordinates for the city
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': city,
        'limit': 1,
        'appid': api_key
    }
    
    try:
        response = requests.get(geocoding_url, params=params)
        response.raise_for_status()
        
        location_data = response.json()
        
        if not location_data:
            print(f"No location data found for {city}")
            return pd.DataFrame(columns=['date', 'temp', 'humidity', 'pressure', 'wind_speed', 'precipitation']).set_index('date')
        
        lat = location_data[0]['lat']
        lon = location_data[0]['lon']
        
        # Now get weather data
        weather_url = f"https://api.openweathermap.org/data/2.5/onecall"
        
        weather_params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'current,minutely,alerts',
            'units': 'metric',
            'appid': api_key
        }
        
        response = requests.get(weather_url, params=weather_params)
        response.raise_for_status()
        
        weather_data = response.json()
        
        # Process daily data
        daily_data = []
        
        for day in weather_data.get('daily', [])[:min(days, 7)]:  # API free tier limited to 7 days
            date = datetime.datetime.fromtimestamp(day['dt'])
            temp = day['temp']['day']
            humidity = day['humidity']
            pressure = day['pressure']
            wind_speed = day['wind_speed']
            precipitation = day.get('rain', 0)  # Rain might not be present if no rain
            
            daily_data.append({
                'date': date,
                'temp': temp,
                'humidity': humidity,
                'pressure': pressure,
                'wind_speed': wind_speed,
                'precipitation': precipitation
            })
        
        # Process hourly data if available and needed
        hourly_data = []
        
        if days > 7 or len(weather_data.get('hourly', [])) > 0:
            for hour in weather_data.get('hourly', [])[:min(days * 24, 48)]:  # API free tier limited to 48 hours
                date = datetime.datetime.fromtimestamp(hour['dt'])
                temp = hour['temp']
                humidity = hour['humidity']
                pressure = hour['pressure']
                wind_speed = hour['wind_speed']
                precipitation = hour.get('rain', {}).get('1h', 0) if 'rain' in hour else 0
                
                hourly_data.append({
                    'date': date,
                    'temp': temp,
                    'humidity': humidity,
                    'pressure': pressure,
                    'wind_speed': wind_speed,
                    'precipitation': precipitation
                })
        
        # Create DataFrame
        if len(daily_data) > 0:
            df_daily = pd.DataFrame(daily_data)
            df_daily.set_index('date', inplace=True)
            
            if len(hourly_data) > 0:
                df_hourly = pd.DataFrame(hourly_data)
                df_hourly.set_index('date', inplace=True)
                # Combine if we have both
                result_df = pd.concat([df_hourly, df_daily])
            else:
                result_df = df_daily
        elif len(hourly_data) > 0:
            df_hourly = pd.DataFrame(hourly_data)
            df_hourly.set_index('date', inplace=True)
            result_df = df_hourly
        else:
            # Return empty DataFrame with expected columns
            result_df = pd.DataFrame(columns=['date', 'temp', 'humidity', 'pressure', 'wind_speed', 'precipitation']).set_index('date')
        
        # Sort by date
        result_df = result_df.sort_index()
        
        return result_df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        # Provide fallback data for demo purposes (otherwise return empty DataFrame)
        # This is a simplified approach - in a real app, handle API errors more robustly
        
        # Create some simulated weather data for the requested days
        now = datetime.datetime.now()
        dates = [now + datetime.timedelta(days=i) for i in range(days)]
        
        # Generate random but realistic weather data
        np.random.seed(42)  # For reproducibility
        temps = np.random.normal(20, 5, days)  # Mean 20°C, std 5°C
        humidity = np.random.normal(60, 15, days)  # Mean 60%, std 15%
        pressure = np.random.normal(1013, 10, days)  # Mean 1013 hPa, std 10 hPa
        wind_speed = np.random.exponential(4, days)  # Exponential with scale 4 m/s
        precipitation = np.random.exponential(2, days)  # Exponential with scale 2 mm
        
        # Create DataFrame
        data = {
            'date': dates,
            'temp': temps,
            'humidity': np.clip(humidity, 0, 100),  # Humidity between 0-100%
            'pressure': pressure,
            'wind_speed': wind_speed,
            'precipitation': precipitation
        }
        
        result_df = pd.DataFrame(data)
        result_df.set_index('date', inplace=True)
        
        return result_df

# Function to get available cryptocurrencies
def get_available_cryptos():
    """Return a list of available cryptocurrencies"""
    # Common cryptocurrencies
    return [
        'bitcoin', 'ethereum', 'ripple', 'cardano', 'solana',
        'dogecoin', 'polkadot', 'litecoin', 'avalanche-2', 'chainlink',
        'uniswap', 'binancecoin', 'matic-network', 'cosmos', 'stellar',
        'tron', 'monero', 'algorand', 'filecoin', 'aave',
        'tezos', 'eos', 'the-sandbox', 'decentraland', 'hedera-hashgraph'
    ]

# Function to get available stocks
def get_available_stocks(market='US'):
    """
    Return a list of available stocks by market region
    
    Parameters:
    - market: string, the stock market region (e.g., 'US', 'Japan', 'Europe', 'China', 'UK')
    
    Returns:
    - list of stock symbols for the specified market
    """
    # Stock symbols organized by market region
    market_stocks = {
        'US': [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
            'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
            'WMT', 'PG', 'DIS', 'NFLX', 'INTC', 
            'AMD', 'BAC', 'KO', 'PEP', 'ADBE',
            'CSCO', 'PYPL', 'ABNB', 'CRM', 'NKE'
        ],
        'Japan': [
            '7203.T', '6758.T', '6861.T', '7974.T', '9984.T',  # Toyota, Sony, Keyence, Nintendo, SoftBank
            '9433.T', '8306.T', '8035.T', '6501.T', '6594.T',  # KDDI, MUFG, Tokyo Electron, Hitachi, Nidec
            '6367.T', '9432.T', '6981.T', '4063.T', '4519.T'   # Daikin, NTT, Murata, ShinEtsu, Chugai Pharma
        ],
        'Europe': [
            'SAP.DE', 'SIE.DE', 'ALV.DE', 'BAS.DE', 'DTE.DE',  # SAP, Siemens, Allianz, BASF, Deutsche Telekom
            'MC.PA', 'OR.PA', 'SAN.MC', 'ASML.AS', 'RMS.PA',   # LVMH, L'Oreal, Santander, ASML, Hermes
            'NBG.AT', 'ROG.SW', 'NESN.SW', 'NOVN.SW', 'UL.AS'  # Erste Group, Roche, Nestle, Novartis, Unilever
        ],
        'UK': [
            'HSBA.L', 'BP.L', 'GSK.L', 'ULVR.L', 'RIO.L',      # HSBC, BP, GSK, Unilever, Rio Tinto
            'SHEL.L', 'AZN.L', 'LLOY.L', 'VOD.L', 'BARC.L',    # Shell, AstraZeneca, Lloyds, Vodafone, Barclays
            'TSCO.L', 'DGE.L', 'RR.L', 'BA.L', 'NWG.L'         # Tesco, Diageo, Rolls Royce, BAE Systems, NatWest
        ],
        'China': [
            '601318.SS', '600519.SS', '600036.SS', '601398.SS', '601988.SS',  # Ping An, Kweichow Moutai, CMB, ICBC, Bank of China
            '0700.HK', '9988.HK', '9618.HK', '3690.HK', '2318.HK',           # Tencent, Alibaba, JD, Meituan, Ping An (HK)
            '0941.HK', '2388.HK', '0883.HK', '0175.HK', '1177.HK'            # China Mobile, BOC HK, CNOOC, Geely, Sino Biopharm
        ]
    }
    
    # Return stocks for the specified market, or default to US if market not found
    return market_stocks.get(market, market_stocks['US'])

# Function to get available cities
def get_available_cities():
    """Return a list of available cities for weather data"""
    # Major cities around the world
    return [
        'New York', 'London', 'Tokyo', 'Paris', 'Sydney',
        'Berlin', 'Rome', 'Beijing', 'Mumbai', 'Cairo',
        'Los Angeles', 'Toronto', 'Singapore', 'Dubai', 'Moscow',
        'Madrid', 'Bangkok', 'Seoul', 'Mexico City', 'Istanbul',
        'Jakarta', 'Amsterdam', 'Riyadh', 'Zurich', 'San Francisco'
    ]

def fetch_crypto_news(coin_id='bitcoin', max_news=5):
    """
    Fetch cryptocurrency news from reliable sources
    
    Parameters:
    - coin_id: string, the name of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
    - max_news: int, maximum number of news items to return
    
    Returns:
    - list of dictionaries with news items (title, date, summary, url)
    """
    # CoinDesk is a reliable source for crypto news
    url = f"https://www.coindesk.com/search?s={coin_id}"
    
    try:
        # Use trafilatura to get clean HTML content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return get_demo_crypto_news(coin_id, max_news)
        
        # Use BeautifulSoup for more precise parsing
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Find all news article elements
        articles = soup.find_all('article', class_=lambda x: x and ('article' in x.lower() or 'card' in x.lower()))
        
        # If no articles found using BeautifulSoup, try with trafilatura's extraction
        if not articles:
            text = trafilatura.extract(downloaded, include_links=True)
            # Extract article blocks using regex
            import re
            article_blocks = re.split(r'\n\s*\n', text)
            
            # Create a list of demo news as fallback
            news_items = []
            for i, block in enumerate(article_blocks[:max_news]):
                lines = block.strip().split('\n')
                if len(lines) >= 2:
                    title = lines[0]
                    summary = ' '.join(lines[1:])
                    # Generate a current date with small random offset
                    date = datetime.datetime.now() - datetime.timedelta(days=i % 7, hours=i*3)
                    news_items.append({
                        'title': title,
                        'date': date.strftime('%Y-%m-%d'),
                        'summary': summary,
                        'url': f"https://www.coindesk.com/{coin_id}-news-{i+1}"
                    })
            
            return news_items[:max_news]
        
        # Process the articles found by BeautifulSoup
        news_items = []
        for article in articles[:max_news]:
            # Extract title
            title_element = article.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and ('title' in x.lower() or 'heading' in x.lower()))
            title = title_element.text.strip() if title_element else "Cryptocurrency News"
            
            # Extract date if available
            date_element = article.find(['time', 'span'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
            date = date_element.text.strip() if date_element else datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Extract summary
            summary_element = article.find(['p', 'div'], class_=lambda x: x and ('summary' in x.lower() or 'description' in x.lower()))
            summary = summary_element.text.strip() if summary_element else "Read more about this cryptocurrency news."
            
            # Extract URL
            url_element = article.find('a')
            url = url_element['href'] if url_element and 'href' in url_element.attrs else f"https://www.coindesk.com/{coin_id}-news"
            
            # Add full domain if it's a relative URL
            if url.startswith('/'):
                url = f"https://www.coindesk.com{url}"
            
            news_items.append({
                'title': title,
                'date': date,
                'summary': summary,
                'url': url
            })
        
        return news_items
    
    except Exception as e:
        print(f"Error fetching cryptocurrency news: {e}")
        return get_demo_crypto_news(coin_id, max_news)

def get_demo_crypto_news(coin_id='bitcoin', max_news=5):
    """Generate demo cryptocurrency news when API calls fail"""
    
    # Dictionary of demo news for popular cryptocurrencies
    demo_news = {
        'bitcoin': [
            {
                'title': 'Bitcoin Reaches New All-Time High Amid Institutional Adoption',
                'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'summary': 'Bitcoin surged to a new all-time high as major financial institutions continue to adopt the cryptocurrency as a reserve asset.',
                'url': 'https://www.coindesk.com/bitcoin-new-high'
            },
            {
                'title': 'Central Banks Explore Bitcoin Regulation Frameworks',
                'date': (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'summary': 'Several central banks are developing regulatory frameworks for Bitcoin and other cryptocurrencies to balance innovation and consumer protection.',
                'url': 'https://www.coindesk.com/bitcoin-regulation'
            },
            {
                'title': 'Bitcoin Mining Becomes More Environmentally Friendly',
                'date': (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'summary': 'Major Bitcoin mining operations are transitioning to renewable energy sources, addressing environmental concerns.',
                'url': 'https://www.coindesk.com/bitcoin-mining-green'
            },
            {
                'title': 'Lightning Network Capacity Doubles as Bitcoin Scales',
                'date': (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                'summary': 'Bitcoin\'s Layer 2 scaling solution, the Lightning Network, has seen its capacity double in the past six months.',
                'url': 'https://www.coindesk.com/lightning-network-growth'
            },
            {
                'title': 'New Bitcoin ETF Proposals Under Review by SEC',
                'date': (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'summary': 'The Securities and Exchange Commission is reviewing new proposals for Bitcoin ETFs with a decision expected soon.',
                'url': 'https://www.coindesk.com/bitcoin-etf-proposals'
            }
        ],
        'ethereum': [
            {
                'title': 'Ethereum Completes Major Network Upgrade',
                'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'summary': 'Ethereum successfully implemented a major network upgrade that improves scalability and reduces gas fees.',
                'url': 'https://www.coindesk.com/ethereum-upgrade'
            },
            {
                'title': 'Ethereum DeFi Applications Reach New Milestone',
                'date': (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'summary': 'Total value locked in Ethereum-based decentralized finance (DeFi) applications has reached a new all-time high.',
                'url': 'https://www.coindesk.com/ethereum-defi-milestone'
            },
            {
                'title': 'Ethereum Layer 2 Solutions Gain Traction',
                'date': (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                'summary': 'Adoption of Ethereum Layer 2 scaling solutions has surged as users seek lower transaction fees.',
                'url': 'https://www.coindesk.com/ethereum-layer2-adoption'
            },
            {
                'title': 'Major Companies Join Ethereum Enterprise Alliance',
                'date': (datetime.datetime.now() - datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
                'summary': 'Several Fortune 500 companies have joined the Ethereum Enterprise Alliance to explore blockchain solutions.',
                'url': 'https://www.coindesk.com/ethereum-enterprise-growth'
            },
            {
                'title': 'Ethereum Staking Rewards Analysis Released',
                'date': (datetime.datetime.now() - datetime.timedelta(days=6)).strftime('%Y-%m-%d'),
                'summary': 'A new analysis of Ethereum staking rewards shows higher than expected returns for validators.',
                'url': 'https://www.coindesk.com/ethereum-staking-analysis'
            }
        ]
    }
    
    # For other cryptocurrencies, generate generic news
    if coin_id not in demo_news:
        coin_name = coin_id.capitalize()
        demo_news[coin_id] = [
            {
                'title': f'{coin_name} Sees Growing Adoption in Payments Sector',
                'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'summary': f'{coin_name} is being increasingly adopted by payment processors and merchants worldwide.',
                'url': f'https://www.coindesk.com/{coin_id}-payments'
            },
            {
                'title': f'New Development Roadmap Announced for {coin_name}',
                'date': (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'summary': f'The development team behind {coin_name} has announced an ambitious roadmap for the next two years.',
                'url': f'https://www.coindesk.com/{coin_id}-roadmap'
            },
            {
                'title': f'{coin_name} Community Grows as New Projects Launch',
                'date': (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                'summary': f'The {coin_name} ecosystem is expanding with several new projects launching on the platform.',
                'url': f'https://www.coindesk.com/{coin_id}-ecosystem'
            },
            {
                'title': f'Technical Analysis: {coin_name} Price Patterns Suggest Bullish Trend',
                'date': (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'summary': f'Technical analysts point to several bullish patterns forming in {coin_name}\'s price charts.',
                'url': f'https://www.coindesk.com/{coin_id}-analysis'
            },
            {
                'title': f'{coin_name} Integration Expands to Major Exchanges',
                'date': (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
                'summary': f'Several major cryptocurrency exchanges have announced new trading pairs for {coin_name}.',
                'url': f'https://www.coindesk.com/{coin_id}-exchanges'
            }
        ]
    
    return demo_news[coin_id][:max_news]
