"""
User profile routes.
Handles user profile management.
"""

from flask import Blueprint, request, g
from models.user import User
from middleware.auth_middleware import token_required, admin_required
from utils.response import success_response, error_response, paginated_response
from utils.validators import validate_password, validate_required_fields

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


def init_user_routes(db):
    """
    Initialize user routes with database connection.
    
    Args:
        db: MongoDB database instance
    """
    user_model = User(db)
    
    @user_bp.route('/', methods=['GET'])
    def index():
        """Default route to check if user service is running."""
        return success_response(None, 'User service running')

    @user_bp.route('/profile', methods=['GET'])
    @token_required
    def get_profile():
        """
        Get current user profile.
        
        Returns:
            200: User profile data
            404: User not found
        """
        try:
            user = user_model.find_by_user_id(g.user_id)
            
            if not user:
                return error_response('User not found', 404)
            
            return success_response(user, 'Profile retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get profile: {str(e)}', 500)
    
    @user_bp.route('/profile', methods=['PUT'])
    @token_required
    def update_profile():
        """
        Update current user profile.
        
        Request Body:
            {
                "name": "New Name",
                "metadata": {
                    "phone": "123456789",
                    "class": "12A",
                    "student_id": "2024001"
                }
            }
        
        Returns:
            200: Profile updated successfully
        """
        try:
            data = request.get_json()
            
            # Prepare updates
            updates = {}
            
            if 'name' in data:
                updates['name'] = data['name'].strip()
            
            if 'metadata' in data:
                updates['metadata'] = data['metadata']
            
            if not updates:
                return error_response('No fields to update', 400)
            
            # Update user
            user = user_model.update_user(g.user_id, updates)
            
            if not user:
                return error_response('User not found', 404)
            
            return success_response(user, 'Profile updated successfully')
            
        except Exception as e:
            return error_response(f'Failed to update profile: {str(e)}', 500)
    
    @user_bp.route('/password', methods=['PUT'])
    @token_required
    def change_password():
        """
        Change user password.
        
        Request Body:
            {
                "current_password": "old_password",
                "new_password": "new_password"
            }
        
        Returns:
            200: Password changed successfully
            401: Invalid current password
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            is_valid, missing = validate_required_fields(data, ['current_password', 'new_password'])
            if not is_valid:
                return error_response(
                    'Missing required fields',
                    400,
                    {'missing_fields': missing}
                )
            
            current_password = data['current_password']
            new_password = data['new_password']
            
            # Validate new password
            is_valid, error_msg = validate_password(new_password)
            if not is_valid:
                return error_response(error_msg, 400)
            
            # Get user
            user = user_model.find_by_user_id(g.user_id)
            if not user:
                return error_response('User not found', 404)
            
            # Verify current password
            verified_user = user_model.verify_password(user['email'], current_password)
            if not verified_user:
                return error_response('Current password is incorrect', 401)
            
            # Change password
            success = user_model.change_password(g.user_id, new_password)
            
            if success:
                return success_response(None, 'Password changed successfully')
            else:
                return error_response('Failed to change password', 500)
            
        except Exception as e:
            return error_response(f'Failed to change password: {str(e)}', 500)
    
    @user_bp.route('/account', methods=['DELETE'])
    @token_required
    def delete_account():
        """
        Delete user account (soft delete).
        
        Returns:
            200: Account deleted successfully
        """
        try:
            success = user_model.delete_user(g.user_id)
            
            if success:
                return success_response(None, 'Account deleted successfully')
            else:
                return error_response('Failed to delete account', 500)
            
        except Exception as e:
            return error_response(f'Failed to delete account: {str(e)}', 500)
    
    # Admin routes
    @user_bp.route('/all', methods=['GET'])
    @token_required
    @admin_required
    def get_all_users():
        """
        Get all users (admin only).
        
        Query Parameters:
            role: Filter by role (optional)
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
        
        Returns:
            200: List of users with pagination
        """
        try:
            role = request.args.get('role')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            
            # Calculate skip
            skip = (page - 1) * per_page
            
            # Get users
            users = user_model.get_all_users(role=role, skip=skip, limit=per_page)
            total = user_model.count_users(role=role)
            
            return paginated_response(users, page, per_page, total, 'Users retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get users: {str(e)}', 500)
    
    @user_bp.route('/<user_id>', methods=['GET'])
    @token_required
    @admin_required
    def get_user(user_id):
        """
        Get specific user by ID (admin only).
        
        Returns:
            200: User data
            404: User not found
        """
        try:
            user = user_model.find_by_user_id(user_id)
            
            if not user:
                return error_response('User not found', 404)
            
            return success_response(user, 'User retrieved successfully')
            
        except Exception as e:
            return error_response(f'Failed to get user: {str(e)}', 500)
    
    @user_bp.route('/<user_id>/role', methods=['PUT'])
    @token_required
    @admin_required
    def update_user_role(user_id):
        """
        Update user role (admin only).
        
        Request Body:
            {
                "role": "teacher"
            }
        
        Returns:
            200: Role updated successfully
        """
        try:
            data = request.get_json()
            role = data.get('role')
            
            if not role:
                return error_response('Role is required', 400)
            
            if role not in ['student', 'teacher', 'admin']:
                return error_response('Invalid role', 400)
            
            user = user_model.update_user(user_id, {'role': role})
            
            if not user:
                return error_response('User not found', 404)
            
            return success_response(user, 'Role updated successfully')
            
        except Exception as e:
            return error_response(f'Failed to update role: {str(e)}', 500)
    
    @user_bp.route('/<user_id>', methods=['DELETE'])
    @token_required
    @admin_required
    def delete_user(user_id):
        """
        Delete user (admin only).
        
        Returns:
            200: User deleted successfully
        """
        try:
            success = user_model.delete_user(user_id)
            
            if success:
                return success_response(None, 'User deleted successfully')
            else:
                return error_response('User not found', 404)
            
        except Exception as e:
            return error_response(f'Failed to delete user: {str(e)}', 500)
    
    return user_bp
