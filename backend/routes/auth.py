"""
Authentication routes.
Handles user registration, login, logout, and token refresh.
"""

from flask import Blueprint, request, g
from models.user import User
from middleware.auth_middleware import (
    generate_access_token,
    generate_refresh_token,
    decode_refresh_token,
    token_required,
    blacklist_token
)
from utils.response import success_response, error_response
from utils.validators import validate_email, validate_password, validate_required_fields
import jwt

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def init_auth_routes(db):
    """
    Initialize auth routes with database connection.
    
    Args:
        db: MongoDB database instance
    """
    user_model = User(db)
    
    @auth_bp.route('/', methods=['GET'])
    def index():
        """Default route to check if auth service is running."""
        return success_response(None, 'Auth service running')

    @auth_bp.route('/register', methods=['POST'])
    def register():
        """
        Register a new user.
        
        Request Body:
            {
                "email": "user@example.com",
                "password": "password123",
                "name": "Full Name",
                "role": "student",  // optional, default: student
                "metadata": {}      // optional
            }
        
        Returns:
            201: User created successfully
            400: Validation error or email already exists
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            is_valid, missing = validate_required_fields(data, ['email', 'password', 'name'])
            if not is_valid:
                return error_response(
                    'Missing required fields',
                    400,
                    {'missing_fields': missing}
                )
            
            email = data['email'].strip()
            password = data['password']
            name = data['name'].strip()
            role = data.get('role', 'student')
            metadata = data.get('metadata', {})
            
            # Validate email
            if not validate_email(email):
                return error_response('Invalid email format', 400)
            
            # Validate password
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                return error_response(error_msg, 400)
            
            # Validate role
            if role not in ['student', 'teacher', 'admin']:
                return error_response('Invalid role. Must be: student, teacher, or admin', 400)
            
            # Create user
            try:
                user = user_model.create_user(email, password, name, role, metadata)
                
                # Generate tokens
                access_token = generate_access_token(user['user_id'], user['email'], user['role'])
                refresh_token = generate_refresh_token(user['user_id'])
                
                return success_response(
                    {
                        'user': user,
                        'access_token': access_token,
                        'refresh_token': refresh_token
                    },
                    'User registered successfully',
                    201
                )
                
            except ValueError as e:
                return error_response(str(e), 400)
            
        except Exception as e:
            return error_response(f'Registration failed: {str(e)}', 500)
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        """
        Login user.
        
        Request Body:
            {
                "email": "user@example.com",
                "password": "password123"
            }
        
        Returns:
            200: Login successful with tokens
            401: Invalid credentials
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            is_valid, missing = validate_required_fields(data, ['email', 'password'])
            if not is_valid:
                return error_response(
                    'Missing required fields',
                    400,
                    {'missing_fields': missing}
                )
            
            email = data['email'].strip()
            password = data['password']
            
            # Verify credentials
            user = user_model.verify_password(email, password)
            
            if not user:
                return error_response('Invalid email or password', 401)
            
            # Generate tokens
            access_token = generate_access_token(user['user_id'], user['email'], user['role'])
            refresh_token = generate_refresh_token(user['user_id'])
            
            return success_response(
                {
                    'user': user,
                    'access_token': access_token,
                    'refresh_token': refresh_token
                },
                'Login successful'
            )
            
        except Exception as e:
            return error_response(f'Login failed: {str(e)}', 500)
    
    @auth_bp.route('/logout', methods=['POST'])
    @token_required
    def logout():
        """
        Logout user (blacklist refresh token).
        
        Request Body:
            {
                "refresh_token": "token_here"
            }
        
        Returns:
            200: Logout successful
        """
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            
            if refresh_token:
                blacklist_token(refresh_token)
            
            return success_response(None, 'Logout successful')
            
        except Exception as e:
            return error_response(f'Logout failed: {str(e)}', 500)
    
    @auth_bp.route('/refresh', methods=['POST'])
    def refresh():
        """
        Refresh access token using refresh token.
        
        Request Body:
            {
                "refresh_token": "token_here"
            }
        
        Returns:
            200: New access token
            401: Invalid or expired refresh token
        """
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return error_response('Refresh token is required', 400)
            
            # Check if token is blacklisted
            from middleware.auth_middleware import is_token_blacklisted
            if is_token_blacklisted(refresh_token):
                return error_response('Token has been revoked', 401)
            
            # Decode refresh token
            try:
                payload = decode_refresh_token(refresh_token)
                
                # Verify token type
                if payload.get('type') != 'refresh':
                    return error_response('Invalid token type', 401)
                
                user_id = payload['user_id']
                
                # Get user data
                user = user_model.find_by_user_id(user_id)
                
                if not user:
                    return error_response('User not found', 404)
                
                # Generate new access token
                access_token = generate_access_token(user['user_id'], user['email'], user['role'])
                
                return success_response(
                    {'access_token': access_token},
                    'Token refreshed successfully'
                )
                
            except jwt.ExpiredSignatureError:
                return error_response('Refresh token has expired', 401)
            except jwt.InvalidTokenError:
                return error_response('Invalid refresh token', 401)
            
        except Exception as e:
            return error_response(f'Token refresh failed: {str(e)}', 500)
    
    return auth_bp
