"""
Attendance model for MongoDB.
Handles attendance records and history.
"""

from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING, ASCENDING
from bson.objectid import ObjectId


class Attendance:
    """Attendance model for managing attendance records in MongoDB."""
    
    def __init__(self, db):
        """
        Initialize Attendance model.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.attendance
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for better query performance."""
        self.collection.create_index([('user_id', ASCENDING)])
        self.collection.create_index([('timestamp', DESCENDING)])
        self.collection.create_index([('type', ASCENDING)])
        self.collection.create_index([('status', ASCENDING)])
    
    def create_attendance(self, user_id, attendance_type='check-in', method='face', 
                         confidence=None, location=None, photo_path=None, verified_by=None):
        """
        Create attendance record.
        
        Args:
            user_id (str): User ID
            attendance_type (str): 'check-in' or 'check-out'
            method (str): 'face' or 'manual'
            confidence (float): Face recognition confidence (0-1)
            location (str): Location coordinates or name
            photo_path (str): Path to attendance photo
            verified_by (str): Admin user_id who verified (optional)
            
        Returns:
            dict: Created attendance document
        """
        attendance_doc = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'type': attendance_type,
            'method': method,
            'confidence': confidence,
            'location': location,
            'photo_path': photo_path,
            'verified_by': verified_by,
            'status': 'approved' if method == 'face' and confidence and confidence >= 0.7 else 'pending'
        }
        
        result = self.collection.insert_one(attendance_doc)
        attendance_doc['_id'] = str(result.inserted_id)
        
        return attendance_doc
    
    def get_user_history(self, user_id, start_date=None, end_date=None, skip=0, limit=50):
        """
        Get attendance history for a user.
        
        Args:
            user_id (str): User ID
            start_date (datetime): Start date filter (optional)
            end_date (datetime): End date filter (optional)
            skip (int): Number of documents to skip
            limit (int): Maximum number of documents to return
            
        Returns:
            list: List of attendance documents
        """
        query = {'user_id': user_id}
        
        # Date range filter
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        records = self.collection.find(query).sort('timestamp', DESCENDING).skip(skip).limit(limit)
        return [self._format_attendance(record) for record in records]
    
    def get_daily_attendance(self, date=None):
        """
        Get all attendance for a specific date.
        
        Args:
            date (datetime): Date to query (default: today)
            
        Returns:
            list: List of attendance documents
        """
        if date is None:
            date = datetime.utcnow()
        
        # Start and end of day
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = start_of_day + timedelta(days=1)
        
        query = {
            'timestamp': {
                '$gte': start_of_day,
                '$lt': end_of_day
            }
        }
        
        records = self.collection.find(query).sort('timestamp', DESCENDING)
        return [self._format_attendance(record) for record in records]
    
    def get_attendance_stats(self, user_id=None, start_date=None, end_date=None):
        """
        Get attendance statistics.
        
        Args:
            user_id (str): User ID (optional, for specific user stats)
            start_date (datetime): Start date filter (optional)
            end_date (datetime): End date filter (optional)
            
        Returns:
            dict: Statistics including total, check-ins, check-outs, etc.
        """
        query = {}
        
        if user_id:
            query['user_id'] = user_id
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        total = self.collection.count_documents(query)
        
        # Count by type
        check_ins = self.collection.count_documents({**query, 'type': 'check-in'})
        check_outs = self.collection.count_documents({**query, 'type': 'check-out'})
        
        # Count by method
        face_method = self.collection.count_documents({**query, 'method': 'face'})
        manual_method = self.collection.count_documents({**query, 'method': 'manual'})
        
        # Count by status
        approved = self.collection.count_documents({**query, 'status': 'approved'})
        pending = self.collection.count_documents({**query, 'status': 'pending'})
        rejected = self.collection.count_documents({**query, 'status': 'rejected'})
        
        return {
            'total': total,
            'check_ins': check_ins,
            'check_outs': check_outs,
            'face_method': face_method,
            'manual_method': manual_method,
            'approved': approved,
            'pending': pending,
            'rejected': rejected
        }
    
    def update_status(self, attendance_id, status, verified_by=None):
        """
        Update attendance status.
        
        Args:
            attendance_id (str): Attendance document ID
            status (str): New status ('approved', 'pending', 'rejected')
            verified_by (str): Admin user_id who verified
            
        Returns:
            dict: Updated attendance document or None
        """
        if isinstance(attendance_id, str):
            attendance_id = ObjectId(attendance_id)
        
        update_data = {
            'status': status,
            'verified_at': datetime.utcnow()
        }
        
        if verified_by:
            update_data['verified_by'] = verified_by
        
        result = self.collection.find_one_and_update(
            {'_id': attendance_id},
            {'$set': update_data},
            return_document=True
        )
        
        return self._format_attendance(result) if result else None
    
    def delete_attendance(self, attendance_id):
        """
        Delete attendance record.
        
        Args:
            attendance_id (str): Attendance document ID
            
        Returns:
            bool: True if successful
        """
        if isinstance(attendance_id, str):
            attendance_id = ObjectId(attendance_id)
        
        result = self.collection.delete_one({'_id': attendance_id})
        return result.deleted_count > 0
    
    def get_latest_attendance(self, user_id):
        """
        Get latest attendance record for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Latest attendance document or None
        """
        record = self.collection.find_one(
            {'user_id': user_id},
            sort=[('timestamp', DESCENDING)]
        )
        
        return self._format_attendance(record) if record else None
    
    def count_user_attendance(self, user_id, start_date=None, end_date=None):
        """
        Count attendance records for a user.
        
        Args:
            user_id (str): User ID
            start_date (datetime): Start date filter (optional)
            end_date (datetime): End date filter (optional)
            
        Returns:
            int: Total count
        """
        query = {'user_id': user_id}
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        return self.collection.count_documents(query)
    
    def _format_attendance(self, record):
        """
        Format attendance document.
        
        Args:
            record (dict): Attendance document
            
        Returns:
            dict: Formatted attendance document
        """
        if not record:
            return None
        
        # Convert ObjectId to string
        if '_id' in record:
            record['_id'] = str(record['_id'])
        
        # Format timestamp
        if 'timestamp' in record and isinstance(record['timestamp'], datetime):
            record['timestamp'] = record['timestamp'].isoformat() + 'Z'
        
        if 'verified_at' in record and isinstance(record['verified_at'], datetime):
            record['verified_at'] = record['verified_at'].isoformat() + 'Z'
        
        return record
