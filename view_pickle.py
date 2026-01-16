"""
Script untuk melihat isi file pickle (face_db.pkl atau embeddings.pkl)
"""

import pickle
import numpy as np
from datetime import datetime
import os
import sys

def view_pickle_file(file_path):
    """
    Membaca dan menampilkan isi file pickle.
    
    Args:
        file_path (str): Path ke file .pkl
    """
    if not os.path.exists(file_path):
        print(f"❌ File tidak ditemukan: {file_path}")
        return
    
    print("="*70)
    print(f"📄 VIEWING PICKLE FILE: {file_path}")
    print("="*70)
    
    try:
        # Load pickle file
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\n✅ File loaded successfully!")
        print(f"📊 File size: {os.path.getsize(file_path):,} bytes")
        print(f"🔧 Data type: {type(data)}")
        
        # Jika data adalah dictionary
        if isinstance(data, dict):
            print(f"\n📋 Dictionary keys: {list(data.keys())}")
            
            # Tampilkan metadata jika ada
            if 'metadata' in data:
                print("\n" + "="*70)
                print("METADATA:")
                print("="*70)
                for key, value in data['metadata'].items():
                    print(f"  • {key}: {value}")
            
            # Tampilkan users jika ada
            if 'users' in data:
                users = data['users']
                print("\n" + "="*70)
                print(f"USERS: Total {len(users)} user(s)")
                print("="*70)
                
                for i, (user_id, user_data) in enumerate(users.items(), 1):
                    print(f"\n[{i}] User ID: {user_id}")
                    print(f"    Name: {user_data.get('name', 'N/A')}")
                    
                    # Info embedding
                    if 'embedding' in user_data:
                        embedding = user_data['embedding']
                        if isinstance(embedding, np.ndarray):
                            print(f"    Embedding shape: {embedding.shape}")
                            print(f"    Embedding norm: {np.linalg.norm(embedding):.6f}")
                            print(f"    First 5 values: {embedding[:5]}")
                        else:
                            print(f"    Embedding type: {type(embedding)}")
                    
                    # Info lainnya
                    if 'registered_at' in user_data:
                        print(f"    Registered at: {user_data['registered_at']}")
                    if 'photo_count' in user_data:
                        print(f"    Photo count: {user_data['photo_count']}")
                    
                    # Metadata tambahan
                    if 'metadata' in user_data and user_data['metadata']:
                        print(f"    Metadata: {user_data['metadata']}")
        
        else:
            # Jika bukan dictionary, tampilkan raw data
            print("\n" + "="*70)
            print("RAW DATA:")
            print("="*70)
            print(data)
        
        print("\n" + "="*70)
        print("✅ Done!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error reading pickle file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Default path
    default_paths = [
        "data/embeddings.pkl",
        "data/face_db.pkl",
        "../data/embeddings.pkl",
        "../data/face_db.pkl"
    ]
    
    # Jika ada argument dari command line
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        view_pickle_file(file_path)
    else:
        # Coba semua default paths
        found = False
        for path in default_paths:
            if os.path.exists(path):
                view_pickle_file(path)
                found = True
                break
        
        if not found:
            print("❌ Tidak menemukan file pickle di lokasi default.")
            print("\n💡 Usage:")
            print("   python view_pickle.py <path_to_pickle_file>")
            print("\n📁 Contoh:")
            print("   python view_pickle.py data/embeddings.pkl")
            print("   python view_pickle.py ../data/face_db.pkl")
