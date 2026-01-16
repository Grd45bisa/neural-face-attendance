import cv2
import numpy as np
import time
from datetime import datetime
from collections import defaultdict
import os
from registration.registration import UserRegistration


class LiveFaceTracker:
    """
    Live face tracker untuk real-time face tracking dan recognition.
    Fase 6 - Live face tracking dengan camera integration.
    """
    
    def __init__(self, camera_handler, recognizer, db_manager, config=None):
        """
        Initialize live face tracker.
        
        Args:
            camera_handler: CameraHandler instance
            recognizer: FaceRecognizer instance
            db_manager: DatabaseManager instance
            config (dict): Configuration parameters
        """
        self.camera = camera_handler
        self.recognizer = recognizer
        self.db_manager = db_manager
        
        # Default config
        default_config = {
            'process_every_n_frames': 2,
            'display_fps': True,
            'recognition_interval': 1.0,
            'save_snapshots': False,
            'snapshot_dir': 'output/snapshots',
            'smooth_boxes': True,
            'show_keypoints': False
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Tracking state
        self.is_tracking = False
        self.is_paused = False
        self.frame_count = 0
        self.last_recognition_time = 0
        
        # Statistics
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'total_recognitions': 0,
            'unique_persons': set(),
            'start_time': None,
            'recognition_events': []
        }
        
        # Temporal smoothing untuk stable recognition
        self.person_history = defaultdict(list)  # {user_id: [timestamps]}
        self.last_results = []
        
        # FPS calculation
        self.fps_start_time = None
        self.fps_frame_count = 0
        self.current_fps = 0.0
        
        # Create snapshot directory
        if self.config['save_snapshots']:
            os.makedirs(self.config['snapshot_dir'], exist_ok=True)
    
    def start_tracking(self):
        """
        MAIN METHOD: Start real-time face tracking.
        
        Returns:
            dict: Tracking session summary
        """
        print("\n" + "="*60)
        print("LIVE FACE TRACKING")
        print("="*60)
        print("\nKeyboard Controls:")
        print("  Q / ESC  : Quit")
        print("  S        : Save snapshot")
        print("  P        : Pause/Resume")
        print("  R        : Register new user")
        print("  F        : Force re-recognition")
        print("  +/-      : Adjust threshold")
        print("="*60)
        
        # Start camera jika belum
        if not self.camera.is_camera_opened():
            if not self.camera.start_camera():
                print("✗ Failed to start camera")
                return None
        
        # Initialize tracking
        self.is_tracking = True
        self.stats['start_time'] = time.time()
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        
        try:
            # Main tracking loop
            for frame in self.camera.get_frame_generator():
                if not self.is_tracking:
                    break
                
                self.stats['total_frames'] += 1
                self.frame_count += 1
                
                # Update FPS
                self.fps_frame_count += 1
                if self.fps_frame_count % 30 == 0:
                    elapsed = time.time() - self.fps_start_time
                    self.current_fps = self.fps_frame_count / elapsed
                
                # Process frame (dengan frame skipping untuk performance)
                if not self.is_paused:
                    if self.frame_count % self.config['process_every_n_frames'] == 0:
                        annotated_frame, results = self.process_frame(frame)
                        self.last_results = results
                        self.stats['processed_frames'] += 1
                    else:
                        # Use last results untuk smooth display
                        annotated_frame = self.draw_ui_overlay(
                            frame, 
                            self.last_results, 
                            self.current_fps
                        )
                else:
                    # Paused - just show frame dengan pause indicator
                    annotated_frame = frame.copy()
                    cv2.putText(
                        annotated_frame,
                        "PAUSED",
                        (annotated_frame.shape[1]//2 - 100, annotated_frame.shape[0]//2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0, 0, 255),
                        3
                    )
                
                # Display frame
                cv2.imshow('Live Face Tracking', annotated_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                action = self.handle_keyboard_input(key)
                
                if action == 'quit':
                    break
                elif action == 'save':
                    self._save_snapshot(annotated_frame)
                elif action == 'force_recognize':
                    self.last_recognition_time = 0  # Force next recognition
                elif action == 'register':
                    self._handle_registration()
            
            # Cleanup
            self.is_tracking = False
            cv2.destroyAllWindows()
            
            # Generate summary
            summary = self.get_tracking_statistics()
            
            print("\n" + "="*60)
            print("TRACKING SESSION SUMMARY")
            print("="*60)
            print(f"Duration: {summary['uptime']:.1f} seconds")
            print(f"Total frames: {summary['total_frames']}")
            print(f"Processed frames: {summary['processed_frames']}")
            print(f"Average FPS: {summary['avg_fps']:.1f}")
            print(f"Total recognitions: {summary['total_recognitions']}")
            print(f"Unique persons: {summary['unique_persons_count']}")
            print("="*60)
            
            return summary
            
        except KeyboardInterrupt:
            print("\n⚠ Tracking interrupted by user")
            self.is_tracking = False
            cv2.destroyAllWindows()
            return self.get_tracking_statistics()
        except Exception as e:
            print(f"\n✗ Error during tracking: {e}")
            self.is_tracking = False
            cv2.destroyAllWindows()
            return None
    
    def process_frame(self, frame):
        """
        Process single frame untuk recognition.
        
        Args:
            frame (numpy.ndarray): Input frame
        
        Returns:
            tuple: (annotated_frame, recognition_results)
        """
        # Check recognition interval
        current_time = time.time()
        should_recognize = (current_time - self.last_recognition_time) >= self.config['recognition_interval']
        
        if should_recognize:
            # Perform recognition
            result = self.recognizer.recognize_from_image(frame)
            
            if result['status'] == 'success':
                results = result['results']
                
                # Update statistics
                for res in results:
                    if res['user_id'] not in ['unknown', 'error']:
                        self.stats['unique_persons'].add(res['user_id'])
                        self.stats['total_recognitions'] += 1
                        
                        # Log recognition event
                        self.stats['recognition_events'].append({
                            'timestamp': datetime.now().isoformat(),
                            'user_id': res['user_id'],
                            'name': res['name'],
                            'confidence': res['confidence']
                        })
                        
                        # Update person history untuk temporal smoothing
                        self.person_history[res['user_id']].append(current_time)
                
                self.last_recognition_time = current_time
            else:
                results = []
        else:
            # Use last results
            results = self.last_results
        
        # Draw UI overlay
        annotated_frame = self.draw_ui_overlay(frame, results, self.current_fps)
        
        return annotated_frame, results
    
    def draw_ui_overlay(self, frame, results, fps):
        """
        Gambar UI elements di frame.
        
        Args:
            frame (numpy.ndarray): Input frame
            results (list): Recognition results
            fps (float): Current FPS
        
        Returns:
            numpy.ndarray: Frame dengan UI overlay
        """
        overlay = frame.copy()
        
        # Draw recognition results
        for result in results:
            x, y, w, h = result['box']
            name = result['name']
            confidence = result.get('confidence', 0)
            user_id = result['user_id']
            confidence_level = result.get('confidence_level', 'unknown')
            
            # Color based on confidence level dan status
            if user_id == 'unknown':
                color = (0, 0, 255)  # Red
                label = "Unknown"
            elif user_id == 'error':
                color = (0, 165, 255)  # Orange
                label = "Error"
            else:
                # Color based on confidence level
                if confidence_level == 'high':
                    color = (0, 255, 0)  # Green
                elif confidence_level == 'medium':
                    color = (0, 255, 255)  # Yellow
                else:
                    color = (0, 165, 255)  # Orange
                
                label = f"{name} ({confidence:.0f}%)"
            
            # Draw bounding box
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(
                overlay,
                (x, y - label_size[1] - 10),
                (x + label_size[0] + 10, y),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                overlay,
                label,
                (x + 5, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            # Draw keypoints jika enabled
            if self.config['show_keypoints'] and 'keypoints' in result:
                keypoints = result['keypoints']
                cv2.circle(overlay, keypoints['left_eye'], 2, (255, 0, 0), -1)
                cv2.circle(overlay, keypoints['right_eye'], 2, (255, 0, 0), -1)
                cv2.circle(overlay, keypoints['nose'], 2, (0, 0, 255), -1)
        
        # Draw FPS counter
        if self.config['display_fps']:
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(
                overlay,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # Draw status bar
        status_y = overlay.shape[0] - 10
        
        # Database user count
        db_stats = self.db_manager.get_database_stats()
        db_text = f"DB Users: {db_stats['total_users']}"
        cv2.putText(
            overlay,
            db_text,
            (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        # Detected faces count
        faces_text = f"Faces: {len(results)}"
        cv2.putText(
            overlay,
            faces_text,
            (150, status_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        # Instructions
        instructions = "Q:Quit | S:Save | P:Pause | R:Register | F:Re-rec"
        instr_size, _ = cv2.getTextSize(instructions, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(
            overlay,
            instructions,
            (overlay.shape[1] - instr_size[0] - 10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        return overlay
    
    def handle_keyboard_input(self, key):
        """
        Handle keyboard shortcuts.
        
        Args:
            key (int): Key code dari cv2.waitKey()
        
        Returns:
            str: Action command ('quit', 'save', 'pause', etc.)
        """
        if key == ord('q') or key == 27:  # Q or ESC
            return 'quit'
        
        elif key == ord('s'):  # Save snapshot
            return 'save'
        
        elif key == ord('p'):  # Pause/Resume
            self.is_paused = not self.is_paused
            status = "PAUSED" if self.is_paused else "RESUMED"
            print(f"⏸ Tracking {status}")
            return 'pause'
        
        elif key == ord('f'):  # Force re-recognition (was R)
            print("🔄 Forcing re-recognition...")
            return 'force_recognize'
            
        elif key == ord('r'):  # Register new user (New)
            return 'register'
        
        elif key == ord('+') or key == ord('='):  # Increase threshold
            current = self.recognizer.matcher.threshold
            new_threshold = min(1.0, current + 0.05)
            self.recognizer.matcher.set_threshold(new_threshold)
            print(f"📈 Threshold: {new_threshold:.2f}")
            return 'threshold_up'
        
        elif key == ord('-') or key == ord('_'):  # Decrease threshold
            current = self.recognizer.matcher.threshold
            new_threshold = max(0.0, current - 0.05)
            self.recognizer.matcher.set_threshold(new_threshold)
            print(f"📉 Threshold: {new_threshold:.2f}")
            return 'threshold_down'
        
        return None
    
    def _handle_registration(self):
        """
        Handle registration process.
        Stops tracking, runs registration, then resumes tracking.
        """
        print("\n" + "="*60)
        print("STARTING REGISTRATION")
        print("="*60)
        
        # 1. Stop camera tracking
        print("⏳ Pausing tracking for registration...")
        self.camera.stop_camera()
        cv2.destroyAllWindows()
        
        # 2. Get user input
        try:
            print("\nEnter new user details:")
            name = input("Name: ").strip()
            if not name:
                print("⚠ Name cannot be empty. Registration cancelled.")
                self.camera.start_camera()
                return
                
            user_id = name.lower().replace(" ", "_")
            print(f"User ID: {user_id}")
            
            # 3. Initialize registration module
            registration = UserRegistration(
                detector=self.recognizer.detector,
                preprocessor=self.recognizer.preprocessor,
                encoder=self.recognizer.encoder,
                db_manager=self.db_manager
            )
            
            # 4. Run registration
            result = registration.register_from_camera(
                user_id=user_id, 
                name=name,
                camera_id=self.camera.camera_id
            )
            
            if result['status'] == 'success':
                print(f"\n✓ Registration successful for {name}")
            else:
                print(f"\n✗ Registration failed: {result['message']}")
                
        except Exception as e:
            print(f"\n✗ Error during registration: {e}")
        
        # 5. Resume tracking
        print("\n⏳ Resuming tracking...")
        input("Press ENTER to resume tracking...")
        self.camera.start_camera()
        self.last_recognition_time = 0 # Force re-recognition
        print("✓ Tracking resumed")
    
    def _save_snapshot(self, frame):
        """
        Save current frame as snapshot.
        
        Args:
            frame (numpy.ndarray): Frame to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.jpg"
        filepath = os.path.join(self.config['snapshot_dir'], filename)
        
        cv2.imwrite(filepath, frame)
        print(f"📸 Snapshot saved: {filepath}")
    
    def track_person(self, user_id, duration=10):
        """
        Track specific person untuk duration tertentu.
        
        Args:
            user_id (str): User ID to track
            duration (int): Duration dalam detik
        
        Returns:
            dict: Tracking result
        """
        print(f"\n🎯 Tracking user: {user_id} for {duration} seconds")
        
        user_data = self.db_manager.get_user(user_id)
        if not user_data:
            print(f"✗ User {user_id} not found in database")
            return None
        
        target_name = user_data['name']
        print(f"   Target: {target_name}")
        
        start_time = time.time()
        detections = []
        
        # Start camera jika belum
        if not self.camera.is_camera_opened():
            self.camera.start_camera()
        
        try:
            for frame in self.camera.get_frame_generator():
                elapsed = time.time() - start_time
                
                if elapsed >= duration:
                    break
                
                # Recognize
                result = self.recognizer.recognize_from_image(frame)
                
                # Check if target found
                target_found = False
                if result['status'] == 'success':
                    for res in result['results']:
                        if res['user_id'] == user_id:
                            target_found = True
                            detections.append({
                                'timestamp': time.time(),
                                'confidence': res['confidence']
                            })
                            
                            # Highlight target dengan warna khusus
                            x, y, w, h = res['box']
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 3)
                            cv2.putText(
                                frame,
                                f"TARGET: {target_name}",
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (255, 0, 255),
                                2
                            )
                
                # Draw tracking info
                remaining = duration - elapsed
                info_text = f"Tracking: {target_name} | Time: {remaining:.1f}s"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if not target_found:
                    cv2.putText(frame, "TARGET NOT IN FRAME", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.imshow('Person Tracking', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cv2.destroyAllWindows()
            
            # Summary
            detection_rate = (len(detections) / (duration * 30)) * 100  # Assuming 30 FPS
            
            summary = {
                'user_id': user_id,
                'name': target_name,
                'duration': duration,
                'detections': len(detections),
                'detection_rate': detection_rate
            }
            
            print(f"\n✓ Tracking completed")
            print(f"   Detections: {len(detections)}")
            print(f"   Detection rate: {detection_rate:.1f}%")
            
            return summary
            
        except KeyboardInterrupt:
            print("\n⚠ Tracking interrupted")
            cv2.destroyAllWindows()
            return None
    
    def get_tracking_statistics(self):
        """
        Get tracking statistics.
        
        Returns:
            dict: Tracking statistics
        """
        uptime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        avg_fps = self.stats['total_frames'] / uptime if uptime > 0 else 0
        
        return {
            'total_frames': self.stats['total_frames'],
            'processed_frames': self.stats['processed_frames'],
            'total_recognitions': self.stats['total_recognitions'],
            'unique_persons_count': len(self.stats['unique_persons']),
            'unique_persons': list(self.stats['unique_persons']),
            'uptime': uptime,
            'avg_fps': avg_fps,
            'recognition_events': self.stats['recognition_events']
        }


# Example usage
if __name__ == "__main__":
    from tracking.camera_handler import CameraHandler
    from core.face_recognizer import FaceRecognizer
    from core.face_detector import FaceDetector
    from core.face_preprocessor import FacePreprocessor
    from core.face_encoder import FaceEncoder
    from core.face_matcher import FaceMatcher
    from database.database_manager import DatabaseManager
    
    # Initialize all components
    camera = CameraHandler(camera_id=0, resolution=(1280, 720))
    detector = FaceDetector()
    preprocessor = FacePreprocessor(target_size=(224, 224))
    encoder = FaceEncoder()
    matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
    db_manager = DatabaseManager('data/face_db.pkl')
    
    recognizer = FaceRecognizer(
        detector=detector,
        preprocessor=preprocessor,
        encoder=encoder,
        matcher=matcher,
        db_manager=db_manager
    )
    
    # Initialize tracker
    tracker = LiveFaceTracker(
        camera_handler=camera,
        recognizer=recognizer,
        db_manager=db_manager,
        config={
            'process_every_n_frames': 2,
            'display_fps': True,
            'recognition_interval': 1.0,
            'save_snapshots': True
        }
    )
    
    # Start tracking
    summary = tracker.start_tracking()
    
    if summary:
        print(f"\n✓ Tracked {summary['unique_persons_count']} unique persons")
