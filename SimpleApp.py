import streamlit as st
import pandas as pd
import numpy as np
#import plotly.express as px
#import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Simple Data Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Page title
st.title("Simple Data Analysis Dashboard")

# Create sample data
data = pd.DataFrame({
    'Date': pd.date_range(start='2023-01-01', periods=30),
    'Value': np.random.randn(30).cumsum(),
    'Volume': np.random.randint(100, 1000, size=30)
})

# Display the data
st.subheader("Sample Data")
st.dataframe(data)

# Create a simple time series plot
st.subheader("Time Series Plot")
fig = px.line(data, x='Date', y='Value', title='Sample Time Series')
st.plotly_chart(fig, use_container_width=True)

# Create a candlestick chart
st.subheader("Candlestick Chart")
data['Open'] = data['Value'].shift(1)
data['High'] = data[['Value', 'Open']].max(axis=1) + np.random.uniform(0, 1, size=30)
data['Low'] = data[['Value', 'Open']].min(axis=1) - np.random.uniform(0, 1, size=30)
data['Close'] = data['Value']

fig_candlestick = go.Figure(data=[go.Candlestick(
    x=data['Date'],
    open=data['Open'].fillna(0),
    high=data['High'],
    low=data['Low'],
    close=data['Close']
)])
fig_candlestick.update_layout(title='Sample Candlestick Chart')
st.plotly_chart(fig_candlestick, use_container_width=True)
