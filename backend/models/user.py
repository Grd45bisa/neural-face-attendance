"""
User model for MongoDB.
Handles user data, authentication, and face registration.
"""

from datetime import datetime
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import bcrypt
import uuid


class User:
    """User model for managing user data in MongoDB."""
    
    def __init__(self, db):
        """
        Initialize User model.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.users
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for better query performance."""
        self.collection.create_index([('email', ASCENDING)], unique=True)
        self.collection.create_index([('user_id', ASCENDING)], unique=True)
    
    def create_user(self, email, password, name, role='student', nis=None, class_name=None, phone=None, metadata=None):
        """
        Create a new user.
        
        Args:
            email (str): User email (unique)
            password (str): Plain text password (will be hashed)
            name (str): Full name (full_name)
            role (str): User role (student, teacher, admin)
            nis (str): Nomor Induk Siswa (optional)
            class_name (str): Class name (optional)
            phone (str): Phone number (optional)
            metadata (dict): Additional user metadata
            
        Returns:
            dict: Created user document (without password_hash)
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email exists
        if self.find_by_email(email):
            raise ValueError("Email already registered")
        
        # Generate unique user_id
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user document
        user_doc = {
            'user_id': user_id,
            'email': email.lower(),
            'password_hash': password_hash,
            'full_name': name,  # Changed from 'name' to 'full_name'
            'name': name,  # Keep for backward compatibility
            'nis': nis,
            'class_name': class_name,
            'phone': phone,
            'role': role,
            'is_face_registered': False,  # Changed from 'face_registered'
            'face_registered': False,  # Keep for backward compatibility
            'face_photo_path': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        # Insert into database
        result = self.collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        # Return user without password_hash
        return self._sanitize_user(user_doc)
    
    def find_by_email(self, email):
        """
        Find user by email.
        
        Args:
            email (str): User email
            
        Returns:
            dict: User document or None
        """
        return self.collection.find_one({'email': email.lower()})
    
    def find_by_user_id(self, user_id):
        """
        Find user by user_id (face recognition ID).
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User document (sanitized) or None
        """
        user = self.collection.find_one({'user_id': user_id})
        return self._sanitize_user(user) if user else None
    
    def find_by_id(self, object_id):
        """
        Find user by MongoDB ObjectId.
        
        Args:
            object_id (str or ObjectId): MongoDB _id
            
        Returns:
            dict: User document (sanitized) or None
        """
        if isinstance(object_id, str):
            object_id = ObjectId(object_id)
        
        user = self.collection.find_one({'_id': object_id})
        return self._sanitize_user(user) if user else None
    
    def update_user(self, user_id, updates):
        """
        Update user data.
        
        Args:
            user_id (str): User ID
            updates (dict): Fields to update
            
        Returns:
            dict: Updated user document or None
        """
        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow()
        
        # Update document
        result = self.collection.find_one_and_update(
            {'user_id': user_id},
            {'$set': updates},
            return_document=True
        )
        
        return self._sanitize_user(result) if result else None
    
    def register_face(self, user_id, photo_path):
        """
        Update user face registration status.
        
        Args:
            user_id (str): User ID
            photo_path (str): Path to face photo
            
        Returns:
            dict: Updated user document or None
        """
        return self.update_user(user_id, {
            'face_registered': True,
            'face_photo_path': photo_path
        })
    
    def verify_password(self, email, password):
        """
        Verify user password.
        
        Args:
            email (str): User email
            password (str): Plain text password
            
        Returns:
            dict: User document (sanitized) if password is correct, None otherwise
        """
        user = self.find_by_email(email)
        
        if not user:
            return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            return self._sanitize_user(user)
        
        return None
    
    def change_password(self, user_id, new_password):
        """
        Change user password.
        
        Args:
            user_id (str): User ID
            new_password (str): New plain text password
            
        Returns:
            bool: True if successful
        """
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': {
                'password_hash': password_hash,
                'updated_at': datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    
    def delete_user(self, user_id):
        """
        Delete user (soft delete by marking as deleted).
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if successful
        """
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': {
                'deleted': True,
                'deleted_at': datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    
    def get_all_users(self, role=None, skip=0, limit=50):
        """
        Get all users with optional filtering.
        
        Args:
            role (str): Filter by role (optional)
            skip (int): Number of documents to skip
            limit (int): Maximum number of documents to return
            
        Returns:
            list: List of user documents (sanitized)
        """
        query = {'deleted': {'$ne': True}}
        
        if role:
            query['role'] = role
        
        users = self.collection.find(query).skip(skip).limit(limit)
        return [self._sanitize_user(user) for user in users]
    
    def count_users(self, role=None):
        """
        Count total users.
        
        Args:
            role (str): Filter by role (optional)
            
        Returns:
            int: Total count
        """
        query = {'deleted': {'$ne': True}}
        
        if role:
            query['role'] = role
        
        return self.collection.count_documents(query)
    
    def _sanitize_user(self, user):
        """
        Remove sensitive data from user document.
        
        Args:
            user (dict): User document
            
        Returns:
            dict: Sanitized user document
        """
        if not user:
            return None
        
        # Convert ObjectId to string
        if '_id' in user:
            user['_id'] = str(user['_id'])
        
        # Remove password hash
        user.pop('password_hash', None)
        
        return user
