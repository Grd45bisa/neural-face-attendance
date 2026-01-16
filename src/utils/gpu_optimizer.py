"""
GPU Optimizer - Auto-detect dan configure optimal device
Priority: NVIDIA GPU > AMD Radeon Vega > CPU
"""

import os
import tensorflow as tf
from tensorflow.keras import mixed_precision
import warnings


class GPUOptimizer:
    """
    Auto-detect dan configure optimal computing device.
    Supports: NVIDIA GPU (CUDA), AMD Radeon (ROCm/DirectML), CPU fallback.
    """
    
    def __init__(self, verbose=True):
        """
        Initialize GPU optimizer dengan auto-detection.
        
        Args:
            verbose (bool): Print detailed detection info
        """
        self.verbose = verbose
        self.device_type = None
        self.device_name = None
        self.device_info = {}
        self.recommended_config = {}
        
        # Auto-detect dan configure optimal device
        self._configure_optimal_gpu()
    
    def _print(self, message):
        """Print message jika verbose enabled."""
        if self.verbose:
            print(message)
    
    def _detect_nvidia_gpu(self):
        """
        Detect NVIDIA GPU dengan CUDA support.
        
        Returns:
            tuple: (has_nvidia, gpu_list, gpu_name)
        """
        self._print("\n" + "="*60)
        self._print("NVIDIA GPU DETECTION".center(60))
        self._print("="*60)
        
        try:
            # Check if CUDA is built
            if not tf.test.is_built_with_cuda():
                self._print("✗ TensorFlow not built with CUDA support")
                self._print("  Install: pip install tensorflow[and-cuda]")
                return False, [], None
            
            # Detect NVIDIA GPUs
            gpus = tf.config.list_physical_devices('GPU')
            
            if gpus:
                gpu_name = gpus[0].name
                self._print(f"✓ NVIDIA GPU detected: {len(gpus)} device(s)")
                self._print(f"  GPU 0: {gpu_name}")
                
                # Try to get GPU name from nvidia-smi
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        gpu_model = result.stdout.strip().split('\n')[0]
                        self._print(f"  Model: {gpu_model}")
                        gpu_name = gpu_model
                except:
                    pass
                
                self._print("  ✓ CUDA support: Available")
                return True, gpus, gpu_name
            else:
                self._print("✗ No NVIDIA GPU detected")
                return False, [], None
                
        except Exception as e:
            self._print(f"✗ NVIDIA detection error: {e}")
            return False, [], None
    
    def _detect_amd_gpu(self):
        """
        Detect AMD Radeon GPU (Vega 7 integrated).
        
        Returns:
            tuple: (has_amd, gpu_info)
        """
        self._print("\n" + "="*60)
        self._print("AMD RADEON GPU DETECTION".center(60))
        self._print("="*60)
        
        try:
            # Check for AMD GPU via TensorFlow
            # Note: AMD support via DirectML on Windows or ROCm on Linux
            gpus = tf.config.list_physical_devices('GPU')
            
            if gpus:
                # Check if it's AMD (not NVIDIA)
                gpu_name = str(gpus[0].name).lower()
                if 'amd' in gpu_name or 'radeon' in gpu_name or 'vega' in gpu_name:
                    self._print(f"✓ AMD Radeon GPU detected")
                    self._print(f"  GPU: {gpus[0].name}")
                    self._print(f"  Type: Integrated Graphics (Vega 7)")
                    return True, {'name': 'AMD Radeon Vega 7', 'type': 'integrated'}
            
            # Fallback: Check via DirectML (Windows)
            try:
                # DirectML detection (Windows only)
                self._print("  Checking DirectML support...")
                # This is a placeholder - actual DirectML detection would need tensorflow-directml
                self._print("  ⚠ DirectML not configured")
            except:
                pass
            
            self._print("✗ No AMD Radeon GPU detected")
            return False, None
            
        except Exception as e:
            self._print(f"✗ AMD detection error: {e}")
            return False, None
    
    def _configure_nvidia_gpu(self, gpus):
        """
        Configure NVIDIA GPU untuk optimal performance.
        
        Args:
            gpus (list): List of GPU devices
        """
        self._print("\n" + "="*60)
        self._print("NVIDIA GPU CONFIGURATION".center(60))
        self._print("="*60)
        
        try:
            # Enable memory growth
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
                self._print(f"✓ Memory growth enabled for {gpu.name}")
            
            # Enable XLA (Accelerated Linear Algebra)
            tf.config.optimizer.set_jit(True)
            self._print("✓ XLA optimization enabled")
            
            # Enable Mixed Precision (FP16)
            policy = mixed_precision.Policy('mixed_float16')
            mixed_precision.set_global_policy(policy)
            self._print("✓ Mixed Precision (FP16) enabled")
            
            # Set environment variables
            os.environ['TF_GPU_THREAD_MODE'] = 'gpu_private'
            self._print("✓ GPU thread mode: gpu_private")
            
            self.device_type = 'nvidia_gpu'
            self.device_name = 'NVIDIA GPU (CUDA)'
            
            # Recommended config
            self.recommended_config = {
                'camera_resolution': (1280, 720),
                'target_fps': 30,
                'frame_skip': 2,
                'batch_size': 4,
                'recognition_threshold': 0.6,
                'enable_mixed_precision': True,
                'expected_speedup': '5-10x vs CPU',
                'performance_profile': 'high'
            }
            
            self._print("\n✓ NVIDIA GPU configuration complete")
            self._print(f"  Expected performance: {self.recommended_config['expected_speedup']}")
            
        except Exception as e:
            self._print(f"✗ NVIDIA configuration error: {e}")
            self._print("  Falling back to CPU...")
            self._configure_cpu_fallback()
    
    def _configure_amd_gpu(self, gpu_info):
        """
        Configure AMD Radeon Vega 7 untuk optimal performance.
        
        Args:
            gpu_info (dict): AMD GPU information
        """
        self._print("\n" + "="*60)
        self._print("AMD RADEON GPU CONFIGURATION".center(60))
        self._print("="*60)
        
        try:
            gpus = tf.config.list_physical_devices('GPU')
            
            if gpus:
                # Enable memory growth
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                    self._print(f"✓ Memory growth enabled for {gpu.name}")
                
                # Set memory limit (1536MB for Vega 7 shared memory)
                try:
                    tf.config.set_logical_device_configuration(
                        gpus[0],
                        [tf.config.LogicalDeviceConfiguration(memory_limit=1536)]
                    )
                    self._print("✓ Memory limit set: 1536MB (shared)")
                except:
                    self._print("⚠ Could not set memory limit")
                
                # Set environment variables
                os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
                self._print("✓ Force GPU allow growth: enabled")
            
            self.device_type = 'amd_gpu'
            self.device_name = 'AMD Radeon Vega 7'
            
            # Recommended config untuk Vega 7
            self.recommended_config = {
                'camera_resolution': (640, 480),
                'target_fps': 20,
                'frame_skip': 4,
                'batch_size': 2,
                'recognition_threshold': 0.65,
                'enable_mixed_precision': False,
                'memory_limit_mb': 1536,
                'expected_speedup': '2-3x vs CPU',
                'performance_profile': 'medium'
            }
            
            self._print("\n✓ AMD Radeon configuration complete")
            self._print(f"  Expected performance: {self.recommended_config['expected_speedup']}")
            
        except Exception as e:
            self._print(f"✗ AMD configuration error: {e}")
            self._print("  Falling back to CPU...")
            self._configure_cpu_fallback()
    
    def _configure_cpu_fallback(self):
        """
        Configure CPU (Ryzen 3 Gen 5) untuk optimal performance.
        """
        self._print("\n" + "="*60)
        self._print("CPU CONFIGURATION (FALLBACK)".center(60))
        self._print("="*60)
        
        try:
            # Set threading untuk Ryzen 3 (4 cores / 8 threads)
            tf.config.threading.set_inter_op_parallelism_threads(2)
            tf.config.threading.set_intra_op_parallelism_threads(4)
            self._print("✓ Threading configured: 2 inter + 4 intra threads")
            
            # Enable oneDNN optimizations
            os.environ['TF_ENABLE_ONEDNN_OPTS'] = '1'
            os.environ['OMP_NUM_THREADS'] = '4'
            self._print("✓ oneDNN optimizations enabled")
            self._print("✓ OpenMP threads: 4")
            
            self.device_type = 'cpu'
            self.device_name = 'AMD Ryzen 3 Gen 5 (CPU)'
            
            # Recommended config untuk CPU
            self.recommended_config = {
                'camera_resolution': (640, 480),
                'target_fps': 12,
                'frame_skip': 6,
                'batch_size': 1,
                'recognition_threshold': 0.7,
                'enable_mixed_precision': False,
                'cpu_threads': 4,
                'expected_speedup': '1x (baseline)',
                'performance_profile': 'low'
            }
            
            self._print("\n✓ CPU configuration complete")
            self._print(f"  Performance: {self.recommended_config['expected_speedup']}")
            self._print("  ⚠ For better performance, consider GPU setup")
            
        except Exception as e:
            self._print(f"✗ CPU configuration error: {e}")
            # Use defaults
            self.device_type = 'cpu'
            self.device_name = 'CPU (Default)'
            self.recommended_config = {
                'camera_resolution': (640, 480),
                'target_fps': 10,
                'frame_skip': 6,
                'batch_size': 1,
                'performance_profile': 'low'
            }
    
    def _configure_optimal_gpu(self):
        """
        Main orchestrator - detect dan configure optimal device.
        Priority: NVIDIA GPU > AMD Radeon > CPU
        """
        self._print("\n" + "="*70)
        self._print("AUTO GPU OPTIMIZER".center(70))
        self._print("="*70)
        self._print("Priority: NVIDIA GPU > AMD Radeon Vega 7 > CPU")
        self._print("="*70)
        
        # Try NVIDIA GPU first
        has_nvidia, nvidia_gpus, nvidia_name = self._detect_nvidia_gpu()
        if has_nvidia:
            self._configure_nvidia_gpu(nvidia_gpus)
            self.device_info = {
                'type': 'nvidia_gpu',
                'name': nvidia_name or 'NVIDIA GPU',
                'count': len(nvidia_gpus),
                'cuda_available': True
            }
            return
        
        # Try AMD Radeon second
        has_amd, amd_info = self._detect_amd_gpu()
        if has_amd:
            self._configure_amd_gpu(amd_info)
            self.device_info = {
                'type': 'amd_gpu',
                'name': amd_info['name'],
                'gpu_type': amd_info['type']
            }
            return
        
        # Fallback to CPU
        self._print("\n⚠ No GPU detected, using CPU")
        self._configure_cpu_fallback()
        self.device_info = {
            'type': 'cpu',
            'name': 'AMD Ryzen 3 Gen 5',
            'cores': 4,
            'threads': 8
        }
    
    def get_device_info(self):
        """
        Get detected device information.
        
        Returns:
            dict: Device information
        """
        return {
            'device_type': self.device_type,
            'device_name': self.device_name,
            'device_info': self.device_info,
            'config': self.recommended_config
        }
    
    def get_recommended_config(self):
        """
        Get recommended configuration untuk detected device.
        
        Returns:
            dict: Recommended settings
        """
        return self.recommended_config
    
    def print_summary(self):
        """Print formatted summary of detection dan configuration."""
        print("\n" + "="*70)
        print("DEVICE CONFIGURATION SUMMARY".center(70))
        print("="*70)
        print(f"Device Type:     {self.device_type.upper()}")
        print(f"Device Name:     {self.device_name}")
        print(f"Performance:     {self.recommended_config.get('performance_profile', 'N/A').upper()}")
        print()
        print("Recommended Settings:")
        print(f"  Resolution:    {self.recommended_config.get('camera_resolution', 'N/A')}")
        print(f"  Target FPS:    {self.recommended_config.get('target_fps', 'N/A')}")
        print(f"  Frame Skip:    Every {self.recommended_config.get('frame_skip', 'N/A')} frames")
        print(f"  Batch Size:    {self.recommended_config.get('batch_size', 'N/A')}")
        print(f"  Threshold:     {self.recommended_config.get('recognition_threshold', 'N/A')}")
        print(f"  Mixed Precision: {self.recommended_config.get('enable_mixed_precision', False)}")
        print()
        print(f"Expected Speedup: {self.recommended_config.get('expected_speedup', 'N/A')}")
        print("="*70)


# Example usage
if __name__ == "__main__":
    # Auto-detect dan configure
    optimizer = GPUOptimizer(verbose=True)
    
    # Get device info
    info = optimizer.get_device_info()
    print(f"\nDetected: {info['device_name']}")
    
    # Get recommended config
    config = optimizer.get_recommended_config()
    print(f"Recommended FPS: {config['target_fps']}")
    
    # Print summary
    optimizer.print_summary()
