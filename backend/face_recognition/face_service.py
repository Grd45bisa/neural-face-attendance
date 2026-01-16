"""
Face Recognition Service.
Wrapper class that integrates existing face recognition code with MongoDB storage.
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime

# Add face_recognition module to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from face_detector import FaceDetector
from face_preprocessor import FacePreprocessor
from face_encoder import FaceEncoder
from face_matcher import FaceMatcher


class FaceRecognitionService:
    """
    Service class for face recognition operations.
    Bridges existing face recognition code with MongoDB storage.
    """
    
    def __init__(self, face_embedding_model, confidence_threshold=0.7):
        """
        Initialize face recognition service.
        
        Args:
            face_embedding_model: FaceEmbedding model instance
            confidence_threshold (float): Minimum confidence for match
        """
        self.face_embedding_model = face_embedding_model
        self.confidence_threshold = confidence_threshold
        
        # Initialize face recognition components
        self.detector = FaceDetector(min_confidence=0.5)
        self.preprocessor = FacePreprocessor()
        self.encoder = FaceEncoder()
        self.matcher = FaceMatcher(threshold=confidence_threshold)
        
        print("Face Recognition Service initialized")
    
    def register_user_face(self, user_id, photos_list):
        """
        Register user face from multiple photos.
        
        Args:
            user_id (str): User ID
            photos_list (list): List of image arrays (BGR format)
            
        Returns:
            dict: {
                'success': bool,
                'embeddings': numpy.ndarray,
                'photo_count': int,
                'message': str
            }
            
        Raises:
            ValueError: If validation fails
        """
        if not photos_list or len(photos_list) == 0:
            raise ValueError("No photos provided")
        
        if len(photos_list) < 3:
            raise ValueError("Minimum 3 photos required for registration")
        
        if len(photos_list) > 10:
            raise ValueError("Maximum 10 photos allowed")
        
        # Check if user already registered
        existing = self.face_embedding_model.get_by_user_id(user_id)
        if existing:
            raise ValueError("User already has face registered")
        
        embeddings_list = []
        processed_count = 0
        
        for idx, image in enumerate(photos_list):
            try:
                # Detect faces
                faces = self.detector.detect_faces(image)
                
                if len(faces) == 0:
                    print(f"Warning: No face detected in photo {idx + 1}")
                    continue
                
                if len(faces) > 1:
                    print(f"Warning: Multiple faces detected in photo {idx + 1}, using first face")
                
                # Get first face
                face_data = faces[0]
                
                # Preprocess face
                preprocessed_face = self.preprocessor.preprocess(image, face_data['box'], face_data['keypoints'])
                
                if preprocessed_face is None:
                    print(f"Warning: Failed to preprocess photo {idx + 1}")
                    continue
                
                # Extract embedding
                embedding = self.encoder.encode_face(preprocessed_face)
                
                if embedding is None:
                    print(f"Warning: Failed to extract embedding from photo {idx + 1}")
                    continue
                
                embeddings_list.append(embedding)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing photo {idx + 1}: {str(e)}")
                continue
        
        # Validate processed photos
        if processed_count < 3:
            raise ValueError(f"Only {processed_count} photos processed successfully. Minimum 3 required.")
        
        # Average embeddings for better accuracy
        averaged_embedding = np.mean(embeddings_list, axis=0)
        
        # Normalize
        averaged_embedding = averaged_embedding / np.linalg.norm(averaged_embedding)
        
        # Save to MongoDB
        face_doc = self.face_embedding_model.register_face(
            user_id=user_id,
            embeddings=averaged_embedding,
            photo_count=processed_count
        )
        
        return {
            'success': True,
            'embeddings': averaged_embedding,
            'photo_count': processed_count,
            'message': f'Face registered successfully with {processed_count} photos'
        }
    
    def verify_user_face(self, user_id, photo):
        """
        Verify user face against registered embedding.
        
        Args:
            user_id (str): User ID to verify
            photo (numpy.ndarray): Image array (BGR format)
            
        Returns:
            dict: {
                'is_match': bool,
                'confidence': float,
                'message': str
            }
        """
        # Get registered embedding
        face_data = self.face_embedding_model.get_by_user_id(user_id)
        
        if not face_data:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'User face not registered'
            }
        
        registered_embedding = face_data['embeddings_array']
        
        # Detect face in photo
        faces = self.detector.detect_faces(photo)
        
        if len(faces) == 0:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'No face detected in photo'
            }
        
        if len(faces) > 1:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'Multiple faces detected. Please use photo with single face.'
            }
        
        # Get face
        face = faces[0]
        
        # Preprocess
        preprocessed_face = self.preprocessor.preprocess(photo, face['box'], face['keypoints'])
        
        if preprocessed_face is None:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'Failed to preprocess face'
            }
        
        # Extract embedding
        current_embedding = self.encoder.encode_face(preprocessed_face)
        
        if current_embedding is None:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'Failed to extract face embedding'
            }
        
        # Calculate similarity
        similarity = self.matcher.compute_similarity(current_embedding, registered_embedding)
        
        is_match = similarity >= self.confidence_threshold
        
        # Update verification stats if match
        if is_match:
            self.face_embedding_model.update_verification(user_id)
        
        return {
            'is_match': is_match,
            'confidence': float(similarity),
            'message': 'Face verified' if is_match else f'Face does not match (confidence: {similarity:.2f})'
        }
    
    def recognize_face(self, photo):
        """
        Recognize face from photo against all registered users.
        
        Args:
            photo (numpy.ndarray): Image array (BGR format)
            
        Returns:
            dict: {
                'user_id': str or None,
                'confidence': float,
                'message': str
            }
        """
        # Detect face
        faces = self.detector.detect_faces(photo)
        
        if len(faces) == 0:
            return {
                'user_id': None,
                'confidence': 0.0,
                'message': 'No face detected in photo'
            }
        
        if len(faces) > 1:
            return {
                'user_id': None,
                'confidence': 0.0,
                'message': 'Multiple faces detected. Please use photo with single face.'
            }
        
        # Get face
        face = faces[0]
        
        # Preprocess
        preprocessed_face = self.preprocessor.preprocess(photo, face['box'], face['keypoints'])
        
        if preprocessed_face is None:
            return {
                'user_id': None,
                'confidence': 0.0,
                'message': 'Failed to preprocess face'
            }
        
        # Extract embedding
        current_embedding = self.encoder.encode_face(preprocessed_face)
        
        if current_embedding is None:
            return {
                'user_id': None,
                'confidence': 0.0,
                'message': 'Failed to extract face embedding'
            }
        
        # Get all registered embeddings
        all_embeddings = self.face_embedding_model.get_all_embeddings()
        
        if not all_embeddings:
            return {
                'user_id': None,
                'confidence': 0.0,
                'message': 'No registered faces in database'
            }
        
        # Find best match
        best_match_user_id = None
        best_similarity = 0.0
        
        for user_id, registered_embedding in all_embeddings.items():
            similarity = self.matcher.compute_similarity(current_embedding, registered_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_user_id = user_id
        
        # Check if best match meets threshold
        if best_similarity >= self.confidence_threshold:
            # Update verification stats
            self.face_embedding_model.update_verification(best_match_user_id)
            
            return {
                'user_id': best_match_user_id,
                'confidence': float(best_similarity),
                'message': f'Face recognized as user {best_match_user_id}'
            }
        else:
            return {
                'user_id': None,
                'confidence': float(best_similarity),
                'message': f'No match found (best confidence: {best_similarity:.2f})'
            }
    
    def delete_user_face(self, user_id):
        """
        Delete user face registration.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if deleted
        """
        return self.face_embedding_model.delete_by_user_id(user_id)
    
    def get_stats(self):
        """
        Get face recognition statistics.
        
        Returns:
            dict: Statistics
        """
        return self.face_embedding_model.get_registration_stats()
