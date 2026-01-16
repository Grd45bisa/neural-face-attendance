"""
JWT authentication middleware.
Provides token validation and protection for routes.
"""

from functools import wraps
from flask import request, g
import jwt
from datetime import datetime

from utils.response import error_response
from config import get_config

config = get_config()


def generate_access_token(user_id, email, role):
    """
    Generate JWT access token.
    
    Args:
        user_id (str): User ID
        email (str): User email
        role (str): User role
        
    Returns:
        str: JWT token
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'type': 'access',
        'exp': datetime.utcnow() + config.JWT_ACCESS_TOKEN_EXPIRES
    }
    
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def generate_refresh_token(user_id):
    """
    Generate JWT refresh token.
    
    Args:
        user_id (str): User ID
        
    Returns:
        str: JWT refresh token
    """
    payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + config.JWT_REFRESH_TOKEN_EXPIRES
    }
    
    return jwt.encode(payload, config.JWT_REFRESH_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token):
    """
    Decode and validate access token.
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def decode_refresh_token(token):
    """
    Decode and validate refresh token.
    
    Args:
        token (str): JWT refresh token
        
    Returns:
        dict: Token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, config.JWT_REFRESH_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def token_required(f):
    """
    Decorator to protect routes with JWT authentication.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            user_id = g.user_id
            return {'message': 'Protected data'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                # Expected format: "Bearer <token>"
                token = auth_header.split(' ')[1]
            except IndexError:
                return error_response('Invalid token format. Use: Bearer <token>', 401)
        
        if not token:
            return error_response('Authentication token is missing', 401)
        
        try:
            # Decode token
            payload = decode_access_token(token)
            
            # Verify token type
            if payload.get('type') != 'access':
                return error_response('Invalid token type', 401)
            
            # Store user info in Flask's g object
            g.user_id = payload['user_id']
            g.user_email = payload['email']
            g.user_role = payload['role']
            
        except jwt.ExpiredSignatureError:
            return error_response('Token has expired', 401)
        except jwt.InvalidTokenError:
            return error_response('Invalid token', 401)
        except Exception as e:
            return error_response(f'Token validation failed: {str(e)}', 401)
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator to protect routes requiring admin role.
    Must be used after @token_required.
    
    Usage:
        @app.route('/admin')
        @token_required
        @admin_required
        def admin_route():
            return {'message': 'Admin only data'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_role') or g.user_role != 'admin':
            return error_response('Admin access required', 403)
        
        return f(*args, **kwargs)
    
    return decorated


def teacher_or_admin_required(f):
    """
    Decorator to protect routes requiring teacher or admin role.
    Must be used after @token_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_role') or g.user_role not in ['teacher', 'admin']:
            return error_response('Teacher or admin access required', 403)
        
        return f(*args, **kwargs)
    
    return decorated


# Token blacklist (in-memory, for production use Redis)
token_blacklist = set()


def blacklist_token(token):
    """
    Add token to blacklist (for logout).
    
    Args:
        token (str): Token to blacklist
    """
    token_blacklist.add(token)


def is_token_blacklisted(token):
    """
    Check if token is blacklisted.
    
    Args:
        token (str): Token to check
        
    Returns:
        bool: True if blacklisted
    """
    return token in token_blacklist
