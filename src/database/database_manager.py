import pickle
import os
import numpy as np
from datetime import datetime
import shutil
import warnings
import json
import base64


class DatabaseManager:
    """
    Database manager untuk mengelola face embeddings dan user data.
    Fase 4 - CRUD operations untuk face recognition database.
    """
    
    def __init__(self, db_path='data/embeddings.pkl', auto_save=True):
        """
        Initialize database manager.
        
        Args:
            db_path (str): Path ke database file
            auto_save (bool): Auto-save setiap kali ada perubahan
        """
        self.db_path = db_path
        self.auto_save = auto_save
        self.database = None
        
        # Auto-create directory jika belum ada
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"✓ Created directory: {db_dir}")
        
        # Load atau initialize database
        if os.path.exists(db_path):
            self.load_database()
        else:
            self._initialize_database()
    
    def _initialize_database(self):
        """
        Initialize empty database dengan struktur default.
        """
        self.database = {
            'users': {},
            'metadata': {
                'total_users': 0,
                'embedding_dim': None,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
        self.save_database()
        print("✓ Initialized new database")
    
    def add_user(self, user_id, name, embedding, metadata=None):
        """
        Tambah user baru ke database.
        
        Args:
            user_id (str): Unique user identifier
            name (str): Nama user
            embedding (numpy.ndarray): Face embedding vector
            metadata (dict, optional): Additional metadata
        
        Returns:
            bool: True jika sukses
        
        Raises:
            ValueError: Jika user_id sudah ada atau embedding invalid
        
        Example:
            >>> db = DatabaseManager('data/face_db.pkl')
            >>> db.add_user('user_001', 'Alice', embedding_vector)
        """
        # Check duplicate user_id
        if user_id in self.database['users']:
            raise ValueError(f"User ID '{user_id}' sudah terdaftar. Gunakan update_user() untuk update.")
        
        # Validate embedding
        if not isinstance(embedding, np.ndarray):
            raise ValueError("Embedding harus berupa numpy array.")
        
        if embedding.ndim != 1:
            raise ValueError(f"Embedding harus 1D array, got shape {embedding.shape}")
        
        # Check embedding dimension consistency
        if self.database['metadata']['embedding_dim'] is None:
            # First user, set embedding dimension
            self.database['metadata']['embedding_dim'] = len(embedding)
        else:
            # Validate dimension consistency
            expected_dim = self.database['metadata']['embedding_dim']
            if len(embedding) != expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch. Expected {expected_dim}, got {len(embedding)}"
                )
        
        # Add user to database
        self.database['users'][user_id] = {
            'name': name,
            'embedding': embedding,
            'registered_at': datetime.now().isoformat(),
            'photo_count': 1,
            'metadata': metadata or {}
        }
        
        # Update metadata
        self.database['metadata']['total_users'] = len(self.database['users'])
        self.database['metadata']['last_updated'] = datetime.now().isoformat()
        
        # Auto-save
        if self.auto_save:
            self.save_database()
        
        print(f"✓ User '{name}' (ID: {user_id}) added to database")
        return True
    
    def update_user(self, user_id, embedding=None, name=None, average_embedding=False):
        """
        Update user data yang sudah ada.
        
        Args:
            user_id (str): User ID yang akan di-update
            embedding (numpy.ndarray, optional): New embedding
            name (str, optional): New name
            average_embedding (bool): Jika True, average dengan embedding lama
        
        Returns:
            bool: True jika sukses
        
        Raises:
            ValueError: Jika user tidak ditemukan
        """
        # Check user exists
        if user_id not in self.database['users']:
            raise ValueError(f"User ID '{user_id}' tidak ditemukan.")
        
        user_data = self.database['users'][user_id]
        
        # Update name
        if name is not None:
            user_data['name'] = name
        
        # Update embedding
        if embedding is not None:
            # Validate embedding
            if not isinstance(embedding, np.ndarray) or embedding.ndim != 1:
                raise ValueError("Embedding harus berupa 1D numpy array.")
            
            expected_dim = self.database['metadata']['embedding_dim']
            if len(embedding) != expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch. Expected {expected_dim}, got {len(embedding)}"
                )
            
            # Average dengan embedding lama jika diminta
            if average_embedding:
                old_embedding = user_data['embedding']
                photo_count = user_data['photo_count']
                
                # Weighted average
                new_embedding = (old_embedding * photo_count + embedding) / (photo_count + 1)
                
                # Re-normalize
                new_embedding = new_embedding / np.linalg.norm(new_embedding)
                
                user_data['embedding'] = new_embedding
                user_data['photo_count'] += 1
            else:
                user_data['embedding'] = embedding
                user_data['photo_count'] = 1
        
        # Update metadata
        self.database['metadata']['last_updated'] = datetime.now().isoformat()
        
        # Auto-save
        if self.auto_save:
            self.save_database()
        
        print(f"✓ User '{user_id}' updated")
        return True
    
    def delete_user(self, user_id):
        """
        Hapus user dari database.
        
        Args:
            user_id (str): User ID yang akan dihapus
        
        Returns:
            bool: True jika sukses, False jika user tidak ditemukan
        """
        if user_id not in self.database['users']:
            print(f"⚠ User ID '{user_id}' tidak ditemukan")
            return False
        
        # Delete user
        user_name = self.database['users'][user_id]['name']
        del self.database['users'][user_id]
        
        # Update metadata
        self.database['metadata']['total_users'] = len(self.database['users'])
        self.database['metadata']['last_updated'] = datetime.now().isoformat()
        
        # Auto-save
        if self.auto_save:
            self.save_database()
        
        print(f"✓ User '{user_name}' (ID: {user_id}) deleted")
        return True
    
    def get_user(self, user_id):
        """
        Retrieve user data by ID.
        
        Args:
            user_id (str): User ID
        
        Returns:
            dict: User data atau None jika tidak ditemukan
        """
        return self.database['users'].get(user_id, None)
    
    def get_all_users(self):
        """
        Get list of all users (tanpa embeddings untuk performance).
        
        Returns:
            list: List of dicts dengan user_id dan name
        """
        users = []
        for user_id, user_data in self.database['users'].items():
            users.append({
                'user_id': user_id,
                'name': user_data['name'],
                'registered_at': user_data['registered_at'],
                'photo_count': user_data['photo_count']
            })
        return users
    
    def get_all_embeddings(self):
        """
        Get all embeddings untuk matching purposes.
        
        Returns:
            dict: {user_id: embedding} mapping
        """
        embeddings = {}
        for user_id, user_data in self.database['users'].items():
            embeddings[user_id] = user_data['embedding']
        return embeddings
    
    def save_database(self):
        """
        Save database ke file (pickle format).
        
        Returns:
            bool: True jika sukses
        """
        try:
            # Backup database lama sebelum overwrite
            if os.path.exists(self.db_path):
                backup_path = self.db_path + '.backup'
                shutil.copy2(self.db_path, backup_path)
            
            # Save database
            with open(self.db_path, 'wb') as f:
                pickle.dump(self.database, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            return True
            
        except PermissionError:
            raise PermissionError(f"Permission denied: tidak bisa write ke {self.db_path}")
        except Exception as e:
            raise RuntimeError(f"Error saving database: {e}")
    
    def load_database(self):
        """
        Load database dari file.
        
        Returns:
            bool: True jika sukses, False jika gagal
        """
        try:
            with open(self.db_path, 'rb') as f:
                self.database = pickle.load(f)
            
            print(f"✓ Database loaded from {self.db_path}")
            return True
            
        except FileNotFoundError:
            warnings.warn(f"Database file tidak ditemukan: {self.db_path}", UserWarning)
            self._initialize_database()
            return False
            
        except (pickle.UnpicklingError, EOFError) as e:
            # Database corrupted, try restore from backup
            warnings.warn(f"Database corrupted: {e}", UserWarning)
            
            backup_path = self.db_path + '.backup'
            if os.path.exists(backup_path):
                print("⚠ Attempting to restore from backup...")
                try:
                    with open(backup_path, 'rb') as f:
                        self.database = pickle.load(f)
                    print("✓ Database restored from backup")
                    return True
                except Exception as backup_error:
                    warnings.warn(f"Backup restoration failed: {backup_error}", UserWarning)
            
            # Initialize new database jika restore gagal
            print("⚠ Initializing new database")
            self._initialize_database()
            return False
    
    def get_database_stats(self):
        """
        Get database statistics.
        
        Returns:
            dict: Database statistics
        """
        stats = {
            'total_users': self.database['metadata']['total_users'],
            'embedding_dim': self.database['metadata']['embedding_dim'],
            'created_at': self.database['metadata']['created_at'],
            'last_updated': self.database['metadata']['last_updated'],
            'database_size_bytes': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        }
        return stats
    
    def export_to_json(self, export_path):
        """
        Export database ke JSON format (untuk analisis/portability).
        
        Args:
            export_path (str): Path untuk export file
        """
        export_data = {
            'users': {},
            'metadata': self.database['metadata']
        }
        
        # Convert numpy arrays ke list untuk JSON serialization
        for user_id, user_data in self.database['users'].items():
            export_data['users'][user_id] = {
                'name': user_data['name'],
                'embedding': user_data['embedding'].tolist(),  # numpy to list
                'registered_at': user_data['registered_at'],
                'photo_count': user_data['photo_count'],
                'metadata': user_data.get('metadata', {})
            }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✓ Database exported to {export_path}")
    
    def import_from_json(self, import_path):
        """
        Import database dari JSON format.
        
        Args:
            import_path (str): Path ke JSON file
        """
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        # Convert list kembali ke numpy arrays
        for user_id, user_data in import_data['users'].items():
            user_data['embedding'] = np.array(user_data['embedding'])
        
        self.database = import_data
        
        # Save to pickle format
        if self.auto_save:
            self.save_database()
        
        print(f"✓ Database imported from {import_path}")


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = DatabaseManager('data/face_db.pkl')
    
    # Example: Add user
    dummy_embedding = np.random.rand(1280)
    dummy_embedding = dummy_embedding / np.linalg.norm(dummy_embedding)  # Normalize
    
    try:
        db.add_user(
            user_id='user_001',
            name='Alice',
            embedding=dummy_embedding,
            metadata={'department': 'Engineering'}
        )
    except ValueError as e:
        print(f"User already exists: {e}")
    
    # Get all users
    users = db.get_all_users()
    print(f"\n=== All Users ===")
    for user in users:
        print(f"- {user['name']} (ID: {user['user_id']})")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"\n=== Database Stats ===")
    print(f"Total users: {stats['total_users']}")
    print(f"Embedding dimension: {stats['embedding_dim']}")
    print(f"Database size: {stats['database_size_bytes']} bytes")
    print(f"Last updated: {stats['last_updated']}")
    
    # Get all embeddings for matching
    embeddings_dict = db.get_all_embeddings()
    print(f"\n=== Embeddings ===")
    print(f"Total embeddings: {len(embeddings_dict)}")
    
    # Export to JSON
    db.export_to_json('data/face_db_export.json')
