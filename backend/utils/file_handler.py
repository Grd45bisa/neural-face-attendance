"""
File handling utilities.
Provides functions for file upload, storage, and management.
"""

import os
import uuid
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import io


def save_uploaded_file(file, upload_folder, subfolder=None, max_size=(1920, 1920)):
    """
    Save uploaded file with unique filename.
    
    Args:
        file (FileStorage): Uploaded file
        upload_folder (str): Base upload folder
        subfolder (str): Optional subfolder (e.g., user_id)
        max_size (tuple): Maximum image dimensions (width, height)
        
    Returns:
        str: Relative path to saved file
        
    Raises:
        ValueError: If file is invalid
    """
    if not file or file.filename == '':
        raise ValueError("No file provided")
    
    # Create folder structure
    if subfolder:
        folder_path = os.path.join(upload_folder, subfolder)
    else:
        folder_path = upload_folder
    
    os.makedirs(folder_path, exist_ok=True)
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    file_path = os.path.join(folder_path, unique_filename)
    
    # Save and optionally resize image
    try:
        image = Image.open(file.stream)
        
        # Resize if needed
        if max_size and (image.width > max_size[0] or image.height > max_size[1]):
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert RGBA to RGB if needed
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Save
        image.save(file_path, quality=95, optimize=True)
        
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")
    
    # Return relative path
    if subfolder:
        return os.path.join(subfolder, unique_filename)
    return unique_filename


def save_base64_image(base64_string, upload_folder, subfolder=None):
    """
    Save base64 encoded image.
    
    Args:
        base64_string (str): Base64 encoded image
        upload_folder (str): Base upload folder
        subfolder (str): Optional subfolder
        
    Returns:
        str: Relative path to saved file
        
    Raises:
        ValueError: If base64 string is invalid
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        
        # Create folder structure
        if subfolder:
            folder_path = os.path.join(upload_folder, subfolder)
        else:
            folder_path = upload_folder
        
        os.makedirs(folder_path, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(folder_path, unique_filename)
        
        # Convert RGBA to RGB if needed
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Save
        image.save(file_path, 'JPEG', quality=95, optimize=True)
        
        # Return relative path
        if subfolder:
            return os.path.join(subfolder, unique_filename)
        return unique_filename
        
    except Exception as e:
        raise ValueError(f"Failed to process base64 image: {str(e)}")


def delete_file(file_path):
    """
    Delete file if exists.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        bool: True if deleted, False if file doesn't exist
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    return False


def create_user_folder(upload_folder, user_id):
    """
    Create folder for user uploads.
    
    Args:
        upload_folder (str): Base upload folder
        user_id (str): User ID
        
    Returns:
        str: Path to user folder
    """
    user_folder = os.path.join(upload_folder, user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def get_file_extension(filename):
    """
    Get file extension.
    
    Args:
        filename (str): Filename
        
    Returns:
        str: File extension (lowercase) or empty string
    """
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def generate_unique_filename(original_filename):
    """
    Generate unique filename while preserving extension.
    
    Args:
        original_filename (str): Original filename
        
    Returns:
        str: Unique filename
    """
    extension = get_file_extension(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    
    if extension:
        return f"{timestamp}_{unique_id}.{extension}"
    return f"{timestamp}_{unique_id}"
