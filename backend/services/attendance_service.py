"""
Attendance business logic with specific rules.
Handles check-in validation, late detection, and timezone handling.
"""

from datetime import datetime, time, timedelta
import pytz
from models.attendance import Attendance
from models.user import User
from models.face_embedding import FaceEmbedding


# Timezone WIB (UTC+7)
WIB = pytz.timezone('Asia/Jakarta')

# Business rules constants
LATE_TIME = time(7, 30)  # 07:30 WIB
MIN_CONFIDENCE = 0.6
MAX_CHECK_INS_PER_DAY = 1


class AttendanceService:
    """Service class for attendance business logic."""
    
    def __init__(self, db):
        """
        Initialize attendance service.
        
        Args:
            db: MongoDB database instance
        """
        self.attendance_model = Attendance(db)
        self.user_model = User(db)
        self.face_embedding_model = FaceEmbedding(db)
    
    def check_in(self, user_id, photo_path, confidence_score):
        """
        Process check-in with business rules validation.
        
        Business Rules:
        - User can only check-in once per day
        - Check-in after 07:30 WIB is marked as 'late'
        - Minimum confidence score: 0.6
        - User must have registered face
        
        Args:
            user_id (str): User ID
            photo_path (str): Path to uploaded photo
            confidence_score (float): Face recognition confidence (0-1)
            
        Returns:
            dict: {
                'success': bool,
                'attendance': dict or None,
                'message': str
            }
            
        Raises:
            ValueError: If validation fails
        """
        # 1. Check if user exists and has registered face
        user = self.user_model.find_by_user_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not user.get('is_face_registered') and not user.get('face_registered'):
            raise ValueError("User has not registered face. Please register face first.")
        
        # 2. Validate confidence score
        if confidence_score < MIN_CONFIDENCE:
            return {
                'success': False,
                'attendance': None,
                'message': f'Confidence score too low ({confidence_score:.2f}). Minimum required: {MIN_CONFIDENCE}'
            }
        
        # 3. Check for duplicate check-in today
        today_wib = datetime.now(WIB)
        start_of_day = today_wib.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Convert to UTC for MongoDB query
        start_of_day_utc = start_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
        end_of_day_utc = end_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
        
        existing_checkin = self.attendance_model.collection.find_one({
            'user_id': user_id,
            'type': 'check-in',
            'timestamp': {
                '$gte': start_of_day_utc,
                '$lt': end_of_day_utc
            }
        })
        
        if existing_checkin:
            return {
                'success': False,
                'attendance': None,
                'message': 'You have already checked in today'
            }
        
        # 4. Determine status (present or late)
        current_time_wib = today_wib.time()
        status = 'late' if current_time_wib > LATE_TIME else 'present'
        
        # 5. Create attendance record
        attendance_doc = {
            'user_id': user_id,
            'date': today_wib.date().isoformat(),  # YYYY-MM-DD
            'check_in_time': datetime.now(pytz.UTC).replace(tzinfo=None),  # Store in UTC
            'photo_url': photo_path,
            'confidence_score': confidence_score,
            'status': status,
            'type': 'check-in',
            'method': 'face',
            'created_at': datetime.now(pytz.UTC).replace(tzinfo=None)
        }
        
        result = self.attendance_model.collection.insert_one(attendance_doc)
        attendance_doc['_id'] = str(result.inserted_id)
        
        # Format timestamp for response
        check_in_time_wib = datetime.now(WIB)
        attendance_doc['check_in_time_wib'] = check_in_time_wib.strftime('%H:%M:%S')
        
        return {
            'success': True,
            'attendance': attendance_doc,
            'message': f'Check-in successful! Status: {status.upper()}'
        }
    
    def get_today_attendance(self, user_id):
        """
        Get today's attendance for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Attendance record or None
        """
        today_wib = datetime.now(WIB)
        start_of_day = today_wib.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Convert to UTC
        start_of_day_utc = start_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
        end_of_day_utc = end_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
        
        record = self.attendance_model.collection.find_one({
            'user_id': user_id,
            'timestamp': {
                '$gte': start_of_day_utc,
                '$lt': end_of_day_utc
            }
        })
        
        if record:
            record['_id'] = str(record['_id'])
            # Convert UTC to WIB for display
            if 'check_in_time' in record:
                utc_time = record['check_in_time'].replace(tzinfo=pytz.UTC)
                wib_time = utc_time.astimezone(WIB)
                record['check_in_time_wib'] = wib_time.strftime('%H:%M:%S')
        
        return record
    
    def get_attendance_history(self, user_id, month=None, year=None, page=1, per_page=20):
        """
        Get attendance history for a user with pagination.
        
        Args:
            user_id (str): User ID
            month (int): Month (1-12) (optional)
            year (int): Year (optional)
            page (int): Page number (default: 1)
            per_page (int): Items per page (default: 20)
            
        Returns:
            dict: {
                'records': list,
                'total': int,
                'page': int,
                'per_page': int,
                'total_pages': int
            }
        """
        query = {'user_id': user_id}
        
        # Filter by month and year
        if month and year:
            # Get first and last day of month in WIB
            first_day_wib = datetime(year, month, 1, tzinfo=WIB)
            if month == 12:
                last_day_wib = datetime(year + 1, 1, 1, tzinfo=WIB)
            else:
                last_day_wib = datetime(year, month + 1, 1, tzinfo=WIB)
            
            # Convert to UTC
            first_day_utc = first_day_wib.astimezone(pytz.UTC).replace(tzinfo=None)
            last_day_utc = last_day_wib.astimezone(pytz.UTC).replace(tzinfo=None)
            
            query['check_in_time'] = {
                '$gte': first_day_utc,
                '$lt': last_day_utc
            }
        
        # Get total count
        total = self.attendance_model.collection.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        # Get records
        records = list(self.attendance_model.collection.find(query)
                      .sort('check_in_time', -1)
                      .skip(skip)
                      .limit(per_page))
        
        # Format records
        for record in records:
            record['_id'] = str(record['_id'])
            if 'check_in_time' in record:
                utc_time = record['check_in_time'].replace(tzinfo=pytz.UTC)
                wib_time = utc_time.astimezone(WIB)
                record['check_in_time_wib'] = wib_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'records': records,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
    
    def get_attendance_stats(self, user_id, start_date=None, end_date=None):
        """
        Get attendance statistics for a user.
        
        Args:
            user_id (str): User ID
            start_date (datetime): Start date (optional)
            end_date (datetime): End date (optional)
            
        Returns:
            dict: {
                'total_present': int,
                'total_late': int,
                'total_absent': int,
                'attendance_percentage': float,
                'streak': int
            }
        """
        query = {'user_id': user_id}
        
        if start_date or end_date:
            query['check_in_time'] = {}
            if start_date:
                query['check_in_time']['$gte'] = start_date
            if end_date:
                query['check_in_time']['$lte'] = end_date
        
        # Count by status
        total_present = self.attendance_model.collection.count_documents({**query, 'status': 'present'})
        total_late = self.attendance_model.collection.count_documents({**query, 'status': 'late'})
        total_absent = self.attendance_model.collection.count_documents({**query, 'status': 'absent'})
        
        total_days = total_present + total_late + total_absent
        
        # Calculate attendance percentage (present + late)
        if total_days > 0:
            attendance_percentage = ((total_present + total_late) / total_days) * 100
        else:
            attendance_percentage = 0.0
        
        # Calculate streak (consecutive days with attendance)
        streak = self._calculate_streak(user_id)
        
        return {
            'total_present': total_present,
            'total_late': total_late,
            'total_absent': total_absent,
            'total_days': total_days,
            'attendance_percentage': round(attendance_percentage, 2),
            'streak': streak
        }
    
    def _calculate_streak(self, user_id):
        """
        Calculate consecutive attendance streak.
        
        Args:
            user_id (str): User ID
            
        Returns:
            int: Number of consecutive days with attendance
        """
        today_wib = datetime.now(WIB).date()
        streak = 0
        current_date = today_wib
        
        # Check backwards from today
        for i in range(30):  # Check last 30 days max
            start_of_day = datetime.combine(current_date, time.min, tzinfo=WIB)
            end_of_day = start_of_day + timedelta(days=1)
            
            start_utc = start_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            end_utc = end_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            
            record = self.attendance_model.collection.find_one({
                'user_id': user_id,
                'check_in_time': {
                    '$gte': start_utc,
                    '$lt': end_utc
                },
                'status': {'$in': ['present', 'late']}
            })
            
            if record:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def create_absent_records(self, date=None):
        """
        Auto-create absent records for users who didn't check in.
        Should be run daily (e.g., via cron job at end of day).
        
        Args:
            date (datetime): Date to create absent records for (default: yesterday)
            
        Returns:
            int: Number of absent records created
        """
        if date is None:
            # Default to yesterday
            date = (datetime.now(WIB) - timedelta(days=1)).date()
        
        # Get all students with registered faces
        all_users = self.user_model.collection.find({
            'role': 'student',
            'is_face_registered': True,
            'deleted': {'$ne': True}
        })
        
        absent_count = 0
        
        for user in all_users:
            user_id = user['user_id']
            
            # Check if user has attendance for this date
            start_of_day = datetime.combine(date, time.min, tzinfo=WIB)
            end_of_day = start_of_day + timedelta(days=1)
            
            start_utc = start_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            end_utc = end_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            
            existing = self.attendance_model.collection.find_one({
                'user_id': user_id,
                'check_in_time': {
                    '$gte': start_utc,
                    '$lt': end_utc
                }
            })
            
            if not existing:
                # Create absent record
                absent_doc = {
                    'user_id': user_id,
                    'date': date.isoformat(),
                    'check_in_time': None,
                    'photo_url': None,
                    'confidence_score': None,
                    'status': 'absent',
                    'type': 'absent',
                    'method': 'auto',
                    'created_at': datetime.now(pytz.UTC).replace(tzinfo=None)
                }
                
                self.attendance_model.collection.insert_one(absent_doc)
                absent_count += 1
        
        return absent_count
