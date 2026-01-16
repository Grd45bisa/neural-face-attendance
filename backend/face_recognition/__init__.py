"""
Face recognition module initialization.
Provides singleton instances of face recognition components.
"""

import os
import sys

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from face_detector import FaceDetector
from face_preprocessor import FacePreprocessor
from face_encoder import FaceEncoder
from face_matcher import FaceMatcher
from face_recognizer import FaceRecognizer
from database_manager import DatabaseManager

# Singleton instances
_detector = None
_preprocessor = None
_encoder = None
_matcher = None
_recognizer = None
_db_manager = None


def get_face_detector():
    """Get singleton FaceDetector instance."""
    global _detector
    if _detector is None:
        _detector = FaceDetector(min_confidence=0.5)
    return _detector


def get_face_preprocessor():
    """Get singleton FacePreprocessor instance."""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = FacePreprocessor()
    return _preprocessor


def get_face_encoder():
    """Get singleton FaceEncoder instance."""
    global _encoder
    if _encoder is None:
        _encoder = FaceEncoder()
    return _encoder


def get_face_matcher():
    """Get singleton FaceMatcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = FaceMatcher(similarity_threshold=0.7)
    return _matcher


def get_database_manager(db_path=None):
    """
    Get singleton DatabaseManager instance.
    
    Args:
        db_path (str): Path to database file (optional)
    """
    global _db_manager
    if _db_manager is None:
        if db_path is None:
            # Default path relative to backend
            db_path = os.path.join(os.path.dirname(current_dir), '..', 'data', 'embeddings.pkl')
        _db_manager = DatabaseManager(db_path=db_path, auto_save=True)
    return _db_manager


def get_face_recognizer(db_path=None):
    """
    Get singleton FaceRecognizer instance.
    
    Args:
        db_path (str): Path to database file (optional)
    """
    global _recognizer
    if _recognizer is None:
        detector = get_face_detector()
        preprocessor = get_face_preprocessor()
        encoder = get_face_encoder()
        matcher = get_face_matcher()
        db_manager = get_database_manager(db_path)
        
        _recognizer = FaceRecognizer(
            detector=detector,
            preprocessor=preprocessor,
            encoder=encoder,
            matcher=matcher,
            db_manager=db_manager,
            mode='multiple',
            debug=False
        )
    return _recognizer


__all__ = [
    'get_face_detector',
    'get_face_preprocessor',
    'get_face_encoder',
    'get_face_matcher',
    'get_database_manager',
    'get_face_recognizer'
]
