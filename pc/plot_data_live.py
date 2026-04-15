#!/usr/bin/env python3
"""
Live time series plotting script for Pico data files.
Monitors CSV file for new data and updates Plotly plot in real-time.
"""

import argparse
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import time
import threading
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration variables for y-axis limits
# Set to None to use auto-scaling, or specify min/max values
Y_AXIS_LIMITS = {
    'current': {'ymin': None, 'ymax': None},      # Current plots (A)
    'voltage': {'ymin': None, 'ymax': None},      # Voltage plots (V)
    'pgood': {'ymin': None, 'ymax': None}         # Power-good signals
}

# Example custom limits (uncomment and modify as needed):
# Y_AXIS_LIMITS = {
#     'current': {'ymin': 0, 'ymax': 20},         # Force 0-20A range
#     'voltage': {'ymin': 0, 'ymax': 5},          # Force 0-5V range
#     'pgood': {'ymin': 0, 'ymax': 5}             # Force 0-5 range
# }


class LivePlotHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for live plot serving with auto-refresh."""
    
    def __init__(self, *args, plots_data=None, **kwargs):
        self.plots_data = plots_data or {}
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve main dashboard page
            self.serve_dashboard()
        elif parsed_path.path.startswith('/plot/'):
            # Serve individual plot with auto-refresh
            plot_type = parsed_path.path.split('/')[-1]
            self.serve_live_plot(plot_type)
        elif parsed_path.path == '/data':
            # Serve current plot data as JSON
            self.serve_plot_data()
        else:
            # Serve static files
            super().do_GET()
    
    def serve_dashboard(self):
        """Serve main dashboard with all plots."""
        dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Pico Data Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .plot-container { margin: 20px 0; border: 1px solid #ccc; padding: 10px; }
        .plot-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        iframe { width: 100%; height: 600px; border: none; }
        .status { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Live Pico Data Dashboard</h1>
    <div class="status">
        <strong>Status:</strong> <span id="status">Monitoring...</span> | 
        <strong>Last Update:</strong> <span id="last-update">Never</span>
    </div>
"""
        
        for plot_type in ['current', 'voltage', 'pgood']:
            if plot_type in self.plots_data:
                dashboard_html += f"""
    <div class="plot-container">
        <div class="plot-title">{plot_type.title()} Measurements (Live)</div>
        <iframe src="/plot/{plot_type}" id="{plot_type}-frame"></iframe>
    </div>
"""
        
        dashboard_html += """
    <script>
        // Auto-refresh dashboard status
        setInterval(() => {
            fetch('/data').then(response => response.json()).then(data => {
                document.getElementById('status').textContent = data.status;
                document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleTimeString();
            }).catch(err => console.log('Status update failed:', err));
        }, 1000);
    </script>
</body>
</html>
"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(dashboard_html.encode())
    
    def serve_live_plot(self, plot_type):
        """Serve individual plot with auto-refresh."""
        if plot_type not in self.plots_data:
            self.send_error(404, "Plot not found")
            return
        
        fig = self.plots_data[plot_type]
        html_content = fig.to_html(include_plotlyjs='cdn')
        
        # Add auto-refresh script
        refresh_script = """
<script>
    setInterval(() => {
        location.reload();
    }, 2000);  // Refresh every 2 seconds
</script>
"""
        
        html_content = html_content.replace('</body>', refresh_script + '</body>')
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_plot_data(self):
        """Serve current plot data as JSON."""
        data = {
            'status': 'Monitoring',
            'timestamp': time.time() * 1000,
            'plots': list(self.plots_data.keys())
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging for cleaner output."""
        pass


class CSVFileHandler(FileSystemEventHandler):
    """Handle CSV file changes for live monitoring."""
    
    def __init__(self, callback):
        self.callback = callback
        
    def on_modified(self, event):
        if event.src_path.endswith('.csv'):
            print(f"File updated: {event.src_path}")
            self.callback(event.src_path)


def parse_data_file(file_path):
    """Parse a tab-separated CSV file with timestamp and elapsed time columns."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        delimiter_line_idx = None
        header_line = None
        data_start_line = None

        for i, line in enumerate(lines):
            parts = line.strip().split('\t')
            if len(parts) >= 4 and parts[3].strip() == "==========":
                delimiter_line_idx = i
                if i + 1 < len(lines):
                    header_line = lines[i + 1].strip()
                data_start_line = i + 2
                break

        if header_line is None:
            return None, None

        headers = [h.strip() for h in header_line.split('\t') if h.strip()]

        data_lines = []
        for line in lines[data_start_line:]:
            if line and not line.startswith('[INFO]') and not line.startswith('LTMControl') and '==========' not in line:
                parts = [p.strip() for p in line.split('\t') if p.strip()]
                if len(parts) == len(headers):
                    data_lines.append(parts)

        if not data_lines:
            return None, None

        df = pd.DataFrame(data_lines, columns=headers)
        elapsed_col = df.columns[2]

        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna(subset=[elapsed_col])

        if len(df) > 0:
            df[elapsed_col] -= df[elapsed_col].iloc[0]

        return df, elapsed_col
            
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None


def categorize_columns(columns):
    current_cols = [col for col in columns if col.startswith('c_')]
    voltage_cols = [col for col in columns if col.startswith('v_')]
    pgood_cols = [col for col in columns if col.startswith('pg_')]
    return current_cols, voltage_cols, pgood_cols


def create_time_series_plot(df, time_col, data_cols, title, yaxis_title, dose_rate=None, num_ticks=10, ymin=None, ymax=None):
    if not data_cols:
        return None

    fig = go.Figure()

    colors = px.colors.qualitative.Set1

    for i, col in enumerate(data_cols):
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=6),
        ))

    # --- ticks ---
    tmin, tmax = df[time_col].min(), df[time_col].max()

    time_ticks = [
        tmin + (tmax - tmin) * i / (num_ticks - 1)
        for i in range(num_ticks)
    ]

    tid_labels = []

    if dose_rate is not None:
        # Compute TID labels
        tid_labels = [f"{t * dose_rate:.1f}" for t in time_ticks]

        # ✅ Dummy trace (required to force axis rendering)
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=[None] * len(df),   # no visible data
            xaxis='x2',
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.update_layout(
            xaxis2=dict(
                title=f"TID (rad) @ {dose_rate} rad/s",
                overlaying='x',
                side='top',

                # 🔥 alignment fix
                matches='x',
                anchor='y',

                tickmode='array',
                tickvals=time_ticks,
                ticktext=tid_labels,

                showline=True,
            )
        )

    # --- base layout ---
    fig.update_layout(
        title=title,
        xaxis=dict(
            title='Time (seconds)',
            tickmode='array',
            tickvals=time_ticks,
            ticktext=[f"{t:.1f}" for t in time_ticks],
            showgrid=True,
        ),
        yaxis=dict(
            title=yaxis_title,
            showgrid=True,
            range=[ymin, ymax] if ymin is not None and ymax is not None else None,
        ),
        font=dict(size=18),
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0.5,
            xanchor="center"
        ),
        margin=dict(b=150)
    )

    return fig


def update_plot(fig, df, time_col, data_cols, dose_rate=None, num_ticks=10, ymin=None, ymax=None):
    """Update existing plot with new data."""
    
    # Clear existing traces
    fig.data = []
    
    # Re-add traces with new data
    colors = px.colors.qualitative.Set1
    
    for i, col in enumerate(data_cols):
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=6),
        ))

    # Update ticks and layout
    tmin, tmax = df[time_col].min(), df[time_col].max()

    time_ticks = [
        tmin + (tmax - tmin) * i / (num_ticks - 1)
        for i in range(num_ticks)
    ]

    # Update x-axis ticks
    fig.update_xaxes(tickmode='array', tickvals=time_ticks, 
                  ticktext=[f"{t:.1f}" for t in time_ticks])

    # Update y-axis range if specified
    if ymin is not None and ymax is not None:
        fig.update_yaxes(range=[ymin, ymax])

    # Update TID axis if dose rate is provided
    if dose_rate is not None:
        tid_labels = [f"{t * dose_rate:.1f}" for t in time_ticks]
        
        # Add/update TID axis
        if 'xaxis2' not in fig.layout:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=[None] * len(df),
                xaxis='x2',
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(xaxis2=dict(
            title=f"TID (rad) @ {dose_rate} rad/s",
            overlaying='x',
            side='top',
            matches='x',
            anchor='y',
            tickmode='array',
            tickvals=time_ticks,
            ticktext=tid_labels,
            showline=True,
        ))


def save_plots_to_disk(plots, output_dir, base_name):
    """Save plots to disk (called periodically or on exit)."""
    print(f"Saving plots to disk...")
    for plot_type, fig in plots.items():
        output_file = os.path.join(output_dir, f"{base_name}_{plot_type}_live.html")
        fig.write_html(output_file)
        print(f"Saved: {output_file}")

def create_live_plots(file_path, output_dir, dose_rate=None, num_ticks=10, port=8080):
    """Create and display live plots that update when CSV file changes."""
    
    print(f"Starting live monitoring of: {file_path}")
    if dose_rate is not None:
        print(f"Using dose rate: {dose_rate} rad/s for TID calculation")
    
    # Parse initial data
    df, time_col = parse_data_file(file_path)
    if df is None:
        print("Error: Could not parse initial data")
        return
    
    print(f"Initial data shape: {df.shape}")
    print(f"Time column: {time_col}")
    
    # Categorize columns
    current_cols, voltage_cols, pgood_cols = categorize_columns(df.columns)
    
    print(f"Found {len(current_cols)} current columns: {current_cols}")
    print(f"Found {len(voltage_cols)} voltage columns: {voltage_cols}")
    print(f"Found {len(pgood_cols)} pgood columns: {pgood_cols}")
    
    # Create plots (memory only)
    plots = {}
    
    # Current plot
    if current_cols:
        plots['current'] = create_time_series_plot(
            df, time_col, current_cols,
            f'Current - {os.path.basename(file_path)} (LIVE)',
            'Current (A)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['current']['ymin'], Y_AXIS_LIMITS['current']['ymax']
        )

    # Voltage plot
    if voltage_cols:
        plots['voltage'] = create_time_series_plot(
            df, time_col, voltage_cols,
            f'Voltage - {os.path.basename(file_path)} (LIVE)',
            'Voltage (V)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['voltage']['ymin'], Y_AXIS_LIMITS['voltage']['ymax']
        )

    # Power-good plot
    if pgood_cols:
        plots['pgood'] = create_time_series_plot(
            df, time_col, pgood_cols,
            f'PowerGood - {os.path.basename(file_path)} (LIVE)',
            'Signal', dose_rate, num_ticks,
            Y_AXIS_LIMITS['pgood']['ymin'], Y_AXIS_LIMITS['pgood']['ymax']
        )

    # Function to update plots when file changes
    def on_file_updated(file_path):
        print(f"\n=== File updated: {file_path} ===")
        
        # Re-parse data
        new_df, time_col = parse_data_file(file_path)
        if new_df is None:
            print("Error: Could not parse updated data")
            return
        
        print(f"New data shape: {new_df.shape}")
        
        # Update each plot in memory only
        for plot_type, fig in plots.items():
            if plot_type == 'current':
                update_plot(fig, new_df, time_col, current_cols, dose_rate, num_ticks,
                          Y_AXIS_LIMITS['current']['ymin'], Y_AXIS_LIMITS['current']['ymax'])
            elif plot_type == 'voltage':
                update_plot(fig, new_df, time_col, voltage_cols, dose_rate, num_ticks,
                          Y_AXIS_LIMITS['voltage']['ymin'], Y_AXIS_LIMITS['voltage']['ymax'])
            elif plot_type == 'pgood':
                update_plot(fig, new_df, time_col, pgood_cols, dose_rate, num_ticks,
                          Y_AXIS_LIMITS['pgood']['ymin'], Y_AXIS_LIMITS['pgood']['ymax'])

    # Set up file watcher
    event_handler = CSVFileHandler(on_file_updated)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(file_path), recursive=False)
    observer.start()
    
    print(f"File watcher started. Monitoring {file_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Start web server
    def handler_factory(*args, **kwargs):
        return LivePlotHandler(*args, plots_data=plots, **kwargs)
    
    server = HTTPServer(('localhost', port), handler_factory)
    
    print(f"\n=== Live Plot Server Started ===")
    print(f"Dashboard URL: http://localhost:{port}")
    print(f"Individual plots:")
    for plot_type in plots.keys():
        print(f"  http://localhost:{port}/plot/{plot_type}")
    print(f"\nPress Ctrl+C to stop monitoring...")
    print("Plots will automatically refresh every 2 seconds when data is available.")
    print("Plots are saved to disk every 1 minute and on exit to reduce SSD wear.")
    
    try:
        # Start server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Open browser automatically
        import webbrowser
        webbrowser.open(f'http://localhost:{port}')
        
        # Periodic save timer (every 60 seconds)
        save_counter = 0
        save_interval = 60  # seconds
        
        # Keep script running to monitor file
        while True:
            time.sleep(1)
            save_counter += 1
            
            # Save to disk periodically
            if save_counter >= save_interval:
                save_plots_to_disk(plots, output_dir, base_name)
                save_counter = 0
                
    except KeyboardInterrupt:
        print("\nStopping live monitoring...")
        # Save final plots before exit
        save_plots_to_disk(plots, output_dir, base_name)
        print("Final plots saved to disk.")
        
        server.shutdown()
        observer.stop()
        observer.join()
        print("Live monitoring stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate live time series plots from Pico data files with real-time updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python plot_data_live.py ../data/log_2026-04-14_23-36-16_pirotest.csv --output-dir plots
    python plot_data_live.py ../data/log_2026-04-14_23-36-16_pirotest.csv --output-dir ../plots --dose-rate 5 --ticks 15
        """
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='Data files to plot (CSV format)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for plot files (default: current directory)'
    )
    
    parser.add_argument(
        '--dose-rate',
        type=float,
        help='Dose rate in rad/s for Total Ionizing Dose (TID) calculation on second x-axis'
    )
    
    parser.add_argument('--ticks', type=int, default=10, help='Number of ticks on axes (default: 10)')
    parser.add_argument('--port', type=int, default=8080, help='Port for web server (default: 8080)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each file
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found, skipping...")
            continue
        
        create_live_plots(file_path, args.output_dir, args.dose_rate, args.ticks, args.port)


if __name__ == "__main__":
    main()
