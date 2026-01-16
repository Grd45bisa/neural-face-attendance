"""
Face Embeddings model for MongoDB.
Stores face recognition embeddings with metadata.
"""

from datetime import datetime
from pymongo import ASCENDING
from bson.objectid import ObjectId
import numpy as np


class FaceEmbedding:
    """Face embedding model for managing face recognition data in MongoDB."""
    
    def __init__(self, db):
        """
        Initialize FaceEmbedding model.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.face_embeddings
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for better query performance."""
        self.collection.create_index([('user_id', ASCENDING)], unique=True)
    
    def register_face(self, user_id, embeddings, photo_count):
        """
        Register face embeddings for a user.
        
        Args:
            user_id (str): User ID
            embeddings (numpy.ndarray): Face embeddings (can be single or averaged)
            photo_count (int): Number of photos used
            
        Returns:
            dict: Created face embedding document
            
        Raises:
            ValueError: If user already has face registered
        """
        # Check if user already registered
        existing = self.get_by_user_id(user_id)
        if existing:
            raise ValueError("User already has face registered. Delete existing registration first.")
        
        # Convert numpy array to list for MongoDB storage
        if isinstance(embeddings, np.ndarray):
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = embeddings
        
        # Create document
        face_doc = {
            'user_id': user_id,
            'embeddings': embeddings_list,
            'registered_at': datetime.utcnow(),
            'photo_count': photo_count,
            'last_verified': None,
            'verification_count': 0
        }
        
        result = self.collection.insert_one(face_doc)
        face_doc['_id'] = str(result.inserted_id)
        
        return face_doc
    
    def get_by_user_id(self, user_id):
        """
        Get face embedding by user ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Face embedding document or None
        """
        doc = self.collection.find_one({'user_id': user_id})
        if doc:
            doc['_id'] = str(doc['_id'])
            # Convert embeddings list back to numpy array
            doc['embeddings_array'] = np.array(doc['embeddings'], dtype=np.float32)
        return doc
    
    def get_all_embeddings(self):
        """
        Get all face embeddings for matching.
        
        Returns:
            dict: {user_id: embeddings_array} mapping
        """
        embeddings_dict = {}
        
        for doc in self.collection.find():
            user_id = doc['user_id']
            embeddings_array = np.array(doc['embeddings'], dtype=np.float32)
            embeddings_dict[user_id] = embeddings_array
        
        return embeddings_dict
    
    def update_verification(self, user_id):
        """
        Update last verification timestamp and count.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if successful
        """
        result = self.collection.update_one(
            {'user_id': user_id},
            {
                '$set': {'last_verified': datetime.utcnow()},
                '$inc': {'verification_count': 1}
            }
        )
        
        return result.modified_count > 0
    
    def delete_by_user_id(self, user_id):
        """
        Delete face embedding by user ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if deleted
        """
        result = self.collection.delete_one({'user_id': user_id})
        return result.deleted_count > 0
    
    def count_registered_faces(self):
        """
        Count total registered faces.
        
        Returns:
            int: Total count
        """
        return self.collection.count_documents({})
    
    def get_registration_stats(self):
        """
        Get registration statistics.
        
        Returns:
            dict: Statistics
        """
        total = self.count_registered_faces()
        
        # Get average photo count
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'avg_photos': {'$avg': '$photo_count'},
                    'total_verifications': {'$sum': '$verification_count'}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        if result:
            stats = result[0]
            return {
                'total_registered': total,
                'avg_photos_per_user': round(stats.get('avg_photos', 0), 2),
                'total_verifications': stats.get('total_verifications', 0)
            }
        
        return {
            'total_registered': total,
            'avg_photos_per_user': 0,
            'total_verifications': 0
        }
