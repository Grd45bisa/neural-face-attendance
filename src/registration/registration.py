import cv2
import numpy as np
import time
from datetime import datetime
import os


class UserRegistration:
    """
    User registration module untuk mendaftarkan user baru ke face recognition system.
    Fase 4 - Register new users dengan quality control.
    """
    
    def __init__(self, detector, preprocessor, encoder, db_manager, 
                 min_confidence=0.9, required_photos=5):
        """
        Initialize user registration system.
        
        Args:
            detector: FaceDetector instance
            preprocessor: FacePreprocessor instance
            encoder: FaceEncoder instance
            db_manager: DatabaseManager instance
            min_confidence (float): Minimum detection confidence threshold
            required_photos (int): Jumlah foto yang dibutuhkan untuk registration
        """
        self.detector = detector
        self.preprocessor = preprocessor
        self.encoder = encoder
        self.db_manager = db_manager
        self.min_confidence = min_confidence
        self.required_photos = required_photos
        
        # Instructions untuk setiap foto
        self.photo_instructions = [
            "Foto 1: Hadap depan, ekspresi netral",
            "Foto 2: Sedikit ke kiri",
            "Foto 3: Sedikit ke kanan",
            "Foto 4: Senyum",
            "Foto 5: Ekspresi netral lagi"
        ]
    
    def capture_photo(self, camera_id=0, instruction="Posisikan wajah di tengah"):
        """
        Capture single photo dari webcam dengan live preview.
        
        Args:
            camera_id (int): Camera device ID
            instruction (str): Instruksi untuk user
        
        Returns:
            numpy.ndarray: Captured image atau None jika cancel
        """
        # Open camera
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            raise RuntimeError("Camera tidak dapat diakses. Pastikan camera tersedia dan tidak digunakan aplikasi lain.")
        
        # Set camera resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        captured_image = None
        
        print(f"\n{instruction}")
        print("Tekan SPACE untuk capture, ESC untuk cancel")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("⚠ Gagal membaca frame dari camera")
                break
            
            # Create display frame
            display_frame = frame.copy()
            
            # Detect faces untuk preview
            try:
                faces = self.detector.detect_faces(frame)
                
                # Draw bounding boxes
                for face in faces:
                    x, y, w, h = face['box']
                    confidence = face['confidence']
                    
                    # Color based on confidence
                    if confidence >= self.min_confidence:
                        color = (0, 255, 0)  # Green - good quality
                        status = "READY"
                    else:
                        color = (0, 165, 255)  # Orange - low quality
                        status = "LOW CONFIDENCE"
                    
                    # Draw box
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
                    
                    # Draw confidence
                    cv2.putText(
                        display_frame,
                        f"{status}: {confidence:.2f}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )
            except Exception as e:
                print(f"⚠ Detection error: {e}")
            
            # Draw instruction
            cv2.putText(
                display_frame,
                instruction,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )
            
            cv2.putText(
                display_frame,
                "SPACE: Capture | ESC: Cancel",
                (20, display_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            # Show frame
            cv2.imshow('Registration - Camera Preview', display_frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            
            if key == 32:  # SPACE
                captured_image = frame.copy()
                print("✓ Foto captured!")
                break
            elif key == 27:  # ESC
                print("✗ Capture cancelled")
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        return captured_image
    
    def capture_multiple_photos(self, count=5, camera_id=0):
        """
        Capture multiple photos dengan instruksi berbeda.
        
        Args:
            count (int): Jumlah foto yang akan di-capture
            camera_id (int): Camera device ID
        
        Returns:
            list: List of captured images
        """
        captured_images = []
        
        for i in range(count):
            instruction = self.photo_instructions[i] if i < len(self.photo_instructions) else f"Foto {i+1}"
            
            print(f"\n{'='*50}")
            print(f"FOTO {i+1}/{count}")
            print(f"{'='*50}")
            
            # Countdown
            print("Bersiap dalam: ", end='', flush=True)
            for countdown in range(3, 0, -1):
                print(f"{countdown}... ", end='', flush=True)
                time.sleep(1)
            print("GO!")
            
            # Capture photo
            image = self.capture_photo(camera_id, instruction)
            
            if image is None:
                print("⚠ Capture dibatalkan. Ulangi foto ini.")
                i -= 1  # Retry
                continue
            
            # Validate face detection
            try:
                faces = self.detector.detect_faces(image)
                
                if len(faces) == 0:
                    print("⚠ Tidak ada wajah terdeteksi. Ulangi foto ini.")
                    retry = input("Retry foto ini? (y/n): ").strip().lower()
                    if retry == 'y':
                        i -= 1
                    continue
                
                if len(faces) > 1:
                    print("⚠ Terdeteksi lebih dari 1 wajah. Pastikan hanya 1 orang di frame.")
                    retry = input("Retry foto ini? (y/n): ").strip().lower()
                    if retry == 'y':
                        i -= 1
                    continue
                
                # Check confidence
                confidence = faces[0]['confidence']
                if confidence < self.min_confidence:
                    print(f"⚠ Confidence terlalu rendah ({confidence:.2f}). Minimum: {self.min_confidence}")
                    retry = input("Retry foto ini? (y/n): ").strip().lower()
                    if retry == 'y':
                        i -= 1
                    continue
                
                # Photo accepted
                captured_images.append(image)
                print(f"✓ Foto {i+1} diterima (confidence: {confidence:.2f})")
                
            except Exception as e:
                print(f"⚠ Error validating photo: {e}")
                retry = input("Retry foto ini? (y/n): ").strip().lower()
                if retry == 'y':
                    i -= 1
                continue
        
        return captured_images
    
    def register_from_camera(self, user_id, name, photo_count=5, camera_id=0):
        """
        MAIN METHOD: Register user dari camera capture.
        
        Args:
            user_id (str): Unique user ID
            name (str): Nama user
            photo_count (int): Jumlah foto untuk registration
            camera_id (int): Camera device ID
        
        Returns:
            dict: Registration result dengan status, message, quality_score
        """
        print("\n" + "="*60)
        print(f"REGISTRATION: {name} (ID: {user_id})")
        print("="*60)
        
        # Check duplicate user_id
        existing_user = self.db_manager.get_user(user_id)
        if existing_user:
            print(f"⚠ User ID '{user_id}' sudah terdaftar sebagai '{existing_user['name']}'")
            overwrite = input("Overwrite user ini? (y/n): ").strip().lower()
            if overwrite != 'y':
                return {
                    'status': 'cancelled',
                    'message': 'Registration dibatalkan (duplicate user_id)',
                    'user_id': user_id,
                    'name': name
                }
        
        # Step 1: Capture multiple photos
        print("\n[Step 1/5] Capture Photos")
        images = self.capture_multiple_photos(photo_count, camera_id=camera_id)
        
        if len(images) < photo_count:
            return {
                'status': 'failed',
                'message': f'Hanya {len(images)}/{photo_count} foto berhasil di-capture',
                'user_id': user_id,
                'name': name
            }
        
        # Step 2: Preview registration
        print("\n[Step 2/5] Preview Photos")
        self.preview_registration(images)
        
        confirm = input("\nLanjutkan registration dengan foto ini? (y/n): ").strip().lower()
        if confirm != 'y':
            return {
                'status': 'cancelled',
                'message': 'Registration dibatalkan oleh user',
                'user_id': user_id,
                'name': name
            }
        
        # Step 3: Extract embeddings
        print("\n[Step 3/5] Extract Embeddings")
        embeddings = []
        
        for i, image in enumerate(images):
            try:
                # Detect face
                faces = self.detector.detect_faces(image)
                face = faces[0]  # Already validated earlier
                
                # Preprocess
                preprocessed = self.preprocessor.preprocess(
                    image,
                    face['box'],
                    face['keypoints']
                )
                
                # Encode
                embedding = self.encoder.encode_face(preprocessed)
                embeddings.append(embedding)
                
                print(f"  ✓ Foto {i+1}: Embedding extracted")
                
            except Exception as e:
                print(f"  ✗ Foto {i+1}: Error - {e}")
                return {
                    'status': 'failed',
                    'message': f'Error extracting embedding: {e}',
                    'user_id': user_id,
                    'name': name
                }
        
        # Step 4: Average embeddings
        print("\n[Step 4/5] Average Embeddings")
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Re-normalize
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
        
        print(f"  ✓ Averaged {len(embeddings)} embeddings")
        print(f"  ✓ Final embedding norm: {np.linalg.norm(avg_embedding):.6f}")
        
        # Step 5: Validate and save
        print("\n[Step 5/5] Save to Database")
        
        is_valid, reason = self.validate_registration(avg_embedding)
        if not is_valid:
            return {
                'status': 'failed',
                'message': f'Validation failed: {reason}',
                'user_id': user_id,
                'name': name
            }
        
        # Save to database
        try:
            if existing_user:
                self.db_manager.update_user(user_id, embedding=avg_embedding, name=name)
            else:
                self.db_manager.add_user(user_id, name, avg_embedding)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(embeddings)
            
            print(f"\n{'='*60}")
            print(f"✓ REGISTRATION BERHASIL!")
            print(f"{'='*60}")
            print(f"User: {name}")
            print(f"ID: {user_id}")
            print(f"Quality Score: {quality_score:.2f}/100")
            
            return {
                'status': 'success',
                'message': 'User berhasil terdaftar',
                'user_id': user_id,
                'name': name,
                'quality_score': quality_score,
                'photo_count': len(images)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Error saving to database: {e}',
                'user_id': user_id,
                'name': name
            }
    
    def register_from_file(self, user_id, name, image_path):
        """
        Register user dari file image.
        
        Args:
            user_id (str): Unique user ID
            name (str): Nama user
            image_path (str): Path ke image file
        
        Returns:
            dict: Registration result
        """
        # Load image
        image = cv2.imread(image_path)
        
        if image is None:
            return {
                'status': 'failed',
                'message': f'Gagal load image dari {image_path}',
                'user_id': user_id,
                'name': name
            }
        
        # Detect face
        try:
            faces = self.detector.detect_faces(image)
            
            if len(faces) == 0:
                return {
                    'status': 'failed',
                    'message': 'Tidak ada wajah terdeteksi di image',
                    'user_id': user_id,
                    'name': name
                }
            
            if len(faces) > 1:
                print(f"⚠ Terdeteksi {len(faces)} wajah. Menggunakan wajah dengan confidence tertinggi.")
            
            face = faces[0]  # Highest confidence
            
            # Preprocess
            preprocessed = self.preprocessor.preprocess(
                image,
                face['box'],
                face['keypoints']
            )
            
            # Encode
            embedding = self.encoder.encode_face(preprocessed)
            
            # Validate
            is_valid, reason = self.validate_registration(embedding)
            if not is_valid:
                return {
                    'status': 'failed',
                    'message': f'Validation failed: {reason}',
                    'user_id': user_id,
                    'name': name
                }
            
            # Save to database
            self.db_manager.add_user(user_id, name, embedding)
            
            return {
                'status': 'success',
                'message': 'User berhasil terdaftar dari file',
                'user_id': user_id,
                'name': name,
                'confidence': face['confidence']
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Error: {e}',
                'user_id': user_id,
                'name': name
            }
    
    def validate_registration(self, embedding):
        """
        Validate embedding quality sebelum save.
        
        Args:
            embedding (numpy.ndarray): Embedding vector
        
        Returns:
            tuple: (is_valid, reason)
        """
        # Check embedding norm
        norm = np.linalg.norm(embedding)
        if abs(norm - 1.0) > 0.1:
            return False, f"Embedding norm abnormal: {norm:.3f}"
        
        # Check untuk duplicate (similarity terlalu tinggi dengan existing users)
        all_embeddings = self.db_manager.get_all_embeddings()
        
        for existing_user_id, existing_embedding in all_embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(embedding, existing_embedding)
            
            # Threshold untuk duplicate detection (0.95 = sangat mirip)
            if similarity > 0.95:
                existing_user = self.db_manager.get_user(existing_user_id)
                return False, f"Terlalu mirip dengan user existing: {existing_user['name']} (similarity: {similarity:.3f})"
        
        return True, "Valid"
    
    def preview_registration(self, images):
        """
        Show preview semua foto yang akan di-register.
        
        Args:
            images (list): List of images
        """
        # Create grid preview
        rows = 1
        cols = len(images)
        
        # Resize images untuk preview
        preview_size = (300, 300)
        previews = []
        
        for i, img in enumerate(images):
            # Resize
            resized = cv2.resize(img, preview_size)
            
            # Detect dan draw face
            try:
                faces = self.detector.detect_faces(img)
                if faces:
                    face = faces[0]
                    x, y, w, h = face['box']
                    
                    # Scale coordinates
                    scale_x = preview_size[0] / img.shape[1]
                    scale_y = preview_size[1] / img.shape[0]
                    
                    x_scaled = int(x * scale_x)
                    y_scaled = int(y * scale_y)
                    w_scaled = int(w * scale_x)
                    h_scaled = int(h * scale_y)
                    
                    cv2.rectangle(resized, (x_scaled, y_scaled), 
                                (x_scaled + w_scaled, y_scaled + h_scaled), 
                                (0, 255, 0), 2)
            except:
                pass
            
            # Add label
            cv2.putText(resized, f"Foto {i+1}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            previews.append(resized)
        
        # Concatenate horizontally
        grid = np.hstack(previews)
        
        # Show
        cv2.imshow('Registration Preview - Tekan sembarang key untuk close', grid)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def _calculate_quality_score(self, embeddings):
        """
        Calculate quality score dari embeddings.
        
        Args:
            embeddings (list): List of embedding vectors
        
        Returns:
            float: Quality score (0-100)
        """
        # Calculate variance (diversity)
        embeddings_array = np.array(embeddings)
        variance = np.var(embeddings_array, axis=0).mean()
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                sim = np.dot(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        avg_similarity = np.mean(similarities) if similarities else 0
        
        # Quality score: balance antara consistency (high similarity) dan diversity (low variance)
        # High similarity = consistent captures (good)
        # Low variance = stable embeddings (good)
        
        consistency_score = avg_similarity * 100  # 0-100
        stability_score = (1 - min(variance * 10, 1)) * 100  # 0-100
        
        quality_score = (consistency_score * 0.6 + stability_score * 0.4)
        
        return quality_score


# Example usage
if __name__ == "__main__":
    from core.face_detector import FaceDetector
    from core.face_preprocessor import FacePreprocessor
    from core.face_encoder import FaceEncoder
    from database.database_manager import DatabaseManager
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    db_manager = DatabaseManager('data/face_db.pkl')
    
    # Initialize registration
    registration = UserRegistration(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        db_manager=db_manager
    )
    
    # Register user dari camera
    result = registration.register_from_camera(
        user_id='user_002',
        name='Bob',
        photo_count=5
    )
    
    print(f"\n{'='*60}")
    print(f"RESULT: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    if result['status'] == 'success':
        print(f"Quality Score: {result['quality_score']:.2f}/100")
    print(f"{'='*60}")
