"""
Face recognition routes with MongoDB storage.
Handles face registration and verification using FaceRecognitionService.
"""

import os
import cv2
import numpy as np
from flask import Blueprint, request, g

from models.user import User
from models.attendance import Attendance
from models.face_embedding import FaceEmbedding
from middleware.auth_middleware import token_required, admin_required
from utils.response import success_response, error_response
from utils.validators import validate_image_file, validate_file_size
from utils.file_handler import save_uploaded_file
from config import get_config

# Import face recognition service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'face_recognition'))
from face_service import FaceRecognitionService

config = get_config()
face_bp = Blueprint('face', __name__, url_prefix='/api/face')

# Global service instance (will be initialized in init_face_routes)
face_service = None


def init_face_routes(db):
    """
    Initialize face routes with database connection.
    
    Args:
        db: MongoDB database instance
    """
    global face_service
    
    user_model = User(db)
    attendance_model = Attendance(db)
    face_embedding_model = FaceEmbedding(db)
    
    # Initialize face recognition service
    face_service = FaceRecognitionService(
        face_embedding_model=face_embedding_model,
        confidence_threshold=config.FACE_CONFIDENCE_THRESHOLD
    )
    
    @face_bp.route('/', methods=['GET'])
    def index():
        """Default route to check if face service is running."""
        return success_response(None, 'Face service running')

    @face_bp.route('/register', methods=['POST'])
    @token_required
    def register_face():
        """
        Register user face with multiple photos (5-10 photos recommended).
        
        Request:
            - Form data with multiple 'photos' file uploads
            OR
            - JSON with 'photos_base64' array
        
        Returns:
            200: Face registered successfully
            400: Validation error
        """
        try:
            # Get user
            user = user_model.find_by_user_id(g.user_id)
            if not user:
                return error_response('User not found', 404)
            
            photos_list = []
            saved_paths = []
            
            # Try file uploads first
            if 'photos' in request.files:
                files = request.files.getlist('photos')
                
                if len(files) < 3:
                    return error_response('Minimum 3 photos required for registration', 400)
                
                if len(files) > 10:
                    return error_response('Maximum 10 photos allowed', 400)
                
                upload_folder = os.path.join(config.UPLOAD_FOLDER, 'faces')
                
                for idx, file in enumerate(files):
                    # Validate file
                    is_valid, error_msg = validate_image_file(file)
                    if not is_valid:
                        return error_response(f'Photo {idx + 1}: {error_msg}', 400)
                    
                    # Validate file size
                    if not validate_file_size(file, config.MAX_FILE_SIZE):
                        return error_response(
                            f'Photo {idx + 1}: File too large. Maximum size: {config.MAX_FILE_SIZE / 1024 / 1024}MB',
                            400
                        )
                    
                    # Save file
                    try:
                        relative_path = save_uploaded_file(file, upload_folder, subfolder=g.user_id)
                        photo_path = os.path.join(upload_folder, relative_path)
                        saved_paths.append(relative_path)
                        
                        # Read image
                        image = cv2.imread(photo_path)
                        if image is None:
                            return error_response(f'Photo {idx + 1}: Failed to read image', 400)
                        
                        photos_list.append(image)
                        
                    except Exception as e:
                        return error_response(f'Photo {idx + 1}: {str(e)}', 400)
            
            # Try JSON with base64
            elif request.is_json:
                data = request.get_json()
                photos_base64 = data.get('photos_base64', [])
                
                if len(photos_base64) < 3:
                    return error_response('Minimum 3 photos required for registration', 400)
                
                if len(photos_base64) > 10:
                    return error_response('Maximum 10 photos allowed', 400)
                
                for idx, base64_str in enumerate(photos_base64):
                    try:
                        # Decode base64
                        import base64
                        import io
                        from PIL import Image
                        
                        # Remove data URL prefix if present
                        if ',' in base64_str:
                            base64_str = base64_str.split(',')[1]
                        
                        image_data = base64.b64decode(base64_str)
                        pil_image = Image.open(io.BytesIO(image_data))
                        
                        # Convert to BGR for OpenCV
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        photos_list.append(image)
                        
                    except Exception as e:
                        return error_response(f'Photo {idx + 1}: Invalid base64 image - {str(e)}', 400)
            
            else:
                return error_response('No photos provided. Send files or base64 images.', 400)
            
            # Register face using service
            try:
                result = face_service.register_user_face(g.user_id, photos_list)
                
                if not result['success']:
                    return error_response(result['message'], 400)
                
                # Update user in MongoDB
                user_model.register_face(g.user_id, ','.join(saved_paths) if saved_paths else None)
                
                return success_response(
                    {
                        'user_id': g.user_id,
                        'photo_count': result['photo_count'],
                        'message': result['message']
                    },
                    'Face registered successfully',
                    201
                )
                
            except ValueError as e:
                return error_response(str(e), 400)
            except Exception as e:
                return error_response(f'Face registration failed: {str(e)}', 500)
            
        except Exception as e:
            return error_response(f'Registration failed: {str(e)}', 500)
    
    @face_bp.route('/verify', methods=['POST'])
    @token_required
    def verify_face():
        """
        Verify user face for attendance check-in.
        
        Request:
            - Form data with 'photo' file upload
            OR
            - JSON with 'photo_base64' field
        
        Returns:
            200: Face verified with match result
            400: Validation error
        """
        try:
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
                    
                except Exception as e:
                    return error_response(f'Invalid base64 image: {str(e)}', 400)
            
            else:
                return error_response('No photo provided', 400)
            
            if image is None:
                return error_response('Failed to read image', 400)
            
            # Verify face using service
            result = face_service.verify_user_face(g.user_id, image)
            
            if not result['is_match']:
                return error_response(result['message'], 400, {
                    'confidence': result['confidence']
                })
            
            # Auto create attendance record
            attendance = attendance_model.create_attendance(
                user_id=g.user_id,
                attendance_type='check-in',
                method='face',
                confidence=result['confidence'],
                photo_path=photo_path
            )
            
            return success_response(
                {
                    'verified': True,
                    'user_id': g.user_id,
                    'confidence': result['confidence'],
                    'message': result['message'],
                    'attendance': attendance
                },
                'Face verified successfully'
            )
            
        except Exception as e:
            return error_response(f'Verification failed: {str(e)}', 500)
    
    @face_bp.route('/recognize', methods=['POST'])
    @token_required
    def recognize_face():
        """
        Recognize face from photo (identify user).
        
        Request:
            - Form data with 'photo' file upload
            OR
            - JSON with 'photo_base64' field
        
        Returns:
            200: Recognition result with user_id and confidence
        """
        try:
            # Get image
            image = None
            
            # Try file upload first
            if 'photo' in request.files:
                file = request.files['photo']
                
                # Validate file
                is_valid, error_msg = validate_image_file(file)
                if not is_valid:
                    return error_response(error_msg, 400)
                
                # Save file temporarily
                upload_folder = os.path.join(config.UPLOAD_FOLDER, 'temp')
                os.makedirs(upload_folder, exist_ok=True)
                relative_path = save_uploaded_file(file, upload_folder)
                photo_path = os.path.join(upload_folder, relative_path)
                
                # Read image
                image = cv2.imread(photo_path)
                
                # Delete temp file
                try:
                    os.remove(photo_path)
                except:
                    pass
                
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
                    
                except Exception as e:
                    return error_response(f'Invalid base64 image: {str(e)}', 400)
            
            else:
                return error_response('No photo provided', 400)
            
            if image is None:
                return error_response('Failed to read image', 400)
            
            # Recognize face using service
            result = face_service.recognize_face(image)
            
            if result['user_id'] is None:
                return error_response(result['message'], 404, {
                    'confidence': result['confidence']
                })
            
            # Get user info
            user = user_model.find_by_user_id(result['user_id'])
            
            return success_response(
                {
                    'user_id': result['user_id'],
                    'user_name': user['name'] if user else 'Unknown',
                    'confidence': result['confidence'],
                    'message': result['message']
                },
                'Face recognized successfully'
            )
            
        except Exception as e:
            return error_response(f'Recognition failed: {str(e)}', 500)
    
    @face_bp.route('/status', methods=['GET'])
    @token_required
    def get_face_status():
        """
        Check face registration status for current user.
        
        Returns:
            200: Registration status
        """
        try:
            user = user_model.find_by_user_id(g.user_id)
            
            if not user:
                return error_response('User not found', 404)
            
            face_data = face_embedding_model.get_by_user_id(g.user_id)
            
            return success_response(
                {
                    'user_id': g.user_id,
                    'face_registered': face_data is not None,
                    'photo_count': face_data['photo_count'] if face_data else 0,
                    'registered_at': face_data['registered_at'].isoformat() if face_data else None,
                    'verification_count': face_data.get('verification_count', 0) if face_data else 0
                },
                'Status retrieved successfully'
            )
            
        except Exception as e:
            return error_response(f'Failed to get status: {str(e)}', 500)
    
    @face_bp.route('/delete', methods=['DELETE'])
    @token_required
    def delete_face():
        """
        Delete face registration for current user.
        
        Returns:
            200: Face registration deleted
        """
        try:
            success = face_service.delete_user_face(g.user_id)
            
            if success:
                # Update user in MongoDB
                user_model.update_user(g.user_id, {
                    'face_registered': False,
                    'face_photo_path': None
                })
                
                return success_response(None, 'Face registration deleted successfully')
            else:
                return error_response('No face registration found', 404)
            
        except Exception as e:
            return error_response(f'Failed to delete face registration: {str(e)}', 500)
    
    @face_bp.route('/stats', methods=['GET'])
    @token_required
    @admin_required
    def get_stats():
        """
        Get face recognition statistics (admin only).
        
        Returns:
            200: Statistics
        """
        try:
            stats = face_service.get_stats()
            
            return success_response(stats, 'Statistics retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get statistics: {str(e)}', 500)
    
    return face_bp
