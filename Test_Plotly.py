import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

print("Successfully imported plotly!")

# Create a simple plot
data = pd.DataFrame({
    'x': range(10),
    'y': [i**2 for i in range(10)]
})

fig = px.line(data, x='x', y='y')
print("Created a plot successfully!")
