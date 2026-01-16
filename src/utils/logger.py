import os
import json
import sqlite3
import cv2
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
import warnings


class RecognitionLogger:
    """
    Comprehensive logging system untuk face recognition events.
    Track recognition history, system events, dan generate analytics.
    """
    
    def __init__(self, log_dir='logs', config=None):
        """
        Initialize recognition logger.
        
        Args:
            log_dir (str): Base directory untuk logs
            config (dict): Configuration untuk logging behavior
        """
        self.log_dir = log_dir
        
        # Default config
        default_config = {
            'save_snapshots': False,
            'snapshot_rules': {
                'high_confidence': True,  # Save jika confidence > 0.9
                'unknown_only': False,
                'quality_threshold': 0.8
            },
            'retention_days': 30,
            'enable_alerts': False,
            'compress_snapshots': True
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Setup directory structure
        self._setup_directories()
        
        # Initialize database
        self.db_path = os.path.join(log_dir, 'recognition_logs.db')
        self._init_database()
        
        print(f"✓ Logger initialized: {log_dir}")
    
    def _setup_directories(self):
        """Create directory structure untuk logs."""
        dirs = [
            self.log_dir,
            os.path.join(self.log_dir, 'events'),
            os.path.join(self.log_dir, 'system'),
            os.path.join(self.log_dir, 'errors'),
            os.path.join(self.log_dir, 'snapshots')
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database untuk structured logging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recognition events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recognition_events (
                event_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                user_id TEXT,
                name TEXT,
                confidence REAL,
                similarity_score REAL,
                detection_confidence REAL,
                camera_id INTEGER,
                frame_number INTEGER,
                processing_time_ms REAL,
                face_box_x INTEGER,
                face_box_y INTEGER,
                face_box_w INTEGER,
                face_box_h INTEGER,
                success BOOLEAN,
                snapshot_path TEXT
            )
        ''')
        
        # Registration events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registration_events (
                registration_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                user_id TEXT,
                name TEXT,
                photo_count INTEGER,
                status TEXT,
                quality_score REAL
            )
        ''')
        
        # System events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                event_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                event_type TEXT,
                level TEXT,
                message TEXT,
                details TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON recognition_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON recognition_events(user_id)')
        
        conn.commit()
        conn.close()
    
    def log_recognition_event(self, event_data):
        """
        Log recognition event.
        
        Args:
            event_data (dict): Event data dengan keys:
                - event_id, timestamp, user_id, name, confidence, etc.
        """
        # Ensure event_id dan timestamp
        if 'event_id' not in event_data:
            event_data['event_id'] = str(uuid.uuid4())
        
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.now()
        
        # Write ke database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        face_box = event_data.get('face_box', [0, 0, 0, 0])
        
        cursor.execute('''
            INSERT INTO recognition_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data['event_id'],
            event_data['timestamp'],
            event_data.get('user_id', 'unknown'),
            event_data.get('name', 'Unknown'),
            event_data.get('confidence', 0.0),
            event_data.get('similarity_score', 0.0),
            event_data.get('detection_confidence', 0.0),
            event_data.get('camera_id', 0),
            event_data.get('frame_number', 0),
            event_data.get('processing_time_ms', 0.0),
            face_box[0], face_box[1], face_box[2], face_box[3],
            event_data.get('success', True),
            event_data.get('snapshot_path', None)
        ))
        
        conn.commit()
        conn.close()
        
        # Also write ke JSON Lines file (daily)
        date_str = event_data['timestamp'].strftime('%Y-%m-%d')
        json_path = os.path.join(self.log_dir, 'events', f'events_{date_str}.jsonl')
        
        with open(json_path, 'a') as f:
            # Convert datetime to string untuk JSON
            event_copy = event_data.copy()
            event_copy['timestamp'] = event_copy['timestamp'].isoformat()
            f.write(json.dumps(event_copy) + '\n')
    
    def log_registration_event(self, registration_data):
        """
        Log user registration event.
        
        Args:
            registration_data (dict): Registration data
        """
        reg_id = registration_data.get('registration_id', str(uuid.uuid4()))
        timestamp = registration_data.get('timestamp', datetime.now())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registration_events VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            reg_id,
            timestamp,
            registration_data['user_id'],
            registration_data['name'],
            registration_data.get('photo_count', 0),
            registration_data.get('status', 'success'),
            registration_data.get('quality_score', 0.0)
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Logged registration: {registration_data['name']}")
    
    def log_system_event(self, event_type, message, level='INFO', **kwargs):
        """
        Log system event.
        
        Args:
            event_type (str): Type of event
            message (str): Event message
            level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional details
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_events VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event_id,
            timestamp,
            event_type,
            level,
            message,
            json.dumps(kwargs)
        ))
        
        conn.commit()
        conn.close()
        
        # Also write ke file
        date_str = timestamp.strftime('%Y-%m-%d')
        log_path = os.path.join(self.log_dir, 'system', f'system_{date_str}.log')
        
        with open(log_path, 'a') as f:
            f.write(f"[{timestamp.isoformat()}] [{level}] {event_type}: {message}\n")
    
    def log_error(self, error, context=None):
        """
        Log error dengan stack trace.
        
        Args:
            error (Exception): Exception object
            context (dict): Additional context
        """
        import traceback
        
        error_msg = str(error)
        stack_trace = traceback.format_exc()
        
        self.log_system_event(
            event_type='ERROR',
            message=error_msg,
            level='ERROR',
            stack_trace=stack_trace,
            context=context or {}
        )
        
        # Write ke error log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        error_path = os.path.join(self.log_dir, 'errors', f'errors_{date_str}.log')
        
        with open(error_path, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{datetime.now().isoformat()}]\n")
            f.write(f"Error: {error_msg}\n")
            if context:
                f.write(f"Context: {json.dumps(context, indent=2)}\n")
            f.write(f"\nStack Trace:\n{stack_trace}\n")
    
    def save_snapshot(self, frame, event_id, user_id, confidence):
        """
        Save frame snapshot.
        
        Args:
            frame (numpy.ndarray): Frame image
            event_id (str): Event ID
            user_id (str): User ID
            confidence (float): Recognition confidence
        """
        if not self.config['save_snapshots']:
            return None
        
        # Check snapshot rules
        rules = self.config['snapshot_rules']
        
        should_save = False
        
        if rules['high_confidence'] and confidence > 0.9:
            should_save = True
        
        if rules['unknown_only'] and user_id == 'unknown':
            should_save = True
        
        if confidence >= rules['quality_threshold']:
            should_save = True
        
        if not should_save:
            return None
        
        # Create date folder
        date_str = datetime.now().strftime('%Y-%m-%d')
        snapshot_dir = os.path.join(self.log_dir, 'snapshots', date_str)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Filename
        filename = f"{event_id}_{user_id}_{confidence:.2f}.jpg"
        filepath = os.path.join(snapshot_dir, filename)
        
        # Save image
        cv2.imwrite(filepath, frame)
        
        return filepath
    
    def get_recognition_history(self, filters=None, limit=None):
        """
        Get recognition history dengan filters.
        
        Args:
            filters (dict): Filter criteria
            limit (int): Maximum results
        
        Returns:
            list: List of recognition events
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM recognition_events WHERE 1=1"
        params = []
        
        if filters:
            if 'user_id' in filters:
                query += " AND user_id = ?"
                params.append(filters['user_id'])
            
            if 'start_date' in filters:
                query += " AND timestamp >= ?"
                params.append(filters['start_date'])
            
            if 'end_date' in filters:
                query += " AND timestamp <= ?"
                params.append(filters['end_date'])
            
            if 'min_confidence' in filters:
                query += " AND confidence >= ?"
                params.append(filters['min_confidence'])
            
            if 'camera_id' in filters:
                query += " AND camera_id = ?"
                params.append(filters['camera_id'])
            
            if 'success_only' in filters and filters['success_only']:
                query += " AND success = 1"
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        
        return results
    
    def get_user_history(self, user_id, limit=100):
        """
        Get recognition history untuk specific user.
        
        Args:
            user_id (str): User ID
            limit (int): Maximum results
        
        Returns:
            list: User's recognition history
        """
        return self.get_recognition_history(
            filters={'user_id': user_id},
            limit=limit
        )
    
    def export_logs(self, output_path, format='csv', filters=None):
        """
        Export logs ke file.
        
        Args:
            output_path (str): Output file path
            format (str): Export format (csv, json)
            filters (dict): Filter criteria
        """
        history = self.get_recognition_history(filters=filters)
        
        if format == 'csv':
            import csv
            
            if not history:
                print("⚠ No data to export")
                return
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=history[0].keys())
                writer.writeheader()
                writer.writerows(history)
        
        elif format == 'json':
            with open(output_path, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        
        print(f"✓ Exported {len(history)} records to {output_path}")
    
    def get_statistics(self, time_period='today', detailed=False):
        """
        Generate statistics dari logs.
        
        Args:
            time_period (str): Time period ('today', 'week', 'month', 'all')
            detailed (bool): Include detailed breakdown
        
        Returns:
            dict: Statistics
        """
        # Determine date range
        now = datetime.now()
        
        if time_period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == 'yesterday':
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_date = now.replace(hour=0, minute=0, second=0)
        elif time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = datetime(2000, 1, 1)
        
        # Get history
        filters = {'start_date': start_date}
        if time_period == 'yesterday':
            filters['end_date'] = end_date
        
        history = self.get_recognition_history(filters=filters)
        
        if not history:
            return {
                'total_recognitions': 0,
                'successful_recognitions': 0,
                'unknown_detections': 0,
                'unique_persons': 0
            }
        
        # Calculate statistics
        total = len(history)
        successful = sum(1 for h in history if h['user_id'] != 'unknown')
        unknown = total - successful
        unique_persons = len(set(h['user_id'] for h in history if h['user_id'] != 'unknown'))
        
        confidences = [h['confidence'] for h in history if h['confidence'] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        processing_times = [h['processing_time_ms'] for h in history if h['processing_time_ms'] > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Peak hour analysis
        hours = defaultdict(int)
        for h in history:
            hour = datetime.fromisoformat(h['timestamp']).hour if isinstance(h['timestamp'], str) else h['timestamp'].hour
            hours[hour] += 1
        
        peak_hour = max(hours.items(), key=lambda x: x[1])[0] if hours else 0
        
        # Top users
        user_counts = defaultdict(int)
        for h in history:
            if h['user_id'] != 'unknown':
                user_counts[h['name']] += 1
        
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats = {
            'total_recognitions': total,
            'successful_recognitions': successful,
            'unknown_detections': unknown,
            'unique_persons': unique_persons,
            'avg_confidence': avg_confidence,
            'avg_processing_time_ms': avg_processing_time,
            'peak_hour': peak_hour,
            'top_users': top_users
        }
        
        return stats
    
    def get_daily_summary(self, date=None):
        """
        Get summary untuk specific date.
        
        Args:
            date (datetime): Date (default: today)
        
        Returns:
            dict: Daily summary
        """
        if date is None:
            date = datetime.now()
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        history = self.get_recognition_history(filters={
            'start_date': start,
            'end_date': end
        })
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'total_events': len(history),
            'unique_persons': len(set(h['user_id'] for h in history if h['user_id'] != 'unknown'))
        }
    
    def cleanup_old_logs(self, retention_days=30):
        """
        Delete logs older than retention period.
        
        Args:
            retention_days (int): Number of days to keep
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old recognition events
        cursor.execute('DELETE FROM recognition_events WHERE timestamp < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✓ Cleaned up {deleted_count} old log entries")
        
        self.log_system_event(
            event_type='CLEANUP',
            message=f'Deleted {deleted_count} logs older than {retention_days} days',
            level='INFO'
        )


# Example usage
if __name__ == "__main__":
    # Initialize logger
    logger = RecognitionLogger(
        log_dir='logs',
        config={
            'save_snapshots': True,
            'snapshot_rules': {
                'high_confidence': True,
                'unknown_only': False,
                'quality_threshold': 0.8
            },
            'retention_days': 30
        }
    )
    
    # Log sample recognition event
    logger.log_recognition_event({
        'event_id': str(uuid.uuid4()),
        'timestamp': datetime.now(),
        'user_id': 'user_001',
        'name': 'Alice',
        'confidence': 0.87,
        'similarity_score': 0.89,
        'detection_confidence': 0.95,
        'camera_id': 0,
        'frame_number': 1523,
        'processing_time_ms': 45.2,
        'face_box': [120, 80, 200, 200],
        'success': True
    })
    
    # Get statistics
    stats = logger.get_statistics(time_period='today', detailed=True)
    
    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    print(f"Total recognitions: {stats['total_recognitions']}")
    print(f"Successful: {stats['successful_recognitions']}")
    print(f"Unknown: {stats['unknown_detections']}")
    print(f"Unique persons: {stats['unique_persons']}")
    print(f"Average confidence: {stats['avg_confidence']:.2%}")
    print(f"Peak hour: {stats['peak_hour']}:00")
    
    if stats['top_users']:
        print("\nTop Users:")
        for name, count in stats['top_users']:
            print(f"  {name}: {count} times")
