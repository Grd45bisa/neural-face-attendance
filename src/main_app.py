"""
Face Recognition System - Main Application
Entry point untuk CLI-based face recognition application
"""

import argparse
import sys
import os
from datetime import datetime
import glob

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from core.face_detector import FaceDetector
from core.face_preprocessor import FacePreprocessor
from core.face_encoder import FaceEncoder
from core.face_matcher import FaceMatcher
from core.face_recognizer import FaceRecognizer
from database.database_manager import DatabaseManager
from registration.registration import UserRegistration
from tracking.camera_handler import CameraHandler
from tracking.live_tracker import LiveFaceTracker


class FaceRecognitionApp:
    """Main application class untuk face recognition system."""
    
    def __init__(self):
        """Initialize application dan load semua components."""
        print("\n" + "="*60)
        print("FACE RECOGNITION SYSTEM")
        print("="*60)
        print("\n⏳ Loading components...")
        
        # Initialize components
        self.detector = None
        self.preprocessor = None
        self.encoder = None
        self.matcher = None
        self.db_manager = None
        self.recognizer = None
        self.camera_handler = None
        
        self._initialize_components()
        
        print("✓ All components loaded successfully!\n")
    
    def _initialize_components(self):
        """Initialize semua modules."""
        try:
            print("  Loading face detector...")
            self.detector = FaceDetector()
            
            print("  Loading preprocessor...")
            self.preprocessor = FacePreprocessor(target_size=(224, 224))
            
            print("  Loading face encoder (this may take a while)...")
            self.encoder = FaceEncoder()
            
            print("  Loading database...")
            self.db_manager = DatabaseManager('data/face_db.pkl')
            
            print("  Loading matcher...")
            self.matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
            
            print("  Loading recognizer...")
            self.recognizer = FaceRecognizer(
                detector=self.detector,
                preprocessor=self.preprocessor,
                encoder=self.encoder,
                matcher=self.matcher,
                db_manager=self.db_manager
            )
            
        except Exception as e:
            print(f"\n✗ Error initializing components: {e}")
            sys.exit(1)
    
    def cmd_register(self, args):
        """Register user baru."""
        print("\n" + "="*60)
        print("USER REGISTRATION")
        print("="*60)
        
        # Generate user_id jika tidak ada
        user_id = args.user_id
        if not user_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = f"user_{timestamp}"
            print(f"Auto-generated User ID: {user_id}")
        
        # Initialize registration
        registration = UserRegistration(
            detector=self.detector,
            preprocessor=self.preprocessor,
            encoder=self.encoder,
            db_manager=self.db_manager
        )
        
        # Register dari file atau camera
        if args.from_file:
            result = registration.register_from_file(
                user_id=user_id,
                name=args.name,
                image_path=args.from_file
            )
        else:
            result = registration.register_from_camera(
                user_id=user_id,
                name=args.name,
                photo_count=args.photos
            )
        
        # Show result
        print("\n" + "="*60)
        if result['status'] == 'success':
            print("✓ REGISTRATION SUCCESSFUL")
            print(f"  User: {result['name']}")
            print(f"  ID: {result['user_id']}")
            if 'quality_score' in result:
                print(f"  Quality Score: {result['quality_score']:.2f}/100")
        else:
            print("✗ REGISTRATION FAILED")
            print(f"  Reason: {result['message']}")
        print("="*60)
    
    def cmd_recognize(self, args):
        """Start live recognition."""
        print("\n" + "="*60)
        print("LIVE FACE RECOGNITION")
        print("="*60)
        
        # Initialize camera
        self.camera_handler = CameraHandler(
            camera_id=args.camera_id,
            resolution=(1280, 720),
            fps=args.fps
        )
        
        # Set threshold
        self.matcher.set_threshold(args.threshold)
        
        # Initialize tracker
        tracker = LiveFaceTracker(
            camera_handler=self.camera_handler,
            recognizer=self.recognizer,
            db_manager=self.db_manager,
            config={
                'process_every_n_frames': 2,
                'display_fps': True,
                'recognition_interval': 1.0,
                'save_snapshots': args.save_log
            }
        )
        
        # Start tracking
        summary = tracker.start_tracking()
        
        # Show summary
        if summary:
            print(f"\n✓ Recognized {summary['unique_persons_count']} unique persons")
    
    def cmd_test(self, args):
        """Test recognition dari image file."""
        print("\n" + "="*60)
        print("IMAGE RECOGNITION TEST")
        print("="*60)
        
        # Support wildcard
        image_paths = glob.glob(args.image_path)
        
        if not image_paths:
            print(f"✗ No images found: {args.image_path}")
            return
        
        print(f"\nTesting {len(image_paths)} image(s)...\n")
        
        for img_path in image_paths:
            print(f"\n{'='*60}")
            print(f"Image: {os.path.basename(img_path)}")
            print(f"{'='*60}")
            
            # Recognize
            result = self.recognizer.recognize_from_file(img_path)
            
            if result['status'] == 'success':
                for i, res in enumerate(result['results']):
                    print(f"\nFace {i+1}:")
                    print(f"  Name: {res['name']}")
                    print(f"  User ID: {res['user_id']}")
                    print(f"  Confidence: {res['confidence']:.2f}%")
                    print(f"  Similarity: {res['similarity']:.4f}")
                
                # Show/save annotated image
                if args.show or args.save:
                    import cv2
                    image = cv2.imread(img_path)
                    annotated = self.recognizer.annotate_image(image, result)
                    
                    if args.show:
                        cv2.imshow('Recognition Result', annotated)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    
                    if args.save:
                        save_path = f"output/annotated_{os.path.basename(img_path)}"
                        os.makedirs('output', exist_ok=True)
                        cv2.imwrite(save_path, annotated)
                        print(f"\n✓ Saved annotated image: {save_path}")
            else:
                print(f"\n✗ {result['message']}")
    
    def cmd_list_users(self, args):
        """List semua registered users."""
        users = self.db_manager.get_all_users()
        
        print("\n" + "="*60)
        print("REGISTERED USERS")
        print("="*60)
        
        if not users:
            print("\nNo users registered yet.")
            return
        
        if args.format == 'table':
            # Table format
            print(f"\n{'User ID':<20} {'Name':<20} {'Registered':<20} {'Photos':<10}")
            print("-" * 70)
            for user in users:
                print(f"{user['user_id']:<20} {user['name']:<20} {user['registered_at'][:10]:<20} {user['photo_count']:<10}")
        
        elif args.format == 'json':
            import json
            print(json.dumps(users, indent=2))
        
        elif args.format == 'csv':
            print("user_id,name,registered_at,photo_count")
            for user in users:
                print(f"{user['user_id']},{user['name']},{user['registered_at']},{user['photo_count']}")
        
        print(f"\nTotal users: {len(users)}")
    
    def cmd_delete_user(self, args):
        """Delete user dari database."""
        # Get user info
        user = self.db_manager.get_user(args.user_id)
        
        if not user:
            print(f"\n✗ User ID '{args.user_id}' not found")
            return
        
        # Show user info
        print("\n" + "="*60)
        print("DELETE USER")
        print("="*60)
        print(f"\nUser ID: {args.user_id}")
        print(f"Name: {user['name']}")
        print(f"Registered: {user['registered_at']}")
        
        # Confirm
        if not args.force:
            confirm = input("\nAre you sure you want to delete this user? (yes/no): ")
            if confirm.lower() != 'yes':
                print("✗ Deletion cancelled")
                return
        
        # Delete
        success = self.db_manager.delete_user(args.user_id)
        
        if success:
            print(f"\n✓ User '{user['name']}' deleted successfully")
        else:
            print(f"\n✗ Failed to delete user")
    
    def cmd_update_user(self, args):
        """Update user data."""
        # Check user exists
        user = self.db_manager.get_user(args.user_id)
        
        if not user:
            print(f"\n✗ User ID '{args.user_id}' not found")
            return
        
        print("\n" + "="*60)
        print("UPDATE USER")
        print("="*60)
        print(f"\nCurrent User: {user['name']} (ID: {args.user_id})")
        
        # Update name
        if args.name:
            self.db_manager.update_user(args.user_id, name=args.name)
            print(f"✓ Name updated to: {args.name}")
        
        # Re-register
        if args.re_register:
            print("\nStarting re-registration...")
            registration = UserRegistration(
                detector=self.detector,
                preprocessor=self.preprocessor,
                encoder=self.encoder,
                db_manager=self.db_manager
            )
            
            result = registration.register_from_camera(
                user_id=args.user_id,
                name=args.name or user['name'],
                photo_count=5
            )
            
            if result['status'] == 'success':
                print(f"\n✓ Re-registration successful")
            else:
                print(f"\n✗ Re-registration failed: {result['message']}")
    
    def cmd_stats(self, args):
        """Show database statistics."""
        stats = self.db_manager.get_database_stats()
        
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"\nTotal Users: {stats['total_users']}")
        print(f"Embedding Dimension: {stats['embedding_dim']}")
        print(f"Database Size: {stats['database_size_bytes'] / 1024:.2f} KB")
        print(f"Created: {stats['created_at'][:10]}")
        print(f"Last Updated: {stats['last_updated'][:10]}")
        print("="*60)
    
    def cmd_export(self, args):
        """Export database."""
        print(f"\n⏳ Exporting database to {args.output}...")
        
        if args.format == 'json':
            self.db_manager.export_to_json(args.output)
        else:
            print(f"✗ Format '{args.format}' not supported yet")
            return
        
        print(f"✓ Database exported successfully")
    
    def cmd_import(self, args):
        """Import database dari file."""
        if not os.path.exists(args.input):
            print(f"\n✗ File not found: {args.input}")
            return
        
        print(f"\n⏳ Importing database from {args.input}...")
        
        # Confirm if not merge
        if not args.merge:
            confirm = input("This will replace the current database. Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("✗ Import cancelled")
                return
        
        try:
            self.db_manager.import_from_json(args.input)
            print(f"✓ Database imported successfully")
        except Exception as e:
            print(f"✗ Import failed: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        if self.camera_handler:
            self.camera_handler.stop_camera()
        if self.db_manager:
            self.db_manager.save_database()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Face Recognition System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register new user')
    register_parser.add_argument('--name', required=True, help='User name')
    register_parser.add_argument('--user-id', help='User ID (auto-generated if not provided)')
    register_parser.add_argument('--photos', type=int, default=5, help='Number of photos to capture')
    register_parser.add_argument('--from-file', help='Register from image file')
    
    # Recognize command
    recognize_parser = subparsers.add_parser('recognize', help='Start live recognition')
    recognize_parser.add_argument('--camera-id', type=int, default=0, help='Camera ID')
    recognize_parser.add_argument('--threshold', type=float, default=0.6, help='Similarity threshold')
    recognize_parser.add_argument('--fps', type=int, default=30, help='Target FPS')
    recognize_parser.add_argument('--save-log', action='store_true', help='Enable logging')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test recognition from image')
    test_parser.add_argument('--image-path', required=True, help='Path to image file')
    test_parser.add_argument('--show', action='store_true', default=True, help='Display result')
    test_parser.add_argument('--save', action='store_true', help='Save annotated image')
    
    # List users command
    list_parser = subparsers.add_parser('list-users', help='List all registered users')
    list_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Output format')
    
    # Delete user command
    delete_parser = subparsers.add_parser('delete-user', help='Delete user from database')
    delete_parser.add_argument('--user-id', required=True, help='User ID to delete')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Update user command
    update_parser = subparsers.add_parser('update-user', help='Update user data')
    update_parser.add_argument('--user-id', required=True, help='User ID')
    update_parser.add_argument('--name', help='New name')
    update_parser.add_argument('--re-register', action='store_true', help='Capture new photos')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export database')
    export_parser.add_argument('--output', required=True, help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import database')
    import_parser.add_argument('--input', required=True, help='Input file path')
    import_parser.add_argument('--merge', action='store_true', help='Merge with existing database')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize app
    try:
        app = FaceRecognitionApp()
        
        # Execute command
        command_map = {
            'register': app.cmd_register,
            'recognize': app.cmd_recognize,
            'test': app.cmd_test,
            'list-users': app.cmd_list_users,
            'delete-user': app.cmd_delete_user,
            'update-user': app.cmd_update_user,
            'stats': app.cmd_stats,
            'export': app.cmd_export,
            'import': app.cmd_import
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        
        # Cleanup
        app.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
