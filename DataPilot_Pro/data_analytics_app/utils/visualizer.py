import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json

class Visualizer:
    def __init__(self, df):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    def create_histogram(self, column, bins=30):
        """Create histogram for numeric column"""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=self.df[column].dropna(),
            nbinsx=bins,
            marker_color='#4285F4',
            opacity=0.7,
            hovertemplate='Range: %{x}<br>Frequency: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Distribution of {column}',
            xaxis_title=column,
            yaxis_title='Frequency',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        return fig.to_json()
    
    def create_box_plot(self, column):
        """Create box plot for numeric column"""
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=self.df[column].dropna(),
            name=column,
            marker_color='#4285F4',
            boxmean='sd',
            hovertemplate='Median: %{y}<br>Mean: %{mean}<br>Q1: %{q1}<br>Q3: %{q3}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Box Plot of {column}',
            yaxis_title=column,
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig.to_json()
    
    def create_scatter_plot(self, x_col, y_col, color_col=None):
        """Create scatter plot between two numeric columns"""
        fig = go.Figure()
        
        if color_col and color_col in self.categorical_cols:
            for category in self.df[color_col].unique():
                mask = self.df[color_col] == category
                fig.add_trace(go.Scatter(
                    x=self.df[mask][x_col],
                    y=self.df[mask][y_col],
                    mode='markers',
                    name=str(category),
                    marker=dict(size=8, opacity=0.6)
                ))
        else:
            fig.add_trace(go.Scatter(
                x=self.df[x_col],
                y=self.df[y_col],
                mode='markers',
                marker=dict(
                    size=8,
                    color='#4285F4',
                    opacity=0.6
                ),
                name='Data Points'
            ))
        
        fig.update_layout(
            title=f'{y_col} vs {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='closest'
        )
        
        return fig.to_json()
    
    def create_bar_chart(self, column, top_n=20):
        """Create bar chart for categorical column"""
        value_counts = self.df[column].value_counts().head(top_n)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=value_counts.index.astype(str),
            y=value_counts.values,
            marker_color='#4285F4',
            hovertemplate='Category: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Top {top_n} Categories in {column}',
            xaxis_title=column,
            yaxis_title='Count',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False,
            xaxis={'tickangle': 45}
        )
        
        return fig.to_json()
    
    def create_pie_chart(self, column, top_n=10):
        """Create pie chart for categorical column"""
        value_counts = self.df[column].value_counts().head(top_n)
        
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=value_counts.index.astype(str),
            values=value_counts.values,
            textinfo='percent+label',
            hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
            marker=dict(colors=px.colors.qualitative.Set3)
        ))
        
        fig.update_layout(
            title=f'Distribution of {column}',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=True
        )
        
        return fig.to_json()
    
    def create_line_chart(self, x_col, y_col):
        """Create line chart for time series data"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=self.df[x_col],
            y=self.df[y_col],
            mode='lines+markers',
            name=y_col,
            marker_color='#4285F4',
            line=dict(width=2),
            hovertemplate='%{x}<br>%{y}: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{y_col} over {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='x'
        )
        
        return fig.to_json()
    
    def create_correlation_heatmap(self):
        """Create correlation heatmap for numeric columns"""
        if len(self.numeric_cols) < 2:
            return None
        
        corr_matrix = self.df[self.numeric_cols].corr()
        
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>',
            text=corr_matrix.values.round(3),
            texttemplate='%{text}',
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title='Correlation Heatmap',
            template='plotly_white',
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis={'side': 'bottom'}
        )
        
        return fig.to_json()