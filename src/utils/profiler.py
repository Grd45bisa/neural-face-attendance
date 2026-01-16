import time
import numpy as np
from collections import defaultdict
from datetime import datetime
import json
import os


class SystemProfiler:
    """
    System profiler untuk benchmarking dan performance analysis.
    """
    
    def __init__(self, recognizer, config=None):
        """
        Initialize system profiler.
        
        Args:
            recognizer: FaceRecognizer instance
            config (dict): Profiling configuration
        """
        self.recognizer = recognizer
        
        # Default config
        default_config = {
            'verbose': True,
            'save_results': True,
            'output_dir': 'reports'
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Storage untuk results
        self.results = {
            'pipeline': None,
            'fps': None,
            'memory': None,
            'gpu': None
        }
        
        # Create output directory
        if self.config['save_results']:
            os.makedirs(self.config['output_dir'], exist_ok=True)
    
    def profile_pipeline(self, test_images, iterations=10):
        """
        Profile complete pipeline performance.
        
        Args:
            test_images (list): List of test image paths
            iterations (int): Number of iterations per image
        
        Returns:
            dict: Profiling results
        """
        print("\n" + "="*64)
        print("PIPELINE PERFORMANCE PROFILE".center(64))
        print("="*64)
        print(f"Test Images: {len(test_images)}")
        print(f"Iterations: {iterations}")
        print(f"Total Samples: {len(test_images) * iterations}")
        print()
        
        # Storage untuk timing data
        timings = {
            'detection': [],
            'preprocessing': [],
            'encoding': [],
            'matching': [],
            'total': []
        }
        
        # Run profiling
        import cv2
        
        for img_path in test_images:
            image = cv2.imread(img_path)
            if image is None:
                continue
            
            for _ in range(iterations):
                # Total time
                total_start = time.time()
                
                # 1. Detection
                det_start = time.time()
                faces = self.recognizer.detector.detect_faces(image)
                det_time = (time.time() - det_start) * 1000
                timings['detection'].append(det_time)
                
                if not faces:
                    continue
                
                face = faces[0]
                
                # 2. Preprocessing
                prep_start = time.time()
                preprocessed = self.recognizer.preprocessor.preprocess(
                    image, face['box'], face['keypoints']
                )
                prep_time = (time.time() - prep_start) * 1000
                timings['preprocessing'].append(prep_time)
                
                # 3. Encoding
                enc_start = time.time()
                embedding = self.recognizer.encoder.encode_face(preprocessed)
                enc_time = (time.time() - enc_start) * 1000
                timings['encoding'].append(enc_time)
                
                # 4. Matching
                match_start = time.time()
                db_embeddings = self.recognizer.db_manager.get_all_embeddings()
                if db_embeddings:
                    _ = self.recognizer.matcher.find_best_match(embedding, db_embeddings)
                match_time = (time.time() - match_start) * 1000
                timings['matching'].append(match_time)
                
                # Total
                total_time = (time.time() - total_start) * 1000
                timings['total'].append(total_time)
        
        # Calculate statistics
        results = {
            'summary': {},
            'components': {},
            'raw_data': timings
        }
        
        # Calculate stats untuk each component
        for component, times in timings.items():
            if not times:
                continue
            
            times_array = np.array(times)
            
            stats = {
                'avg_ms': float(np.mean(times_array)),
                'min_ms': float(np.min(times_array)),
                'max_ms': float(np.max(times_array)),
                'std_ms': float(np.std(times_array)),
                'p50_ms': float(np.percentile(times_array, 50)),
                'p95_ms': float(np.percentile(times_array, 95)),
                'p99_ms': float(np.percentile(times_array, 99))
            }
            
            results['components'][component] = stats
        
        # Calculate percentages
        total_avg = results['components']['total']['avg_ms']
        for component in ['detection', 'preprocessing', 'encoding', 'matching']:
            if component in results['components']:
                comp_avg = results['components'][component]['avg_ms']
                results['components'][component]['percent'] = (comp_avg / total_avg) * 100
        
        # Summary
        results['summary'] = {
            'total_avg_ms': total_avg,
            'total_min_ms': results['components']['total']['min_ms'],
            'total_max_ms': results['components']['total']['max_ms'],
            'fps_estimate': 1000 / total_avg if total_avg > 0 else 0
        }
        
        # Find bottleneck
        bottleneck = max(
            [(k, v['avg_ms']) for k, v in results['components'].items() if k != 'total'],
            key=lambda x: x[1]
        )
        results['summary']['bottleneck'] = bottleneck[0]
        
        # Print results
        self._print_pipeline_results(results)
        
        # Save results
        self.results['pipeline'] = results
        if self.config['save_results']:
            self._save_json(results, 'pipeline_profile.json')
        
        return results
    
    def _print_pipeline_results(self, results):
        """Print formatted pipeline results."""
        print("\nComponent              Avg(ms)  Min(ms)  Max(ms)  StdDev   % Total")
        print("-" * 64)
        
        for component in ['detection', 'preprocessing', 'encoding', 'matching']:
            if component not in results['components']:
                continue
            
            stats = results['components'][component]
            name = component.capitalize()[:20].ljust(20)
            
            print(f"{name} {stats['avg_ms']:7.1f}  {stats['min_ms']:7.1f}  "
                  f"{stats['max_ms']:7.1f}  {stats['std_ms']:6.1f}  "
                  f"{stats.get('percent', 0):6.1f}%")
        
        print("-" * 64)
        total = results['components']['total']
        print(f"{'TOTAL PIPELINE':<20} {total['avg_ms']:7.1f}  {total['min_ms']:7.1f}  "
              f"{total['max_ms']:7.1f}  {total['std_ms']:6.1f}  100.0%")
        
        print(f"\nFPS Estimate: {results['summary']['fps_estimate']:.1f} fps")
        print(f"Primary Bottleneck: {results['summary']['bottleneck'].capitalize()}")
        
        print("\nRecommendations:")
        bottleneck = results['summary']['bottleneck']
        if bottleneck == 'encoding':
            print("• Consider model quantization untuk speed up embedding extraction")
            print("• Use GPU acceleration (estimated 2-3x speedup)")
        elif bottleneck == 'detection':
            print("• Consider using faster detector (Haar Cascade)")
            print("• Reduce input resolution")
        
        print("• Implement frame skipping (process every 2-3 frames)")
        print("="*64)
    
    def benchmark_fps(self, duration=60, camera_id=0):
        """
        Benchmark real-time FPS.
        
        Args:
            duration (int): Test duration in seconds
            camera_id (int): Camera ID
        
        Returns:
            dict: FPS benchmark results
        """
        print("\n" + "="*64)
        print("FPS BENCHMARK".center(64))
        print("="*64)
        print(f"Test Duration: {duration} seconds")
        print("Starting benchmark...\n")
        
        from tracking.camera_handler import CameraHandler
        
        camera = CameraHandler(camera_id=camera_id)
        
        if not camera.start_camera():
            print("✗ Failed to start camera")
            return None
        
        fps_samples = []
        frame_count = 0
        start_time = time.time()
        last_fps_time = start_time
        last_fps_count = 0
        
        scenario_counts = defaultdict(int)
        
        try:
            while (time.time() - start_time) < duration:
                ret, frame = camera.read_frame()
                
                if not ret:
                    continue
                
                frame_count += 1
                
                # Recognize
                result = self.recognizer.recognize_from_image(frame)
                
                # Track scenario
                if result['status'] == 'success':
                    face_count = len(result['results'])
                    if face_count == 0:
                        scenario_counts['no_face'] += 1
                    elif face_count == 1:
                        scenario_counts['single_face'] += 1
                    elif face_count == 2:
                        scenario_counts['2_faces'] += 1
                    else:
                        scenario_counts['3+_faces'] += 1
                
                # Calculate FPS every second
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    fps = (frame_count - last_fps_count) / (current_time - last_fps_time)
                    fps_samples.append(fps)
                    last_fps_time = current_time
                    last_fps_count = frame_count
                    
                    print(f"\rFPS: {fps:.1f} | Frames: {frame_count}", end='', flush=True)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Benchmark interrupted")
        finally:
            camera.stop_camera()
        
        # Calculate results
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        results = {
            'duration_sec': int(elapsed),
            'total_frames': frame_count,
            'avg_fps': avg_fps,
            'min_fps': min(fps_samples) if fps_samples else 0,
            'max_fps': max(fps_samples) if fps_samples else 0,
            'fps_over_time': fps_samples,
            'scenarios': {}
        }
        
        # Calculate scenario stats
        for scenario, count in scenario_counts.items():
            results['scenarios'][scenario] = {
                'frame_count': count,
                'percentage': (count / frame_count * 100) if frame_count > 0 else 0
            }
        
        # Print results
        self._print_fps_results(results)
        
        # Save
        self.results['fps'] = results
        if self.config['save_results']:
            self._save_json(results, 'fps_benchmark.json')
        
        return results
    
    def _print_fps_results(self, results):
        """Print formatted FPS results."""
        print("\n\n" + "="*64)
        print("FPS BENCHMARK RESULTS".center(64))
        print("="*64)
        print(f"Test Duration: {results['duration_sec']} seconds")
        print(f"Total Frames Processed: {results['total_frames']:,}")
        print()
        print("Overall Performance:")
        print(f"• Average FPS: {results['avg_fps']:.1f} fps")
        print(f"• Min FPS: {results['min_fps']:.1f} fps")
        print(f"• Max FPS: {results['max_fps']:.1f} fps")
        
        if results['scenarios']:
            print("\nScenario Breakdown:")
            print("┌" + "─"*20 + "┬" + "─"*13 + "┐")
            print("│ Scenario           │ Frame Count │")
            print("├" + "─"*20 + "┼" + "─"*13 + "┤")
            
            for scenario, data in results['scenarios'].items():
                name = scenario.replace('_', ' ').title()[:18].ljust(18)
                count = str(data['frame_count']).rjust(11)
                print(f"│ {name} │ {count} │")
            
            print("└" + "─"*20 + "┴" + "─"*13 + "┘")
        
        # Performance grade
        if results['avg_fps'] >= 25:
            grade = "A (Excellent)"
        elif results['avg_fps'] >= 20:
            grade = "B+ (Good)"
        elif results['avg_fps'] >= 15:
            grade = "B (Acceptable)"
        else:
            grade = "C (Needs Optimization)"
        
        print(f"\nPerformance Grade: {grade}")
        print("="*64)
    
    def get_statistics(self):
        """
        Get summary statistics dari all profiling.
        
        Returns:
            dict: Summary statistics
        """
        stats = {
            'pipeline': self.results.get('pipeline'),
            'fps': self.results.get('fps'),
            'timestamp': datetime.now().isoformat()
        }
        
        return stats
    
    def _save_json(self, data, filename):
        """Save results to JSON file."""
        filepath = os.path.join(self.config['output_dir'], filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to {filepath}")
    
    def generate_report(self, output_path=None):
        """
        Generate text report.
        
        Args:
            output_path (str): Output file path
        """
        if output_path is None:
            output_path = os.path.join(self.config['output_dir'], 'performance_report.txt')
        
        with open(output_path, 'w') as f:
            f.write("="*64 + "\n")
            f.write("FACE RECOGNITION SYSTEM - PERFORMANCE REPORT\n")
            f.write("="*64 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*64 + "\n\n")
            
            # Pipeline results
            if self.results['pipeline']:
                f.write("PIPELINE PROFILE\n")
                f.write("-"*64 + "\n")
                
                pipeline = self.results['pipeline']
                f.write(f"Average Total Time: {pipeline['summary']['total_avg_ms']:.1f} ms\n")
                f.write(f"Estimated FPS: {pipeline['summary']['fps_estimate']:.1f} fps\n")
                f.write(f"Bottleneck: {pipeline['summary']['bottleneck'].capitalize()}\n\n")
            
            # FPS results
            if self.results['fps']:
                f.write("FPS BENCHMARK\n")
                f.write("-"*64 + "\n")
                
                fps = self.results['fps']
                f.write(f"Duration: {fps['duration_sec']} seconds\n")
                f.write(f"Total Frames: {fps['total_frames']}\n")
                f.write(f"Average FPS: {fps['avg_fps']:.1f} fps\n")
                f.write(f"Min FPS: {fps['min_fps']:.1f} fps\n")
                f.write(f"Max FPS: {fps['max_fps']:.1f} fps\n\n")
        
        print(f"✓ Report saved to {output_path}")


# Example usage
if __name__ == "__main__":
    print("SystemProfiler - Performance Profiling Tool")
    print("="*64)
    print("\nThis tool requires a FaceRecognizer instance.")
    print("Example usage:")
    print("""
    from src.utils.profiler import SystemProfiler
    
    # Initialize profiler
    profiler = SystemProfiler(face_recognizer)
    
    # Profile pipeline
    results = profiler.profile_pipeline(test_images=['test1.jpg', 'test2.jpg'])
    
    # Benchmark FPS
    fps_results = profiler.benchmark_fps(duration=30)
    
    # Generate report
    profiler.generate_report()
    """)
