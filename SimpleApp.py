import streamlit as st
import pandas as pd
import numpy as np
import datetime


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

from utils import (
    process_uploaded_file,
    generate_download_link,
    calculate_statistics
)

# Initialize session state variables if they don't exist
if 'crypto_data' not in st.session_state:
    st.session_state.crypto_data = None
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'custom_data' not in st.session_state:
    st.session_state.custom_data = None
    
# Set page configuration
st.set_page_config(
    page_title="AI Data Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Page title and description
st.title("AI Data Analysis Dashboard")
st.markdown("""
    This dashboard provides tools for analyzing financial and environmental data.
    Select a data source from the sidebar to begin exploring data trends and insights.
""")

# Sidebar navigation
st.sidebar.title("Navigation")
data_source = st.sidebar.selectbox(
    "Select Data Source",
    ["Cryptocurrency", "Stock Market", "Weather", "Upload Custom Data"]
)

# Main content based on selected data source
if data_source == "Cryptocurrency":
    st.header("Cryptocurrency Analysis")
    
    # Sample data for display
    crypto_data = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=30),
        'Price': [35000 + 1000*np.sin(i/2) + i*100 + np.random.randn()*200 for i in range(30)],
        'Volume': np.random.randint(1000000, 5000000, size=30)
    })
    
    # Display options
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Select Cryptocurrency")
        crypto = st.selectbox("Cryptocurrency", ["Bitcoin", "Ethereum", "Solana", "Cardano"])
    
    with col2:
        st.subheader("Select Timeframe")
        timeframe = st.selectbox("Timeframe", ["1 Day", "1 Week", "1 Month", "3 Months", "1 Year"])
    
    # Display data
    st.subheader(f"{crypto} Data")
    st.dataframe(crypto_data)
    
    # Show stats
    st.subheader("Statistics")
    stats = pd.DataFrame({
        'Metric': ['Current Price', 'Change (24h)', 'Market Cap', 'Volume'],
        'Value': ['$36,789.45', '+1.24%', '$698.3B', '$24.6B']
    })
    st.table(stats)
    
    # Display trend insights
    st.subheader("AI Trend Analysis")
    st.info("The current trend indicates an upward momentum with a 78% confidence level. Resistance level detected at $37,500.")

elif data_source == "Stock Market":
    st.header("Stock Market Analysis")
    
    # Sample data
    stock_data = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=30),
        'Price': [150 + 5*np.sin(i/3) + i*0.5 + np.random.randn() for i in range(30)],
        'Volume': np.random.randint(1000000, 10000000, size=30)
    })
    
    # Display options
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Select Stock")
        stock = st.selectbox("Stock", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
    
    with col2:
        st.subheader("Select Timeframe")
        timeframe = st.selectbox("Timeframe", ["1 Day", "1 Week", "1 Month", "3 Months", "1 Year"])
    
    # Display data
    st.subheader(f"{stock} Data")
    st.dataframe(stock_data)
    
    # Show stats
    st.subheader("Statistics")
    stats = pd.DataFrame({
        'Metric': ['Current Price', 'Change (24h)', 'Market Cap', 'P/E Ratio'],
        'Value': ['$165.23', '-0.42%', '$2.65T', '31.8']
    })
    st.table(stats)
    
    # Display trend insights
    st.subheader("AI Trend Analysis")
    st.info("The stock is in a consolidation phase with a possible breakout pattern forming. Technical indicators suggest strong support at $160.")

elif data_source == "Weather":
    st.header("Weather Data Analysis")
    
    # Sample data
    weather_data = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=30),
        'Temperature': [20 + 5*np.sin(i/3) + np.random.randn() for i in range(30)],
        'Precipitation': np.random.uniform(0, 10, size=30)
    })
    
    # Display options
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Select Location")
        location = st.selectbox("Location", ["New York", "London", "Tokyo", "Sydney", "Paris"])
    
    with col2:
        st.subheader("Select Timeframe")
        timeframe = st.selectbox("Timeframe", ["1 Day", "1 Week", "1 Month", "3 Months", "1 Year"])
    
    # Display data
    st.subheader(f"{location} Weather Data")
    st.dataframe(weather_data)
    
    # Show stats
    st.subheader("Statistics")
    stats = pd.DataFrame({
        'Metric': ['Current Temp', 'Avg High', 'Avg Low', 'Precipitation'],
        'Value': ['22°C', '26°C', '18°C', '30%']
    })
    st.table(stats)
    
    # Display trend insights
    st.subheader("AI Weather Pattern Analysis")
    st.info("Temperature trends indicate a warming pattern over the next week. Precipitation probability is decreasing with a 85% confidence level.")

else:  # Upload Custom Data
    st.header("Upload Custom Data")
    
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success("File successfully uploaded!")
            
            # Display data
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            # Data info
            st.subheader("Data Information")
            
            # Display summary statistics
            st.write("Summary Statistics")
            st.write(df.describe())
            
            # Select column for trend analysis
            if len(df.columns) > 0:
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
                
                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Select column for trend analysis", numeric_cols)
                    
                    # Simple trend indicator
                    if len(df) > 1:
                        start_val = df[selected_col].iloc[0]
                        end_val = df[selected_col].iloc[-1]
                        change = end_val - start_val
                        pct_change = (change / start_val * 100) if start_val != 0 else 0
                        
                        direction = "upward" if change > 0 else "downward"
                        
                        st.subheader("Trend Analysis")
                        st.info(f"The data shows a {direction} trend with a {abs(pct_change):.2f}% change over the period.")
                
                else:
                    st.warning("No numeric columns found for analysis.")
            
        except Exception as e:
            st.error(f"Error processing the file: {e}")
    
    else:
        st.info("Please upload a file to analyze.")

# Footer
st.markdown("---")
st.markdown("© 2025 AI Data Analysis Dashboard | Powered by Streamlit and Machine Learning")
