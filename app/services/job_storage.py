#!/usr/bin/env python3
"""
Job Storage Service - Manages processing job history using MongoDB
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure


class JobStorage:
    """
    Service for storing and retrieving processing job history
    Uses MongoDB for storage
    """

    def __init__(self, connection_string=None, database_name='display_tracking'):
        """
        Initialize Job Storage with MongoDB connection

        Args:
            connection_string: MongoDB connection string
            database_name: Database name
        """
        from db_manager import DatabaseManager

        self.db_manager = DatabaseManager(connection_string, database_name)
        self.logger = logging.getLogger(__name__)
        self.collection = self.db_manager.db.job_history
        self._create_indexes()

    def _create_indexes(self):
        """Create MongoDB indexes for optimal performance"""
        try:
            self.collection.create_index([('job_id', ASCENDING)], unique=True)
            self.collection.create_index([('week_num', DESCENDING)])
            self.collection.create_index([('timestamp', DESCENDING)])
            self.collection.create_index([('status', ASCENDING)])
            self.logger.info("Job history indexes created successfully")
        except Exception as e:
            self.logger.warning(f"Error creating job history indexes: {e}")

    def save_job(self, job_id: str, job_data: Dict) -> bool:
        """
        Save a processing job to MongoDB

        Args:
            job_id: Unique job identifier
            job_data: Complete job data including metadata and results

        Returns:
            bool: True if saved successfully
        """
        try:
            # Create MongoDB document
            doc = {
                'job_id': job_id,
                'week_num': job_data.get('week_num'),
                'timestamp': datetime.now(),
                'status': job_data.get('status', 'processing'),
                'summary': job_data.get('summary', {}),
                'files': {
                    'report_file': job_data.get('updated_report_file'),
                    'alert_file': job_data.get('alert_file'),
                    'decreases_file': job_data.get('decreases_file')
                },
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Add error if job failed
            if job_data.get('status') == 'failed' and 'error' in job_data:
                doc['error'] = job_data['error']

            # Use upsert to update if exists, insert if not
            self.collection.replace_one(
                {'job_id': job_id},
                doc,
                upsert=True
            )

            self.logger.info(f"Saved job: {job_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving job {job_id}: {e}")
            return False

    def get_all_jobs(self, page: int = 1, limit: int = 20) -> Dict:
        """
        Get all jobs with pagination

        Args:
            page: Page number (1-indexed)
            limit: Number of jobs per page

        Returns:
            Dict with jobs list and pagination info
        """
        try:
            # Get total count
            total = self.collection.count_documents({})

            # Calculate pagination
            skip = (page - 1) * limit

            # Get paginated jobs
            cursor = self.collection.find({}).sort('timestamp', DESCENDING).skip(skip).limit(limit)
            jobs = []

            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                # Convert datetime to string for JSON serialization
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                    doc['created_at'] = doc['created_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                jobs.append(doc)

            return {
                'success': True,
                'jobs': jobs,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': (total + limit - 1) // limit
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting all jobs: {e}")
            return {
                'success': False,
                'error': str(e),
                'jobs': [],
                'pagination': {'page': 1, 'limit': limit, 'total': 0, 'total_pages': 0}
            }

    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """
        Get complete job data by ID

        Args:
            job_id: Job identifier

        Returns:
            Complete job data or None if not found
        """
        try:
            doc = self.collection.find_one({'job_id': job_id})
            if doc:
                doc['_id'] = str(doc['_id'])
                # Convert datetime to string for JSON serialization
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                    doc['created_at'] = doc['created_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                return doc
            return None

        except Exception as e:
            self.logger.error(f"Error getting job {job_id}: {e}")
            return None

    def get_jobs_by_week(self, week_num: int) -> List[Dict]:
        """
        Get all jobs for a specific week

        Args:
            week_num: Week number

        Returns:
            List of jobs for that week
        """
        try:
            cursor = self.collection.find({'week_num': week_num}).sort('timestamp', DESCENDING)
            jobs = []

            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                # Convert datetime to string for JSON serialization
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                    doc['created_at'] = doc['created_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                jobs.append(doc)

            return jobs

        except Exception as e:
            self.logger.error(f"Error getting jobs for week {week_num}: {e}")
            return []

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from MongoDB

        Args:
            job_id: Job identifier

        Returns:
            bool: True if deleted successfully
        """
        try:
            result = self.collection.delete_one({'job_id': job_id})

            if result.deleted_count > 0:
                self.logger.info(f"Deleted job: {job_id}")
                return True
            else:
                self.logger.warning(f"Job not found for deletion: {job_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def cleanup_old_jobs(self, days: int = 90) -> int:
        """
        Delete jobs older than specified days

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of jobs deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            result = self.collection.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })

            deleted_count = result.deleted_count
            self.logger.info(f"Cleaned up {deleted_count} old jobs")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old jobs: {e}")
            return 0
