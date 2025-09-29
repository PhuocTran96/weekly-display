#!/usr/bin/env python3
"""
Unified Display Tracking Scripts
Combines all functionality from script_*.py files into a single executable script.
This includes data exploration, processing, and the complete tracking system.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('logs', 'unified_scripts.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def explore_data(report_file='report-week-38.csv', raw_file='raw-display-w39.csv'):
    """
    Data exploration functionality from initial scripts
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting data exploration...")

    try:
        # Load initial data (from script_1.py)
        rep_df = pd.read_csv(report_file, encoding='utf-8')
        raw_df = pd.read_csv(raw_file, encoding='utf-8')

        logger.info(f"Report data shape: {rep_df.shape}")
        logger.info(f"Raw data shape: {raw_df.shape}")
        logger.info(f"Report columns (first 10): {rep_df.columns[:10].tolist()}")

        # Display sample data
        print("=== DATA EXPLORATION ===")
        print(f"Report DataFrame shape: {rep_df.shape}")
        print(f"Raw DataFrame shape: {raw_df.shape}")
        print("\nRaw data sample:")
        print(raw_df.head())
        print(f"\nReport columns (first 10): {rep_df.columns[:10].tolist()}")

        return rep_df, raw_df

    except Exception as e:
        logger.error(f"Error in data exploration: {e}")
        raise

def process_and_merge_data(rep_df, raw_df):
    """
    Core data processing and merging functionality
    Combines logic from scripts 3-6
    """
    logger = logging.getLogger(__name__)
    logger.info("Processing and merging data...")

    try:
        # Define dimension columns
        dims = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']

        # Clean report data (from script_3.py)
        rep_clean = rep_df.copy()
        for col in rep_clean.columns[4:]:
            rep_clean[col] = pd.to_numeric(rep_clean[col].replace(' -   ', 0))

        # Process raw data
        raw_df['Value'] = pd.to_numeric(raw_df['Value'])
        raw_pivot = raw_df.pivot_table(
            index=dims,
            columns='Model',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Convert IDs to string (from script_4.py)
        for col in dims:
            rep_clean[col] = rep_clean[col].astype(str)
            raw_pivot[col] = raw_pivot[col].astype(str)

        # Merge datasets (from script_5.py)
        merged = rep_clean.merge(raw_pivot, on=dims, how='outer', suffixes=('_old', '_add'))

        # Fill NaN with 0 for numeric columns
        for col in merged.columns[4:]:
            merged[col] = merged[col].fillna(0)

        # Identify model column pairs
        model_cols = []
        for col in merged.columns[4:]:
            if col.endswith('_old'):
                base = col[:-4]
                add_col = base + '_add'
                if add_col in merged.columns:
                    model_cols.append((base, col, add_col))
                else:
                    merged[add_col] = 0
                    model_cols.append((base, col, add_col))

        # Compute updated cumulative values
        for base, old_col, add_col in model_cols:
            merged[base] = merged[old_col] + merged[add_col]

        logger.info(f"Merged data shape: {merged.shape}")
        logger.info(f"Model columns identified: {len(model_cols)}")

        return merged, model_cols, rep_clean, raw_pivot

    except Exception as e:
        logger.error(f"Error in data processing: {e}")
        raise

def analyze_changes(rep_clean, raw_pivot, dims):
    """
    Change analysis using long format approach
    From script_6.py
    """
    logger = logging.getLogger(__name__)
    logger.info("Analyzing changes...")

    try:
        # Build long format of old counts
        old_long = rep_clean.melt(
            id_vars=dims,
            value_vars=rep_clean.columns[4:],
            var_name='Model',
            value_name='Prev'
        )

        # Build long format of current counts
        raw_melt = raw_pivot.melt(
            id_vars=dims,
            value_vars=[c for c in raw_pivot.columns if c not in dims],
            var_name='Model',
            value_name='Curr'
        )

        # Combine and compute differences
        combined = old_long.merge(raw_melt, on=dims+['Model'], how='outer')
        combined['Prev'] = combined['Prev'].fillna(0)
        combined['Curr'] = combined['Curr'].fillna(0)
        combined['Diff'] = combined['Curr'] - combined['Prev']

        # Aggregate by model
        model_diff = combined.groupby('Model')[['Prev', 'Curr', 'Diff']].sum().reset_index()

        # Compute increased and decreased lists
        increased = model_diff[model_diff['Diff'] > 0].sort_values('Diff', ascending=False)
        decreased = model_diff[model_diff['Diff'] < 0].sort_values('Diff')
        unchanged = model_diff[model_diff['Diff'] == 0]

        logger.info(f"Models increased: {len(increased)}")
        logger.info(f"Models decreased: {len(decreased)}")
        logger.info(f"Models unchanged: {len(unchanged)}")

        return model_diff, increased, decreased, unchanged, combined

    except Exception as e:
        logger.error(f"Error in change analysis: {e}")
        raise

def generate_reports(merged, model_cols, increased, decreased, unchanged, week_num=39):
    """
    Generate output reports and summaries
    From scripts 8-11
    """
    logger = logging.getLogger(__name__)
    logger.info("Generating reports...")

    try:
        dims = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']

        # Print analysis results (from scripts 8-9)
        print("\n=== CHANGE ANALYSIS RESULTS ===")
        print('Top 10 increases:')
        print(increased.head(10))
        print('\nTop 10 decreases:')
        print(decreased.head(10))

        # Save updated weekly report (from script_10.py)
        updated_report = merged.copy()
        final_cols = dims + [base for base, _, _ in model_cols[:50]]  # Limit columns
        updated_report_clean = updated_report[final_cols[:min(len(final_cols), 100)]]

        report_filename = f'report-week-{week_num}.csv'
        updated_report_clean.to_csv(report_filename, index=False, encoding='utf-8')

        # Create change alerts summary (from script_11.py)
        alert_summary = {
            'week': week_num,
            'total_models_tracked': len(increased) + len(decreased) + len(unchanged),
            'models_increased': len(increased),
            'models_decreased': len(decreased),
            'models_unchanged': len(unchanged),
            'top_increases': increased.head(15).to_dict('records'),
            'top_decreases': decreased.head(10).to_dict('records')
        }

        alert_filename = f'weekly_alert_report_unified.json'
        with open(alert_filename, 'w', encoding='utf-8') as f:
            json.dump(alert_summary, f, indent=2, ensure_ascii=False)

        print(f"\n=== REPORTS GENERATED ===")
        print(f"Updated report saved: {report_filename} (shape: {updated_report_clean.shape})")
        print(f"Alert summary saved: {alert_filename}")
        print(f"\nWeek {week_num} Analysis Summary:")
        print(f"- Models increased: {alert_summary['models_increased']}")
        print(f"- Models decreased: {alert_summary['models_decreased']}")
        print(f"- Models unchanged: {alert_summary['models_unchanged']}")
        print(f"- Total models tracked: {alert_summary['total_models_tracked']}")

        logger.info(f"Reports generated successfully")
        return report_filename, alert_filename, alert_summary

    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        raise

class DisplayTracker:
    """
    Complete DisplayTracker class from script_12.py / display_tracking_system.py
    Integrated into the unified script
    """
    def __init__(self, log_file='display_tracker.log'):
        # Setup logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_report_data(self, report_file):
        """Load and clean previous week report data"""
        try:
            df = pd.read_csv(report_file, encoding='utf-8')
            # Clean data: convert '-' to 0 and make numeric
            for col in df.columns[4:]:
                df[col] = pd.to_numeric(df[col].replace(' -   ', 0))

            # Convert ID columns to string
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            for col in id_cols:
                df[col] = df[col].astype(str)

            self.logger.info(f"Loaded report data: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading report data: {e}")
            raise

    def load_raw_data(self, raw_file):
        """Load and process raw display data"""
        try:
            df = pd.read_csv(raw_file, encoding='utf-8')
            df['Value'] = pd.to_numeric(df['Value'])

            # Convert ID columns to string
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            for col in id_cols:
                df[col] = df[col].astype(str)

            # Pivot to store-model format
            pivot_df = df.pivot_table(
                index=id_cols,
                columns='Model',
                values='Value',
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            self.logger.info(f"Loaded and pivoted raw data: {pivot_df.shape}")
            return pivot_df
        except Exception as e:
            self.logger.error(f"Error loading raw data: {e}")
            raise

    def merge_and_update(self, report_df, raw_pivot_df):
        """Merge previous report with new raw data"""
        try:
            # Merge datasets
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            merged = report_df.merge(
                raw_pivot_df,
                on=id_cols,
                how='outer',
                suffixes=('_old', '_add')
            )

            # Fill NaN with 0
            for col in merged.columns[4:]:
                merged[col] = merged[col].fillna(0)

            # Identify model column pairs and compute new totals
            model_cols = []
            for col in merged.columns[4:]:
                if col.endswith('_old'):
                    base = col[:-4]
                    add_col = base + '_add'
                    if add_col in merged.columns:
                        model_cols.append((base, col, add_col))
                        merged[base] = merged[col] + merged[add_col]
                    else:
                        merged[add_col] = 0
                        model_cols.append((base, col, add_col))
                        merged[base] = merged[col]

            # Create final updated report
            final_cols = id_cols + [base for base, _, _ in model_cols]
            updated_report = merged[final_cols]

            self.logger.info(f"Merged data successfully: {updated_report.shape}")
            return updated_report, model_cols, merged

        except Exception as e:
            self.logger.error(f"Error merging data: {e}")
            raise

    def generate_alerts(self, merged_df, model_cols):
        """Generate change alerts for models"""
        try:
            # Create long format for analysis
            changes = []
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']

            for base, old_col, add_col in model_cols:
                for idx, row in merged_df.iterrows():
                    prev_val = row[old_col]
                    curr_val = row[old_col] + row[add_col]  # Cumulative total
                    diff = curr_val - prev_val

                    if diff != 0:  # Only track changes
                        changes.append({
                            'Elux_ID': row['Elux ID'],
                            'Dealer_ID': row['Dealer ID'],
                            'Channel': row['Channel'],
                            'Store_name': row['Store_name'],
                            'Model': base,
                            'Previous': prev_val,
                            'Current': curr_val,
                            'Difference': diff,
                            'Change_Type': 'Increase' if diff > 0 else 'Decrease'
                        })

            changes_df = pd.DataFrame(changes)

            # Generate model summary
            model_summary = changes_df.groupby('Model').agg({
                'Previous': 'sum',
                'Current': 'sum',
                'Difference': 'sum'
            }).reset_index()

            # Split increases and decreases
            increases = model_summary[model_summary['Difference'] > 0].sort_values('Difference', ascending=False)
            decreases = model_summary[model_summary['Difference'] < 0].sort_values('Difference')

            alert_summary = {
                'timestamp': datetime.now().isoformat(),
                'total_models_tracked': len(model_summary),
                'models_increased': len(increases),
                'models_decreased': len(decreases),
                'models_unchanged': len(model_cols) - len(model_summary),
                'top_increases': increases.head(15).to_dict('records'),
                'top_decreases': decreases.head(10).to_dict('records'),
                'all_changes': changes_df.to_dict('records')
            }

            self.logger.info(f"Generated alerts: {len(changes)} total changes")
            return alert_summary

        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            raise

    def save_results(self, updated_report, alert_summary, week_num):
        """Save updated report and alert summary"""
        try:
            # Save updated report
            report_filename = f'report-week-{week_num}.csv'
            updated_report.to_csv(report_filename, index=False, encoding='utf-8')

            # Save alert summary
            alert_filename = f'alerts-week-{week_num}.json'
            with open(alert_filename, 'w', encoding='utf-8') as f:
                json.dump(alert_summary, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved results: {report_filename}, {alert_filename}")
            return report_filename, alert_filename

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise

    def process_weekly_data(self, raw_file, previous_report_file, week_num):
        """Main processing function"""
        try:
            self.logger.info(f"Starting weekly processing for Week {week_num}")

            # Load data
            report_df = self.load_report_data(previous_report_file)
            raw_pivot_df = self.load_raw_data(raw_file)

            # Merge and update
            updated_report, model_cols, merged_df = self.merge_and_update(report_df, raw_pivot_df)

            # Generate alerts
            alert_summary = self.generate_alerts(merged_df, model_cols)

            # Save results
            report_file, alert_file = self.save_results(updated_report, alert_summary, week_num)

            self.logger.info(f"Weekly processing completed successfully")

            return {
                'success': True,
                'updated_report_file': report_file,
                'alert_file': alert_file,
                'summary': {
                    'models_increased': alert_summary['models_increased'],
                    'models_decreased': alert_summary['models_decreased'],
                    'total_changes': len(alert_summary['all_changes'])
                }
            }

        except Exception as e:
            self.logger.error(f"Weekly processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """
    Main execution function that runs all unified functionality
    """
    logger = setup_logging()
    logger.info("Starting unified scripts execution...")

    try:
        print("=" * 60)
        print("UNIFIED DISPLAY TRACKING SCRIPTS")
        print("=" * 60)

        # Step 1: Data exploration
        rep_df, raw_df = explore_data()

        # Step 2: Process and merge data
        merged, model_cols, rep_clean, raw_pivot = process_and_merge_data(rep_df, raw_df)

        # Step 3: Analyze changes
        dims = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
        model_diff, increased, decreased, unchanged, combined = analyze_changes(rep_clean, raw_pivot, dims)

        # Step 4: Generate reports
        report_file, alert_file, alert_summary = generate_reports(merged, model_cols, increased, decreased, unchanged)

        # Step 5: Run complete DisplayTracker system
        print("\n" + "=" * 60)
        print("RUNNING COMPLETE DISPLAYTRACKER SYSTEM")
        print("=" * 60)

        tracker = DisplayTracker()
        result = tracker.process_weekly_data(
            raw_file='raw-display-w39.csv',
            previous_report_file='report-week-38.csv',
            week_num=39
        )

        if result['success']:
            print("\nDisplayTracker processing completed successfully!")
            print(f"Models increased: {result['summary']['models_increased']}")
            print(f"Models decreased: {result['summary']['models_decreased']}")
            print(f"Total changes: {result['summary']['total_changes']}")
        else:
            print(f"DisplayTracker processing failed: {result['error']}")

        logger.info("Unified scripts execution completed successfully")
        print("\n" + "=" * 60)
        print("ALL PROCESSING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()