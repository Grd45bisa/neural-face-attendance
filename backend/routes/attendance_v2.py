"""
Attendance routes with business logic.
Handles check-in, history, and statistics with validation.
"""

from flask import Blueprint, request, g
from datetime import datetime

from models.user import User
from models.face_embedding import FaceEmbedding
from services.attendance_service import AttendanceService
from middleware.auth_middleware import token_required, admin_required
from utils.response import success_response, error_response
from utils.validators import validate_image_file, validate_file_size
from utils.file_handler import save_uploaded_file
from config import get_config

# Import face recognition service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'face_recognition'))
from face_service import FaceRecognitionService

config = get_config()
attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

# Global service instances
attendance_service = None
face_service = None


def init_attendance_routes(db):
    """
    Initialize attendance routes with database connection.
    
    Args:
        db: MongoDB database instance
    """
    global attendance_service, face_service
    
    user_model = User(db)
    face_embedding_model = FaceEmbedding(db)
    
    # Initialize services
    attendance_service = AttendanceService(db)
    face_service = FaceRecognitionService(
        face_embedding_model=face_embedding_model,
        confidence_threshold=config.FACE_CONFIDENCE_THRESHOLD
    )
    
    @attendance_bp.route('/checkin', methods=['POST'])
    @token_required
    def check_in():
        """
        Check-in with face verification.
        
        Business Rules:
        - User can only check-in once per day
        - Check-in after 07:30 WIB is marked as 'late'
        - Minimum confidence score: 0.6
        - User must have registered face
        
        Request:
            - Form data with 'photo' file upload
            OR
            - JSON with 'photo_base64' field
        
        Returns:
            201: Check-in successful
            400: Validation error or duplicate check-in
        """
        try:
            import cv2
            import numpy as np
            from utils.helpers import dataURLtoBlob, blobToFile
            
            # Get image
            image = None
            photo_path = None
            
            # Try file upload first
            if 'photo' in request.files:
                file = request.files['photo']
                
                # Validate file
                is_valid, error_msg = validate_image_file(file)
                if not is_valid:
                    return error_response(error_msg, 400)
                
                # Validate file size
                if not validate_file_size(file, config.MAX_FILE_SIZE):
                    return error_response(
                        f'File too large. Maximum size: {config.MAX_FILE_SIZE / 1024 / 1024}MB',
                        400
                    )
                
                # Save file
                upload_folder = os.path.join(config.UPLOAD_FOLDER, 'attendance')
                relative_path = save_uploaded_file(file, upload_folder, subfolder=g.user_id)
                photo_path = os.path.join(upload_folder, relative_path)
                
                # Read image
                image = cv2.imread(photo_path)
                
            # Try base64
            elif request.is_json:
                data = request.get_json()
                photo_base64 = data.get('photo_base64')
                
                if not photo_base64:
                    return error_response('No photo provided', 400)
                
                try:
                    import base64
                    import io
                    from PIL import Image
                    
                    # Remove data URL prefix if present
                    if ',' in photo_base64:
                        photo_base64 = photo_base64.split(',')[1]
                    
                    image_data = base64.b64decode(photo_base64)
                    pil_image = Image.open(io.BytesIO(image_data))
                    
                    # Convert to BGR for OpenCV
                    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                    # Save image
                    upload_folder = os.path.join(config.UPLOAD_FOLDER, 'attendance')
                    os.makedirs(os.path.join(upload_folder, g.user_id), exist_ok=True)
                    photo_path = os.path.join(upload_folder, g.user_id, f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
                    cv2.imwrite(photo_path, image)
                    
                except Exception as e:
                    return error_response(f'Invalid base64 image: {str(e)}', 400)
            
            else:
                return error_response('No photo provided', 400)
            
            if image is None:
                return error_response('Failed to read image', 400)
            
            # Verify face using face service
            verify_result = face_service.verify_user_face(g.user_id, image)
            
            if not verify_result['is_match']:
                return error_response(verify_result['message'], 400, {
                    'confidence': verify_result['confidence']
                })
            
            confidence_score = verify_result['confidence']
            
            # Process check-in with business logic
            try:
                result = attendance_service.check_in(
                    user_id=g.user_id,
                    photo_path=photo_path,
                    confidence_score=confidence_score
                )
                
                if not result['success']:
                    return error_response(result['message'], 400)
                
                return success_response(
                    result['attendance'],
                    result['message'],
                    201
                )
                
            except ValueError as e:
                return error_response(str(e), 400)
            
        except Exception as e:
            return error_response(f'Check-in failed: {str(e)}', 500)
    
    @attendance_bp.route('/today', methods=['GET'])
    @token_required
    def get_today():
        """
        Get today's attendance for current user.
        
        Returns:
            200: Today's attendance record or null
        """
        try:
            attendance = attendance_service.get_today_attendance(g.user_id)
            
            if attendance:
                return success_response(attendance, 'Today\'s attendance retrieved successfully')
            else:
                return success_response(None, 'No attendance record for today')
            
        except Exception as e:
            return error_response(f'Failed to get today\'s attendance: {str(e)}', 500)
    
    @attendance_bp.route('/history', methods=['GET'])
    @token_required
    def get_history():
        """
        Get attendance history for current user.
        
        Query Parameters:
            user_id: User ID (optional, defaults to current user)
            month: Month (1-12) (optional)
            year: Year (optional)
            page: Page number (default: 1)
            per_page: Items per page (default: 20)
        
        Returns:
            200: Attendance history with pagination
        """
        try:
            # Parse query parameters
            user_id = request.args.get('user_id', g.user_id)
            month = request.args.get('month', type=int)
            year = request.args.get('year', type=int)
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            # Validate month and year
            if month and (month < 1 or month > 12):
                return error_response('Invalid month. Must be between 1 and 12', 400)
            
            if year and (year < 2000 or year > 2100):
                return error_response('Invalid year', 400)
            
            # Get history
            result = attendance_service.get_attendance_history(
                user_id=user_id,
                month=month,
                year=year,
                page=page,
                per_page=per_page
            )
            
            return success_response(result, 'History retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get history: {str(e)}', 500)
    
    @attendance_bp.route('/stats', methods=['GET'])
    @token_required
    def get_stats():
        """
        Get attendance statistics for current user.
        
        Query Parameters:
            user_id: User ID (optional, defaults to current user)
        
        Returns:
            200: Attendance statistics
        """
        try:
            user_id = request.args.get('user_id', g.user_id)
            
            stats = attendance_service.get_attendance_stats(user_id)
            
            return success_response(stats, 'Statistics retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get statistics: {str(e)}', 500)
    
    @attendance_bp.route('/admin/create-absent', methods=['POST'])
    @token_required
    @admin_required
    def create_absent_records():
        """
        Create absent records for users who didn't check in (admin only).
        
        Request Body:
            {
                "date": "YYYY-MM-DD" (optional, defaults to yesterday)
            }
        
        Returns:
            200: Number of absent records created
        """
        try:
            data = request.get_json() or {}
            date_str = data.get('date')
            
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return error_response('Invalid date format. Use YYYY-MM-DD', 400)
            else:
                date = None
            
            count = attendance_service.create_absent_records(date)
            
            return success_response(
                {'absent_records_created': count},
                f'Created {count} absent records'
            )
            
        except Exception as e:
            return error_response(f'Failed to create absent records: {str(e)}', 500)
    
    return attendance_bp
