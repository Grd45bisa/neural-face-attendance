import cv2
import numpy as np
import time
import warnings
from datetime import datetime


class CameraHandler:
    """
    Camera handler untuk mengelola akses kamera dan frame capture.
    Fase 6 - Camera integration untuk real-time tracking.
    """
    
    def __init__(self, camera_id=0, resolution=(640, 480), fps=30):
        """
        Initialize camera handler.
        
        Args:
            camera_id (int): Camera device ID (0 = default webcam)
            resolution (tuple): Target resolution (width, height)
            fps (int): Target FPS
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        self.is_opened = False
        
        # FPS monitoring
        self.frame_count = 0
        self.start_time = None
        self.actual_fps = 0.0
    
    def start_camera(self):
        """
        Buka koneksi ke camera dan set properties.
        
        Returns:
            bool: True jika sukses, False jika gagal
        
        Raises:
            RuntimeError: Jika camera tidak dapat diakses
        """
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Camera ID {self.camera_id} tidak dapat diakses. "
                    "Pastikan:\n"
                    "1. Camera terhubung dengan benar\n"
                    "2. Camera tidak digunakan aplikasi lain\n"
                    "3. Permission camera sudah diberikan"
                )
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Optional: Set autofocus
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            # Warmup camera (capture beberapa frame untuk stabilisasi)
            print("⏳ Warming up camera...")
            for _ in range(10):
                ret, _ = self.cap.read()
                if not ret:
                    warnings.warn("Warning: Frame dropped during warmup", UserWarning)
            
            self.is_opened = True
            self.start_time = time.time()
            self.frame_count = 0
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"✓ Camera started successfully")
            print(f"  Resolution: {actual_width}x{actual_height}")
            print(f"  FPS: {actual_fps}")
            
            return True
            
        except RuntimeError as e:
            print(f"✗ Error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error starting camera: {e}")
            return False
    
    def stop_camera(self):
        """
        Release camera resource dengan aman.
        """
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
            print("✓ Camera stopped and resources released")
        
        # Close all OpenCV windows
        cv2.destroyAllWindows()
    
    def read_frame(self):
        """
        Capture single frame dari camera.
        
        Returns:
            tuple: (success, frame)
                  success: bool - True jika frame berhasil di-capture
                  frame: numpy.ndarray atau None
        """
        if not self.is_opened or self.cap is None:
            warnings.warn("Camera belum di-start. Call start_camera() terlebih dahulu.", UserWarning)
            return False, None
        
        # Read frame
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            
            # Update FPS calculation
            if self.frame_count % 30 == 0:  # Update every 30 frames
                elapsed_time = time.time() - self.start_time
                self.actual_fps = self.frame_count / elapsed_time
        
        return ret, frame
    
    def get_frame_generator(self):
        """
        Generator yang yield frames continuously.
        Berguna untuk real-time processing loop.
        
        Yields:
            numpy.ndarray: Frame dari camera
        
        Example:
            >>> camera = CameraHandler()
            >>> camera.start_camera()
            >>> for frame in camera.get_frame_generator():
            ...     cv2.imshow('Live', frame)
            ...     if cv2.waitKey(1) & 0xFF == ord('q'):
            ...         break
        """
        if not self.is_opened:
            raise RuntimeError("Camera belum di-start. Call start_camera() terlebih dahulu.")
        
        while self.is_opened:
            ret, frame = self.read_frame()
            
            if ret:
                yield frame
            else:
                warnings.warn("Frame capture failed", UserWarning)
                break
    
    def is_camera_opened(self):
        """
        Check apakah camera masih aktif.
        
        Returns:
            bool: True jika camera aktif
        """
        return self.is_opened and self.cap is not None and self.cap.isOpened()
    
    def get_camera_properties(self):
        """
        Get camera properties.
        
        Returns:
            dict: Camera properties
        """
        if not self.is_opened or self.cap is None:
            return {}
        
        properties = {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'exposure': self.cap.get(cv2.CAP_PROP_EXPOSURE),
            'actual_fps': self.actual_fps,
            'frame_count': self.frame_count
        }
        
        return properties
    
    def set_camera_property(self, property_name, value):
        """
        Adjust camera settings dynamically.
        
        Args:
            property_name (str): Property name ('brightness', 'contrast', 'saturation', 'exposure')
            value (float): Property value
        
        Returns:
            bool: True jika sukses
        """
        if not self.is_opened or self.cap is None:
            warnings.warn("Camera belum di-start", UserWarning)
            return False
        
        property_map = {
            'brightness': cv2.CAP_PROP_BRIGHTNESS,
            'contrast': cv2.CAP_PROP_CONTRAST,
            'saturation': cv2.CAP_PROP_SATURATION,
            'exposure': cv2.CAP_PROP_EXPOSURE,
            'fps': cv2.CAP_PROP_FPS,
            'width': cv2.CAP_PROP_FRAME_WIDTH,
            'height': cv2.CAP_PROP_FRAME_HEIGHT
        }
        
        if property_name not in property_map:
            warnings.warn(f"Unknown property: {property_name}", UserWarning)
            return False
        
        success = self.cap.set(property_map[property_name], value)
        
        if success:
            print(f"✓ Set {property_name} to {value}")
        else:
            warnings.warn(f"Failed to set {property_name}", UserWarning)
        
        return success
    
    def record_video(self, output_path, duration=10):
        """
        Record video dari camera.
        
        Args:
            output_path (str): Path untuk save video
            duration (int): Durasi recording dalam detik
        
        Returns:
            bool: True jika sukses
        """
        if not self.is_opened:
            print("✗ Camera belum di-start")
            return False
        
        # Get camera properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        # Define codec dan create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        print(f"🎥 Recording video to {output_path}")
        print(f"   Duration: {duration} seconds")
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while (time.time() - start_time) < duration:
                ret, frame = self.read_frame()
                
                if ret:
                    out.write(frame)
                    frame_count += 1
                    
                    # Show recording indicator
                    cv2.putText(
                        frame,
                        "REC",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2
                    )
                    
                    cv2.imshow('Recording', frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("⚠ Recording stopped by user")
                        break
                else:
                    warnings.warn("Frame capture failed during recording", UserWarning)
                    break
            
            print(f"✓ Recording completed: {frame_count} frames")
            return True
            
        except KeyboardInterrupt:
            print("\n⚠ Recording interrupted by user")
            return False
        finally:
            out.release()
            cv2.destroyWindow('Recording')
    
    def get_fps(self):
        """
        Get actual FPS dari camera.
        
        Returns:
            float: Actual FPS
        """
        return self.actual_fps
    
    @staticmethod
    def list_available_cameras(max_cameras=10):
        """
        Detect semua available cameras.
        
        Args:
            max_cameras (int): Maximum camera IDs to check
        
        Returns:
            list: List of available camera IDs
        """
        available_cameras = []
        
        print("🔍 Scanning for available cameras...")
        
        for camera_id in range(max_cameras):
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                available_cameras.append(camera_id)
                print(f"  ✓ Camera {camera_id} available")
                cap.release()
        
        if not available_cameras:
            print("  ✗ No cameras found")
        
        return available_cameras
    
    def __enter__(self):
        """Context manager support."""
        self.start_camera()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.stop_camera()
    
    def __del__(self):
        """Destructor untuk ensure cleanup."""
        if self.cap is not None:
            self.stop_camera()


# Example usage
if __name__ == "__main__":
    # List available cameras
    available = CameraHandler.list_available_cameras()
    
    if not available:
        print("⚠ No cameras available")
        exit(1)
    
    # Initialize camera
    camera = CameraHandler(camera_id=0, resolution=(1280, 720), fps=30)
    
    try:
        if camera.start_camera():
            print("\n" + "="*60)
            print("CAMERA TEST")
            print("="*60)
            
            # Show camera properties
            props = camera.get_camera_properties()
            print(f"\nCamera Properties:")
            print(f"  Resolution: {props['width']}x{props['height']}")
            print(f"  Target FPS: {props['fps']}")
            print(f"  Brightness: {props['brightness']}")
            print(f"  Contrast: {props['contrast']}")
            
            print("\n📹 Live preview (Press 'q' to quit, 'r' to record)")
            
            # Live preview
            for frame in camera.get_frame_generator():
                # Show FPS
                fps_text = f"FPS: {camera.get_fps():.1f}"
                cv2.putText(
                    frame,
                    fps_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow('Camera Test - Press Q to quit', frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # Record 5 seconds
                    camera.record_video('test_recording.mp4', duration=5)
            
            camera.stop_camera()
        else:
            print("✗ Failed to start camera")
    
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        camera.stop_camera()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        camera.stop_camera()
