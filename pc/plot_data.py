#!/usr/bin/env python3
"""
Time series plotting script for Pico data files.
"""

import argparse
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# Configuration variables for y-axis limits
# Set to None to use auto-scaling, or specify min/max values
Y_AXIS_LIMITS = {
    'current': {'ymin': 0, 'ymax': 15},      # Current plots (A)
    'voltage': {'ymin': None, 'ymax': None},      # Voltage plots (V)
    'pgood': {'ymin': None, 'ymax': None}         # Power-good signals
}

# Example custom limits (uncomment and modify as needed):
# Y_AXIS_LIMITS = {
#     'current': {'ymin': 0, 'ymax': 20},         # Force 0-20A range
#     'voltage': {'ymin': 0, 'ymax': 5},          # Force 0-5V range
#     'pgood': {'ymin': 0, 'ymax': 5}             # Force 0-5 range
# }


def parse_data_file(file_path):
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
            line = line.strip()
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

    # --- second axis (FIXED) ---
    if dose_rate is not None:
        fig.update_layout(
            xaxis2=dict(
                title=f"TID (rad) @ {dose_rate} rad/s",
                overlaying='x',
                side='top',

                # 🔥 critical fixes
                matches='x',
                anchor='y',

                tickmode='array',
                tickvals=time_ticks,
                ticktext=tid_labels,

                showline=True,
            )
        )

    return fig


def plot_file_data(file_path, output_dir, dose_rate=None, num_ticks=10):
    df, time_col = parse_data_file(file_path)
    if df is None:
        return

    current_cols, voltage_cols, pgood_cols = categorize_columns(df.columns)

    plots = []

    if current_cols:
        plots.append(('current', create_time_series_plot(
            df, time_col, current_cols,
            f'Current - {os.path.basename(file_path)}',
            'Current (A)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['current']['ymin'], Y_AXIS_LIMITS['current']['ymax'])))

    if voltage_cols:
        plots.append(('voltage', create_time_series_plot(
            df, time_col, voltage_cols,
            f'Voltage - {os.path.basename(file_path)}',
            'Voltage (V)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['voltage']['ymin'], Y_AXIS_LIMITS['voltage']['ymax'])))

    if pgood_cols:
        plots.append(('pgood', create_time_series_plot(
            df, time_col, pgood_cols,
            f'PowerGood - {os.path.basename(file_path)}',
            'Signal', dose_rate, num_ticks,
            Y_AXIS_LIMITS['pgood']['ymin'], Y_AXIS_LIMITS['pgood']['ymax'])))

    base = os.path.splitext(os.path.basename(file_path))[0]

    for name, fig in plots:
        if fig:
            out = os.path.join(output_dir, f"{base}_{name}.html")
            fig.write_html(out)
            print(f"Saved: {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--output-dir', default='.')
    parser.add_argument('--dose-rate', type=float)
    parser.add_argument('--ticks', type=int, default=10, help='Number of ticks on axes (default: 10)')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    for f in args.files:
        if os.path.exists(f):
            plot_file_data(f, args.output_dir, args.dose_rate, args.ticks)


if __name__ == "__main__":
    main()