import pandas as pd
import numpy as np
from datetime import datetime
import json

class DataAnalyzer:
    def __init__(self, df):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    def get_basic_info(self):
        """Get basic information about the dataset"""
        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'columns': self.df.columns.tolist(),
            'numeric_columns': self.numeric_cols,
            'categorical_columns': self.categorical_cols,
            'datetime_columns': self.datetime_cols,
            'memory_usage': self.df.memory_usage(deep=True).sum() / 1024,  # KB
            'duplicate_rows': self.df.duplicated().sum(),
            'missing_values': self.df.isnull().sum().sum()
        }
    
    def get_column_stats(self, column):
        """Get statistics for a specific column"""
        if column in self.numeric_cols:
            return {
                'type': 'numeric',
                'count': self.df[column].count(),
                'mean': self.df[column].mean(),
                'median': self.df[column].median(),
                'mode': self.df[column].mode().iloc[0] if not self.df[column].mode().empty else None,
                'min': self.df[column].min(),
                'max': self.df[column].max(),
                'std': self.df[column].std(),
                'variance': self.df[column].var(),
                'skewness': self.df[column].skew(),
                'kurtosis': self.df[column].kurtosis(),
                'missing': self.df[column].isnull().sum(),
                'unique_values': self.df[column].nunique()
            }
        elif column in self.categorical_cols:
            value_counts = self.df[column].value_counts()
            return {
                'type': 'categorical',
                'count': self.df[column].count(),
                'unique_values': self.df[column].nunique(),
                'most_frequent': value_counts.index[0] if not value_counts.empty else None,
                'frequency': value_counts.iloc[0] if not value_counts.empty else 0,
                'top_values': value_counts.head(5).to_dict(),
                'missing': self.df[column].isnull().sum()
            }
        return {'type': 'other'}
    
    def get_correlation_matrix(self):
        """Get correlation matrix for numeric columns"""
        if len(self.numeric_cols) > 1:
            return self.df[self.numeric_cols].corr().round(4)
        return None
    
    def get_data_quality_report(self):
        """Generate a comprehensive data quality report"""
        report = {
            'missing_data': {},
            'outliers': {},
            'data_types': self.df.dtypes.astype(str).to_dict()
        }
        
        # Missing data analysis
        for col in self.df.columns:
            missing_count = self.df[col].isnull().sum()
            if missing_count > 0:
                report['missing_data'][col] = {
                    'count': missing_count,
                    'percentage': (missing_count / len(self.df)) * 100
                }
        
        # Outlier detection using IQR method
        for col in self.numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            if not outliers.empty:
                report['outliers'][col] = {
                    'count': len(outliers),
                    'percentage': (len(outliers) / len(self.df)) * 100,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
        
        return report