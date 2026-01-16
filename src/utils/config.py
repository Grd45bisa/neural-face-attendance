"""
Configuration file untuk Face Recognition System.
Centralized configuration untuk semua modules.
"""

import os

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
APP_NAME = "Face Recognition System"
APP_VERSION = "1.0.0"

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Database
DATABASE_PATH = os.path.join(DATA_DIR, 'face_db.pkl')

# Logs
LOG_DATABASE_PATH = os.path.join(LOG_DIR, 'recognition_logs.db')
SNAPSHOT_DIR = os.path.join(LOG_DIR, 'snapshots')

# ============================================================================
# CAMERA SETTINGS
# ============================================================================
CAMERA_ID = 0
# OPTIMIZED for entry-level CPU (Ryzen 5 Gen 3, Intel i5)
# 640x480 provides good quality with 3x better performance vs 720p
CAMERA_RESOLUTION = (640, 480)  # Width x Height (was 1280x720)
CAMERA_FPS = 30

# ============================================================================
# FACE DETECTION SETTINGS (MTCNN)
# ============================================================================
DETECTION_MIN_CONFIDENCE = 0.9  # Minimum confidence untuk face detection
DETECTION_MIN_FACE_SIZE = 50    # Minimum face size (pixels)

# ============================================================================
# FACE PREPROCESSING SETTINGS
# ============================================================================
PREPROCESSING_TARGET_SIZE = (224, 224)  # Target size untuk model input
PREPROCESSING_MARGIN = 0.2              # Margin around face (20%)

# ============================================================================
# FACE ENCODING SETTINGS (MobileNetV2)
# ============================================================================
ENCODER_MODEL = 'mobilenetv2'
ENCODER_WEIGHTS = 'imagenet'
EMBEDDING_DIMENSION = 1280  # MobileNetV2 output dimension

# ============================================================================
# FACE MATCHING SETTINGS
# ============================================================================
SIMILARITY_METRIC = 'cosine'  # Options: 'cosine', 'euclidean', 'manhattan'
RECOGNITION_THRESHOLD = 0.6   # Threshold untuk match/no-match
                              # Lower = more permissive (more matches)
                              # Higher = more strict (fewer matches)

# Recommended thresholds:
# - 0.5-0.6: Permissive (good for varied lighting)
# - 0.6-0.7: Balanced (recommended)
# - 0.7-0.8: Strict (high accuracy, may miss some matches)

# ============================================================================
# REGISTRATION SETTINGS
# ============================================================================
REGISTRATION_PHOTO_COUNT = 5  # Number of photos untuk registration
REGISTRATION_MIN_QUALITY = 0.8  # Minimum quality score

# ============================================================================
# LIVE TRACKING SETTINGS
# ============================================================================
# OPTIMIZED: Process every 4 frames instead of 2 for 2x FPS improvement
# This means: if camera is 30fps, we process 7.5fps (still smooth)
TRACKING_PROCESS_EVERY_N_FRAMES = 4  # Process every N frames (was 2)
TRACKING_RECOGNITION_INTERVAL = 1.0  # Recognition interval (seconds)
TRACKING_DISPLAY_FPS = True          # Show FPS counter
TRACKING_SAVE_SNAPSHOTS = False      # Auto-save snapshots

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOGGING_ENABLED = True
LOGGING_SAVE_SNAPSHOTS = False
LOGGING_RETENTION_DAYS = 30  # Keep logs for N days
LOGGING_SNAPSHOT_RULES = {
    'high_confidence': True,   # Save jika confidence > 0.9
    'unknown_only': False,     # Save only unknown faces
    'quality_threshold': 0.8   # Minimum quality untuk save
}

# ============================================================================
# PERFORMANCE OPTIMIZATION SETTINGS
# ============================================================================
# Frame optimization - optimized for entry-level CPU
OPTIMIZATION_SKIP_FRAMES = 4  # Increased from 2 for better FPS
OPTIMIZATION_ADAPTIVE_SKIP = True
OPTIMIZATION_MOTION_THRESHOLD = 0.05

# Multi-threading
OPTIMIZATION_USE_MULTITHREADING = False
OPTIMIZATION_NUM_WORKERS = 2

# GPU
OPTIMIZATION_USE_GPU = True  # Use GPU jika available

# ============================================================================
# UI SETTINGS
# ============================================================================
UI_THEME = 'light'  # Options: 'light', 'dark'
UI_LANGUAGE = 'en'  # Options: 'en', 'id'
UI_SHOW_CONFIDENCE = True
UI_SHOW_KEYPOINTS = False

# ============================================================================
# ALERT SETTINGS
# ============================================================================
ALERTS_ENABLED = False
ALERTS_UNKNOWN_THRESHOLD = 10  # Alert jika > N unknown detections
ALERTS_EMAIL = None            # Email untuk alerts (optional)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config_dict():
    """
    Get all configuration as dictionary.
    
    Returns:
        dict: Configuration dictionary
    """
    return {
        'app': {
            'name': APP_NAME,
            'version': APP_VERSION
        },
        'paths': {
            'base_dir': BASE_DIR,
            'data_dir': DATA_DIR,
            'log_dir': LOG_DIR,
            'output_dir': OUTPUT_DIR,
            'database_path': DATABASE_PATH
        },
        'camera': {
            'camera_id': CAMERA_ID,
            'resolution': CAMERA_RESOLUTION,
            'fps': CAMERA_FPS
        },
        'detection': {
            'min_confidence': DETECTION_MIN_CONFIDENCE,
            'min_face_size': DETECTION_MIN_FACE_SIZE
        },
        'preprocessing': {
            'target_size': PREPROCESSING_TARGET_SIZE,
            'margin': PREPROCESSING_MARGIN
        },
        'encoding': {
            'model': ENCODER_MODEL,
            'embedding_dim': EMBEDDING_DIMENSION
        },
        'matching': {
            'metric': SIMILARITY_METRIC,
            'threshold': RECOGNITION_THRESHOLD
        },
        'registration': {
            'photo_count': REGISTRATION_PHOTO_COUNT,
            'min_quality': REGISTRATION_MIN_QUALITY
        },
        'tracking': {
            'process_every_n_frames': TRACKING_PROCESS_EVERY_N_FRAMES,
            'recognition_interval': TRACKING_RECOGNITION_INTERVAL,
            'display_fps': TRACKING_DISPLAY_FPS
        },
        'logging': {
            'enabled': LOGGING_ENABLED,
            'retention_days': LOGGING_RETENTION_DAYS
        },
        'optimization': {
            'skip_frames': OPTIMIZATION_SKIP_FRAMES,
            'use_gpu': OPTIMIZATION_USE_GPU
        }
    }


def print_config():
    """Print current configuration."""
    config = get_config_dict()
    
    print("\n" + "="*60)
    print("FACE RECOGNITION SYSTEM - CONFIGURATION".center(60))
    print("="*60)
    
    for section, settings in config.items():
        print(f"\n[{section.upper()}]")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print_config()
