import cv2
import numpy as np
import math


class FacePreprocessor:
    """
    Preprocessor untuk mempersiapkan wajah yang terdeteksi agar siap diinput ke model.
    Pipeline: crop → align → resize → normalize
    """
    
    def __init__(self, target_size=(224, 224)):
        """
        Initialize face preprocessor.
        
        Args:
            target_size (tuple): Target size untuk resize image (width, height).
                                Default (224, 224) untuk MobileNetV2.
        """
        self.target_size = target_size
        
    def crop_face(self, image, face_box):
        """
        Crop wajah dari image dengan margin tambahan.
        
        Args:
            image (numpy.ndarray): Input image dalam format BGR
            face_box (list): [x, y, width, height] bounding box dari detector
            
        Returns:
            numpy.ndarray: Cropped face image dengan margin 20%
            
        Raises:
            ValueError: Jika face terlalu kecil (<50x50 px)
        """
        x, y, width, height = face_box
        
        # Validasi ukuran minimum
        if width < 50 or height < 50:
            raise ValueError(f"Face terlalu kecil ({width}x{height}). Minimum 50x50 pixels.")
        
        # Tambahkan margin 20% di sekeliling box
        margin = 0.2
        margin_x = int(width * margin)
        margin_y = int(height * margin)
        
        # Calculate new coordinates dengan margin
        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(image.shape[1], x + width + margin_x)
        y2 = min(image.shape[0], y + height + margin_y)
        
        # Crop image
        cropped_face = image[y1:y2, x1:x2]
        
        return cropped_face
    
    def align_face(self, image, keypoints):
        """
        Align face berdasarkan posisi mata menggunakan affine transformation.
        Rotasi image agar mata berada pada posisi horizontal.
        
        Args:
            image (numpy.ndarray): Cropped face image
            keypoints (dict): Dictionary dengan posisi mata, hidung, mulut
                             Keys: 'left_eye', 'right_eye', 'nose', 'mouth_left', 'mouth_right'
            
        Returns:
            numpy.ndarray: Aligned face image
            
        Note:
            Jika alignment gagal, return original image
        """
        try:
            # Extract eye coordinates
            left_eye = keypoints['left_eye']
            right_eye = keypoints['right_eye']
            
            # Calculate angle antara kedua mata
            delta_x = right_eye[0] - left_eye[0]
            delta_y = right_eye[1] - left_eye[1]
            angle = math.degrees(math.atan2(delta_y, delta_x))
            
            # Calculate center point antara kedua mata
            # Convert to int untuk avoid float parsing error di cv2
            eyes_center = (
                int((left_eye[0] + right_eye[0]) / 2),
                int((left_eye[1] + right_eye[1]) / 2)
            )
            
            # Get rotation matrix
            rotation_matrix = cv2.getRotationMatrix2D(eyes_center, angle, scale=1.0)
            
            # Apply affine transformation
            aligned_face = cv2.warpAffine(
                image,
                rotation_matrix,
                (image.shape[1], image.shape[0]),
                flags=cv2.INTER_CUBIC
            )
            
            return aligned_face
            
        except Exception as e:
            # Jika alignment gagal, return original image
            print(f"Warning: Face alignment gagal ({str(e)}). Skip alignment.")
            return image
    
    def resize_image(self, image):
        """
        Resize image ke target size dengan interpolasi yang baik.
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: Resized image dengan ukuran target_size
        """
        # Gunakan INTER_AREA untuk downsampling (lebih baik untuk resize ke ukuran lebih kecil)
        resized = cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
        return resized
    
    def normalize_pixels(self, image):
        """
        Normalize pixel values dan convert color space untuk model.
        
        Args:
            image (numpy.ndarray): Input image dalam format BGR
            
        Returns:
            numpy.ndarray: Normalized image dalam format RGB dengan pixel range [0, 1]
        """
        # Convert BGR (OpenCV) ke RGB (untuk model)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize pixel values ke range [0, 1]
        normalized = rgb_image.astype(np.float32) / 255.0
        
        # Alternatif: normalize ke range [-1, 1] (uncomment jika diperlukan)
        # normalized = (rgb_image.astype(np.float32) / 127.5) - 1.0
        
        return normalized
    
    def preprocess(self, image, face_box, keypoints):
        """
        METHOD UTAMA: Preprocess face dengan pipeline lengkap.
        Pipeline: crop → align → resize → normalize
        
        Args:
            image (numpy.ndarray): Raw input image dalam format BGR
            face_box (list): [x, y, width, height] bounding box dari detector
            keypoints (dict): Dictionary dengan posisi facial landmarks
            
        Returns:
            numpy.ndarray: Preprocessed face ready untuk model input
            
        Raises:
            ValueError: Jika input invalid atau face terlalu kecil
            
        Example:
            >>> preprocessor = FacePreprocessor(target_size=(224, 224))
            >>> face = faces[0]  # dari detector
            >>> processed_face = preprocessor.preprocess(
            ...     image, 
            ...     face['box'], 
            ...     face['keypoints']
            ... )
        """
        # Validasi input
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError("Input image harus berupa numpy array yang valid.")
        
        # Step 1: Crop face dengan margin
        cropped = self.crop_face(image, face_box)
        
        # Step 2: Align face berdasarkan posisi mata
        aligned = self.align_face(cropped, keypoints)
        
        # Step 3: Resize ke target size
        resized = self.resize_image(aligned)
        
        # Step 4: Normalize pixels
        normalized = self.normalize_pixels(resized)
        
        return normalized
    
    def preprocess_crop(self, face_crop):
        """
        Preprocess image yang sudah di-crop (bypass alignment).
        Used for hybrid processing where client sends crops.
        
        Args:
            face_crop (numpy.ndarray): Cropped face image (BGR)
            
        Returns:
            numpy.ndarray: Preprocessed face ready untuk model input
        """
        # Validasi input
        if face_crop is None or not isinstance(face_crop, np.ndarray):
            raise ValueError("Input crop harus berupa numpy array yang valid.")
            
        # Step 1: Resize ke target size
        resized = self.resize_image(face_crop)
        
        # Step 2: Normalize pixels
        normalized = self.normalize_pixels(resized)
        
        return normalized
    
    def visualize_preprocessing(self, original, processed):
        """
        Visualize side-by-side comparison untuk debugging.
        
        Args:
            original (numpy.ndarray): Original image (BGR format)
            processed (numpy.ndarray): Processed image (RGB normalized format)
            
        Note:
            Tekan sembarang key untuk menutup window
        """
        # Convert processed image kembali ke format displayable
        if processed.dtype == np.float32 or processed.dtype == np.float64:
            # Denormalize dari [0, 1] ke [0, 255]
            display_processed = (processed * 255).astype(np.uint8)
        else:
            display_processed = processed
        
        # Convert RGB kembali ke BGR untuk display
        display_processed = cv2.cvtColor(display_processed, cv2.COLOR_RGB2BGR)
        
        # Resize original untuk matching height dengan processed
        original_resized = cv2.resize(
            original, 
            (self.target_size[0], self.target_size[1]),
            interpolation=cv2.INTER_AREA
        )
        
        # Concatenate side by side
        comparison = np.hstack([original_resized, display_processed])
        
        # Add labels
        cv2.putText(
            comparison,
            "Original",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        cv2.putText(
            comparison,
            "Processed",
            (self.target_size[0] + 10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Display
        cv2.imshow("Preprocessing Comparison", comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def denormalize(self, normalized_image):
        """
        Helper method untuk reverse normalization (debugging purposes).
        
        Args:
            normalized_image (numpy.ndarray): Normalized image [0, 1] range
            
        Returns:
            numpy.ndarray: Denormalized image [0, 255] range dalam BGR format
        """
        # Denormalize dari [0, 1] ke [0, 255]
        denormalized = (normalized_image * 255).astype(np.uint8)
        
        # Convert RGB kembali ke BGR
        bgr_image = cv2.cvtColor(denormalized, cv2.COLOR_RGB2BGR)
        
        return bgr_image


# Example usage
if __name__ == "__main__":
    from face_detector import FaceDetector
    
    # Initialize detector dan preprocessor
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    
    # Load image
    image = cv2.imread('photo.jpg')
    
    if image is not None:
        # Detect faces
        faces = detector.detect_faces(image)
        
        if faces:
            print(f"Terdeteksi {len(faces)} wajah")
            
            # Preprocess wajah pertama
            face = faces[0]
            processed_face = preprocessor.preprocess(
                image,
                face['box'],
                face['keypoints']
            )
            
            print(f"Processed face shape: {processed_face.shape}")
            print(f"Pixel range: [{processed_face.min():.3f}, {processed_face.max():.3f}]")
            
            # Visualize preprocessing
            cropped = preprocessor.crop_face(image, face['box'])
            preprocessor.visualize_preprocessing(cropped, processed_face)
        else:
            print("Tidak ada wajah terdeteksi")
    else:
        print("Gagal load image")
