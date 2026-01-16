import cv2
import numpy as np
from datetime import datetime
import warnings


class FaceRecognizer:
    """
    Face recognizer yang mengintegrasikan semua komponen untuk face recognition.
    Fase 5 - Recognition logic dengan orchestration semua modules.
    """
    
    def __init__(self, detector, preprocessor, encoder, matcher, db_manager, 
                 mode='multiple', debug=False):
        """
        Initialize face recognizer.
        
        Args:
            detector: FaceDetector instance
            preprocessor: FacePreprocessor instance
            encoder: FaceEncoder instance
            matcher: FaceMatcher instance
            db_manager: DatabaseManager instance
            mode (str): 'single' atau 'multiple' face recognition
            debug (bool): Enable debug mode untuk save intermediate results
        """
        self.detector = detector
        self.preprocessor = preprocessor
        self.encoder = encoder
        self.matcher = matcher
        self.db_manager = db_manager
        self.mode = mode
        self.debug = debug
        
        # Statistics tracking
        self.stats = {
            'total_attempts': 0,
            'successful_recognitions': 0,
            'unknown_faces': 0,
            'errors': 0
        }
        
        # Cache database embeddings untuk performance
        self._db_embeddings_cache = None
        self._cache_timestamp = None
    
    def _get_database_embeddings(self, force_refresh=False):
        """
        Get database embeddings dengan caching.
        
        Args:
            force_refresh (bool): Force refresh cache
        
        Returns:
            dict: {user_id: embedding}
        """
        # Refresh cache jika belum ada atau force refresh
        if self._db_embeddings_cache is None or force_refresh:
            self._db_embeddings_cache = self.db_manager.get_all_embeddings()
            self._cache_timestamp = datetime.now()
        
        return self._db_embeddings_cache
    
    def recognize_from_image(self, image):
        """
        MAIN METHOD: Recognize faces dari image.
        
        Args:
            image (numpy.ndarray): Input image dalam format BGR
        
        Returns:
            list: List of recognition results, format:
                [{
                    'box': [x, y, w, h],
                    'user_id': 'user_001' atau 'unknown',
                    'name': 'Alice' atau 'Unknown',
                    'confidence': 0.85,
                    'similarity': 0.85,
                    'confidence_level': 'high',
                    'keypoints': {...}
                }, ...]
        """
        self.stats['total_attempts'] += 1
        
        # Validate input
        if image is None or not isinstance(image, np.ndarray):
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'message': 'Invalid input image',
                'results': []
            }
        
        try:
            # Step 1: Detect faces
            faces = self.detector.detect_faces(image)
            
            if len(faces) == 0:
                return {
                    'status': 'no_face',
                    'message': 'Tidak ada wajah terdeteksi',
                    'results': []
                }
            
            # Get database embeddings
            db_embeddings = self._get_database_embeddings()
            
            if not db_embeddings:
                warnings.warn("Database kosong. Tidak ada user terdaftar.", UserWarning)
                return {
                    'status': 'empty_database',
                    'message': 'Database kosong',
                    'results': []
                }
            
            # Step 2: Process each face
            recognition_results = []
            face_embeddings = []
            
            # Extract embeddings untuk semua faces (batch processing)
            for i, face in enumerate(faces):
                try:
                    # Preprocess
                    preprocessed = self.preprocessor.preprocess(
                        image,
                        face['box'],
                        face['keypoints']
                    )
                    
                    # Extract embedding
                    embedding = self.encoder.encode_face(preprocessed)
                    face_embeddings.append(embedding)
                    
                except Exception as e:
                    warnings.warn(f"Error processing face {i}: {e}", UserWarning)
                    face_embeddings.append(None)
            
            # Step 3: Match dengan database
            for i, (face, embedding) in enumerate(zip(faces, face_embeddings)):
                if embedding is None:
                    # Error saat preprocessing/encoding
                    result = {
                        'box': face['box'],
                        'user_id': 'error',
                        'name': 'Error',
                        'confidence': 0.0,
                        'similarity': 0.0,
                        'confidence_level': 'error',
                        'keypoints': face['keypoints'],
                        'detection_confidence': face['confidence']
                    }
                    self.stats['errors'] += 1
                else:
                    # Match dengan database
                    match_result = self.matcher.find_best_match(embedding, db_embeddings)
                    
                    if match_result['is_match']:
                        # Known person
                        user_data = self.db_manager.get_user(match_result['user_id'])
                        confidence_level, confidence_pct = self.get_recognition_confidence(
                            match_result['similarity']
                        )
                        
                        result = {
                            'box': face['box'],
                            'user_id': match_result['user_id'],
                            'name': user_data['name'],
                            'confidence': confidence_pct,
                            'similarity': match_result['similarity'],
                            'confidence_level': confidence_level,
                            'keypoints': face['keypoints'],
                            'detection_confidence': face['confidence']
                        }
                        self.stats['successful_recognitions'] += 1
                    else:
                        # Unknown person
                        result = {
                            'box': face['box'],
                            'user_id': 'unknown',
                            'name': 'Unknown',
                            'confidence': 0.0,
                            'similarity': match_result['similarity'],
                            'confidence_level': 'unknown',
                            'keypoints': face['keypoints'],
                            'detection_confidence': face['confidence']
                        }
                        self.stats['unknown_faces'] += 1
                
                recognition_results.append(result)
            
            return {
                'status': 'success',
                'message': f'Terdeteksi {len(recognition_results)} wajah',
                'results': recognition_results,
                'face_count': len(recognition_results)
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'message': f'Error during recognition: {e}',
                'results': []
            }
            
    def recognize_from_face_crop(self, face_crop):
        """
        Recognize face dari image yang sudah di-crop (bypass detection).
        
        Args:
            face_crop (numpy.ndarray): Cropped face image (BGR)
            
        Returns:
            dict: Recognition result (single face)
        """
        self.stats['total_attempts'] += 1
        
        try:
            # Get database embeddings
            db_embeddings = self._get_database_embeddings()
            
            if not db_embeddings:
                return {
                    'status': 'empty_database',
                    'message': 'Database kosong',
                    'results': []
                }
            
            # Preprocess crop
            try:
                preprocessed = self.preprocessor.preprocess_crop(face_crop)
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Preprocessing failed: {e}',
                    'results': []
                }
            
            # Encode
            embedding = self.encoder.encode_face(preprocessed)
            
            if embedding is None:
                return {
                    'status': 'error',
                    'message': 'Encoding failed',
                    'results': []
                }
            
            # Match
            match_result = self.matcher.find_best_match(embedding, db_embeddings)
            
            if match_result['is_match']:
                user_data = self.db_manager.get_user(match_result['user_id'])
                confidence_level, confidence_pct = self.get_recognition_confidence(
                    match_result['similarity']
                )
                
                result = {
                    'user_id': match_result['user_id'],
                    'name': user_data['name'],
                    'confidence': confidence_pct,
                    'similarity': match_result['similarity'],
                    'confidence_level': confidence_level
                }
                self.stats['successful_recognitions'] += 1
            else:
                result = {
                    'user_id': 'unknown',
                    'name': 'Unknown',
                    'confidence': 0.0,
                    'similarity': match_result['similarity'],
                    'confidence_level': 'unknown'
                }
                self.stats['unknown_faces'] += 1
                
            return {
                'status': 'success',
                'message': 'Face recognized',
                'results': [result]
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'message': f'Error during recognition: {e}',
                'results': []
            }
    
    def recognize_single_face(self, image):
        """
        Optimized untuk image dengan hanya 1 wajah.
        
        Args:
            image (numpy.ndarray): Input image
        
        Returns:
            dict: Single recognition result
        
        Raises:
            ValueError: Jika terdeteksi multiple faces atau no face
        """
        # Detect faces
        faces = self.detector.detect_faces(image)
        
        if len(faces) == 0:
            raise ValueError("Tidak ada wajah terdeteksi di image")
        
        if len(faces) > 1:
            raise ValueError(f"Terdeteksi {len(faces)} wajah. Gunakan recognize_from_image() untuk multiple faces.")
        
        # Process single face
        result = self.recognize_from_image(image)
        
        if result['status'] == 'success' and len(result['results']) > 0:
            return result['results'][0]
        else:
            raise RuntimeError(f"Recognition gagal: {result['message']}")
    
    def recognize_from_file(self, image_path):
        """
        Recognize dari file path.
        
        Args:
            image_path (str): Path ke image file
        
        Returns:
            dict: Recognition results (same format as recognize_from_image)
        """
        # Load image
        image = cv2.imread(image_path)
        
        if image is None:
            return {
                'status': 'error',
                'message': f'Gagal load image dari {image_path}',
                'results': []
            }
        
        # Recognize
        return self.recognize_from_image(image)
    
    def annotate_image(self, image, recognition_results):
        """
        Gambar hasil recognition di image.
        
        Args:
            image (numpy.ndarray): Input image
            recognition_results (list): Results dari recognize_from_image()
        
        Returns:
            numpy.ndarray: Annotated image
        """
        annotated = image.copy()
        
        # Handle both formats: dict with 'results' key atau direct list
        if isinstance(recognition_results, dict):
            results = recognition_results.get('results', [])
        else:
            results = recognition_results
        
        for result in results:
            x, y, w, h = result['box']
            name = result['name']
            confidence = result.get('confidence', 0)
            user_id = result['user_id']
            
            # Color based on recognition status
            if user_id == 'unknown':
                color = (0, 0, 255)  # Red untuk unknown
                label = f"{name}"
            elif user_id == 'error':
                color = (0, 165, 255)  # Orange untuk error
                label = "Error"
            else:
                color = (0, 255, 0)  # Green untuk known
                label = f"{name} ({confidence:.0f}%)"
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(
                annotated,
                (x, y - label_size[1] - 10),
                (x + label_size[0], y),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                annotated,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            # Draw keypoints (optional)
            if 'keypoints' in result:
                keypoints = result['keypoints']
                
                # Eyes (blue)
                cv2.circle(annotated, keypoints['left_eye'], 2, (255, 0, 0), -1)
                cv2.circle(annotated, keypoints['right_eye'], 2, (255, 0, 0), -1)
                
                # Nose (red)
                cv2.circle(annotated, keypoints['nose'], 2, (0, 0, 255), -1)
        
        return annotated
    
    def get_recognition_confidence(self, similarity_score):
        """
        Convert similarity score ke confidence level.
        
        Args:
            similarity_score (float): Similarity score dari matcher
        
        Returns:
            tuple: (confidence_level, percentage)
                  confidence_level: 'high' | 'medium' | 'low'
                  percentage: 0-100
        """
        percentage = similarity_score * 100
        
        if similarity_score >= 0.8:
            level = 'high'
        elif similarity_score >= 0.6:
            level = 'medium'
        else:
            level = 'low'
        
        return level, percentage
    
    def get_statistics(self):
        """
        Get recognition statistics.
        
        Returns:
            dict: Statistics dengan success rate, dll
        """
        total = self.stats['total_attempts']
        
        if total == 0:
            success_rate = 0.0
        else:
            success_rate = (self.stats['successful_recognitions'] / total) * 100
        
        return {
            'total_attempts': total,
            'successful_recognitions': self.stats['successful_recognitions'],
            'unknown_faces': self.stats['unknown_faces'],
            'errors': self.stats['errors'],
            'success_rate': success_rate
        }
    
    def reset_statistics(self):
        """Reset statistics counter."""
        self.stats = {
            'total_attempts': 0,
            'successful_recognitions': 0,
            'unknown_faces': 0,
            'errors': 0
        }
        print("✓ Statistics reset")
    
    def refresh_database_cache(self):
        """Force refresh database embeddings cache."""
        self._get_database_embeddings(force_refresh=True)
        print("✓ Database cache refreshed")


# Example usage
if __name__ == "__main__":
    from core.face_detector import FaceDetector
    from core.face_preprocessor import FacePreprocessor
    from core.face_encoder import FaceEncoder
    from core.face_matcher import FaceMatcher
    from database.database_manager import DatabaseManager
    
    # Initialize all components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = DatabaseManager('data/face_db.pkl')
    
    # Initialize recognizer
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager,
        mode='multiple'
    )
    
    # Test recognition
    image = cv2.imread('test.jpg')
    
    if image is not None:
        print("\n" + "="*60)
        print("FACE RECOGNITION TEST")
        print("="*60)
        
        # Recognize
        result = recognizer.recognize_from_image(image)
        
        print(f"\nStatus: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"\n{'='*60}")
            print(f"RECOGNITION RESULTS:")
            print(f"{'='*60}")
            
            for i, res in enumerate(result['results']):
                print(f"\nFace {i+1}:")
                print(f"  Name: {res['name']}")
                print(f"  User ID: {res['user_id']}")
                print(f"  Confidence: {res['confidence']:.2f}%")
                print(f"  Confidence Level: {res['confidence_level']}")
                print(f"  Similarity: {res['similarity']:.4f}")
            
            # Annotate image
            annotated = recognizer.annotate_image(image, result)
            
            # Show result
            cv2.imshow('Recognition Result', annotated)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # Show statistics
        stats = recognizer.get_statistics()
        print(f"\n{'='*60}")
        print(f"STATISTICS:")
        print(f"{'='*60}")
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful recognitions: {stats['successful_recognitions']}")
        print(f"Unknown faces: {stats['unknown_faces']}")
        print(f"Errors: {stats['errors']}")
        print(f"Success rate: {stats['success_rate']:.2f}%")
    else:
        print("⚠ Gagal load test image")
