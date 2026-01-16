"""
Test script untuk Face Detection module.
Test MTCNN detector dengan berbagai scenarios.
"""

import sys
import os
import cv2

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.face_detector import FaceDetector


def test_single_face():
    """Test detection dengan single face."""
    print("\n" + "="*60)
    print("TEST 1: Single Face Detection")
    print("="*60)
    
    detector = FaceDetector(min_confidence=0.9)
    
    # Load test image
    image_path = 'test_images/single_face.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        print("  Please add test image or use camera")
        return False
    
    image = cv2.imread(image_path)
    
    # Detect faces
    faces = detector.detect_faces(image)
    
    print(f"\nResults:")
    print(f"  Faces detected: {len(faces)}")
    
    if faces:
        face = faces[0]
        print(f"  Confidence: {face['confidence']:.3f}")
        print(f"  Box: {face['box']}")
        print(f"  Keypoints: {list(face['keypoints'].keys())}")
        
        # Draw boxes
        result = detector.draw_boxes(image, faces)
        
        # Show result
        cv2.imshow('Single Face Detection', result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return True
    else:
        print("  ✗ No faces detected")
        return False


def test_multiple_faces():
    """Test detection dengan multiple faces."""
    print("\n" + "="*60)
    print("TEST 2: Multiple Faces Detection")
    print("="*60)
    
    detector = FaceDetector(min_confidence=0.9)
    
    # Load test image
    image_path = 'test_images/multiple_faces.jpg'
    
    if not os.path.exists(image_path):
        print(f"⚠ Test image not found: {image_path}")
        return False
    
    image = cv2.imread(image_path)
    
    # Detect faces
    faces = detector.detect_faces(image)
    
    print(f"\nResults:")
    print(f"  Faces detected: {len(faces)}")
    
    for i, face in enumerate(faces):
        print(f"\n  Face {i+1}:")
        print(f"    Confidence: {face['confidence']:.3f}")
        print(f"    Box: {face['box']}")
    
    if faces:
        # Draw boxes
        result = detector.draw_boxes(image, faces)
        
        # Show result
        cv2.imshow('Multiple Faces Detection', result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return True
    else:
        print("  ✗ No faces detected")
        return False


def test_from_camera():
    """Test detection dari camera."""
    print("\n" + "="*60)
    print("TEST 3: Camera Detection")
    print("="*60)
    print("Press 'q' to quit, 's' to save screenshot")
    
    detector = FaceDetector(min_confidence=0.9)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Cannot open camera")
        return False
    
    frame_count = 0
    detected_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        frame_count += 1
        
        # Detect faces
        faces = detector.detect_faces(frame)
        
        if faces:
            detected_count += 1
            
            # Draw boxes
            frame = detector.draw_boxes(frame, faces)
            
            # Show count
            cv2.putText(
                frame,
                f"Faces: {len(faces)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # Show frame
        cv2.imshow('Camera Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save screenshot
            filename = f'test_output/camera_test_{frame_count}.jpg'
            os.makedirs('test_output', exist_ok=True)
            cv2.imwrite(filename, frame)
            print(f"  Screenshot saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nCamera Test Results:")
    print(f"  Total frames: {frame_count}")
    print(f"  Frames with faces: {detected_count}")
    print(f"  Detection rate: {(detected_count/frame_count*100):.1f}%")
    
    return True


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    detector = FaceDetector(min_confidence=0.9)
    
    # Test 1: None image
    print("\n  Test 4.1: None image")
    try:
        faces = detector.detect_faces(None)
        print("    ✗ Should raise ValueError")
    except ValueError as e:
        print(f"    ✓ Correctly raised ValueError: {e}")
    
    # Test 2: Empty image
    print("\n  Test 4.2: Empty image")
    try:
        empty_image = cv2.imread('nonexistent.jpg')
        faces = detector.detect_faces(empty_image)
        print("    ✗ Should raise ValueError")
    except ValueError as e:
        print(f"    ✓ Correctly raised ValueError")
    
    # Test 3: No face in image
    print("\n  Test 4.3: No face in image")
    # Create blank image
    blank = cv2.imread('test_images/no_face.jpg')
    if blank is None:
        import numpy as np
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
    
    faces = detector.detect_faces(blank)
    print(f"    Faces detected: {len(faces)}")
    print(f"    ✓ Correctly returned empty list" if len(faces) == 0 else "    ⚠ Unexpected detection")
    
    return True


def run_all_tests():
    """Run all detection tests."""
    print("\n" + "="*60)
    print("FACE DETECTION TEST SUITE".center(60))
    print("="*60)
    
    results = {
        'Single Face': test_single_face(),
        'Multiple Faces': test_multiple_faces(),
        'Camera': test_from_camera(),
        'Edge Cases': test_edge_cases()
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
