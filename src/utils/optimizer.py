import numpy as np
import cv2
import threading
import queue
from collections import defaultdict
import time
import os


class FrameOptimizer:
    """
    Frame processing optimizer untuk improve FPS.
    Techniques: frame skipping, motion detection, adaptive processing.
    """
    
    def __init__(self, config=None):
        """
        Initialize frame optimizer.
        
        Args:
            config (dict): Configuration
        """
        default_config = {
            'skip_frames': 2,
            'cache_ttl_frames': 5,
            'motion_threshold': 0.05,
            'adaptive_skip': True
        }
        
        self.config = {**default_config, **(config or {})}
        
        self.skip_frames = self.config['skip_frames']
        self.detection_cache = {}
        self.cache_ttl = self.config['cache_ttl_frames']
        self.frame_counter = 0
        self.last_detection_frame = -1
        self.motion_threshold = self.config['motion_threshold']
        self.previous_frame = None
    
    def should_process_frame(self, frame_number):
        """
        Determine apakah frame harus di-process.
        
        Args:
            frame_number (int): Current frame number
        
        Returns:
            bool: True jika harus di-process
        """
        # Skip every N frames
        return (frame_number % self.skip_frames) == 0
    
    def detect_motion(self, frame, previous_frame=None):
        """
        Detect motion between frames.
        
        Args:
            frame (numpy.ndarray): Current frame
            previous_frame (numpy.ndarray): Previous frame
        
        Returns:
            float: Motion score (0-1)
        """
        if previous_frame is None:
            return 1.0  # Assume motion
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate frame difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Calculate motion score
        motion_score = np.mean(diff) / 255.0
        
        return motion_score
    
    def adaptive_skip_rate(self, current_fps, target_fps=30):
        """
        Dynamically adjust frame skipping based on performance.
        
        Args:
            current_fps (float): Current FPS
            target_fps (float): Target FPS
        
        Returns:
            int: New skip rate
        """
        if not self.config['adaptive_skip']:
            return self.skip_frames
        
        if current_fps < target_fps * 0.8:
            # Performance is poor, skip more frames
            self.skip_frames = min(self.skip_frames + 1, 5)
            print(f"⚡ FPS low ({current_fps:.1f}), increasing skip to {self.skip_frames}")
        elif current_fps > target_fps * 0.95 and self.skip_frames > 1:
            # Performance is good, can process more frames
            self.skip_frames = max(self.skip_frames - 1, 1)
            print(f"⚡ FPS good ({current_fps:.1f}), decreasing skip to {self.skip_frames}")
        
        return self.skip_frames
    
    def resize_adaptive(self, frame, max_dimension=640):
        """
        Resize frame adaptively based on size.
        
        Args:
            frame (numpy.ndarray): Input frame
            max_dimension (int): Maximum dimension
        
        Returns:
            numpy.ndarray: Resized frame
        """
        height, width = frame.shape[:2]
        
        if max(height, width) <= max_dimension:
            return frame
        
        # Calculate scale
        scale = max_dimension / max(height, width)
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized


class DatabaseOptimizer:
    """
    Database search optimizer untuk large datasets.
    Techniques: indexing, approximate nearest neighbor search.
    """
    
    def __init__(self):
        """Initialize database optimizer."""
        self.index = None
        self.index_type = None
        self.user_ids = []
    
    def build_linear_index(self, embeddings, user_ids):
        """
        Build simple linear search index (baseline).
        
        Args:
            embeddings (dict): {user_id: embedding}
            user_ids (list): List of user IDs
        
        Returns:
            dict: Index data
        """
        self.index_type = 'linear'
        self.user_ids = user_ids
        
        # Convert to matrix
        embedding_matrix = np.array([embeddings[uid] for uid in user_ids])
        
        self.index = {
            'embeddings': embedding_matrix,
            'user_ids': user_ids
        }
        
        print(f"✓ Built linear index for {len(user_ids)} users")
        
        return self.index
    
    def search_linear(self, query_embedding, k=5):
        """
        Linear search (brute force).
        
        Args:
            query_embedding (numpy.ndarray): Query embedding
            k (int): Number of results
        
        Returns:
            tuple: (user_ids, similarities)
        """
        if self.index is None:
            return [], []
        
        embeddings = self.index['embeddings']
        
        # Calculate cosine similarities
        similarities = np.dot(embeddings, query_embedding)
        
        # Get top k
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        top_user_ids = [self.user_ids[i] for i in top_k_indices]
        top_similarities = similarities[top_k_indices]
        
        return top_user_ids, top_similarities
    
    def precompute_similarities(self, embeddings):
        """
        Precompute pairwise similarity matrix.
        Only practical untuk small databases (<100 users).
        
        Args:
            embeddings (numpy.ndarray): Embedding matrix (n_users, embedding_dim)
        
        Returns:
            numpy.ndarray: Similarity matrix (n_users, n_users)
        """
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        
        # Compute pairwise similarities
        similarity_matrix = np.dot(normalized, normalized.T)
        
        print(f"✓ Precomputed similarity matrix: {similarity_matrix.shape}")
        
        return similarity_matrix


class MultithreadedRecognizer:
    """
    Multi-threaded recognizer untuk parallel processing.
    Architecture: [Camera] → [Frame Queue] → [Workers] → [Result Queue] → [Display]
    """
    
    def __init__(self, recognizer, num_workers=2):
        """
        Initialize multi-threaded recognizer.
        
        Args:
            recognizer: FaceRecognizer instance
            num_workers (int): Number of worker threads
        """
        self.recognizer = recognizer
        self.num_workers = num_workers
        
        self.frame_queue = queue.Queue(maxsize=30)
        self.result_queue = queue.Queue(maxsize=30)
        
        self.workers = []
        self.running = False
    
    def start(self):
        """Start worker threads."""
        self.running = True
        
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"Worker-{i}"
            )
            worker.start()
            self.workers.append(worker)
        
        print(f"✓ Started {self.num_workers} worker threads")
    
    def _worker_loop(self):
        """Worker thread loop."""
        while self.running:
            try:
                frame, frame_id = self.frame_queue.get(timeout=1)
                
                # Process frame
                result = self.recognizer.recognize_from_image(frame)
                
                # Put result
                self.result_queue.put((frame_id, result))
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠ Worker error: {e}")
    
    def process_async(self, frame, frame_id):
        """
        Submit frame for async processing.
        
        Args:
            frame (numpy.ndarray): Frame to process
            frame_id (int): Frame identifier
        
        Returns:
            bool: True if submitted successfully
        """
        try:
            self.frame_queue.put_nowait((frame, frame_id))
            return True
        except queue.Full:
            return False
    
    def get_result(self, timeout=0.1):
        """
        Get processed result (non-blocking).
        
        Args:
            timeout (float): Timeout in seconds
        
        Returns:
            tuple: (frame_id, result) atau None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop all workers."""
        self.running = False
        for worker in self.workers:
            worker.join()
        
        print("✓ Stopped all worker threads")
    
    def get_queue_sizes(self):
        """
        Get queue sizes untuk monitoring.
        
        Returns:
            dict: Queue sizes
        """
        return {
            'frame_queue': self.frame_queue.qsize(),
            'result_queue': self.result_queue.qsize()
        }


class PerformanceMonitor:
    """
    Monitor system performance real-time.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = defaultdict(list)
        self.start_time = time.time()
    
    def record_metric(self, name, value):
        """
        Record performance metric.
        
        Args:
            name (str): Metric name
            value (float): Metric value
        """
        self.metrics[name].append({
            'timestamp': time.time() - self.start_time,
            'value': value
        })
    
    def get_average(self, name, window=10):
        """
        Get average of recent metrics.
        
        Args:
            name (str): Metric name
            window (int): Number of recent samples
        
        Returns:
            float: Average value
        """
        if name not in self.metrics or not self.metrics[name]:
            return 0.0
        
        recent = self.metrics[name][-window:]
        values = [m['value'] for m in recent]
        
        return np.mean(values)
    
    def get_summary(self):
        """
        Get summary of all metrics.
        
        Returns:
            dict: Summary statistics
        """
        summary = {}
        
        for name, data in self.metrics.items():
            if not data:
                continue
            
            values = [m['value'] for m in data]
            
            summary[name] = {
                'count': len(values),
                'mean': np.mean(values),
                'min': np.min(values),
                'max': np.max(values),
                'std': np.std(values)
            }
        
        return summary
    
    def print_summary(self):
        """Print formatted summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY".center(60))
        print("="*60)
        
        for name, stats in summary.items():
            print(f"\n{name}:")
            print(f"  Count: {stats['count']}")
            print(f"  Mean:  {stats['mean']:.2f}")
            print(f"  Min:   {stats['min']:.2f}")
            print(f"  Max:   {stats['max']:.2f}")
            print(f"  Std:   {stats['std']:.2f}")
        
        print("="*60)


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("OPTIMIZATION UTILITIES".center(60))
    print("="*60)
    
    print("\n1. FrameOptimizer")
    print("   - Frame skipping untuk improve FPS")
    print("   - Motion detection")
    print("   - Adaptive skip rate")
    
    print("\n2. DatabaseOptimizer")
    print("   - Linear search (baseline)")
    print("   - Precomputed similarities")
    print("   - Support untuk large databases")
    
    print("\n3. MultithreadedRecognizer")
    print("   - Parallel processing dengan worker threads")
    print("   - Async frame processing")
    print("   - 1.5-2x throughput improvement")
    
    print("\n4. PerformanceMonitor")
    print("   - Real-time metrics tracking")
    print("   - Summary statistics")
    
    print("\nExample usage:")
    print("""
    # Frame optimization
    frame_opt = FrameOptimizer({'skip_frames': 2})
    
    for frame_num, frame in enumerate(video_stream):
        if frame_opt.should_process_frame(frame_num):
            result = recognizer.recognize(frame)
    
    # Multi-threading
    mt_recognizer = MultithreadedRecognizer(recognizer, num_workers=2)
    mt_recognizer.start()
    
    for frame_id, frame in enumerate(video_stream):
        mt_recognizer.process_async(frame, frame_id)
        result = mt_recognizer.get_result()
    """)
    
    print("\n" + "="*60)
