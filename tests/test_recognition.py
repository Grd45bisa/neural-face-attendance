"""
Test script untuk Recognition module.
Test complete face recognition pipeline.
"""

import sys
import os
import cv2

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.face_detector import FaceDetector
from core.face_preprocessor import FacePreprocessor
from core.face_encoder import FaceEncoder
from core.face_matcher import FaceMatcher
from core.face_recognizer import FaceRecognizer
from database.database_manager import DatabaseManager


def setup_test_database():
    """Setup test database dengan dummy users."""
    print("Setting up test database...")
    
    db_manager = DatabaseManager('data/test_recognition_db.pkl')
    
    # Create dummy embeddings
    import numpy as np
    
    test_users = [
        {'user_id': 'alice_001', 'name': 'Alice'},
        {'user_id': 'bob_002', 'name': 'Bob'},
        {'user_id': 'charlie_003', 'name': 'Charlie'}
    ]
    
    for user in test_users:
        # Generate random embedding
        embedding = np.random.rand(1280)
        embedding = embedding / np.linalg.norm(embedding)
        
        try:
            db_manager.add_user(
                user_id=user['user_id'],
                name=user['name'],
                embedding=embedding
            )
        except ValueError:
            # User already exists
            pass
    
    print(f"✓ Test database ready with {len(test_users)} users")
    
    return db_manager


def test_recognition_from_image():
    """Test recognition dari image file."""
    print("\n" + "="*60)
    print("TEST 1: Recognition from Image")
    print("="*60)
    
    # Setup
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = setup_test_database()
    
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager
    )
    
    # Test image
    image_path = 'test_images/test_recognition.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    # Recognize
    result = recognizer.recognize_from_file(image_path)
    
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    
    if result['status'] == 'success':
        for i, res in enumerate(result['results']):
            print(f"\n  Face {i+1}:")
            print(f"    Name: {res['name']}")
            print(f"    User ID: {res['user_id']}")
            print(f"    Confidence: {res['confidence']:.2f}%")
            print(f"    Similarity: {res['similarity']:.4f}")
        
        return True
    
    return False


def test_recognition_accuracy():
    """Test recognition accuracy dengan known faces."""
    print("\n" + "="*60)
    print("TEST 2: Recognition Accuracy")
    print("="*60)
    
    # Setup
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = setup_test_database()
    
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager
    )
    
    # Test dengan multiple thresholds
    thresholds = [0.5, 0.6, 0.7, 0.8]
    
    print("\nTesting different thresholds:")
    
    for threshold in thresholds:
        matcher.set_threshold(threshold)
        
        # Test image
        image_path = 'test_images/test_recognition.jpg'
        
        if os.path.exists(image_path):
            result = recognizer.recognize_from_file(image_path)
            
            if result['status'] == 'success':
                matches = sum(1 for r in result['results'] if r['user_id'] != 'unknown')
                total = len(result['results'])
                
                print(f"  Threshold {threshold}: {matches}/{total} matches")
    
    return True


def test_unknown_face():
    """Test recognition dengan unknown face."""
    print("\n" + "="*60)
    print("TEST 3: Unknown Face Recognition")
    print("="*60)
    
    # Setup
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = setup_test_database()
    
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager
    )
    
    # Test dengan unknown face
    image_path = 'test_images/unknown_person.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    result = recognizer.recognize_from_file(image_path)
    
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    
    if result['status'] == 'success':
        for res in result['results']:
            print(f"  Name: {res['name']}")
            print(f"  User ID: {res['user_id']}")
            
            if res['user_id'] == 'unknown':
                print("  ✓ Correctly identified as unknown")
                return True
    
    return False


def test_annotation():
    """Test image annotation."""
    print("\n" + "="*60)
    print("TEST 4: Image Annotation")
    print("="*60)
    
    # Setup
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = setup_test_database()
    
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager
    )
    
    # Test image
    image_path = 'test_images/test_recognition.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    image = cv2.imread(image_path)
    result = recognizer.recognize_from_image(image)
    
    if result['status'] == 'success':
        # Annotate
        annotated = recognizer.annotate_image(image, result)
        
        # Save
        output_path = 'test_output/annotated_recognition.jpg'
        os.makedirs('test_output', exist_ok=True)
        cv2.imwrite(output_path, annotated)
        
        print(f"\n✓ Annotated image saved: {output_path}")
        
        # Show
        cv2.imshow('Annotated Recognition', annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return True
    
    return False


def run_all_tests():
    """Run all recognition tests."""
    print("\n" + "="*60)
    print("RECOGNITION TEST SUITE".center(60))
    print("="*60)
    
    results = {
        'Recognition from Image': test_recognition_from_image(),
        'Recognition Accuracy': test_recognition_accuracy(),
        'Unknown Face': test_unknown_face(),
        'Image Annotation': test_annotation()
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
