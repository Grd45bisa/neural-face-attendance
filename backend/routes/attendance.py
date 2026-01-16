"""
Attendance routes.
Handles attendance check-in, history, and statistics.
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, g

from models.attendance import Attendance
from models.user import User
from middleware.auth_middleware import token_required, admin_required, teacher_or_admin_required
from utils.response import success_response, error_response, paginated_response

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')


def init_attendance_routes(db):
    """
    Initialize attendance routes with database connection.
    
    Args:
        db: MongoDB database instance
    """
    attendance_model = Attendance(db)
    user_model = User(db)
    
    @attendance_bp.route('/', methods=['GET'])
    def index():
        """Default route to check if attendance service is running."""
        return success_response(None, 'Attendance service running')

    @attendance_bp.route('/check-in', methods=['POST'])
    @token_required
    def check_in():
        """
        Manual check-in (for non-face recognition attendance).
        
        Request Body:
            {
                "location": "Room 101",  // optional
                "notes": "Manual check-in"  // optional
            }
        
        Returns:
            201: Check-in successful
        """
        try:
            data = request.get_json() or {}
            
            location = data.get('location')
            notes = data.get('notes')
            
            # Create attendance record
            attendance = attendance_model.create_attendance(
                user_id=g.user_id,
                attendance_type='check-in',
                method='manual',
                location=location
            )
            
            return success_response(attendance, 'Check-in successful', 201)
            
        except Exception as e:
            return error_response(f'Check-in failed: {str(e)}', 500)
    
    @attendance_bp.route('/check-out', methods=['POST'])
    @token_required
    def check_out():
        """
        Manual check-out.
        
        Request Body:
            {
                "location": "Room 101"  // optional
            }
        
        Returns:
            201: Check-out successful
        """
        try:
            data = request.get_json() or {}
            
            location = data.get('location')
            
            # Create attendance record
            attendance = attendance_model.create_attendance(
                user_id=g.user_id,
                attendance_type='check-out',
                method='manual',
                location=location
            )
            
            return success_response(attendance, 'Check-out successful', 201)
            
        except Exception as e:
            return error_response(f'Check-out failed: {str(e)}', 500)
    
    @attendance_bp.route('/history', methods=['GET'])
    @token_required
    def get_history():
        """
        Get user's attendance history.
        
        Query Parameters:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
        
        Returns:
            200: Attendance history with pagination
        """
        try:
            # Parse query parameters
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            
            # Parse dates
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date + timedelta(days=1)  # Include entire day
            
            # Calculate skip
            skip = (page - 1) * per_page
            
            # Get history
            history = attendance_model.get_user_history(
                user_id=g.user_id,
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=per_page
            )
            
            # Get total count
            total = attendance_model.count_user_attendance(
                user_id=g.user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return paginated_response(history, page, per_page, total, 'History retrieved successfully')
            
        except ValueError as e:
            return error_response(f'Invalid date format. Use YYYY-MM-DD: {str(e)}', 400)
        except Exception as e:
            return error_response(f'Failed to get history: {str(e)}', 500)
    
    @attendance_bp.route('/today', methods=['GET'])
    @token_required
    def get_today():
        """
        Get user's attendance for today.
        
        Returns:
            200: Today's attendance records
        """
        try:
            # Get today's date
            today = datetime.utcnow()
            start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Get attendance
            history = attendance_model.get_user_history(
                user_id=g.user_id,
                start_date=start_of_day,
                end_date=end_of_day
            )
            
            return success_response(history, 'Today\'s attendance retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get today\'s attendance: {str(e)}', 500)
    
    @attendance_bp.route('/stats', methods=['GET'])
    @token_required
    def get_stats():
        """
        Get user's attendance statistics.
        
        Query Parameters:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
        
        Returns:
            200: Attendance statistics
        """
        try:
            # Parse query parameters
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            # Parse dates
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date + timedelta(days=1)
            
            # Get statistics
            stats = attendance_model.get_attendance_stats(
                user_id=g.user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return success_response(stats, 'Statistics retrieved successfully')
            
        except ValueError as e:
            return error_response(f'Invalid date format. Use YYYY-MM-DD: {str(e)}', 400)
        except Exception as e:
            return error_response(f'Failed to get statistics: {str(e)}', 500)
    
    @attendance_bp.route('/latest', methods=['GET'])
    @token_required
    def get_latest():
        """
        Get user's latest attendance record.
        
        Returns:
            200: Latest attendance record
        """
        try:
            latest = attendance_model.get_latest_attendance(g.user_id)
            
            if not latest:
                return success_response(None, 'No attendance records found')
            
            return success_response(latest, 'Latest attendance retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get latest attendance: {str(e)}', 500)
    
    # Admin/Teacher routes
    @attendance_bp.route('/all', methods=['GET'])
    @token_required
    @teacher_or_admin_required
    def get_all_attendance():
        """
        Get all attendance records (admin/teacher only).
        
        Query Parameters:
            date: Specific date (YYYY-MM-DD) (optional, default: today)
        
        Returns:
            200: All attendance for specified date
        """
        try:
            date_str = request.args.get('date')
            
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date = datetime.utcnow()
            
            # Get daily attendance
            attendance_list = attendance_model.get_daily_attendance(date)
            
            # Enrich with user data
            for record in attendance_list:
                user = user_model.find_by_user_id(record['user_id'])
                if user:
                    record['user_name'] = user['name']
                    record['user_email'] = user['email']
            
            return success_response(
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'total': len(attendance_list),
                    'records': attendance_list
                },
                'Attendance retrieved successfully'
            )
            
        except ValueError as e:
            return error_response(f'Invalid date format. Use YYYY-MM-DD: {str(e)}', 400)
        except Exception as e:
            return error_response(f'Failed to get attendance: {str(e)}', 500)
    
    @attendance_bp.route('/<attendance_id>/verify', methods=['PUT'])
    @token_required
    @admin_required
    def verify_attendance(attendance_id):
        """
        Approve or reject attendance (admin only).
        
        Request Body:
            {
                "status": "approved" | "rejected"
            }
        
        Returns:
            200: Attendance status updated
        """
        try:
            data = request.get_json()
            status = data.get('status')
            
            if not status:
                return error_response('Status is required', 400)
            
            if status not in ['approved', 'rejected']:
                return error_response('Invalid status. Must be: approved or rejected', 400)
            
            # Update status
            attendance = attendance_model.update_status(
                attendance_id=attendance_id,
                status=status,
                verified_by=g.user_id
            )
            
            if not attendance:
                return error_response('Attendance record not found', 404)
            
            return success_response(attendance, f'Attendance {status} successfully')
            
        except Exception as e:
            return error_response(f'Failed to verify attendance: {str(e)}', 500)
    
    @attendance_bp.route('/<attendance_id>', methods=['DELETE'])
    @token_required
    @admin_required
    def delete_attendance(attendance_id):
        """
        Delete attendance record (admin only).
        
        Returns:
            200: Attendance deleted successfully
        """
        try:
            success = attendance_model.delete_attendance(attendance_id)
            
            if success:
                return success_response(None, 'Attendance deleted successfully')
            else:
                return error_response('Attendance record not found', 404)
            
        except Exception as e:
            return error_response(f'Failed to delete attendance: {str(e)}', 500)
    
    @attendance_bp.route('/report', methods=['GET'])
    @token_required
    @teacher_or_admin_required
    def get_report():
        """
        Generate attendance report (admin/teacher only).
        
        Query Parameters:
            start_date: Start date (YYYY-MM-DD) (required)
            end_date: End date (YYYY-MM-DD) (required)
        
        Returns:
            200: Attendance report with statistics
        """
        try:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            if not start_date_str or not end_date_str:
                return error_response('start_date and end_date are required', 400)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)
            
            # Get overall statistics
            stats = attendance_model.get_attendance_stats(
                start_date=start_date,
                end_date=end_date
            )
            
            return success_response(
                {
                    'period': {
                        'start': start_date_str,
                        'end': end_date_str
                    },
                    'statistics': stats
                },
                'Report generated successfully'
            )
            
        except ValueError as e:
            return error_response(f'Invalid date format. Use YYYY-MM-DD: {str(e)}', 400)
        except Exception as e:
            return error_response(f'Failed to generate report: {str(e)}', 500)
    
    return attendance_bp
