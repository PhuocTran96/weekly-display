#!/usr/bin/env python3
"""
Alert Filter Service - Manages filtering rules for alerts
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path


class FilterService:
    """
    Service for managing and applying alert filters
    """

    def __init__(self, filters_file: str = 'alert_filters.json'):
        """
        Initialize Filter Service

        Args:
            filters_file: Path to filters configuration file
        """
        self.filters_file = Path(filters_file)
        self.logger = logging.getLogger(__name__)
        self._default_filters = {
            'min_threshold': 5,
            'max_threshold': None,
            'whitelisted_models': [],
            'blacklisted_models': [],
            'channels': [],
            'stores': [],
            'enabled': True
        }
        self._ensure_filters_file()

    def _ensure_filters_file(self):
        """Ensure filters file exists with default configuration"""
        try:
            if not self.filters_file.exists():
                self.save_filters(self._default_filters)
                self.logger.info(f"Created default filters file: {self.filters_file}")
        except Exception as e:
            self.logger.warning(f"Error creating filters file: {e}")

    def load_filters(self) -> Dict[str, Any]:
        """
        Load current filters from file

        Returns:
            Dictionary containing current filter configuration
        """
        try:
            if self.filters_file.exists():
                with open(self.filters_file, 'r', encoding='utf-8') as f:
                    filters = json.load(f)

                # Ensure all required keys exist
                for key, default_value in self._default_filters.items():
                    if key not in filters:
                        filters[key] = default_value

                return filters
            else:
                return self._default_filters.copy()

        except Exception as e:
            self.logger.error(f"Error loading filters: {e}")
            return self._default_filters.copy()

    def save_filters(self, filters: Dict[str, Any]) -> bool:
        """
        Save filters to file

        Args:
            filters: Filter configuration to save

        Returns:
            bool: True if saved successfully
        """
        try:
            # Validate filters
            validated_filters = self._validate_filters(filters)

            # Save to file
            with open(self.filters_file, 'w', encoding='utf-8') as f:
                json.dump(validated_filters, f, indent=2, ensure_ascii=False)

            self.logger.info("Filters saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error saving filters: {e}")
            return False

    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize filter configuration

        Args:
            filters: Raw filter configuration

        Returns:
            Validated filter configuration
        """
        validated = self._default_filters.copy()

        # Validate numeric thresholds
        if 'min_threshold' in filters and filters['min_threshold'] is not None:
            try:
                validated['min_threshold'] = int(filters['min_threshold'])
                if validated['min_threshold'] < 0:
                    validated['min_threshold'] = 0
            except (ValueError, TypeError):
                validated['min_threshold'] = 0

        if 'max_threshold' in filters and filters['max_threshold'] is not None:
            try:
                validated['max_threshold'] = int(filters['max_threshold'])
                if validated['max_threshold'] < 0:
                    validated['max_threshold'] = None
            except (ValueError, TypeError):
                validated['max_threshold'] = None

        # Validate lists
        for list_key in ['whitelisted_models', 'blacklisted_models', 'channels', 'stores']:
            if list_key in filters and isinstance(filters[list_key], list):
                validated[list_key] = [str(item).strip() for item in filters[list_key] if item and str(item).strip()]
            else:
                validated[list_key] = []

        # Validate enabled flag
        if 'enabled' in filters:
            validated['enabled'] = bool(filters['enabled'])

        return validated

    def apply_filters(self, alerts: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Apply filters to alert list

        Args:
            alerts: List of alert dictionaries
            filters: Optional filter configuration (uses current if None)

        Returns:
            Filtered list of alerts
        """
        if filters is None:
            filters = self.load_filters()

        # If filtering is disabled, return all alerts
        if not filters.get('enabled', True):
            return alerts

        filtered_alerts = []

        for alert in alerts:
            if self._should_include_alert(alert, filters):
                filtered_alerts.append(alert)

        self.logger.info(f"Filtered {len(alerts)} alerts down to {len(filtered_alerts)}")
        return filtered_alerts

    def _should_include_alert(self, alert: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if an alert should be included based on filters

        Args:
            alert: Single alert dictionary
            filters: Filter configuration

        Returns:
            bool: True if alert should be included
        """
        try:
            # Get relevant data from alert (handle both old and new field names)
            model = alert.get('model', alert.get('Model', '')).lower().strip()
            change = alert.get('change', alert.get('Difference', 0))
            channel = alert.get('channel', alert.get('Channel', '')).lower().strip()
            store = alert.get('store', alert.get('Store', '')).lower().strip()

            # Skip if essential data is missing
            if not model:
                return False

            # Apply threshold filters
            min_threshold = filters.get('min_threshold', 0)
            max_threshold = filters.get('max_threshold')

            # For decreases, we want more negative values (greater magnitude)
            if change < 0:
                abs_change = abs(change)
                if abs_change < min_threshold:
                    return False
                if max_threshold is not None and abs_change > max_threshold:
                    return False
            else:
                # For increases
                if change < min_threshold:
                    return False
                if max_threshold is not None and change > max_threshold:
                    return False

            # Apply model filters
            whitelisted_models = [m.lower().strip() for m in filters.get('whitelisted_models', [])]
            blacklisted_models = [m.lower().strip() for m in filters.get('blacklisted_models', [])]

            # If whitelist exists and is not empty, only include whitelisted models
            if whitelisted_models:
                if model not in whitelisted_models:
                    return False

            # Exclude blacklisted models
            if blacklisted_models and model in blacklisted_models:
                return False

            # Apply channel filter (if specified) - since channel data isn't available,
            # we'll only apply this if we have channel data
            channels = [c.lower().strip() for c in filters.get('channels', [])]
            if channels and channel and channel not in channels:
                return False

            # Apply store filter (if specified) - since store data isn't available,
            # we'll only apply this if we have store data
            stores = [s.lower().strip() for s in filters.get('stores', [])]
            if stores and store and store not in stores:
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Error filtering alert: {e}")
            return True  # Include alert if there's an error

    def get_filter_summary(self, original_count: int, filtered_count: int) -> Dict[str, Any]:
        """
        Get summary of filtering results

        Args:
            original_count: Number of alerts before filtering
            filtered_count: Number of alerts after filtering

        Returns:
            Summary statistics
        """
        hidden_count = original_count - filtered_count

        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'hidden_count': hidden_count,
            'reduction_percentage': (hidden_count / original_count * 100) if original_count > 0 else 0
        }

    def preview_filters(self, sample_alerts: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Preview filtering results on sample data

        Args:
            sample_alerts: Sample alerts to test filters on
            filters: Optional filter configuration

        Returns:
            Preview results with before/after statistics
        """
        original_count = len(sample_alerts)
        filtered_alerts = self.apply_filters(sample_alerts, filters)
        filtered_count = len(filtered_alerts)

        summary = self.get_filter_summary(original_count, filtered_count)

        # Get examples of filtered out alerts
        hidden_alerts = []
        for alert in sample_alerts:
            if not self._should_include_alert(alert, filters or self.load_filters()):
                hidden_alerts.append(alert)
                if len(hidden_alerts) >= 5:  # Limit to 5 examples
                    break

        return {
            'summary': summary,
            'sample_filtered_alerts': filtered_alerts[:5],  # Show first 5
            'sample_hidden_alerts': hidden_alerts
        }