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
    'current': {'ymin': None, 'ymax': None},      # Current plots (A)
    'voltage': {'ymin': None, 'ymax': None},      # Voltage plots (V)
    'pgood': {'ymin': None, 'ymax': None},        # Power-good signals
    'power': {'ymin': None, 'ymax': None}         # Power states
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

        # Handle power state columns (ATX, LTM) as strings
        power_cols = [col for col in headers if col in ['ATX', 'LTM']]
        numeric_cols = [col for col in headers if col not in power_cols]
        
        # Convert numeric columns
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df = df.dropna(subset=[elapsed_col])
        
        # Convert ON/OFF to 1/0 for power columns
        for col in power_cols:
            if col in df.columns:
                df[col] = df[col].map({'ON': 1, 'OFF': 0})

        if len(df) > 0:
            df[elapsed_col] -= df[elapsed_col].iloc[0]

        return df, elapsed_col

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None


def get_dose_rate_with_unit(dose_rate, time_unit_label='seconds'):
    """Convert dose rate from Gy/s to appropriate unit based on time unit."""
    if dose_rate is None:
        return None, None
    
    conversion_factors = {
        'seconds': (1.0, 'Gy/s'),
        'minutes': (60.0, 'Gy/min'),
        'hours': (3600.0, 'Gy/h'),
        'days': (86400.0, 'Gy/day')
    }
    
    factor, unit = conversion_factors.get(time_unit_label, (1.0, 'Gy/s'))
    return dose_rate * factor, unit


def categorize_columns(columns):
    current_cols = [col for col in columns if col.startswith('c_')]
    voltage_cols = [col for col in columns if col.startswith('v_')]
    pgood_cols = [col for col in columns if col.startswith('pg_')]
    power_cols = [col for col in columns if col in ['ATX', 'LTM']]
    return current_cols, voltage_cols, pgood_cols, power_cols


def create_time_series_plot(df, time_col, data_cols, title, yaxis_title, dose_rate=None, num_ticks=10, ymin=None, ymax=None, time_unit_label='seconds'):
    if not data_cols:
        return None

    # Time unit conversion factors
    time_factors = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0
    }
    time_factor = time_factors.get(time_unit_label, 1.0)

    fig = go.Figure()

    colors = px.colors.qualitative.Set1

    for i, col in enumerate(data_cols):
        fig.add_trace(go.Scatter(
            x=df[time_col] / time_factor,
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=6),
        ))

    # --- ticks ---
    tmin_raw, tmax_raw = df[time_col].min(), df[time_col].max()
    tmin = tmin_raw / time_factor
    tmax = tmax_raw / time_factor

    time_ticks = [
        tmin + (tmax - tmin) * i / (num_ticks - 1)
        for i in range(num_ticks)
    ]

    tid_labels = []

    if dose_rate is not None:
        # Compute TID labels based on raw time values
        time_ticks_raw = [t * time_factor for t in time_ticks]
        tid_labels = [f"{t_raw * dose_rate:.1f}" for t_raw in time_ticks_raw]

        # Dummy trace (required to force axis rendering)
        fig.add_trace(go.Scatter(
            x=df[time_col] / time_factor,
            y=[None] * len(df),   # no visible data
            xaxis='x2',
            showlegend=False,
            hoverinfo='skip'
        ))

        # Convert dose rate for display unit
        dose_rate_display, dose_unit = get_dose_rate_with_unit(dose_rate, time_unit_label)
        
        fig.update_layout(
            xaxis2=dict(
                title=dict(text=f"TID (Gy) @ {dose_rate_display:.3g} {dose_unit}", font=dict(size=26)),
                overlaying='x',
                side='top',
                matches='x',
                anchor='y',
                tickmode='array',
                tickvals=time_ticks,
                ticktext=tid_labels,
                tickfont=dict(size=22),
                showline=True,
                showgrid=False,
            )
        )

    # --- base layout ---
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        xaxis=dict(
            title=dict(text=f'Time ({time_unit_label})', font=dict(size=26)),
            tickmode='array',
            tickvals=time_ticks,
            ticktext=[f"{t:.2f}" if time_unit_label in ['hours', 'days'] else f"{t:.1f}" for t in time_ticks],
            tickfont=dict(size=22),
            showgrid=True,
        ),
        yaxis=dict(
            title=dict(text=yaxis_title, font=dict(size=26)),
            showgrid=True,
            range=[ymin, ymax] if ymin is not None and ymax is not None else None,
            tickfont=dict(size=22),
        ),
        font=dict(size=28),
        legend=dict(
            orientation="h",
            y=-0.15,
            x=0.5,
            xanchor="center",
            font=dict(size=24)
        ),
        margin=dict(b=150)
    )

    return fig


def create_power_state_plot(df, time_col, power_cols, title, dose_rate=None, num_ticks=10, ymin=None, ymax=None, time_unit_label='seconds'):
    """Create a plot for ATX/LTM power states with categorical y-axis."""
    if not power_cols:
        return None

    # Time unit conversion factors
    time_factors = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0
    }
    time_factor = time_factors.get(time_unit_label, 1.0)

    fig = go.Figure()

    colors = px.colors.qualitative.Set1

    # Define categorical y-axis positions
    state_positions = {
        'atx_on': 3,
        'atx_off': 2,
        'ltm_on': 1,
        'ltm_off': 0
    }

    # Create continuous traces for ATX and LTM that show state transitions
    for col in power_cols:
        if col in df.columns:
            # Create continuous trace that moves between ON and OFF positions
            y_values = []
            for _, row in df.iterrows():
                if row[col] == 1:  # ON state
                    y_values.append(state_positions[f'{col.lower()}_on'])
                else:  # OFF state
                    y_values.append(state_positions[f'{col.lower()}_off'])

            fig.add_trace(go.Scatter(
                x=df[time_col] / time_factor,
                y=y_values,
                mode='lines+markers',
                name=col,
                line=dict(color=colors[0] if col == 'ATX' else colors[1], width=2),
                marker=dict(size=4),
                yaxis='y'
            ))

    # --- ticks ---
    tmin_raw, tmax_raw = df[time_col].min(), df[time_col].max()
    tmin = tmin_raw / time_factor
    tmax = tmax_raw / time_factor

    time_ticks = [
        tmin + (tmax - tmin) * i / (num_ticks - 1)
        for i in range(num_ticks)
    ]

    tid_labels = []

    if dose_rate is not None:
        # Compute TID labels based on raw time values
        time_ticks_raw = [t * time_factor for t in time_ticks]
        tid_labels = [f"{t_raw * dose_rate:.1f}" for t_raw in time_ticks_raw]

        # Dummy trace (required to force axis rendering)
        fig.add_trace(go.Scatter(
            x=df[time_col] / time_factor,
            y=[None] * len(df),   # no visible data
            xaxis='x2',
            showlegend=False,
            hoverinfo='skip'
        ))

        # Convert dose rate for display unit
        dose_rate_display, dose_unit = get_dose_rate_with_unit(dose_rate, time_unit_label)
        
        fig.update_layout(
            xaxis2=dict(
                title=dict(text=f"TID (Gy) @ {dose_rate_display:.3g} {dose_unit}", font=dict(size=26)),
                overlaying='x',
                side='top',
                matches='x',
                anchor='y',
                tickmode='array',
                tickvals=time_ticks,
                ticktext=tid_labels,
                tickfont=dict(size=22),
                showline=True,
                showgrid=False,
            )
        )

    # --- base layout ---
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        xaxis=dict(
            title=dict(text=f'Time ({time_unit_label})', font=dict(size=26)),
            tickmode='array',
            tickvals=time_ticks,
            ticktext=[f"{t:.2f}" if time_unit_label in ['hours', 'days'] else f"{t:.1f}" for t in time_ticks],
            tickfont=dict(size=22),
            showgrid=True,
        ),
        yaxis=dict(
            title=dict(text='Power State', font=dict(size=26)),
            showgrid=True,
            range=[-0.5, 3.5],  # Fixed range for all 4 categorical states
            tickmode='array',
            tickvals=[0, 1, 2, 3],
            ticktext=['ltm_off', 'ltm_on', 'atx_off', 'atx_on'],
            tickfont=dict(size=22),
        ),
        font=dict(size=28),
        legend=dict(
            orientation="h",
            y=-0.15,
            x=0.5,
            xanchor="center",
            font=dict(size=24)
        ),
        margin=dict(b=150)
    )

    return fig


def plot_file_data(file_path, output_dir, dose_rate=None, num_ticks=10, time_unit='seconds', max_points=None):
    df, time_col = parse_data_file(file_path)
    if df is None:
        return

    # Limit data points if max_points is specified
    if max_points is not None and max_points > 0 and len(df) > max_points:
        step = max(1, (len(df) - 1) // (max_points - 1))
        indices = list(range(0, len(df), step))
        if indices[-1] != len(df) - 1:
            indices.append(len(df) - 1)
        df = df.iloc[indices]

    current_cols, voltage_cols, pgood_cols, power_cols = categorize_columns(df.columns)

    plots = []

    if current_cols:
        plots.append(('current', create_time_series_plot(
            df, time_col, current_cols,
            f'Current - {os.path.basename(file_path)}',
            'Current (A)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['current']['ymin'], Y_AXIS_LIMITS['current']['ymax'], time_unit)))

    if voltage_cols:
        plots.append(('voltage', create_time_series_plot(
            df, time_col, voltage_cols,
            f'Voltage - {os.path.basename(file_path)}',
            'Voltage (V)', dose_rate, num_ticks,
            Y_AXIS_LIMITS['voltage']['ymin'], Y_AXIS_LIMITS['voltage']['ymax'], time_unit)))

    if pgood_cols:
        plots.append(('pgood', create_time_series_plot(
            df, time_col, pgood_cols,
            f'PowerGood - {os.path.basename(file_path)}',
            'Signal', dose_rate, num_ticks,
            Y_AXIS_LIMITS['pgood']['ymin'], Y_AXIS_LIMITS['pgood']['ymax'], time_unit)))

    if power_cols:
        plots.append(('power', create_power_state_plot(
            df, time_col, power_cols,
            f'Power States - {os.path.basename(file_path)}',
            dose_rate, num_ticks,
            Y_AXIS_LIMITS['power']['ymin'], Y_AXIS_LIMITS['power']['ymax'], time_unit)))

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
    parser.add_argument('--time-unit', default='seconds', choices=['seconds', 'minutes', 'hours', 'days'],
                        help='Time unit for x-axis display (default: seconds)')
    parser.add_argument('--max-points', type=int, default=None,
                        help='Maximum number of data points to plot (default: all points)')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    for f in args.files:
        if os.path.exists(f):
            plot_file_data(f, args.output_dir, args.dose_rate, args.ticks, args.time_unit, args.max_points)


if __name__ == "__main__":
    main()