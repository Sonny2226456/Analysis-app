import pandas as pd
import numpy as np
import base64
import io
import json

def process_uploaded_file(uploaded_file):
    """
    Process an uploaded file into a pandas DataFrame
    
    Parameters:
    - uploaded_file: UploadedFile object from Streamlit
    
    Returns:
    - tuple: (DataFrame, file_details_dict)
    """
    filename = uploaded_file.name
    filetype = filename.split('.')[-1].lower()
    
    # Read the file based on its type
    if filetype == 'csv':
        df = pd.read_csv(uploaded_file)
    elif filetype in ['xlsx', 'xls']:
        df = pd.read_excel(uploaded_file)
    elif filetype == 'json':
        df = pd.read_json(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {filetype}")
    
    # Try to identify date/time columns and convert them
    for col in df.columns:
        # Check if column name suggests it's a date
        if any(date_term in col.lower() for date_term in ['date', 'time', 'day', 'timestamp']):
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                # If conversion fails, leave as is
                pass
    
    # Create file details dictionary
    file_details = {
        'filename': filename,
        'filetype': filetype,
        'rows': df.shape[0],
        'columns': df.shape[1],
        'column_list': df.columns.tolist()
    }
    
    return df, file_details

def generate_download_link(df, filename, format_type='CSV'):
    """
    Generate a download link for a DataFrame
    
    Parameters:
    - df: pandas DataFrame to download
    - filename: string, base name for the downloaded file
    - format_type: string, format to download ('CSV', 'JSON', 'Excel')
    
    Returns:
    - string, HTML link element for downloading
    """
    if format_type == 'CSV':
        # Convert to CSV
        csv = df.to_csv(index=True)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
        filename = f"{filename}.csv"
    elif format_type == 'JSON':
        # Convert to JSON
        json_str = df.to_json(orient='records', date_format='iso')
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'data:file/json;base64,{b64}'
        filename = f"{filename}.json"
    elif format_type == 'Excel':
        # Convert to Excel
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=True, sheet_name='Sheet1')
        writer.save()
        processed_data = output.getvalue()
        b64 = base64.b64encode(processed_data).decode()
        href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
        filename = f"{filename}.xlsx"
    else:
        # Default to CSV
        csv = df.to_csv(index=True)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
        filename = f"{filename}.csv"
    
    # Generate download link HTML
    download_link = f'<a href="{href}" download="{filename}" class="btn">Download {format_type}</a>'
    
    return download_link

def calculate_statistics(data, column):
    """
    Calculate basic statistics for a data column
    
    Parameters:
    - data: pandas DataFrame containing the data
    - column: string, name of the column to analyze
    
    Returns:
    - dict with statistics (mean, std, min, max, etc.)
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
            # No numeric columns, return empty dict
            return {
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'volatility': np.nan
            }
    
    # Get series
    series = df[column]
    
    # Calculate basic statistics
    stats = {
        'mean': series.mean(),
        'median': series.median(),
        'std': series.std(),
        'min': series.min(),
        'max': series.max()
    }
    
    # Calculate volatility (coefficient of variation)
    if stats['mean'] != 0:
        stats['volatility'] = (stats['std'] / abs(stats['mean'])) * 100
    else:
        stats['volatility'] = np.nan
    
    return stats
