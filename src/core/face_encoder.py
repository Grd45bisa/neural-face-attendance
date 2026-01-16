import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
import warnings


class FaceEncoder:
    """
    Face encoder menggunakan MobileNetV2 untuk extract face embeddings.
    Fase 3 - Extract embeddings dari preprocessed face images.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize face encoder dengan MobileNetV2.
        
        Args:
            model_path (str, optional): Path ke custom trained weights.
                                       Jika None, gunakan pretrained ImageNet weights.
        """
        self.model_path = model_path
        self.model = None
        self.embedding_dim = 1280  # MobileNetV2 output dimension
        
        # Advanced GPU detection dan configuration
        self._configure_gpu()
        
        # Load model
        self.model = self.load_model()
        
        # Warmup inference untuk first-time loading
        self._warmup()
    
    def _configure_gpu(self):
        """
        Auto-detect dan configure GPU (NVIDIA atau AMD).
        Fallback ke CPU jika tidak ada GPU.
        """
        # Detect GPU
        gpus = tf.config.list_physical_devices('GPU')
        
        if gpus:
            print(f"\n{'='*60}")
            print("GPU DETECTION".center(60))
            print(f"{'='*60}")
            print(f"✓ GPU detected: {len(gpus)} device(s)")
            
            # Get GPU details
            for i, gpu in enumerate(gpus):
                gpu_name = gpu.name
                print(f"  GPU {i}: {gpu_name}")
                
                try:
                    # Enable memory growth untuk avoid OOM errors
                    tf.config.experimental.set_memory_growth(gpu, True)
                    print(f"  [OK] Memory growth enabled for GPU {i}")
                except RuntimeError as e:
                    print(f"  [WARN] Could not set memory growth: {e}")
            
            # Set GPU as preferred device
            try:
                # Limit GPU memory (optional, untuk share GPU dengan aplikasi lain)
                # tf.config.set_logical_device_configuration(
                #     gpus[0],
                #     [tf.config.LogicalDeviceConfiguration(memory_limit=2048)]
                # )
                
                print(f"  [OK] GPU akan digunakan untuk inference")
                print(f"  [OK] Expected speedup: 2-3x vs CPU")
                
                # Check if CUDA is available (NVIDIA)
                if tf.test.is_built_with_cuda():
                    print(f"  [OK] CUDA support: Available (NVIDIA GPU)")
                
            except Exception as e:
                print(f"  [WARN] GPU configuration warning: {e}")
            
            print(f"{'='*60}\n")
            
        else:
            # No GPU detected
            print(f"\n{'='*60}")
            print("GPU DETECTION".center(60))
            print(f"{'='*60}")
            print("[X] No GPU detected")
            print("  Running on CPU (slower)")
            print("  For better performance:")
            print("    - NVIDIA: Install CUDA + cuDNN")
            print("    - AMD: Install ROCm (Linux only)")
            print("  Or use CPU-optimized settings (OPTIMIZATION_GUIDE.md)")
            print(f"{'='*60}\n")
            
            # Configure CPU optimization (skip if already configured)
            try:
                tf.config.threading.set_inter_op_parallelism_threads(2)
                tf.config.threading.set_intra_op_parallelism_threads(4)
            except RuntimeError:
                # Already configured, skip
                pass
    
    def load_model(self):
        """
        Setup MobileNetV2 model untuk face embedding extraction.
        
        Returns:
            tf.keras.Model: Configured MobileNetV2 model tanpa classification head
        """
        # Load MobileNetV2 dengan pretrained ImageNet weights
        base_model = MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,  # Remove classification head
            weights='imagenet' if self.model_path is None else None,
            pooling='avg'  # Global average pooling untuk fixed-size output
        )
        
        # Set model ke evaluation mode (freeze weights)
        base_model.trainable = False
        
        # Jika ada custom weights, load
        if self.model_path is not None:
            try:
                base_model.load_weights(self.model_path)
                print(f"[OK] Loaded custom weights from {self.model_path}")
            except Exception as e:
                warnings.warn(f"⚠ Gagal load custom weights: {e}. Using ImageNet weights.", UserWarning)
        
        # Create model dengan output embedding
        model = Model(inputs=base_model.input, outputs=base_model.output)
        
        print(f"[OK] Model loaded. Embedding dimension: {self.embedding_dim}")
        
        return model
    
    def _warmup(self):
        """
        Warmup inference untuk optimize first-time loading.
        """
        dummy_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
        _ = self.model.predict(dummy_input, verbose=0)
        print("[OK] Model warmup completed")
    
    def encode_face(self, preprocessed_face):
        """
        Encode single preprocessed face ke embedding vector.
        
        Args:
            preprocessed_face (numpy.ndarray): Preprocessed face image
                                              Shape: (224, 224, 3), normalized [0, 1]
        
        Returns:
            numpy.ndarray: L2-normalized embedding vector, shape (embedding_dim,)
        
        Raises:
            ValueError: Jika input shape atau format tidak valid
        
        Example:
            >>> encoder = FaceEncoder()
            >>> embedding = encoder.encode_face(preprocessed_face)
            >>> print(f"Embedding shape: {embedding.shape}")  # (1280,)
            >>> print(f"Embedding norm: {np.linalg.norm(embedding)}")  # ~1.0
        """
        # Validasi input
        if preprocessed_face is None or not isinstance(preprocessed_face, np.ndarray):
            raise ValueError("Input harus berupa numpy array yang valid.")
        
        if preprocessed_face.shape != (224, 224, 3):
            raise ValueError(f"Input shape harus (224, 224, 3), got {preprocessed_face.shape}")
        
        # Expand dimensions untuk batch processing (1, 224, 224, 3)
        face_batch = np.expand_dims(preprocessed_face, axis=0)
        
        # Forward pass through model
        try:
            embedding = self.model.predict(face_batch, verbose=0)
        except Exception as e:
            if "out of memory" in str(e).lower() or "oom" in str(e).lower():
                raise MemoryError("Out of memory error. Coba reduce batch size atau gunakan GPU.")
            else:
                raise RuntimeError(f"Error during model inference: {e}")
        
        # Squeeze batch dimension (1, 1280) -> (1280,)
        embedding = embedding.squeeze()
        
        # L2 normalization untuk cosine similarity
        embedding = self._normalize_embedding(embedding)
        
        return embedding
    
    def encode_batch(self, preprocessed_faces):
        """
        Encode multiple preprocessed faces sekaligus (batch processing).
        Lebih efisien daripada encode satu per satu.
        
        Args:
            preprocessed_faces (list): List of preprocessed face images
                                      Each shape: (224, 224, 3), normalized [0, 1]
        
        Returns:
            numpy.ndarray: L2-normalized embeddings, shape (n_faces, embedding_dim)
        
        Example:
            >>> encoder = FaceEncoder()
            >>> embeddings = encoder.encode_batch([face1, face2, face3])
            >>> print(embeddings.shape)  # (3, 1280)
        """
        # Validasi input
        if not preprocessed_faces or len(preprocessed_faces) == 0:
            raise ValueError("Input list tidak boleh kosong.")
        
        # Convert list ke batch array
        try:
            face_batch = np.array(preprocessed_faces)
        except Exception as e:
            raise ValueError(f"Gagal convert list ke array: {e}")
        
        # Validasi shape
        if face_batch.ndim != 4 or face_batch.shape[1:] != (224, 224, 3):
            raise ValueError(f"Batch shape harus (n, 224, 224, 3), got {face_batch.shape}")
        
        # Forward pass through model
        try:
            embeddings = self.model.predict(face_batch, verbose=0)
        except Exception as e:
            if "out of memory" in str(e).lower() or "oom" in str(e).lower():
                # Fallback: process one by one jika OOM
                warnings.warn("⚠ OOM error. Fallback ke sequential processing.", UserWarning)
                embeddings = []
                for face in preprocessed_faces:
                    emb = self.encode_face(face)
                    embeddings.append(emb)
                embeddings = np.array(embeddings)
            else:
                raise RuntimeError(f"Error during batch inference: {e}")
        
        # L2 normalization untuk setiap embedding
        embeddings = self._normalize_batch(embeddings)
        
        return embeddings
    
    def _normalize_embedding(self, embedding):
        """
        L2 normalize single embedding vector ke unit vector.
        
        Args:
            embedding (numpy.ndarray): Raw embedding vector
        
        Returns:
            numpy.ndarray: L2-normalized embedding (norm = 1.0)
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            warnings.warn("⚠ Embedding norm is zero. Returning zero vector.", UserWarning)
            return embedding
        return embedding / norm
    
    def _normalize_batch(self, embeddings):
        """
        L2 normalize batch of embeddings.
        
        Args:
            embeddings (numpy.ndarray): Batch of embeddings, shape (n, embedding_dim)
        
        Returns:
            numpy.ndarray: L2-normalized embeddings
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        return embeddings / norms
    
    def get_embedding_dimension(self):
        """
        Return dimensi embedding vector.
        
        Returns:
            int: Embedding dimension (1280 untuk MobileNetV2)
        """
        return self.embedding_dim
    
    def save_weights(self, save_path):
        """
        Save model weights untuk future use.
        
        Args:
            save_path (str): Path untuk save weights (format .h5 atau .weights.h5)
        """
        try:
            self.model.save_weights(save_path)
            print(f"[OK] Model weights saved to {save_path}")
        except Exception as e:
            raise RuntimeError(f"Gagal save weights: {e}")
    
    def load_weights(self, weights_path):
        """
        Load custom trained weights.
        
        Args:
            weights_path (str): Path ke weights file
        """
        try:
            self.model.load_weights(weights_path)
            print(f"[OK] Loaded weights from {weights_path}")
        except Exception as e:
            raise RuntimeError(f"Gagal load weights: {e}")


# Example usage
if __name__ == "__main__":
    from face_detector import FaceDetector
    from face_preprocessor import FacePreprocessor
    
    # Initialize components
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    
    # Load image
    image = cv2.imread('photo.jpg')
    
    if image is not None:
        # Detect faces
        faces = detector.detect_faces(image)
        
        if faces:
            print(f"\nTerdeteksi {len(faces)} wajah")
            
            # Preprocess dan encode wajah pertama
            face = faces[0]
            preprocessed_face = preprocessor.preprocess(
                image,
                face['box'],
                face['keypoints']
            )
            
            # Encode to embedding
            embedding = encoder.encode_face(preprocessed_face)
            
            print(f"\n=== Embedding Info ===")
            print(f"Embedding shape: {embedding.shape}")
            print(f"Embedding dimension: {encoder.get_embedding_dimension()}")
            print(f"Embedding norm: {np.linalg.norm(embedding):.6f}")
            print(f"Embedding sample (first 10): {embedding[:10]}")
            
            # Test batch processing
            if len(faces) > 1:
                preprocessed_faces = []
                for face in faces[:3]:  # Max 3 faces
                    prep_face = preprocessor.preprocess(
                        image,
                        face['box'],
                        face['keypoints']
                    )
                    preprocessed_faces.append(prep_face)
                
                embeddings = encoder.encode_batch(preprocessed_faces)
                print(f"\n=== Batch Encoding ===")
                print(f"Batch embeddings shape: {embeddings.shape}")
        else:
            print("Tidak ada wajah terdeteksi")
    else:
        print("Gagal load image")
