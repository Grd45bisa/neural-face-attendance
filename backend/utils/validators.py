"""
Input validation utilities.
Provides validators for common input types.
"""

import re
from werkzeug.datastructures import FileStorage


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 simplified regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength.
    Requirements:
    - Minimum 8 characters
    - At least one letter
    - At least one number
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_file_type(filename, allowed_extensions):
    """
    Validate file extension.
    
    Args:
        filename (str): Filename to validate
        allowed_extensions (set): Set of allowed extensions (e.g., {'jpg', 'png'})
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not filename:
        return False
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_file_size(file, max_size):
    """
    Validate file size.
    
    Args:
        file (FileStorage): Uploaded file
        max_size (int): Maximum size in bytes
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not file:
        return False
    
    # Seek to end to get file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    return size <= max_size


def validate_image_file(file):
    """
    Validate that file is a valid image.
    
    Args:
        file (FileStorage): Uploaded file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if not validate_file_type(file.filename, allowed_extensions):
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    return True, None


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present.
    
    Args:
        data (dict): Data to validate
        required_fields (list): List of required field names
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    if not data:
        return False, required_fields
    
    missing = [field for field in required_fields if field not in data or not data[field]]
    
    return len(missing) == 0, missing


def sanitize_string(text, max_length=None):
    """
    Sanitize string input.
    
    Args:
        text (str): Text to sanitize
        max_length (int): Maximum length (optional)
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text
