import pandas as pd
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

def perform_trend_analysis(data, column, date_col=None):
    """
    Perform trend analysis on time series data
    
    Parameters:
    - data: pandas DataFrame containing the time series data
    - column: string, name of the column to analyze
    - date_col: string, name of the date column (if not the index)
    
    Returns:
    - pandas DataFrame with original data and trend indicators
    """
    # Create a copy of the data to avoid modifying the original
    if date_col is not None and date_col in data.columns:
        df = data.set_index(date_col).copy()
    else:
        df = data.copy()
    
    # Ensure the data is sorted by date
    df = df.sort_index()
    
    # Extract the series to analyze
    if column in df.columns:
        series = df[column]
    else:
        # If column doesn't exist, take the first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            series = df[numeric_cols[0]]
            column = numeric_cols[0]
        else:
            # No numeric columns, return the original dataframe
            return df
    
    # Calculate Simple Moving Averages (SMA)
    df[f'{column}_SMA7'] = series.rolling(window=7, min_periods=1).mean()
    df[f'{column}_SMA14'] = series.rolling(window=14, min_periods=1).mean()
    df[f'{column}_SMA30'] = series.rolling(window=30, min_periods=1).mean()
    
    # Calculate Exponential Moving Averages (EMA)
    df[f'{column}_EMA7'] = series.ewm(span=7, adjust=False).mean()
    df[f'{column}_EMA14'] = series.ewm(span=14, adjust=False).mean()
    
    # Calculate Relative Strength Index (RSI)
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)  # Replace zeros to avoid division by zero
    df[f'{column}_RSI'] = 100 - (100 / (1 + rs))
    df[f'{column}_RSI'] = df[f'{column}_RSI'].fillna(50)  # Fill NaN values with neutral RSI
    
    # Calculate Bollinger Bands
    window = 20
    df[f'{column}_SMA20'] = series.rolling(window=window, min_periods=1).mean()
    df[f'{column}_BOLU'] = df[f'{column}_SMA20'] + 2 * series.rolling(window=window, min_periods=1).std()
    df[f'{column}_BOLD'] = df[f'{column}_SMA20'] - 2 * series.rolling(window=window, min_periods=1).std()
    
    # Calculate MACD
    df[f'{column}_MACD'] = df[f'{column}_EMA14'] - df[f'{column}_EMA7']
    df[f'{column}_MACD_signal'] = df[f'{column}_MACD'].ewm(span=9, adjust=False).mean()
    
    # Linear regression trend
    try:
        # Create a feature for days since the start
        X = np.array(range(len(df))).reshape(-1, 1)
        y = series.values.reshape(-1, 1)
        
        # Handle NaN values
        mask = ~np.isnan(y).flatten()
        if np.sum(mask) > 1:  # Need at least 2 points for regression
            X_valid = X[mask]
            y_valid = y[mask]
            
            # Simple linear regression implementation
            # Calculate mean of X and y
            mean_x = np.mean(X_valid)
            mean_y = np.mean(y_valid)
            
            # Calculate slope
            numerator = np.sum((X_valid - mean_x) * (y_valid - mean_y))
            denominator = np.sum((X_valid - mean_x) ** 2)
            slope = numerator / denominator if denominator != 0 else 0
            
            # Calculate intercept
            intercept = mean_y - slope * mean_x
            
            # Predict for all points
            trend = intercept + slope * X
            df[f'{column}_trend'] = trend
        else:
            df[f'{column}_trend'] = np.nan
    except Exception as e:
        # If regression fails, set trend to NaN
        df[f'{column}_trend'] = np.nan
    
    return df

def detect_patterns(data, column, date_col=None):
    """
    Detect common patterns in time series data
    
    Parameters:
    - data: pandas DataFrame containing the time series data
    - column: string, name of the column to analyze
    - date_col: string, name of the date column (if not the index)
    
    Returns:
    - dictionary with detected patterns and confidence scores
    """
    # Create a copy of the data to avoid modifying the original
    if date_col is not None and date_col in data.columns:
        df = data.set_index(date_col).copy()
    else:
        df = data.copy()
    
    # Ensure the data is sorted by date
    df = df.sort_index()
    
    # Extract the series to analyze
    if column in df.columns:
        series = df[column]
    else:
        # If column doesn't exist, take the first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            series = df[numeric_cols[0]]
        else:
            # No numeric columns, return empty dict
            return {}
    
    # Detect Trend
    try:
        # Create a feature for days since the start
        X = np.array(range(len(df))).reshape(-1, 1)
        y = series.values.reshape(-1, 1)
        
        # Handle NaN values
        mask = ~np.isnan(y).flatten()
        if np.sum(mask) > 1:  # Need at least 2 points for regression
            X_valid = X[mask]
            y_valid = y[mask]
            
            # Simple linear regression implementation
            # Calculate mean of X and y
            mean_x = np.mean(X_valid)
            mean_y = np.mean(y_valid)
            
            # Calculate slope
            numerator = np.sum((X_valid - mean_x) * (y_valid - mean_y))
            denominator = np.sum((X_valid - mean_x) ** 2)
            slope = numerator / denominator if denominator != 0 else 0
            
            # Calculate intercept
            intercept = mean_y - slope * mean_x
            
            # Calculate predictions
            y_pred = intercept + slope * X_valid
            
            # Calculate R-squared
            ss_total = np.sum((y_valid - mean_y) ** 2)
            ss_residual = np.sum((y_valid - y_pred) ** 2)
            r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
            
            patterns = {}
            
            # Strong trend if R-squared is high
            if r_squared > 0.7:
                confidence = r_squared * 100
                if slope > 0:
                    patterns["Upward Trend"] = confidence
                else:
                    patterns["Downward Trend"] = confidence
            
            # Simple check for potential mean reversion
            # Calculate the deviation from mean
            series_std = np.std(series.dropna())
            series_mean = np.mean(series.dropna())
            
            # Calculate recent deviation from mean
            recent_data = series.dropna()[-10:]
            if len(recent_data) > 0:
                recent_mean = np.mean(recent_data)
                deviation = abs(recent_mean - series_mean) / series_std if series_std > 0 else 0
                
                # If recent data is close to the mean, it might be mean-reverting
                if deviation < 0.5:  # Arbitrary threshold
                    confidence = (1 - deviation) * 100
                    patterns["Mean Reversion"] = confidence
            
            # Detect potential head and shoulders pattern
            # (This is a simplified approach - real pattern detection is complex)
            if len(series) >= 30:  # Need enough data points
                # Smooth the series to reduce noise
                smoothed = series.rolling(window=3, min_periods=1).mean()
                
                # Find local peaks (simplified approach)
                peaks = []
                for i in range(2, len(smoothed) - 2):
                    if (smoothed.iloc[i] > smoothed.iloc[i-1] and 
                        smoothed.iloc[i] > smoothed.iloc[i-2] and
                        smoothed.iloc[i] > smoothed.iloc[i+1] and
                        smoothed.iloc[i] > smoothed.iloc[i+2]):
                        peaks.append((i, smoothed.iloc[i]))
                
                # Need at least 3 peaks for head and shoulders
                if len(peaks) >= 3:
                    # Get the highest 3 peaks
                    top_peaks = sorted(peaks, key=lambda x: x[1], reverse=True)[:3]
                    top_peaks = sorted(top_peaks, key=lambda x: x[0])  # Sort by index
                    
                    # Check if middle peak is highest (potential head)
                    if len(top_peaks) == 3 and top_peaks[1][1] > top_peaks[0][1] and top_peaks[1][1] > top_peaks[2][1]:
                        # Check if shoulders are at similar heights (within 20%)
                        shoulder_diff = abs(top_peaks[0][1] - top_peaks[2][1])
                        avg_shoulder = (top_peaks[0][1] + top_peaks[2][1]) / 2
                        
                        if shoulder_diff / avg_shoulder < 0.2:
                            # Calculate confidence based on how well the pattern fits
                            head_prominence = (top_peaks[1][1] - avg_shoulder) / avg_shoulder
                            confidence = min(head_prominence * 100, 90)  # Cap at 90%
                            patterns["Head and Shoulders"] = confidence
            
            # Detect double bottom pattern (simplified)
            if len(series) >= 20:
                # Find local minimums
                minimums = []
                for i in range(2, len(smoothed) - 2):
                    if (smoothed.iloc[i] < smoothed.iloc[i-1] and 
                        smoothed.iloc[i] < smoothed.iloc[i-2] and
                        smoothed.iloc[i] < smoothed.iloc[i+1] and
                        smoothed.iloc[i] < smoothed.iloc[i+2]):
                        minimums.append((i, smoothed.iloc[i]))
                
                if len(minimums) >= 2:
                    # Get the lowest 2 minimums
                    lowest_mins = sorted(minimums, key=lambda x: x[1])[:2]
                    lowest_mins = sorted(lowest_mins, key=lambda x: x[0])  # Sort by index
                    
                    # Check if minimums are at similar levels and separated in time
                    if len(lowest_mins) == 2:
                        min_diff = abs(lowest_mins[0][1] - lowest_mins[1][1])
                        avg_min = (lowest_mins[0][1] + lowest_mins[1][1]) / 2
                        time_diff = lowest_mins[1][0] - lowest_mins[0][0]
                        
                        if min_diff / avg_min < 0.1 and time_diff > 5:
                            # Calculate confidence
                            confidence = (1 - (min_diff / avg_min)) * 100
                            patterns["Double Bottom"] = confidence
            
            return patterns
        
    except Exception as e:
        pass
    
    return {}

def predict_future_values(data, column, periods=7, date_col=None):
    """
    Predict future values using ARIMA model
    
    Parameters:
    - data: pandas DataFrame containing the time series data
    - column: string, name of the column to predict
    - periods: int, number of periods to forecast
    - date_col: string, name of the date column (if not the index)
    
    Returns:
    - pandas DataFrame with forecasted values
    """
    # Create a copy of the data to avoid modifying the original
    if date_col is not None and date_col in data.columns:
        df = data.set_index(date_col).copy()
    else:
        df = data.copy()
    
    # Ensure the data is sorted by date
    df = df.sort_index()
    
    # Extract the series to analyze
    if column in df.columns:
        series = df[column]
    else:
        # If column doesn't exist, take the first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            series = df[numeric_cols[0]]
            column = numeric_cols[0]
        else:
            # No numeric columns, return empty dataframe
            return pd.DataFrame()
    
    # Drop NaN values
    series = series.dropna()
    
    if len(series) < 3:
        # Not enough data for forecasting
        return pd.DataFrame()
    
    # Use simple exponential smoothing for forecasting
    try:
        alpha = 0.3  # Smoothing factor
        smoothed = series.ewm(alpha=alpha, adjust=False).mean()
        
        # Use the last value for all future predictions
        last_value = smoothed.iloc[-1]
        
        # Create forecast DataFrame
        last_date = series.index[-1]
        
        # Generate future dates based on the frequency of the data
        dates = pd.date_range(start=last_date, periods=periods+1, freq=pd.infer_freq(series.index) or 'D')[1:]
        
        # Create DataFrame with forecasted values
        forecast_df = pd.DataFrame({column: [last_value] * periods}, index=dates)
        
        # Add simple confidence intervals (+-10%)
        forecast_df[f'{column}_lower'] = forecast_df[column] * 0.9
        forecast_df[f'{column}_upper'] = forecast_df[column] * 1.1
        
        # Ensure index is datetime
        forecast_df.index = pd.to_datetime(forecast_df.index)
        
        return forecast_df
        
    except Exception as e:
        # If all else fails, return empty dataframe
        return pd.DataFrame()
