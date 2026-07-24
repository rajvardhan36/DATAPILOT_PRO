import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from config import Config
from utils.data_analyzer import DataAnalyzer
from utils.visualizer import Visualizer
import plotly.utils
import io

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(url_for('index'))
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read the Excel file
        df = pd.read_excel(filepath)
        
        if df.empty:
            flash('The uploaded file is empty', 'error')
            os.remove(filepath)
            return redirect(url_for('index'))
        
        # Store dataframe in session (use session or global variable for larger apps)
        # For simplicity, we'll store the file path and read again when needed
        return redirect(url_for('dashboard', filename=filename))
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard/<filename>')
def dashboard(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            flash('File not found', 'error')
            return redirect(url_for('index'))
        
        df = pd.read_excel(filepath)
        analyzer = DataAnalyzer(df)
        
        # Get basic info
        basic_info = analyzer.get_basic_info()
        
        # Get column list for dropdowns
        columns = df.columns.tolist()
        numeric_cols = analyzer.numeric_cols
        categorical_cols = analyzer.categorical_cols
        datetime_cols = analyzer.datetime_cols
        
        return render_template('dashboard.html', 
                             filename=filename,
                             basic_info=basic_info,
                             columns=columns,
                             numeric_cols=numeric_cols,
                             categorical_cols=categorical_cols,
                             datetime_cols=datetime_cols)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/preview/<filename>')
def get_preview(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath)
        
        preview = df.head(100).to_dict('records')
        columns = df.columns.tolist()
        
        return jsonify({
            'columns': columns,
            'data': preview,
            'total_rows': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<filename>/<column>')
def get_column_stats(filename, column):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath)
        analyzer = DataAnalyzer(df)
        
        stats = analyzer.get_column_stats(column)
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visualize/<filename>', methods=['POST'])
def create_visualization(filename):
    try:
        data = request.json
        viz_type = data.get('type')
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath)
        visualizer = Visualizer(df)
        
        if viz_type == 'histogram':
            column = data.get('column')
            bins = data.get('bins', 30)
            fig_json = visualizer.create_histogram(column, bins)
        
        elif viz_type == 'boxplot':
            column = data.get('column')
            fig_json = visualizer.create_box_plot(column)
        
        elif viz_type == 'scatter':
            x_col = data.get('x_col')
            y_col = data.get('y_col')
            color_col = data.get('color_col')
            fig_json = visualizer.create_scatter_plot(x_col, y_col, color_col)
        
        elif viz_type == 'barchart':
            column = data.get('column')
            top_n = data.get('top_n', 20)
            fig_json = visualizer.create_bar_chart(column, top_n)
        
        elif viz_type == 'piechart':
            column = data.get('column')
            top_n = data.get('top_n', 10)
            fig_json = visualizer.create_pie_chart(column, top_n)
        
        elif viz_type == 'line':
            x_col = data.get('x_col')
            y_col = data.get('y_col')
            fig_json = visualizer.create_line_chart(x_col, y_col)
        
        elif viz_type == 'correlation':
            fig_json = visualizer.create_correlation_heatmap()
            if fig_json is None:
                return jsonify({'error': 'Need at least 2 numeric columns for correlation'}), 400
        
        else:
            return jsonify({'error': 'Invalid visualization type'}), 400
        
        return jsonify({'figure': fig_json})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quality_report/<filename>')
def get_quality_report(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath)
        analyzer = DataAnalyzer(df)
        
        report = analyzer.get_data_quality_report()
        return jsonify(report)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<filename>/<format>')
def export_data(filename, format):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath)
        
        if format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            response = app.response_class(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename={filename.replace(".xlsx", ".csv")}'}
            )
            return response
        
        elif format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            output.seek(0)
            return send_file(
                output,
                as_attachment=True,
                download_name=filename.replace('.xlsx', '_export.xlsx'),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        flash('File deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)