"""
Standard API response formatter.
Provides consistent response structure across all endpoints.
"""

from flask import jsonify


def success_response(data=None, message="Success", status=200):
    """
    Create a success response.
    
    Args:
        data: Response data (dict, list, or any JSON-serializable object)
        message (str): Success message
        status (int): HTTP status code
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        >>> return success_response({'user_id': '123'}, 'User created', 201)
    """
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response), status


def error_response(message, status=400, errors=None):
    """
    Create an error response.
    
    Args:
        message (str): Error message
        status (int): HTTP status code
        errors (dict): Additional error details (optional)
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        >>> return error_response('Invalid email', 400, {'email': 'Email format invalid'})
    """
    response = {
        'success': False,
        'message': message
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status


def paginated_response(data, page, per_page, total, message="Success"):
    """
    Create a paginated response.
    
    Args:
        data (list): List of items for current page
        page (int): Current page number
        per_page (int): Items per page
        total (int): Total number of items
        message (str): Success message
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    }
    return jsonify(response), 200
