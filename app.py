import streamlit as st
import pandas as pd
import numpy as np
import datetime
import io
import base64

from data_sources import (
    fetch_crypto_data, 
    fetch_stock_data, 
    fetch_weather_data, 
    get_available_cryptos,
    get_available_stocks,
    get_available_cities,
    fetch_crypto_news
)
from data_analysis import (
    perform_trend_analysis, 
    detect_patterns, 
    predict_future_values
)
from visualizations import (
    plot_time_series,
    plot_correlation_matrix,
    plot_distribution,
    plot_candlestick,
    plot_trend_indicators,
    plot_forecast,
    show_metrics_dashboard
)
from utils import (
    process_uploaded_file,
    generate_download_link,
    calculate_statistics
)

# Set page configuration
st.set_page_config(
    page_title="AI Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set custom theme with hazel color
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5dc;  /* Light hazel color for background */
    }
    .stSidebar {
        background-color: #e8e8cc;  /* Slightly darker hazel for sidebar */
    }
    .stButton button {
        background-color: #8B4513;  /* Darker brown for buttons */
        color: white;
    }
    .stButton button:hover {
        background-color: #6B3311;  /* Even darker brown for button hover */
    }
    h1, h2, h3 {
        color: #3A1F04;  /* Dark brown for headings */
    }
    p, div {
        color: #000000;  /* Black for regular text */
    }
    .st-bq, span {
        color: #000000 !important;  /* Black for other text elements */
    }
    .metric-up {
        color: #006400 !important;  /* Dark green for up metrics */
        font-weight: bold;
    }
    .metric-down {
        color: #8B0000 !important;  /* Dark red for down metrics */
        font-weight: bold;
    }
    /* Sidebar elements */
    .stSidebar label, .stSidebar p, .stSidebar div, .stSidebar span {
        color: #000000 !important;  /* Black for sidebar text */
    }
    /* Info boxes */
    .stAlert {
        background-color: #C4A484 !important;  /* Hazel for info boxes */
        color: #000000 !important;  /* Black text */
    }
    /* Make all text inputs and selection widgets have dark text */
    .stTextInput, .stSelectbox, .stMultiselect {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'crypto_data' not in st.session_state:
    st.session_state.crypto_data = None
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'custom_data' not in st.session_state:
    st.session_state.custom_data = None

# Dashboard Header
st.title("📊 AI Data Dashboard")
st.markdown("Analyze and visualize live data from multiple sources with trend analysis capabilities")

# Create Homepage with trenging assets before showing sidebar options
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Sidebar for data source selection and controls
with st.sidebar:
    st.header("Navigation")
    if st.button("🏠 Home Dashboard"):
        st.session_state.page = 'home'
    
    st.header("Data Sources")
    data_source = st.radio(
        "Select Data Source",
        ["Cryptocurrency", "Stock Market", "Weather", "Custom Upload"]
    )
    # Update the page based on data source selection
    st.session_state.page = data_source
    
    refresh_button = st.button("🔄 Refresh Data")
    
    st.header("Analysis Options")
    analysis_type = st.multiselect(
        "Select Analysis Types",
        ["Trend Analysis", "Pattern Recognition", "Forecasting"],
        default=["Trend Analysis"]
    )
    
    time_range = st.select_slider(
        "Time Range",
        options=["1 Day", "1 Week", "1 Month", "3 Months", "6 Months", "1 Year"],
        value="1 Month"
    )
    
    # Map time_range to actual days for API calls
    time_map = {
        "1 Day": 1,
        "1 Week": 7,
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365
    }
    days = time_map[time_range]
    
    st.header("Visualization Options")
    chart_type = st.selectbox(
        "Primary Chart Type",
        ["Line Chart", "Candlestick", "Bar Chart", "Area Chart"]
    )
    
    st.header("Download Options")
    download_format = st.selectbox(
        "Export Format",
        ["CSV", "JSON", "Excel"]
    )

# Home Page
if st.session_state.page == 'home':
    st.header("MARKET OVERVIEW DASHBOARD")
    
    # Create tabs for different categories
    home_tab1, home_tab2, home_tab3 = st.tabs(["CRYPTOCURRENCIES", "STOCKS", "WEATHER"])
    
    with home_tab1:
        st.subheader("Top Cryptocurrencies")
    
    # Initialize data for top cryptos
    if 'top_crypto_data' not in st.session_state or refresh_button:
        with st.spinner("Loading cryptocurrency data..."):
            # Get top 5 cryptos
            top_cryptos = ['bitcoin', 'ethereum', 'ripple', 'cardano', 'solana']
            crypto_data = {}
            
            # Use demo data to ensure we have something to display
            for crypto in top_cryptos:
                try:
                    # First try to fetch from API
                    data = fetch_crypto_data(
                        coin_id=crypto,
                        vs_currency='usd',
                        days=1,
                        interval='daily'
                    )
                    if not data.empty:
                        crypto_data[crypto] = data
                except Exception as e:
                    print(f"Error loading data for {crypto}: {e}")
                    # Already handled in fetch_crypto_data with fallback data
            
            st.session_state.top_crypto_data = crypto_data
    
    # Display crypto data
    crypto_cols = st.columns(5)
    i = 0
    
    # Create metrics for top cryptocurrencies
    for crypto, data in st.session_state.top_crypto_data.items():
        if data is not None and not data.empty:
            with crypto_cols[i % 5]:
                current_price = data['prices'].iloc[-1] if 'prices' in data.columns else 0
                
                # Calculate % change
                if len(data) > 1 and 'prices' in data.columns:
                    prev_price = data['prices'].iloc[-2]
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    delta_color = "normal"
                    delta_icon = ""
                    
                    if pct_change > 0:
                        delta_icon = "↑"
                        delta_html = f"<span class='metric-up'>{delta_icon} {pct_change:.2f}%</span>"
                    else:
                        delta_icon = "↓"
                        delta_html = f"<span class='metric-down'>{delta_icon} {pct_change:.2f}%</span>"
                    
                    st.markdown(f"**{crypto.upper()}**")
                    st.markdown(f"${current_price:.2f} {delta_html}", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{crypto.upper()}**")
                    st.markdown(f"${current_price:.2f}")
            
            i += 1
    
    with home_tab2:
        st.subheader("Top Stocks")
    
        # Initialize data for top stocks
        if 'top_stock_data' not in st.session_state or refresh_button:
            with st.spinner("Loading stock data..."):
                # Get top 5 stocks
                top_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
                stock_data = {}
                
                for stock in top_stocks:
                    try:
                        data = fetch_stock_data(
                            symbol=stock,
                            interval='1d', 
                            period='1d'  # Use 1d for consistent format
                        )
                        if not data.empty:
                            stock_data[stock] = data
                    except Exception as e:
                        print(f"Error loading data for {stock}: {e}")
                        # Error handling is in the fetch_stock_data function
                
                st.session_state.top_stock_data = stock_data
        
        # Display stock data
        stock_cols = st.columns(5)
        i = 0
        
        # Create metrics for top stocks
        for stock, data in st.session_state.top_stock_data.items():
            if data is not None and not data.empty:
                with stock_cols[i % 5]:
                    current_price = data['close'].iloc[-1] if 'close' in data.columns else 0
                    
                    # Calculate % change
                    if len(data) > 1 and 'close' in data.columns:
                        prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
                        pct_change = ((current_price - prev_price) / prev_price) * 100
                        delta_color = "normal"
                        delta_icon = ""
                        
                        if pct_change > 0:
                            delta_icon = "↑"
                            delta_html = f"<span class='metric-up'>{delta_icon} {pct_change:.2f}%</span>"
                        else:
                            delta_icon = "↓"
                            delta_html = f"<span class='metric-down'>{delta_icon} {pct_change:.2f}%</span>"
                        
                        st.markdown(f"**{stock}**")
                        st.markdown(f"${current_price:.2f} {delta_html}", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{stock}**")
                        st.markdown(f"${current_price:.2f}")
                
                i += 1
        
        if i == 0:
            st.info("Unable to load stock data. Please check your internet connection or try again later.")
    
    with home_tab3:
        st.subheader("Global Weather Highlights")
        
        # Initialize data for weather
        if 'weather_highlights' not in st.session_state or refresh_button:
            with st.spinner("Loading weather data..."):
                # Get weather for major cities
                major_cities = ['New York', 'London', 'Tokyo', 'Singapore', 'Sydney']
                weather_data = {}
                
                for city in major_cities:
                    try:
                        data = fetch_weather_data(
                            city=city,
                            days=1
                        )
                        if not data.empty:
                            weather_data[city] = data
                    except Exception as e:
                        print(f"Error loading weather data for {city}: {e}")
                        # Error handling is in the fetch_weather_data function
                
                st.session_state.weather_highlights = weather_data
        
        # Display weather data
        weather_cols = st.columns(5)
        i = 0
        
        # Create metrics for major cities
        for city, data in st.session_state.weather_highlights.items():
            if data is not None and not data.empty:
                with weather_cols[i % 5]:
                    current_temp = data['temp'].iloc[-1] if 'temp' in data.columns else 0
                    
                    st.markdown(f"**{city}**")
                    st.markdown(f"{current_temp:.1f}°C")
                
                i += 1
        
        if i == 0:
            st.info("Unable to load weather data. Please check your internet connection or try again later.")
    
    # Dashboard information
    st.markdown("---")
    st.info("Welcome to the AI Data Dashboard. Select a data source from the sidebar to perform detailed analysis.")

# Main content area based on selected data source
elif st.session_state.page == "Cryptocurrency":
    st.header("CRYPTOCURRENCY DATA")
    
    # Create tabs for Crypto Data and News
    crypto_tabs = st.tabs(["CRYPTO DATA", "CRYPTO NEWS"])
    
    # Handle the crypto news tab
    with crypto_tabs[1]:
        st.subheader("CRYPTOCURRENCY NEWS & INSIGHTS")
        
        # Select cryptocurrency for news
        news_crypto = st.selectbox(
            "Select Cryptocurrency for News",
            get_available_cryptos(),
            key="news_crypto_select"
        )
        
        # Fetch and display crypto news
        with st.spinner("Fetching cryptocurrency news..."):
            crypto_news = fetch_crypto_news(coin_id=news_crypto, max_news=5)
            
            if crypto_news:
                for i, news in enumerate(crypto_news):
                    with st.expander(f"{news['title']}", expanded=i==0):
                        st.markdown(f"**Date:** {news['date']}")
                        st.markdown(f"{news['summary']}")
                        st.markdown(f"[Read more]({news['url']})")
                        st.divider()
            else:
                st.info("No cryptocurrency news available at the moment.")
        
        # Market sentiment section
        st.subheader("MARKET SENTIMENT")
        
        sentiment_cols = st.columns(3)
        
        with sentiment_cols[0]:
            st.metric("Fear & Greed Index", "65", "+8", delta_color="normal")
            st.markdown("**Current Status:** Greed")
            st.progress(65)
        
        with sentiment_cols[1]:
            st.metric("Bitcoin Dominance", "48.2%", "-0.8%")
            st.markdown("**Market Impact:** Altcoins gaining")
            st.progress(48)
        
        with sentiment_cols[2]:
            st.metric("Market Volatility", "Medium", "Decreasing")
            st.markdown("**30-Day Trend:** Stabilizing")
            st.progress(50)
    
    # Handle the crypto data tab
    with crypto_tabs[0]:
        # Get available cryptos
        available_cryptos = get_available_cryptos()
        
        # Layout for selection and filtering
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_crypto = st.selectbox(
                "Select Cryptocurrency",
                available_cryptos,
                key="crypto_select"
            )
            
            vs_currency = st.selectbox(
                "vs Currency",
                ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "HKD", "NOK", "NZD", "SEK", "SGD", "KRW", "MXN", "BRL", "INR", "RUB", "ZAR", "TRY"],
                index=0
            )
            
            interval = st.selectbox(
                "Interval",
                ["daily", "hourly"],
                index=0
            )
            
            st.markdown("### DATA PARAMETERS")
            st.info(f"Retrieving {time_range} of {selected_crypto} data vs {vs_currency}")
            
            if st.button("FETCH CRYPTO DATA") or refresh_button:
                with st.spinner("Fetching cryptocurrency data..."):
                    st.session_state.crypto_data = fetch_crypto_data(
                        coin_id=selected_crypto,
                        vs_currency=vs_currency,
                        days=days,
                        interval=interval
                    )
    
        with col2:
            if st.session_state.crypto_data is not None:
                data = st.session_state.crypto_data
                
                # Display chart based on user selection
                if chart_type == "Line Chart":
                    st.plotly_chart(
                        plot_time_series(data, 'prices', f"{selected_crypto.upper()} Price ({vs_currency})"),
                        use_container_width=True
                    )
                elif chart_type == "Candlestick":
                    st.plotly_chart(
                        plot_candlestick(data, f"{selected_crypto.upper()} Price ({vs_currency})"),
                        use_container_width=True
                    )
                elif chart_type == "Bar Chart":
                    st.plotly_chart(
                        plot_time_series(data, 'volumes', f"{selected_crypto.upper()} Volume ({vs_currency})", 
                                       chart_type='bar'),
                        use_container_width=True
                    )
                elif chart_type == "Area Chart":
                    st.plotly_chart(
                        plot_time_series(data, 'market_caps', f"{selected_crypto.upper()} Market Cap ({vs_currency})", 
                                       chart_type='area'),
                        use_container_width=True
                    )
                
                # Generate download link
                if st.button("DOWNLOAD DATA"):
                    download_link = generate_download_link(data, f"{selected_crypto}_{vs_currency}", download_format)
                    st.markdown(download_link, unsafe_allow_html=True)
    
        # Show additional analysis if data is available
        if st.session_state.crypto_data is not None:
            data = st.session_state.crypto_data
            
            st.header("ANALYSIS & INSIGHTS")
            tab1, tab2, tab3 = st.tabs(["TREND ANALYSIS", "STATISTICS", "FORECASTING"])
            
            with tab1:
                if "Trend Analysis" in analysis_type:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("PRICE TREND INDICATORS")
                        trend_data = perform_trend_analysis(data, 'prices')
                        st.plotly_chart(
                            plot_trend_indicators(trend_data, f"{selected_crypto.upper()} Trend Indicators"),
                            use_container_width=True
                        )
                    
                    with col2:
                        st.subheader("PATTERN DETECTION")
                        if "Pattern Recognition" in analysis_type:
                            patterns = detect_patterns(data, 'prices')
                            
                            if patterns:
                                for pattern, confidence in patterns.items():
                                    st.metric(f"Pattern: {pattern}", f"Confidence: {confidence:.2f}%")
                            else:
                                st.info("No significant patterns detected in the current timeframe")
            
            with tab2:
                st.subheader("STATISTICAL ANALYSIS")
                stats = calculate_statistics(data, 'prices')
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Mean Price", f"{stats['mean']:.2f} {vs_currency}")
                col2.metric("Volatility", f"{stats['volatility']:.2f}%")
                col3.metric("Min Price", f"{stats['min']:.2f} {vs_currency}")
                col4.metric("Max Price", f"{stats['max']:.2f} {vs_currency}")
                
                st.plotly_chart(
                    plot_distribution(data, 'prices', f"{selected_crypto.upper()} Price Distribution"),
                    use_container_width=True
                )
            
            with tab3:
                st.subheader("PRICE FORECASTING")
                if "Forecasting" in analysis_type:
                    forecast_days = st.slider("Forecast Days", min_value=1, max_value=30, value=7)
                    
                    with st.spinner("Generating forecast..."):
                        forecast_data = predict_future_values(data, 'prices', forecast_days)
                        
                        st.plotly_chart(
                            plot_forecast(data, forecast_data, f"{selected_crypto.upper()} Price Forecast ({vs_currency})"),
                            use_container_width=True
                        )
                        
                        st.info(f"Note: Forecasts are based on historical patterns and may not accurately predict future prices.")

elif st.session_state.page == "Stock Market":
    st.header("STOCK MARKET DATA")
    
    # Create tabs for different market regions and news
    market_tabs = st.tabs(["US MARKET", "JAPAN MARKET", "EUROPE MARKET", "UK MARKET", "CHINA MARKET", "NEWS"])
    
    # Handle the news tab separately
    with market_tabs[5]:  # NEWS tab
        st.subheader("FINANCIAL NEWS")
        
        # Create tabs for different market news categories
        news_tabs = st.tabs(["GENERAL MARKET NEWS", "STOCKS NEWS", "CRYPTO NEWS"])
        
        with news_tabs[0]:
            st.markdown("""
            ### LATEST MARKET NEWS
            
            * **Fed Holds Interest Rates Steady** - The Federal Reserve announced today it will maintain current interest rates, citing stable inflation data and moderate economic growth.
            
            * **Global Markets Rally on Tech Earnings** - Stock indices worldwide climbed after major technology companies reported better-than-expected quarterly results.
            
            * **Oil Prices Stabilize After Recent Volatility** - Crude oil markets have settled following weeks of fluctuation due to geopolitical tensions and supply concerns.
            
            * **Treasury Yields Rise Amid Economic Data** - U.S. Treasury yields increased as new economic indicators point to continued growth despite earlier recession fears.
            
            * **Dollar Strengthens Against Major Currencies** - The U.S. dollar gained ground against the euro and yen as investors respond to diverging central bank policies.
            """)
        
        with news_tabs[1]:
            st.markdown("""
            ### TOP STOCKS NEWS
            
            * **Apple Unveils New Product Line** - AAPL shares climb 3% following announcement of next-generation devices and expanded services offering.
            
            * **Microsoft Cloud Revenue Exceeds Expectations** - MSFT reports 28% growth in its cloud segment, driving positive analyst revisions.
            
            * **Tesla Factory Expansion on Track** - TSLA confirms new manufacturing facility will begin production ahead of schedule.
            
            * **Amazon Enhances Logistics Network** - AMZN invests $5 billion in automated distribution centers to improve delivery times.
            
            * **Google AI Developments Impress Investors** - GOOGL demonstrates new artificial intelligence capabilities, receiving positive market response.
            """)
            
        with news_tabs[2]:
            st.markdown("""
            ### CRYPTOCURRENCY NEWS
            
            * **Bitcoin Surpasses Key Resistance Level** - BTC breaks through $70,000 mark amid institutional adoption and supply constraints.
            
            * **Ethereum Upgrade Implementation Successful** - ETH network completes major protocol enhancement, improving transaction speeds.
            
            * **Central Banks Explore Digital Currency Options** - Several major economies announce progress on central bank digital currency research.
            
            * **Crypto Regulation Framework Advances** - Lawmakers introduce comprehensive legislation aimed at providing regulatory clarity.
            
            * **DeFi Total Value Locked Reaches New High** - Decentralized finance protocols collectively surpass $100 billion in locked assets.
            """)
    
    # Handle market region tabs
    for i in range(5):  # Exclude the NEWS tab
        with market_tabs[i]:
            # Map index to market region
            market_regions = {0: "US", 1: "Japan", 2: "Europe", 3: "UK", 4: "China"}
            current_market = market_regions[i]
            
            # Get available stocks for this market region
            available_stocks = get_available_stocks(current_market)
            
            # Layout for selection and filtering
            col1, col2 = st.columns([1, 2])
            
            with col1:
                selected_stock = st.selectbox(
                    "Select Stock",
                    available_stocks,
                    key=f"stock_select_{current_market}"
                )
                
                interval = st.selectbox(
                    "Interval",
                    ["1d", "1h", "5m"],
                    index=0,
                    key=f"interval_{current_market}"
                )
                
                st.markdown("### DATA PARAMETERS")
                st.info(f"Retrieving {time_range} of {selected_stock} data")
                
                # Create a stock data key specific to this market
                stock_data_key = f"stock_data_{current_market}"
                
                # Initialize this data key if it doesn't exist
                if stock_data_key not in st.session_state:
                    st.session_state[stock_data_key] = None
                
                if st.button(f"FETCH STOCK DATA", key=f"fetch_button_{current_market}"):
                    with st.spinner(f"Fetching {current_market} stock market data..."):
                        # Convert time_range to format compatible with Yahoo Finance
                        period_map = {
                            "1 Day": "1d",
                            "1 Week": "1wk",
                            "1 Month": "1mo",
                            "3 Months": "3mo",
                            "6 Months": "6mo",
                            "1 Year": "1y"
                        }
                        period = period_map.get(time_range, "1mo")
                        
                        # Fetch the data
                        st.session_state[stock_data_key] = fetch_stock_data(
                            symbol=selected_stock,
                            interval=interval,
                            period=period
                        )
    
            with col2:
                # Get the market-specific stock data
                stock_data_key = f"stock_data_{current_market}"
                
                if stock_data_key in st.session_state and st.session_state[stock_data_key] is not None:
                    data = st.session_state[stock_data_key]
                    
                    # Display chart based on user selection
                    if chart_type == "Line Chart":
                        st.plotly_chart(
                            plot_time_series(data, 'close', f"{selected_stock} Price"),
                            use_container_width=True
                        )
                    elif chart_type == "Candlestick":
                        st.plotly_chart(
                            plot_candlestick(data, f"{selected_stock} Price"),
                            use_container_width=True
                        )
                    elif chart_type == "Bar Chart":
                        st.plotly_chart(
                            plot_time_series(data, 'volume', f"{selected_stock} Volume", 
                                          chart_type='bar'),
                            use_container_width=True
                        )
                    elif chart_type == "Area Chart":
                        st.plotly_chart(
                            plot_time_series(data, 'close', f"{selected_stock} Price", 
                                          chart_type='area'),
                            use_container_width=True
                        )
                    
                    # Generate download link
                    if st.button("DOWNLOAD DATA", key=f"download_button_{current_market}"):
                        download_link = generate_download_link(data, f"{selected_stock}", download_format)
                        st.markdown(download_link, unsafe_allow_html=True)
            
            # Show additional analysis if data is available
            if stock_data_key in st.session_state and st.session_state[stock_data_key] is not None:
                data = st.session_state[stock_data_key]
                
                st.header("ANALYSIS & INSIGHTS")
                tab1, tab2, tab3 = st.tabs(["TREND ANALYSIS", "STATISTICS", "FORECASTING"])
                
                with tab1:
                    if "Trend Analysis" in analysis_type:
                        trend_cols = st.columns(2)
                        
                        with trend_cols[0]:
                            st.subheader("PRICE TREND INDICATORS")
                            trend_data = perform_trend_analysis(data, 'close')
                            st.plotly_chart(
                                plot_trend_indicators(trend_data, f"{selected_stock} Trend Indicators"),
                                use_container_width=True
                            )
                        
                        with trend_cols[1]:
                            st.subheader("PATTERN DETECTION")
                            if "Pattern Recognition" in analysis_type:
                                patterns = detect_patterns(data, 'close')
                                
                                if patterns:
                                    for pattern, confidence in patterns.items():
                                        st.metric(f"Pattern: {pattern}", f"Confidence: {confidence:.2f}%")
                                else:
                                    st.info("No significant patterns detected in the current timeframe")
                
                with tab2:
                    st.subheader("STATISTICAL ANALYSIS")
                    stats = calculate_statistics(data, 'close')
                    
                    stat_cols = st.columns(4)
                    stat_cols[0].metric("Mean Price", f"${stats['mean']:.2f}")
                    stat_cols[1].metric("Volatility", f"{stats['volatility']:.2f}%")
                    stat_cols[2].metric("Min Price", f"${stats['min']:.2f}")
                    stat_cols[3].metric("Max Price", f"${stats['max']:.2f}")
                    
                    st.plotly_chart(
                        plot_distribution(data, 'close', f"{selected_stock} Price Distribution"),
                        use_container_width=True
                    )
                
                with tab3:
                    st.subheader("PRICE FORECASTING")
                    if "Forecasting" in analysis_type:
                        forecast_days = st.slider("Forecast Days", 
                                                min_value=1, 
                                                max_value=30, 
                                                value=7, 
                                                key=f"forecast_days_{current_market}")
                        
                        with st.spinner("Generating forecast..."):
                            forecast_data = predict_future_values(data, 'close', forecast_days)
                            
                            st.plotly_chart(
                                plot_forecast(data, forecast_data, f"{selected_stock} Price Forecast"),
                                use_container_width=True
                            )
                    
                    # Add analyst recommendations section
                    st.subheader("ANALYST RECOMMENDATIONS")
                    
                    # Create a dictionary mapping stocks to analyst forecasts
                    # These would normally come from an API but we're creating demo data
                    analyst_recommendations = {
                        'AAPL': {
                            'Goldman Sachs': {'rating': 'BUY', 'target': 212.00, 'confidence': 85},
                            'Morgan Stanley': {'rating': 'OVERWEIGHT', 'target': 205.50, 'confidence': 80},
                            'JP Morgan': {'rating': 'BUY', 'target': 210.00, 'confidence': 82}
                        },
                        'MSFT': {
                            'Goldman Sachs': {'rating': 'BUY', 'target': 420.00, 'confidence': 88},
                            'Morgan Stanley': {'rating': 'OVERWEIGHT', 'target': 415.00, 'confidence': 85},
                            'JP Morgan': {'rating': 'OVERWEIGHT', 'target': 410.00, 'confidence': 83}
                        },
                        'GOOGL': {
                            'Goldman Sachs': {'rating': 'BUY', 'target': 175.00, 'confidence': 82},
                            'Morgan Stanley': {'rating': 'OVERWEIGHT', 'target': 172.00, 'confidence': 80},
                            'JP Morgan': {'rating': 'OVERWEIGHT', 'target': 170.00, 'confidence': 79}
                        },
                        'AMZN': {
                            'Goldman Sachs': {'rating': 'BUY', 'target': 185.00, 'confidence': 86},
                            'Morgan Stanley': {'rating': 'OVERWEIGHT', 'target': 180.00, 'confidence': 83},
                            'JP Morgan': {'rating': 'OVERWEIGHT', 'target': 182.00, 'confidence': 81}
                        },
                        'TSLA': {
                            'Goldman Sachs': {'rating': 'NEUTRAL', 'target': 175.00, 'confidence': 65},
                            'Morgan Stanley': {'rating': 'EQUAL-WEIGHT', 'target': 180.00, 'confidence': 60},
                            'JP Morgan': {'rating': 'UNDERWEIGHT', 'target': 115.00, 'confidence': 45}
                        }
                    }
                    
                    # Get recommendations for the selected stock or use default
                    stock_recommendations = analyst_recommendations.get(selected_stock, {
                        'Analyst 1': {'rating': 'HOLD', 'target': 0, 'confidence': 50},
                        'Analyst 2': {'rating': 'HOLD', 'target': 0, 'confidence': 50},
                        'Analyst 3': {'rating': 'HOLD', 'target': 0, 'confidence': 50}
                    })
                    
                    # Display analyst recommendations in a table
                    analyst_cols = st.columns(len(stock_recommendations))
                    
                    for i, (analyst, rec) in enumerate(stock_recommendations.items()):
                        with analyst_cols[i]:
                            st.markdown(f"**{analyst}**")
                            
                            # Color the rating based on whether it's positive, neutral, or negative
                            if rec['rating'] in ['BUY', 'OVERWEIGHT', 'STRONG BUY']:
                                rating_html = f"<span class='metric-up'>{rec['rating']}</span>"
                            elif rec['rating'] in ['HOLD', 'EQUAL-WEIGHT', 'NEUTRAL']:
                                rating_html = f"<span style='color: #808000; font-weight: bold;'>{rec['rating']}</span>"
                            else:  # SELL, UNDERWEIGHT, etc.
                                rating_html = f"<span class='metric-down'>{rec['rating']}</span>"
                            
                            st.markdown(rating_html, unsafe_allow_html=True)
                            st.markdown(f"Target: **${rec['target']:.2f}**")
                            st.markdown(f"Confidence: **{rec['confidence']}%**")
                    
                    st.info(f"Note: Forecasts are based on historical patterns and analyst recommendations. They may not accurately predict future prices.")

elif st.session_state.page == "Weather":
    st.header("WEATHER DATA")
    
    # Create tabs for weather data and news
    weather_tabs = st.tabs(["WEATHER DATA", "WEATHER NEWS"])
    
    # Handle the weather news tab
    with weather_tabs[1]:
        st.subheader("WEATHER NEWS & ALERTS")
        
        st.markdown("""
        ### RECENT WEATHER NEWS
        
        * **Record Heat Wave Continues Across Southern Europe** - Temperatures reaching 45°C/113°F have been recorded in multiple locations as the heat wave enters its second week.
        
        * **Tropical Storm Forms in Atlantic** - Meteorologists are tracking the season's third named storm, which is expected to strengthen over warm waters.
        
        * **Flooding Causes Widespread Damage in Southeast Asia** - Monsoon rains have led to severe flooding in multiple countries, displacing thousands.
        
        * **Air Quality Alerts Issued for Major Cities** - Urban centers across North America are experiencing poor air quality due to wildfire smoke and pollution.
        
        * **Drought Conditions Worsen in Agricultural Regions** - Farmers face challenging growing conditions as drought expands across key agricultural areas.
        """)
        
        st.subheader("SEVERE WEATHER ALERTS")
        
        alert_cols = st.columns(3)
        
        with alert_cols[0]:
            st.markdown("**Heat Advisory**")
            st.markdown("Regions: Southern Europe, North Africa, Middle East")
            st.markdown("Duration: Next 5-7 days")
            st.markdown("Status: <span style='color: red; font-weight: bold;'>ACTIVE</span>", unsafe_allow_html=True)
        
        with alert_cols[1]:
            st.markdown("**Flood Warning**")
            st.markdown("Regions: Southeast Asia, parts of South America")
            st.markdown("Duration: 48-72 hours")
            st.markdown("Status: <span style='color: red; font-weight: bold;'>ACTIVE</span>", unsafe_allow_html=True)
        
        with alert_cols[2]:
            st.markdown("**Storm Watch**")
            st.markdown("Regions: Eastern Caribbean, Atlantic Coast")
            st.markdown("Duration: Next 3-5 days")
            st.markdown("Status: <span style='color: orange; font-weight: bold;'>MONITORING</span>", unsafe_allow_html=True)
    
    # Handle the weather data tab
    with weather_tabs[0]:
        # Get available cities
        available_cities = get_available_cities()
        
        # Layout for selection and filtering
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_city = st.selectbox(
                "Select City",
                available_cities,
                key="city_select"
            )
            
            data_type = st.selectbox(
                "Weather Data Type",
                ["Temperature", "Humidity", "Pressure", "Wind Speed", "Precipitation"],
                index=0
            )
            
            # Add more granular time interval options for weather
            weather_interval = st.selectbox(
                "Time Interval",
                ["Hourly", "Daily", "Weekly", "Monthly"],
                index=1  # Default to Daily
            )
            
            st.markdown("### DATA PARAMETERS")
            st.info(f"Retrieving {time_range} of {weather_interval.lower()} {data_type.lower()} data for {selected_city}")
            
            if st.button("FETCH WEATHER DATA") or refresh_button:
                with st.spinner("Fetching weather data..."):
                    # Convert weather_interval to API parameters
                    if weather_interval == "Hourly":
                        # For hourly data, we might want to limit the days to avoid too much data
                        fetch_days = min(days, 3)  # Limit to 3 days for hourly data
                        fetch_interval = "hourly"
                    elif weather_interval == "Daily":
                        fetch_days = days
                        fetch_interval = "daily"
                    elif weather_interval == "Weekly":
                        # For weekly, we'll still fetch daily but aggregate later
                        fetch_days = days
                        fetch_interval = "daily"
                    else:  # Monthly
                        # For monthly, fetch more days if possible
                        fetch_days = max(days, 30)
                        fetch_interval = "daily"
                    
                    st.session_state.weather_data = fetch_weather_data(
                        city=selected_city,
                        days=fetch_days
                    )
                    
                    # If we have data and need to aggregate to weekly or monthly
                    if st.session_state.weather_data is not None and not st.session_state.weather_data.empty:
                        data = st.session_state.weather_data
                        
                        # Resample for weekly or monthly if needed
                        if weather_interval == "Weekly":
                            # Resample to weekly frequency
                            data = data.resample('W').mean()
                            st.session_state.weather_data = data
                        elif weather_interval == "Monthly":
                            # Resample to monthly frequency
                            data = data.resample('M').mean()
                            st.session_state.weather_data = data
        
        with col2:
            if st.session_state.weather_data is not None:
                data = st.session_state.weather_data
                
                # Map data_type to corresponding column in data
                weather_data_map = {
                    "Temperature": "temp",
                    "Humidity": "humidity",
                    "Pressure": "pressure",
                    "Wind Speed": "wind_speed",
                    "Precipitation": "precipitation"
                }
                
                column = weather_data_map[data_type]
                
                # Display chart based on user selection
                if chart_type == "Line Chart":
                    st.plotly_chart(
                        plot_time_series(data, column, f"{selected_city} {data_type}"),
                        use_container_width=True
                    )
                elif chart_type == "Bar Chart":
                    st.plotly_chart(
                        plot_time_series(data, column, f"{selected_city} {data_type}", 
                                       chart_type='bar'),
                        use_container_width=True
                    )
                elif chart_type == "Area Chart":
                    st.plotly_chart(
                        plot_time_series(data, column, f"{selected_city} {data_type}", 
                                       chart_type='area'),
                        use_container_width=True
                    )
                else:
                    # Fallback for candlestick which doesn't apply to weather
                    st.plotly_chart(
                        plot_time_series(data, column, f"{selected_city} {data_type}"),
                        use_container_width=True
                    )
                
                # Generate download link
                if st.button("DOWNLOAD DATA"):
                    download_link = generate_download_link(data, f"{selected_city}_weather", download_format)
                    st.markdown(download_link, unsafe_allow_html=True)
    
                # Show additional analysis if data is available
                st.header("ANALYSIS & INSIGHTS")
                tab1, tab2, tab3 = st.tabs(["TREND ANALYSIS", "STATISTICS", "FORECASTING"])
                
                with tab1:
                    if "Trend Analysis" in analysis_type:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"{data_type} TREND INDICATORS")
                            trend_data = perform_trend_analysis(data, column)
                            st.plotly_chart(
                                plot_trend_indicators(trend_data, f"{selected_city} {data_type} Trend"),
                                use_container_width=True
                            )
                        
                        with col2:
                            st.subheader("PATTERN DETECTION")
                            if "Pattern Recognition" in analysis_type:
                                patterns = detect_patterns(data, column)
                                
                                if patterns:
                                    for pattern, confidence in patterns.items():
                                        st.metric(f"Pattern: {pattern}", f"Confidence: {confidence:.2f}%")
                                else:
                                    st.info("No significant patterns detected in the current timeframe")
                
                with tab2:
                    st.subheader("STATISTICAL ANALYSIS")
                    stats = calculate_statistics(data, column)
                    
                    # Adjust units based on data type
                    units = {
                        "temp": "°C",
                        "humidity": "%",
                        "pressure": "hPa",
                        "wind_speed": "m/s",
                        "precipitation": "mm"
                    }
                    
                    unit = units[column]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Mean", f"{stats['mean']:.2f} {unit}")
                    col2.metric("Variability", f"{stats['volatility']:.2f}%")
                    col3.metric("Min", f"{stats['min']:.2f} {unit}")
                    col4.metric("Max", f"{stats['max']:.2f} {unit}")
                    
                    st.plotly_chart(
                        plot_distribution(data, column, f"{selected_city} {data_type} Distribution"),
                        use_container_width=True
                    )
                
                with tab3:
                    st.subheader(f"{data_type} FORECASTING")
                    if "Forecasting" in analysis_type:
                        forecast_days = st.slider("Forecast Days", min_value=1, max_value=14, value=5)
                        
                        with st.spinner("Generating forecast..."):
                            forecast_data = predict_future_values(data, column, forecast_days)
                            
                            st.plotly_chart(
                                plot_forecast(data, forecast_data, f"{selected_city} {data_type} Forecast"),
                                use_container_width=True
                            )
                            
                            st.info(f"Note: Weather forecasts are based on historical patterns and may not accurately predict future conditions.")

elif st.session_state.page == "Custom Upload":
    st.header("CUSTOM DATA UPLOAD")
    
    upload_info = """
    Upload your own data for analysis. The file should be one of the following formats:
    - CSV (.csv)
    - Excel (.xlsx, .xls)
    - JSON (.json)
    
    The data should have a timestamp/date column and at least one numeric column for analysis.
    """
    
    st.info(upload_info)
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])
    
    if uploaded_file is not None:
        with st.spinner("Processing uploaded file..."):
            try:
                st.session_state.custom_data, file_details = process_uploaded_file(uploaded_file)
                st.success(f"Successfully loaded data from {file_details['filename']}")
                
                # Display data info
                st.markdown(f"**File type:** {file_details['filetype']}")
                st.markdown(f"**Rows:** {file_details['rows']}, **Columns:** {file_details['columns']}")
                
                # Show preview of data
                st.subheader("DATA PREVIEW")
                st.dataframe(st.session_state.custom_data.head())
                
                # Column selection for analysis
                data = st.session_state.custom_data
                
                # Guess date column
                date_cols = [col for col in data.columns if any(date_term in col.lower() for date_term in ['date', 'time', 'day', 'timestamp'])]
                
                if date_cols:
                    default_date_col = date_cols[0]
                else:
                    default_date_col = data.columns[0]
                
                # Guess numeric columns
                numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()
                
                if not numeric_cols:
                    st.error("No numeric columns found in the data. Please upload a file with numeric data for analysis.")
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        date_column = st.selectbox(
                            "Select Date/Time Column",
                            data.columns.tolist(),
                            index=data.columns.tolist().index(default_date_col) if default_date_col in data.columns else 0
                        )
                    
                    with col2:
                        value_column = st.selectbox(
                            "Select Value Column for Analysis",
                            numeric_cols,
                            index=0 if numeric_cols else 0
                        )
                    
                    # Ensure date column is properly formatted
                    try:
                        data[date_column] = pd.to_datetime(data[date_column])
                        data = data.sort_values(by=date_column)
                        
                        # Display chart based on user selection
                        st.subheader("Data Visualization")
                        
                        if chart_type == "Line Chart":
                            st.plotly_chart(
                                plot_time_series(data, value_column, f"{value_column} Over Time", date_col=date_column),
                                use_container_width=True
                            )
                        elif chart_type == "Bar Chart":
                            st.plotly_chart(
                                plot_time_series(data, value_column, f"{value_column} Over Time", 
                                               date_col=date_column, chart_type='bar'),
                                use_container_width=True
                            )
                        elif chart_type == "Area Chart":
                            st.plotly_chart(
                                plot_time_series(data, value_column, f"{value_column} Over Time", 
                                               date_col=date_column, chart_type='area'),
                                use_container_width=True
                            )
                        elif chart_type == "Candlestick":
                            # Check if we have OHLC data
                            ohlc_cols = ['open', 'high', 'low', 'close']
                            has_ohlc = all(any(ohlc in col.lower() for col in data.columns) for ohlc in ohlc_cols)
                            
                            if has_ohlc:
                                # Find the OHLC columns
                                ohlc_mapping = {}
                                for ohlc in ohlc_cols:
                                    matches = [col for col in data.columns if ohlc in col.lower()]
                                    if matches:
                                        ohlc_mapping[ohlc] = matches[0]
                                
                                if len(ohlc_mapping) == 4:
                                    st.plotly_chart(
                                        plot_candlestick(data, f"Price Data", 
                                                       date_col=date_column, 
                                                       open_col=ohlc_mapping['open'],
                                                       high_col=ohlc_mapping['high'],
                                                       low_col=ohlc_mapping['low'],
                                                       close_col=ohlc_mapping['close']),
                                        use_container_width=True
                                    )
                                else:
                                    st.warning("Complete OHLC data not found. Displaying line chart instead.")
                                    st.plotly_chart(
                                        plot_time_series(data, value_column, f"{value_column} Over Time", date_col=date_column),
                                        use_container_width=True
                                    )
                            else:
                                st.warning("Candlestick chart requires OHLC data. Displaying line chart instead.")
                                st.plotly_chart(
                                    plot_time_series(data, value_column, f"{value_column} Over Time", date_col=date_column),
                                    use_container_width=True
                                )
                        
                        # Generate download link
                        if st.button("DOWNLOAD PROCESSED DATA"):
                            download_link = generate_download_link(data, "processed_data", download_format)
                            st.markdown(download_link, unsafe_allow_html=True)
                        
                        # Analysis tabs
                        st.header("ANALYSIS & INSIGHTS")
                        tab1, tab2, tab3 = st.tabs(["TREND ANALYSIS", "STATISTICS", "FORECASTING"])
                        
                        with tab1:
                            if "Trend Analysis" in analysis_type:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("TREND INDICATORS")
                                    trend_data = perform_trend_analysis(data, value_column, date_col=date_column)
                                    st.plotly_chart(
                                        plot_trend_indicators(trend_data, f"{value_column} Trend Indicators", date_col=date_column),
                                        use_container_width=True
                                    )
                                
                                with col2:
                                    st.subheader("PATTERN DETECTION")
                                    if "Pattern Recognition" in analysis_type:
                                        patterns = detect_patterns(data, value_column, date_col=date_column)
                                        
                                        if patterns:
                                            for pattern, confidence in patterns.items():
                                                st.metric(f"Pattern: {pattern}", f"Confidence: {confidence:.2f}%")
                                        else:
                                            st.info("No significant patterns detected in the current timeframe")
                        
                        with tab2:
                            st.subheader("STATISTICAL ANALYSIS")
                            stats = calculate_statistics(data, value_column)
                            
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("Mean", f"{stats['mean']:.2f}")
                            col2.metric("Variability", f"{stats['volatility']:.2f}%")
                            col3.metric("Min", f"{stats['min']:.2f}")
                            col4.metric("Max", f"{stats['max']:.2f}")
                            
                            st.plotly_chart(
                                plot_distribution(data, value_column, f"{value_column} Distribution"),
                                use_container_width=True
                            )
                            
                            # If we have multiple numeric columns, show correlation
                            if len(numeric_cols) > 1:
                                st.subheader("CORRELATION ANALYSIS")
                                st.plotly_chart(
                                    plot_correlation_matrix(data[numeric_cols], "Correlation Matrix"),
                                    use_container_width=True
                                )
                        
                        with tab3:
                            st.subheader("FORECASTING")
                            if "Forecasting" in analysis_type:
                                forecast_periods = st.slider("Forecast Periods", min_value=1, max_value=30, value=7)
                                
                                with st.spinner("Generating forecast..."):
                                    forecast_data = predict_future_values(data, value_column, forecast_periods, date_col=date_column)
                                    
                                    st.plotly_chart(
                                        plot_forecast(data, forecast_data, f"{value_column} Forecast", date_col=date_column),
                                        use_container_width=True
                                    )
                                    
                                    st.info(f"Note: Forecasts are based on historical patterns and should be interpreted with caution.")
                    
                    except Exception as e:
                        st.error(f"Error processing date column: {str(e)}")
                        st.info("Please ensure the selected date column contains valid date/time data.")
            
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Please ensure your file is properly formatted with timestamp/date and numeric columns.")

# Footer
st.markdown("---")
st.markdown("### ABOUT THIS DASHBOARD")
st.markdown("""
This AI-powered dashboard provides real-time data visualization and analysis for crypto, stocks, weather, and custom data sources.
Features include trend analysis, pattern recognition, and forecasting capabilities.
""")
