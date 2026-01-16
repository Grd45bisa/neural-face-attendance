import cv2
import numpy as np
import os
import urllib.request

class FaceDetector:
    """
    Face detector menggunakan OpenCV DNN (SSD ResNet10).
    Cepat, akurat, dan tidak konflik dengan TensorFlow.
    """
    
    def __init__(self, min_confidence=0.5):
        """
        Initialize OpenCV DNN face detector.
        Downloads model files if not present.
        """
        self.min_confidence = min_confidence
        
        # Model paths
        self.model_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.prototxt_path = os.path.join(self.model_dir, 'deploy.prototxt')
        self.model_path = os.path.join(self.model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
        
        # Download models if missing
        self._check_and_download_models()
        
        # Load network
        self.net = cv2.dnn.readNetFromCaffe(self.prototxt_path, self.model_path)
        
    def _check_and_download_models(self):
        """Download model files jika belum ada."""
        if not os.path.exists(self.prototxt_path):
            print("Downloading deploy.prototxt...")
            url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
            urllib.request.urlretrieve(url, self.prototxt_path)
            
        if not os.path.exists(self.model_path):
            print("Downloading res10_300x300_ssd_iter_140000.caffemodel...")
            url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
            urllib.request.urlretrieve(url, self.model_path)

    def detect_faces(self, image):
        """
        Deteksi wajah menggunakan OpenCV DNN.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Input image invalid")
            
        (h, w) = image.shape[:2]
        
        # Preprocess: resize to 300x300, mean subtraction
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0))
            
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        
        # Loop over detections
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence >= self.min_confidence:
                # Compute box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Ensure within frame
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w, endX)
                endY = min(h, endY)
                
                width_box = endX - startX
                height_box = endY - startY
                
                # Estimate keypoints (OpenCV DNN doesn't provide landmarks)
                # We'll approximate them based on box for compatibility
                # This is a limitation, but acceptable for recognition alignment if we use center crop or simple alignment
                # Or we can use a separate landmark detector (dlib/facemesh) if needed.
                # For now, let's provide estimated keypoints to avoid breaking the pipeline.
                
                # Simple estimation
                eye_y = startY + int(height_box * 0.35)
                mouth_y = startY + int(height_box * 0.75)
                nose_y = startY + int(height_box * 0.55)
                
                keypoints = {
                    'left_eye': (startX + int(width_box * 0.3), eye_y),
                    'right_eye': (startX + int(width_box * 0.7), eye_y),
                    'nose': (startX + int(width_box * 0.5), nose_y),
                    'mouth_left': (startX + int(width_box * 0.35), mouth_y),
                    'mouth_right': (startX + int(width_box * 0.65), mouth_y)
                }
                
                face_data = {
                    'box': [startX, startY, width_box, height_box],
                    'confidence': float(confidence),
                    'keypoints': keypoints
                }
                faces.append(face_data)
                
        faces.sort(key=lambda x: x['confidence'], reverse=True)
        return faces
    
    def draw_boxes(self, image, faces):
        """
        Gambar bounding box dan keypoints.
        """
        result_image = image.copy()
        
        for face in faces:
            x, y, w, h = face['box']
            confidence = face['confidence']
            keypoints = face['keypoints']
            
            # Box
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Confidence
            cv2.putText(result_image, f"{confidence:.2f}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Keypoints
            for name, point in keypoints.items():
                color = (0, 0, 255) if 'nose' in name else (255, 0, 0)
                cv2.circle(result_image, point, 3, color, -1)
                
        return result_image

    def set_confidence_threshold(self, threshold):
        self.min_confidence = threshold
        # Re-init detector dengan new threshold
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=threshold,
            model_selection=1
        )

if __name__ == "__main__":
    detector = FaceDetector()
    # Test code here if needed
