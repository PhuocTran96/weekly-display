#!/usr/bin/env python3
"""
MongoDB Database Manager for Display Tracking System
Handles all database operations for shop contacts and system data
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    """
    MongoDB database manager for Display Tracking System
    """

    def __init__(self, connection_string=None, database_name='display_tracking'):
        """
        Initialize Database Manager

        Args:
            connection_string: MongoDB connection string (defaults to env variable)
            database_name: Database name (default: 'display_tracking')
        """
        self.connection_string = connection_string or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = database_name
        self.client = None
        self.db = None
        self.logger = logging.getLogger(__name__)

        # Connect to database
        self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.logger.info(f"Connected to MongoDB database: {self.database_name}")

            # Create indexes
            self._create_indexes()

        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Shop contacts indexes
            self.db.shop_contacts.create_index([('elux_id', ASCENDING)], unique=True)
            self.db.shop_contacts.create_index([('store_name', ASCENDING)])
            self.db.shop_contacts.create_index([('dealer_id', ASCENDING)])
            self.db.shop_contacts.create_index([('pic_email', ASCENDING)])
            self.db.shop_contacts.create_index([('active', ASCENDING)])

            # Processing history indexes
            self.db.processing_history.create_index([('week_num', DESCENDING)])
            self.db.processing_history.create_index([('timestamp', DESCENDING)])

            # Job history indexes
            self.db.job_history.create_index([('job_id', ASCENDING)], unique=True)
            self.db.job_history.create_index([('week_num', DESCENDING)])
            self.db.job_history.create_index([('timestamp', DESCENDING)])
            self.db.job_history.create_index([('status', ASCENDING)])

            self.logger.info("Database indexes created successfully")

        except Exception as e:
            self.logger.warning(f"Error creating indexes: {e}")

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")

    # ==================== SHOP CONTACTS OPERATIONS ====================

    def add_contact(self, contact_data: Dict) -> Dict:
        """
        Add a new shop contact

        Args:
            contact_data: Dictionary with contact information

        Returns:
            Dictionary with operation result
        """
        try:
            # Add timestamps
            contact_data['created_at'] = datetime.now()
            contact_data['updated_at'] = datetime.now()
            contact_data['active'] = contact_data.get('active', True)

            # Normalize field names
            normalized_data = self._normalize_contact_data(contact_data)

            # Insert into database
            result = self.db.shop_contacts.insert_one(normalized_data)

            self.logger.info(f"Added contact for store: {normalized_data.get('store_name')}")

            return {
                'success': True,
                'id': str(result.inserted_id),
                'message': 'Contact added successfully'
            }

        except DuplicateKeyError:
            self.logger.error(f"Contact with Elux ID {contact_data.get('elux_id')} already exists")
            return {
                'success': False,
                'error': 'Contact with this Elux ID already exists'
            }
        except Exception as e:
            self.logger.error(f"Error adding contact: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_contact_by_elux_id(self, elux_id: str) -> Optional[Dict]:
        """
        Get contact by Elux ID

        Args:
            elux_id: Store Elux ID

        Returns:
            Contact dictionary or None
        """
        try:
            contact = self.db.shop_contacts.find_one({'elux_id': str(elux_id)})
            if contact:
                contact['_id'] = str(contact['_id'])
            return contact
        except Exception as e:
            self.logger.error(f"Error getting contact: {e}")
            return None

    def get_contact_by_store_name(self, store_name: str) -> Optional[Dict]:
        """
        Get contact by store name

        Args:
            store_name: Store name

        Returns:
            Contact dictionary or None
        """
        try:
            contact = self.db.shop_contacts.find_one({'store_name': str(store_name)})
            if contact:
                contact['_id'] = str(contact['_id'])
            return contact
        except Exception as e:
            self.logger.error(f"Error getting contact: {e}")
            return None

    def get_all_contacts(self, active_only=True) -> List[Dict]:
        """
        Get all shop contacts

        Args:
            active_only: Only return active contacts

        Returns:
            List of contact dictionaries
        """
        try:
            query = {'active': True} if active_only else {}
            contacts = list(self.db.shop_contacts.find(query).sort('store_name', ASCENDING))

            # Convert ObjectId to string
            for contact in contacts:
                contact['_id'] = str(contact['_id'])

            return contacts

        except Exception as e:
            self.logger.error(f"Error getting contacts: {e}")
            return []

    def update_contact(self, elux_id: str, update_data: Dict) -> Dict:
        """
        Update an existing contact

        Args:
            elux_id: Store Elux ID
            update_data: Dictionary with fields to update

        Returns:
            Dictionary with operation result
        """
        try:
            # Add update timestamp
            update_data['updated_at'] = datetime.now()

            # Normalize field names
            normalized_data = self._normalize_contact_data(update_data)

            # Update in database
            result = self.db.shop_contacts.update_one(
                {'elux_id': str(elux_id)},
                {'$set': normalized_data}
            )

            if result.matched_count > 0:
                self.logger.info(f"Updated contact for Elux ID: {elux_id}")
                return {
                    'success': True,
                    'message': 'Contact updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Contact not found'
                }

        except Exception as e:
            self.logger.error(f"Error updating contact: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_contact(self, elux_id: str, soft_delete=True) -> Dict:
        """
        Delete a contact (soft delete by default)

        Args:
            elux_id: Store Elux ID
            soft_delete: If True, mark as inactive; if False, delete from database

        Returns:
            Dictionary with operation result
        """
        try:
            if soft_delete:
                # Soft delete - mark as inactive
                result = self.db.shop_contacts.update_one(
                    {'elux_id': str(elux_id)},
                    {'$set': {'active': False, 'updated_at': datetime.now()}}
                )
                action = 'deactivated'
            else:
                # Hard delete
                result = self.db.shop_contacts.delete_one({'elux_id': str(elux_id)})
                action = 'deleted'

            if result.matched_count > 0 or result.deleted_count > 0:
                self.logger.info(f"Contact {action} for Elux ID: {elux_id}")
                return {
                    'success': True,
                    'message': f'Contact {action} successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Contact not found'
                }

        except Exception as e:
            self.logger.error(f"Error deleting contact: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_contacts_dataframe(self, active_only=True) -> pd.DataFrame:
        """
        Get contacts as pandas DataFrame (for compatibility with existing code)

        Args:
            active_only: Only return active contacts

        Returns:
            Pandas DataFrame with contact information
        """
        try:
            contacts = self.get_all_contacts(active_only=active_only)

            if not contacts:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(contacts)

            # Rename columns to match CSV format (for backward compatibility)
            column_mapping = {
                'elux_id': 'Elux_ID',
                'dealer_id': 'Dealer_ID',
                'store_name': 'Store_name',
                'channel': 'Channel',
                'pic_name': 'PIC_Name',
                'pic_email': 'PIC_Email',
                'boss_cc': 'Boss_CC'
            }

            df = df.rename(columns=column_mapping)

            # Select and reorder columns
            available_cols = [col for col in column_mapping.values() if col in df.columns]
            df = df[available_cols]

            return df

        except Exception as e:
            self.logger.error(f"Error creating DataFrame: {e}")
            return pd.DataFrame()

    def search_contacts(self, search_term: str, active_only=True) -> List[Dict]:
        """
        Search contacts by store name, PIC name, or email

        Args:
            search_term: Search term
            active_only: Only search active contacts

        Returns:
            List of matching contacts
        """
        try:
            query = {
                '$and': [
                    {'active': True} if active_only else {},
                    {
                        '$or': [
                            {'store_name': {'$regex': search_term, '$options': 'i'}},
                            {'pic_name': {'$regex': search_term, '$options': 'i'}},
                            {'pic_email': {'$regex': search_term, '$options': 'i'}},
                            {'elux_id': {'$regex': search_term, '$options': 'i'}}
                        ]
                    }
                ]
            }

            contacts = list(self.db.shop_contacts.find(query).sort('store_name', ASCENDING))

            # Convert ObjectId to string
            for contact in contacts:
                contact['_id'] = str(contact['_id'])

            return contacts

        except Exception as e:
            self.logger.error(f"Error searching contacts: {e}")
            return []

    def bulk_import_contacts(self, contacts_list: List[Dict]) -> Dict:
        """
        Bulk import contacts from list

        Args:
            contacts_list: List of contact dictionaries

        Returns:
            Dictionary with import results
        """
        try:
            success_count = 0
            error_count = 0
            errors = []

            for contact in contacts_list:
                # Normalize and add timestamps
                contact['created_at'] = datetime.now()
                contact['updated_at'] = datetime.now()
                contact['active'] = contact.get('active', True)

                normalized_contact = self._normalize_contact_data(contact)

                try:
                    # Use upsert to update if exists, insert if not
                    self.db.shop_contacts.update_one(
                        {'elux_id': normalized_contact['elux_id']},
                        {'$set': normalized_contact},
                        upsert=True
                    )
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        'elux_id': contact.get('elux_id', 'unknown'),
                        'error': str(e)
                    })

            self.logger.info(f"Bulk import completed: {success_count} success, {error_count} errors")

            return {
                'success': True,
                'imported': success_count,
                'errors': error_count,
                'error_details': errors
            }

        except Exception as e:
            self.logger.error(f"Error in bulk import: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _normalize_contact_data(self, data: Dict) -> Dict:
        """
        Normalize contact data field names to lowercase with underscores

        Args:
            data: Contact data dictionary

        Returns:
            Normalized dictionary
        """
        field_mapping = {
            'Elux_ID': 'elux_id',
            'Elux ID': 'elux_id',
            'elux_id': 'elux_id',
            'Dealer_ID': 'dealer_id',
            'Dealer ID': 'dealer_id',
            'dealer_id': 'dealer_id',
            'Store_name': 'store_name',
            'Store name': 'store_name',
            'store_name': 'store_name',
            'Channel': 'channel',
            'channel': 'channel',
            'PIC_Name': 'pic_name',
            'PIC Name': 'pic_name',
            'pic_name': 'pic_name',
            'PIC_Email': 'pic_email',
            'PIC Email': 'pic_email',
            'pic_email': 'pic_email',
            'Boss_CC': 'boss_cc',
            'Boss CC': 'boss_cc',
            'boss_cc': 'boss_cc'
        }

        normalized = {}
        for key, value in data.items():
            normalized_key = field_mapping.get(key, key.lower().replace(' ', '_'))
            normalized[normalized_key] = value

        return normalized

    # ==================== PROCESSING HISTORY OPERATIONS ====================

    def log_processing(self, week_num: int, result: Dict) -> Dict:
        """
        Log processing result to database

        Args:
            week_num: Week number
            result: Processing result dictionary

        Returns:
            Dictionary with operation result
        """
        try:
            log_entry = {
                'week_num': week_num,
                'timestamp': datetime.now(),
                'success': result.get('success', False),
                'models_increased': result.get('summary', {}).get('models_increased', 0),
                'models_decreased': result.get('summary', {}).get('models_decreased', 0),
                'total_changes': result.get('summary', {}).get('total_changes', 0),
                'files': {
                    'report_file': result.get('updated_report_file'),
                    'alert_file': result.get('alert_file'),
                    'decreases_file': result.get('decreases_file')
                }
            }

            if not result.get('success'):
                log_entry['error'] = result.get('error')

            result = self.db.processing_history.insert_one(log_entry)

            return {
                'success': True,
                'log_id': str(result.inserted_id)
            }

        except Exception as e:
            self.logger.error(f"Error logging processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_processing_history(self, limit=10) -> List[Dict]:
        """
        Get recent processing history

        Args:
            limit: Number of records to return

        Returns:
            List of processing history records
        """
        try:
            history = list(self.db.processing_history.find().sort('timestamp', DESCENDING).limit(limit))

            for record in history:
                record['_id'] = str(record['_id'])

            return history

        except Exception as e:
            self.logger.error(f"Error getting processing history: {e}")
            return []


# Utility functions for backward compatibility

def load_shop_contacts_from_db(db_manager=None) -> pd.DataFrame:
    """
    Load shop contacts from MongoDB (replaces CSV loading)

    Args:
        db_manager: DatabaseManager instance (creates new if None)

    Returns:
        Pandas DataFrame with contact information
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        return db_manager.get_contacts_dataframe(active_only=True)

    except Exception as e:
        logging.error(f"Error loading contacts from database: {e}")
        return pd.DataFrame()


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize database manager
    db_manager = DatabaseManager()

    # Test connection
    print(f"Connected to database: {db_manager.database_name}")

    # Get all contacts
    contacts = db_manager.get_all_contacts()
    print(f"Total contacts: {len(contacts)}")

    # Get as DataFrame
    df = db_manager.get_contacts_dataframe()
    print(f"DataFrame shape: {df.shape}")
    print(df.head())

    # Close connection
    db_manager.close()