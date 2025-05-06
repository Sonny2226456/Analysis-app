import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def plot_time_series(data, column, title, date_col=None, chart_type='line', highlight_peaks=True, window_size=5):
    """
    Create a time series plot with optional peak and bottom highlighting
    
    Parameters:
    - data: pandas DataFrame containing the time series data
    - column: string, name of the column to plot
    - title: string, title of the plot
    - date_col: string, name of the date column (if not index)
    - chart_type: string, type of chart ('line', 'bar', 'area')
    - highlight_peaks: boolean, whether to highlight peaks and bottoms
    - window_size: int, window size for peak detection (higher means fewer peaks detected)
    
    Returns:
    - plotly figure object
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Handle date column
    if date_col is not None and date_col in df.columns:
        x = df[date_col]
    else:
        # Use index as x-axis
        df = df.reset_index()
        if 'index' in df.columns:
            x = df['index']
        else:
            # If reset_index doesn't work as expected, create a basic range
            x = list(range(len(df)))
    
    # Get y values
    if column in df.columns:
        y = df[column]
    else:
        # If column doesn't exist, use first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            y = df[numeric_cols[0]]
            column = numeric_cols[0]
        else:
            # No numeric columns, return empty figure
            return go.Figure()
    
    # Create figure based on chart type
    if chart_type == 'line':
        fig = px.line(df, x=x, y=column, title=title)
    elif chart_type == 'bar':
        fig = px.bar(df, x=x, y=column, title=title)
    elif chart_type == 'area':
        fig = px.area(df, x=x, y=column, title=title)
    else:
        # Default to line chart
        fig = px.line(df, x=x, y=column, title=title)
    
    # Highlight peaks and bottoms if requested and we have enough data points
    if highlight_peaks and len(y) > window_size * 2:
        # Function to find peaks (local maxima and minima)
        def find_peaks(series, window_size=5):
            # Remove NaN values to avoid issues
            series = series.dropna()
            
            # Create arrays for maxima and minima
            peaks = []
            bottoms = []
            
            # Detect peaks and bottoms
            for i in range(window_size, len(series) - window_size):
                # Check if current point is a peak (local maximum)
                if all(series.iloc[i] > series.iloc[i-j] for j in range(1, window_size+1)) and \
                   all(series.iloc[i] > series.iloc[i+j] for j in range(1, window_size+1)):
                    peaks.append(i)
                
                # Check if current point is a bottom (local minimum)
                if all(series.iloc[i] < series.iloc[i-j] for j in range(1, window_size+1)) and \
                   all(series.iloc[i] < series.iloc[i+j] for j in range(1, window_size+1)):
                    bottoms.append(i)
            
            return {'peaks': peaks, 'bottoms': bottoms}
        
        # Find peaks and bottoms
        peak_data = find_peaks(y, window_size)
        
        # Get corresponding X and Y values for peaks
        peak_x = [x.iloc[idx] if hasattr(x, 'iloc') else x[idx] for idx in peak_data['peaks']]
        peak_y = [y.iloc[idx] for idx in peak_data['peaks']]
        
        # Get corresponding X and Y values for bottoms
        bottom_x = [x.iloc[idx] if hasattr(x, 'iloc') else x[idx] for idx in peak_data['bottoms']]
        bottom_y = [y.iloc[idx] for idx in peak_data['bottoms']]
        
        # Add peaks to the plot (green triangles pointing up)
        fig.add_trace(go.Scatter(
            x=peak_x,
            y=peak_y,
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='green',
                line=dict(width=2, color='darkgreen')
            ),
            name='Peaks'
        ))
        
        # Add bottoms to the plot (red triangles pointing down)
        fig.add_trace(go.Scatter(
            x=bottom_x,
            y=bottom_y,
            mode='markers',
            marker=dict(
                symbol='triangle-down',
                size=12,
                color='red',
                line=dict(width=2, color='darkred')
            ),
            name='Bottoms'
        ))
    
    # Customize layout
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title=column,
        legend_title_text="Series",
        hovermode="x unified",
        # Improve date formatting to show specific dates
        xaxis=dict(
            tickformat="%b %d, %Y",  # Format: "Jan 01, 2023"
            tickmode='auto',
            nticks=10,
            tickangle=-45
        )
    )
    
    return fig

def plot_candlestick(data, title, date_col=None, open_col='open', high_col='high', low_col='low', close_col='close'):
    """
    Create a candlestick chart
    
    Parameters:
    - data: pandas DataFrame containing OHLC data
    - title: string, title of the plot
    - date_col: string, name of the date column (if not index)
    - open_col, high_col, low_col, close_col: column names for OHLC data
    
    Returns:
    - plotly figure object
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Handle date column
    if date_col is not None and date_col in df.columns:
        x = df[date_col]
    else:
        # Use index as x-axis
        df = df.reset_index()
        if 'index' in df.columns:
            x = df['index']
        else:
            # If reset_index doesn't work as expected, create a basic range
            x = list(range(len(df)))
    
    # Check if all OHLC columns exist
    if (open_col in df.columns and high_col in df.columns and 
        low_col in df.columns and close_col in df.columns):
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=x,
            open=df[open_col],
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            name="OHLC"
        )])
        
        # Add volume if available
        if 'volume' in df.columns:
            # Create secondary y-axis for volume
            fig.add_trace(go.Bar(
                x=x,
                y=df['volume'],
                name="Volume",
                marker_color='rgba(0, 0, 200, 0.3)',
                opacity=0.3,
                yaxis="y2"
            ))
            
            # Update layout with secondary axis
            fig.update_layout(
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right",
                    showgrid=False
                )
            )
    else:
        # If OHLC columns don't exist, create a regular line chart
        # Get the first available numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            y_col = numeric_cols[0]
        else:
            # No numeric columns, return empty figure
            return go.Figure()
        
        fig = px.line(df, x=x, y=y_col, title=title)
    
    # Customize layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Price",
        legend_title_text="Data",
        hovermode="x unified",
        # Improve date formatting to show specific dates
        xaxis=dict(
            tickformat="%b %d, %Y",  # Format: "Jan 01, 2023"
            tickmode='auto',
            nticks=10,
            tickangle=-45
        )
    )
    
    return fig

def plot_trend_indicators(data, title, date_col=None):
    """
    Create a plot with trend indicators
    
    Parameters:
    - data: pandas DataFrame with trend indicators (from perform_trend_analysis)
    - title: string, title of the plot
    - date_col: string, name of the date column (if not index)
    
    Returns:
    - plotly figure object
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Handle date column
    if date_col is not None and date_col in df.columns:
        df = df.set_index(date_col)
    
    # Reset index to have dates as a column
    df = df.reset_index()
    
    # Find the main data column and the derived columns
    main_cols = [col for col in df.columns if not any(x in col for x in ['SMA', 'EMA', 'RSI', 'BOLU', 'BOLD', 'MACD', 'trend'])]
    main_cols = [col for col in main_cols if col != 'index']
    
    # If no main columns found, return empty figure
    if not main_cols:
        return go.Figure()
    
    # Select main data column
    main_col = main_cols[0]
    
    # Find trend indicator columns
    sma_cols = [col for col in df.columns if 'SMA' in col]
    ema_cols = [col for col in df.columns if 'EMA' in col]
    boll_cols = [col for col in df.columns if 'BOL' in col]
    trend_cols = [col for col in df.columns if 'trend' in col]
    
    # Create figure
    fig = go.Figure()
    
    # Add main data
    fig.add_trace(go.Scatter(
        x=df.index if 'index' not in df.columns else df['index'],
        y=df[main_col],
        mode='lines',
        name=main_col,
        line=dict(color='blue', width=2)
    ))
    
    # Add SMA lines
    for col in sma_cols:
        fig.add_trace(go.Scatter(
            x=df.index if 'index' not in df.columns else df['index'],
            y=df[col],
            mode='lines',
            name=col,
            line=dict(width=1.5, dash='dot')
        ))
    
    # Add trend line if available
    for col in trend_cols:
        fig.add_trace(go.Scatter(
            x=df.index if 'index' not in df.columns else df['index'],
            y=df[col],
            mode='lines',
            name='Linear Trend',
            line=dict(color='red', width=2)
        ))
    
    # Add Bollinger Bands if available
    if boll_cols:
        upper_band = [col for col in boll_cols if 'BOLU' in col]
        lower_band = [col for col in boll_cols if 'BOLD' in col]
        
        if upper_band and lower_band:
            # Add upper band
            fig.add_trace(go.Scatter(
                x=df.index if 'index' not in df.columns else df['index'],
                y=df[upper_band[0]],
                mode='lines',
                name='Upper Bollinger',
                line=dict(color='rgba(0, 128, 0, 0.3)'),
                fill=None
            ))
            
            # Add lower band with fill
            fig.add_trace(go.Scatter(
                x=df.index if 'index' not in df.columns else df['index'],
                y=df[lower_band[0]],
                mode='lines',
                name='Lower Bollinger',
                line=dict(color='rgba(0, 128, 0, 0.3)'),
                fill='tonexty',
                fillcolor='rgba(0, 128, 0, 0.1)'
            ))
    
    # Customize layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title_text="Indicators",
        hovermode="x unified",
        # Improve date formatting to show specific dates
        xaxis=dict(
            tickformat="%b %d, %Y",  # Format: "Jan 01, 2023"
            tickmode='auto',
            nticks=10,
            tickangle=-45
        )
    )
    
    return fig

def plot_distribution(data, column, title):
    """
    Create a histogram and box plot of data distribution
    
    Parameters:
    - data: pandas DataFrame containing the data
    - column: string, name of the column to analyze
    - title: string, title of the plot
    
    Returns:
    - plotly figure object
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Check if column exists
    if column not in df.columns:
        # Find first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            column = numeric_cols[0]
        else:
            # No numeric columns, return empty figure
            return go.Figure()
    
    # Create subplot figure
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=df[column],
        name="Distribution",
        opacity=0.7,
        marker_color='blue',
        nbinsx=30
    ))
    
    # Add KDE (approximated with smoothed histogram)
    hist_values, bin_edges = np.histogram(df[column].dropna(), bins=50, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Smooth the histogram
    from scipy.ndimage import gaussian_filter1d
    smoothed = gaussian_filter1d(hist_values, sigma=2)
    
    # Scale the KDE to match histogram height
    max_hist = np.max(np.histogram(df[column].dropna(), bins=30)[0])
    scale_factor = max_hist / np.max(smoothed) if np.max(smoothed) > 0 else 1
    
    fig.add_trace(go.Scatter(
        x=bin_centers,
        y=smoothed * scale_factor,
        mode='lines',
        name='Density',
        line=dict(color='red', width=2)
    ))
    
    # Add box plot
    fig.add_trace(go.Box(
        x=df[column],
        name="Box Plot",
        marker_color='green',
        boxmean=True,
        orientation='h',
        y0=0
    ))
    
    # Customize layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title=column,
        yaxis_title="Frequency",
        legend_title_text="Analysis",
        hovermode="closest",
        barmode='overlay'
    )
    
    return fig

def plot_correlation_matrix(data, title):
    """
    Create a correlation matrix heatmap
    
    Parameters:
    - data: pandas DataFrame containing numeric data for correlation
    - title: string, title of the plot
    
    Returns:
    - plotly figure object
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Calculate correlation matrix
    corr_matrix = df.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        title=title,
        zmin=-1, zmax=1
    )
    
    # Customize layout
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Variables",
        yaxis_title="Variables"
    )
    
    return fig

def plot_forecast(data, forecast_data, title, date_col=None):
    """
    Create a forecast plot with confidence intervals
    
    Parameters:
    - data: pandas DataFrame with historical data
    - forecast_data: pandas DataFrame with forecasted values
    - title: string, title of the plot
    - date_col: string, name of the date column (if not index)
    
    Returns:
    - plotly figure object
    """
    # Create copies to avoid modifying the originals
    hist_df = data.copy()
    fore_df = forecast_data.copy()
    
    # Handle date column for historical data
    if date_col is not None and date_col in hist_df.columns:
        hist_df = hist_df.set_index(date_col)
    
    # Reset indexes to have dates as columns
    hist_df = hist_df.reset_index()
    fore_df = fore_df.reset_index()
    
    # Rename the index columns to ensure consistency
    hist_df.rename(columns={'index': 'date'}, inplace=True)
    fore_df.rename(columns={'index': 'date'}, inplace=True)
    
    # Find the main data column in historical data
    numeric_cols = hist_df.select_dtypes(include=['float64', 'int64']).columns
    
    # Filter out date columns from numeric columns
    numeric_cols = [col for col in numeric_cols if not pd.api.types.is_datetime64_any_dtype(hist_df[col])]
    
    if len(numeric_cols) == 0:
        return go.Figure()  # No numeric columns found
    
    main_col = numeric_cols[0]
    
    # Find corresponding column in forecast data
    forecast_cols = fore_df.columns.tolist()
    
    # Remove 'date' and confidence interval columns
    forecast_cols = [col for col in forecast_cols if col != 'date' and not ('lower' in col or 'upper' in col)]
    
    if len(forecast_cols) == 0:
        return go.Figure()  # No forecast columns found
    
    fore_col = forecast_cols[0]
    
    # Find confidence interval columns
    lower_col = [col for col in fore_df.columns if 'lower' in col]
    upper_col = [col for col in fore_df.columns if 'upper' in col]
    
    # Create figure
    fig = go.Figure()
    
    # Add historical data
    fig.add_trace(go.Scatter(
        x=hist_df['date'],
        y=hist_df[main_col],
        mode='lines',
        name='Historical',
        line=dict(color='blue', width=2)
    ))
    
    # Add forecast
    fig.add_trace(go.Scatter(
        x=fore_df['date'],
        y=fore_df[fore_col],
        mode='lines',
        name='Forecast',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Add confidence intervals if available
    if lower_col and upper_col:
        lower_col = lower_col[0]
        upper_col = upper_col[0]
        
        # Add upper bound
        fig.add_trace(go.Scatter(
            x=fore_df['date'],
            y=fore_df[upper_col],
            mode='lines',
            name='Upper Bound',
            line=dict(color='rgba(255, 0, 0, 0.3)'),
            fill=None
        ))
        
        # Add lower bound with fill
        fig.add_trace(go.Scatter(
            x=fore_df['date'],
            y=fore_df[lower_col],
            mode='lines',
            name='Lower Bound',
            line=dict(color='rgba(255, 0, 0, 0.3)'),
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.1)'
        ))
    
    # Add vertical line to separate historical and forecast data
    if len(hist_df) > 0 and len(fore_df) > 0:
        last_hist_date = hist_df['date'].iloc[-1]
        
        fig.add_vline(
            x=last_hist_date,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text="Forecast Start",
            annotation_position="top right"
        )
    
    # Customize layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title_text="Series",
        hovermode="x unified",
        # Improve date formatting to show specific dates
        xaxis=dict(
            tickformat="%b %d, %Y",  # Format: "Jan 01, 2023"
            tickmode='auto',
            nticks=10,
            tickangle=-45
        )
    )
    
    return fig

def show_metrics_dashboard(data, column, title, date_col=None):
    """
    Create a dashboard with key metrics
    
    Parameters:
    - data: pandas DataFrame with data
    - column: string, name of the column to analyze
    - title: string, title of the dashboard
    - date_col: string, name of the date column (if not index)
    
    Returns:
    - plotly figure object with multiple charts
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Handle date column
    if date_col is not None and date_col in df.columns:
        df = df.set_index(date_col)
    
    # Check if column exists
    if column not in df.columns:
        # Find first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            column = numeric_cols[0]
        else:
            # No numeric columns, return empty figure
            return go.Figure()
    
    # Calculate key metrics
    latest_value = df[column].iloc[-1] if len(df) > 0 else np.nan
    change_abs = df[column].iloc[-1] - df[column].iloc[-2] if len(df) > 1 else np.nan
    change_pct = (change_abs / df[column].iloc[-2] * 100) if len(df) > 1 and df[column].iloc[-2] != 0 else np.nan
    
    mean_value = df[column].mean()
    median_value = df[column].median()
    std_value = df[column].std()
    min_value = df[column].min()
    max_value = df[column].max()
    
    # Create subplot figure
    fig = go.Figure()
    
    # Add gauge chart for latest value
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=latest_value,
        delta={'reference': df[column].iloc[-2] if len(df) > 1 else latest_value, 'relative': True},
        title={'text': f"Latest {column}"},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [min_value, mean_value-std_value], 'color': "lightgray"},
                {'range': [mean_value-std_value, mean_value+std_value], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value
            }
        },
        domain={'row': 0, 'column': 0}
    ))
    
    # Add indicator for percentage change
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=latest_value,
        delta={
            'reference': df[column].iloc[-2] if len(df) > 1 else latest_value,
            'relative': True,
            'valueformat': '.2%'
        },
        title={'text': "Change (%)"},
        domain={'row': 0, 'column': 1}
    ))
    
    # Customize layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        grid={'rows': 1, 'columns': 2},
        height=250
    )
    
    return fig
