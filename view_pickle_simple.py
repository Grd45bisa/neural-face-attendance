"""
Script sederhana untuk melihat isi file pickle
Tanpa dependency numpy untuk avoid compatibility issues
"""

import pickle
import os
import sys
import json

def view_pickle_simple(file_path):
    """Membaca dan menampilkan isi file pickle dengan format yang mudah dibaca."""
    
    if not os.path.exists(file_path):
        print(f"❌ File tidak ditemukan: {file_path}")
        return
    
    print("="*70)
    print(f"📄 FILE: {file_path}")
    print(f"📊 Size: {os.path.getsize(file_path):,} bytes")
    print("="*70)
    
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\n✅ Loaded successfully!")
        print(f"🔧 Type: {type(data).__name__}\n")
        
        # Tampilkan struktur data
        if isinstance(data, dict):
            print("📋 DICTIONARY CONTENTS:")
            print("-" * 70)
            
            for key, value in data.items():
                print(f"\n[KEY] {key}")
                print(f"  Type: {type(value).__name__}")
                
                if key == 'metadata' and isinstance(value, dict):
                    for k, v in value.items():
                        print(f"    • {k}: {v}")
                
                elif key == 'users' and isinstance(value, dict):
                    print(f"  Total users: {len(value)}")
                    print(f"\n  📝 USER LIST:")
                    for i, (user_id, user_data) in enumerate(value.items(), 1):
                        print(f"    [{i}] {user_id}")
                        if isinstance(user_data, dict):
                            for k, v in user_data.items():
                                if k == 'embedding':
                                    # Jangan tampilkan embedding lengkap (terlalu panjang)
                                    print(f"        • {k}: <{type(v).__name__} array with {len(v) if hasattr(v, '__len__') else '?'} values>")
                                elif k == 'metadata' and isinstance(v, dict):
                                    print(f"        • {k}: {v}")
                                else:
                                    print(f"        • {k}: {v}")
                else:
                    # Untuk value lainnya
                    if isinstance(value, (list, tuple)) and len(value) > 5:
                        print(f"  Preview (first 5): {value[:5]}...")
                    elif hasattr(value, '__len__') and len(str(value)) > 200:
                        print(f"  Length: {len(value)}")
                        print(f"  Preview: {str(value)[:200]}...")
                    else:
                        print(f"  Value: {value}")
        
        elif isinstance(data, list):
            print(f"📋 LIST with {len(data)} items")
            for i, item in enumerate(data[:5]):  # Tampilkan 5 pertama
                print(f"  [{i}] {item}")
            if len(data) > 5:
                print(f"  ... and {len(data) - 5} more items")
        
        else:
            print(f"📋 CONTENT:")
            print(data)
        
        print("\n" + "="*70)
        print("✅ DONE!")
        print("="*70)
        
    except EOFError:
        print("\n❌ ERROR: File is empty or corrupted (EOFError)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Type: {type(e).__name__}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Coba cari file .pkl di current directory dan subdirectories
        file_path = None
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pkl'):
                    file_path = os.path.join(root, file)
                    print(f"🔍 Found: {file_path}\n")
                    break
            if file_path:
                break
        
        if not file_path:
            print("❌ No .pkl files found.")
            print("\n💡 Usage: py view_pickle_simple.py <path_to_file.pkl>")
            sys.exit(1)
    
    view_pickle_simple(file_path)
