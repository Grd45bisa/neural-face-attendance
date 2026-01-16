"""
Test script untuk Registration module.
Test user registration process.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.face_detector import FaceDetector
from core.face_preprocessor import FacePreprocessor
from core.face_encoder import FaceEncoder
from database.database_manager import DatabaseManager
from registration.registration import UserRegistration


def test_registration_from_file():
    """Test registration dari file image."""
    print("\n" + "="*60)
    print("TEST 1: Registration from File")
    print("="*60)
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    db_manager = DatabaseManager('data/test_db.pkl')
    
    registration = UserRegistration(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        db_manager=db_manager
    )
    
    # Test registration
    image_path = 'test_images/test_person.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    result = registration.register_from_file(
        user_id='test_user_001',
        name='Test User',
        image_path=image_path
    )
    
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    
    if result['status'] == 'success':
        print(f"  User ID: {result['user_id']}")
        print(f"  Name: {result['name']}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
        return True
    else:
        return False


def test_registration_validation():
    """Test registration validation."""
    print("\n" + "="*60)
    print("TEST 2: Registration Validation")
    print("="*60)
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    db_manager = DatabaseManager('data/test_db.pkl')
    
    registration = UserRegistration(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        db_manager=db_manager
    )
    
    # Create dummy embedding
    import numpy as np
    dummy_embedding = np.random.rand(1280)
    dummy_embedding = dummy_embedding / np.linalg.norm(dummy_embedding)
    
    # Test validation
    is_valid, reason = registration.validate_registration(dummy_embedding)
    
    print(f"\nValidation Result:")
    print(f"  Valid: {is_valid}")
    print(f"  Reason: {reason}")
    
    return is_valid


def test_duplicate_registration():
    """Test duplicate user registration."""
    print("\n" + "="*60)
    print("TEST 3: Duplicate Registration")
    print("="*60)
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    db_manager = DatabaseManager('data/test_db.pkl')
    
    registration = UserRegistration(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        db_manager=db_manager
    )
    
    # Try to register same user twice
    image_path = 'test_images/test_person.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    # First registration
    result1 = registration.register_from_file(
        user_id='duplicate_test',
        name='Duplicate Test',
        image_path=image_path
    )
    
    print(f"\nFirst Registration:")
    print(f"  Status: {result1['status']}")
    
    # Second registration (should fail or prompt)
    result2 = registration.register_from_file(
        user_id='duplicate_test',
        name='Duplicate Test',
        image_path=image_path
    )
    
    print(f"\nSecond Registration:")
    print(f"  Status: {result2['status']}")
    print(f"  Message: {result2['message']}")
    
    # Cleanup
    db_manager.delete_user('duplicate_test')
    
    return result2['status'] in ['cancelled', 'failed']


def test_quality_score():
    """Test quality score calculation."""
    print("\n" + "="*60)
    print("TEST 4: Quality Score Calculation")
    print("="*60)
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    db_manager = DatabaseManager('data/test_db.pkl')
    
    registration = UserRegistration(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        db_manager=db_manager
    )
    
    # Create dummy embeddings
    import numpy as np
    
    embeddings = []
    for i in range(5):
        emb = np.random.rand(1280)
        emb = emb / np.linalg.norm(emb)
        embeddings.append(emb)
    
    # Calculate quality score
    quality_score = registration._calculate_quality_score(embeddings)
    
    print(f"\nQuality Score: {quality_score:.2f}/100")
    
    return 0 <= quality_score <= 100


def run_all_tests():
    """Run all registration tests."""
    print("\n" + "="*60)
    print("REGISTRATION TEST SUITE".center(60))
    print("="*60)
    
    results = {
        'Registration from File': test_registration_from_file(),
        'Registration Validation': test_registration_validation(),
        'Duplicate Registration': test_duplicate_registration(),
        'Quality Score': test_quality_score()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY".center(60))
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
