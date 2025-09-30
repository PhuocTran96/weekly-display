#!/usr/bin/env python3
"""
Unified Chart Generator for Display Tracking
Combines functionality from chart_script.py and chart_script_1.py
Generates both increase and decrease charts with flexible data input
"""

import plotly.graph_objects as go
import pandas as pd
import json
import argparse
from pathlib import Path

class ChartGenerator:
    """Generate charts for display tracking increases and decreases"""

    def __init__(self):
        self.brand_colors = {
            'increase': '#2E8B57',  # Sea green
            'decrease': '#DB4545',  # Red
            'neutral': '#5A7C95'    # Blue-gray
        }

    def create_increase_chart(self, data=None, title="Top Models: Display Increases", output_prefix="increases"):
        """
        Create chart for model increases
        data: dict with 'Model' and 'Diff' keys, or None for default data
        """
        if data is None:
            # Default data from original chart_script.py
            data = {
                "Model": ["EWF1023P5WC", "EDV904H3WC", "EWF1023P5SC", "EDV804H3WC", "EDV904N3SC",
                         "EWF1043R7SC", "ETD42SKS", "EWW1023P5SC", "EHG8251BC", "EDH803J5SC",
                         "EWF1043R7WC", "EWF9023P5SC", "EDS904H3WC", "EDS904N3SC", "EDH803J5WC"],
                "Diff": [65, 63, 59, 58, 58, 58, 56, 55, 55, 55, 54, 54, 54, 54, 54]
            }

        df = pd.DataFrame(data)

        # Create horizontal bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['Diff'],
            y=df['Model'],
            orientation='h',
            marker_color=self.brand_colors['increase'],
            text=df['Diff'],
            textposition='outside',
            textfont=dict(size=12)
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title='Increase Count',
            yaxis_title='Model Name',
            showlegend=False,
            height=max(400, len(df) * 25),  # Dynamic height based on data
            margin=dict(l=150, r=50, t=50, b=50)  # Better margins for model names
        )

        # Update traces for better appearance
        fig.update_traces(cliponaxis=False)

        # Reverse y-axis order so highest values appear at top
        fig.update_yaxes(autorange="reversed")

        # Save charts
        self._save_chart(fig, output_prefix)

        return fig

    def create_decrease_chart(self, data=None, title="Top Models: Display Decreases", output_prefix="decreases"):
        """
        Create chart for model decreases
        data: dict with 'Model' and 'Diff' keys (negative values), or None for default data
        """
        if data is None:
            # Default data from original chart_script_1.py
            models = ["EDV854N3SB", "EWE451KB-DWG2", "EWE451LB-DPX2", "EWF1042R7SB",
                     "EWF1141R9SB", "EWF9024P5SB", "EQE6000A-B", "ESF5206LOW", "EWF1024P5SB", "ESI5116"]
            diff_values = [-4, -3, -3, -3, -3, -2, -2, -1, -1, -1]

            # Reverse so largest decrease appears at top
            models_reversed = models[::-1]
            diff_values_reversed = diff_values[::-1]
        else:
            # Assume data is already formatted properly
            df = pd.DataFrame(data)
            models_reversed = df['Model'].tolist()
            diff_values_reversed = df['Diff'].tolist()

        # Create horizontal bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=diff_values_reversed,
            y=models_reversed,
            orientation='h',
            marker_color=self.brand_colors['decrease'],
            text=diff_values_reversed,
            textposition='auto',
            texttemplate='%{text}'
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Decrease Count",
            yaxis_title="Model Name",
            showlegend=False,
            height=max(400, len(models_reversed) * 25),  # Dynamic height
            margin=dict(l=150, r=50, t=50, b=50)
        )

        # Update traces for clipping
        fig.update_traces(cliponaxis=False)

        # Save charts
        self._save_chart(fig, output_prefix)

        return fig

    def create_combined_chart(self, increases_data, decreases_data, title="Model Display Changes", output_prefix="combined"):
        """
        Create a combined chart showing both increases and decreases
        """
        fig = go.Figure()

        # Add increases
        if increases_data:
            inc_df = pd.DataFrame(increases_data)
            fig.add_trace(go.Bar(
                x=inc_df['Diff'],
                y=inc_df['Model'],
                orientation='h',
                marker_color=self.brand_colors['increase'],
                name='Increases',
                text=inc_df['Diff'],
                textposition='outside'
            ))

        # Add decreases
        if decreases_data:
            dec_df = pd.DataFrame(decreases_data)
            fig.add_trace(go.Bar(
                x=dec_df['Diff'],
                y=dec_df['Model'],
                orientation='h',
                marker_color=self.brand_colors['decrease'],
                name='Decreases',
                text=dec_df['Diff'],
                textposition='outside'
            ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Change Count",
            yaxis_title="Model Name",
            showlegend=True,
            height=600,
            margin=dict(l=150, r=50, t=50, b=50)
        )

        fig.update_traces(cliponaxis=False)

        # Save charts
        self._save_chart(fig, output_prefix)

        return fig

    def _save_chart(self, fig, prefix):
        """Save chart as both PNG and SVG"""
        import os
        import sys
        import traceback

        # Use absolute path to charts directory
        charts_dir = os.path.abspath('charts')
        os.makedirs(charts_dir, exist_ok=True)

        # Save to charts directory
        png_file = os.path.join(charts_dir, f"{prefix}_chart.png")
        svg_file = os.path.join(charts_dir, f"{prefix}_chart.svg")

        try:
            print(f"Attempting to save PNG chart to: {png_file}")
            print(f"Python version: {sys.version}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Running as user: {os.getenv('USER', 'unknown')}")
            print(f"HOME: {os.getenv('HOME', 'not set')}")
            print(f"TMPDIR: {os.getenv('TMPDIR', 'not set')}")

            fig.write_image(png_file)
            fig.write_image(svg_file, format='svg')
            print(f"Charts saved successfully: {png_file}, {svg_file}")
        except Exception as e:
            print(f"Error saving charts: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Full traceback:")
            traceback.print_exc()
            # Try to save as HTML fallback
            html_file = os.path.join(charts_dir, f"{prefix}_chart.html")
            fig.write_html(html_file)
            print(f"Saved as HTML fallback: {html_file}")
            raise e

    def load_data_from_json(self, json_file):
        """Load data from JSON alert summary file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            increases_data = None
            decreases_data = None

            if 'top_increases' in data:
                increases_data = {
                    'Model': [item['Model'] for item in data['top_increases']],
                    'Diff': [item['Diff'] for item in data['top_increases']]
                }

            if 'top_decreases' in data:
                decreases_data = {
                    'Model': [item['Model'] for item in data['top_decreases']],
                    'Diff': [item['Diff'] for item in data['top_decreases']]
                }

            return increases_data, decreases_data

        except Exception as e:
            print(f"Error loading data from {json_file}: {e}")
            return None, None

    def generate_all_charts(self, json_file=None, week_num=None):
        """Generate all chart types"""
        if json_file and Path(json_file).exists():
            print(f"Loading data from {json_file}...")
            increases_data, decreases_data = self.load_data_from_json(json_file)

            week_suffix = f" W{week_num}" if week_num else ""

            if increases_data:
                self.create_increase_chart(
                    increases_data,
                    f"Top Model Display Increases{week_suffix}",
                    f"week_{week_num}_increases" if week_num else "increases"
                )

            if decreases_data:
                self.create_decrease_chart(
                    decreases_data,
                    f"Top Model Display Decreases{week_suffix}",
                    f"week_{week_num}_decreases" if week_num else "decreases"
                )

            if increases_data and decreases_data:
                self.create_combined_chart(
                    increases_data,
                    decreases_data,
                    f"Model Display Changes{week_suffix}",
                    f"week_{week_num}_combined" if week_num else "combined"
                )
        else:
            print("Using default data...")
            # Use default data from original scripts
            self.create_increase_chart()
            self.create_decrease_chart()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Generate display tracking charts')
    parser.add_argument('--json', help='JSON file with alert data')
    parser.add_argument('--week', type=int, help='Week number for titles')
    parser.add_argument('--type', choices=['increases', 'decreases', 'combined', 'all'],
                       default='all', help='Type of chart to generate')

    args = parser.parse_args()

    generator = ChartGenerator()

    if args.type == 'all':
        generator.generate_all_charts(args.json, args.week)
    elif args.json:
        increases_data, decreases_data = generator.load_data_from_json(args.json)
        week_suffix = f" W{args.week}" if args.week else ""

        if args.type == 'increases' and increases_data:
            generator.create_increase_chart(increases_data, f"Top Model Display Increases{week_suffix}")
        elif args.type == 'decreases' and decreases_data:
            generator.create_decrease_chart(decreases_data, f"Top Model Display Decreases{week_suffix}")
        elif args.type == 'combined' and increases_data and decreases_data:
            generator.create_combined_chart(increases_data, decreases_data, f"Model Display Changes{week_suffix}")
    else:
        # Use default data
        if args.type == 'increases':
            generator.create_increase_chart()
        elif args.type == 'decreases':
            generator.create_decrease_chart()

if __name__ == "__main__":
    main()