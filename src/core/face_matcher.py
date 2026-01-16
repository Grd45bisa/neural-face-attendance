import numpy as np
from sklearn.metrics import roc_curve, auc
import warnings


class FaceMatcher:
    """
    Face matcher untuk menghitung similarity antar embeddings.
    Fase 5 - Calculate similarity dan determine match/no-match.
    """
    
    def __init__(self, similarity_metric='cosine', threshold=0.6):
        """
        Initialize face matcher.
        
        Args:
            similarity_metric (str): Metric yang digunakan: 'cosine', 'euclidean', 'manhattan'
            threshold (float): Threshold untuk menentukan match (0-1)
        """
        valid_metrics = ['cosine', 'euclidean', 'manhattan']
        if similarity_metric not in valid_metrics:
            raise ValueError(f"Invalid metric. Choose from: {valid_metrics}")
        
        self.similarity_metric = similarity_metric
        self.threshold = threshold
        
        # Cache untuk optimization
        self._similarity_cache = {}
    
    def cosine_similarity(self, embedding1, embedding2):
        """
        Hitung cosine similarity antara dua embedding.
        
        Args:
            embedding1 (numpy.ndarray): First embedding vector
            embedding2 (numpy.ndarray): Second embedding vector
        
        Returns:
            float: Cosine similarity score [-1, 1]
                  1 = identical, 0 = orthogonal, -1 = opposite
        
        Formula:
            cos(θ) = dot(A, B) / (||A|| * ||B||)
        """
        # Validate inputs
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes mismatch: {embedding1.shape} vs {embedding2.shape}")
        
        # Compute dot product
        dot_product = np.dot(embedding1, embedding2)
        
        # Compute norms
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        # Handle zero norms
        if norm1 == 0 or norm2 == 0:
            warnings.warn("Zero norm embedding detected", UserWarning)
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [-1, 1] untuk numerical stability
        similarity = np.clip(similarity, -1.0, 1.0)
        
        return float(similarity)
    
    def euclidean_distance(self, embedding1, embedding2):
        """
        Hitung Euclidean distance (L2 distance).
        
        Args:
            embedding1 (numpy.ndarray): First embedding vector
            embedding2 (numpy.ndarray): Second embedding vector
        
        Returns:
            float: Euclidean distance (lower = more similar)
        
        Formula:
            d = sqrt(sum((A - B)^2))
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes mismatch: {embedding1.shape} vs {embedding2.shape}")
        
        # Compute Euclidean distance
        distance = np.linalg.norm(embedding1 - embedding2)
        
        return float(distance)
    
    def manhattan_distance(self, embedding1, embedding2):
        """
        Hitung Manhattan distance (L1 distance).
        
        Args:
            embedding1 (numpy.ndarray): First embedding vector
            embedding2 (numpy.ndarray): Second embedding vector
        
        Returns:
            float: Manhattan distance (lower = more similar)
        
        Formula:
            d = sum(|A - B|)
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes mismatch: {embedding1.shape} vs {embedding2.shape}")
        
        # Compute Manhattan distance
        distance = np.sum(np.abs(embedding1 - embedding2))
        
        return float(distance)
    
    def compute_similarity(self, embedding1, embedding2):
        """
        METHOD UTAMA: Compute similarity menggunakan metric yang dipilih.
        Normalize output ke range [0, 1].
        
        Args:
            embedding1 (numpy.ndarray): First embedding vector
            embedding2 (numpy.ndarray): Second embedding vector
        
        Returns:
            float: Similarity score [0, 1] (1 = most similar)
        """
        if self.similarity_metric == 'cosine':
            # Cosine similarity: [-1, 1] → [0, 1]
            raw_score = self.cosine_similarity(embedding1, embedding2)
            # Normalize to [0, 1]: (score + 1) / 2
            # Tapi untuk L2-normalized embeddings, cosine biasanya [0, 1]
            # Jadi kita langsung return jika sudah positif
            if raw_score < 0:
                similarity = (raw_score + 1) / 2
            else:
                similarity = raw_score
        
        elif self.similarity_metric == 'euclidean':
            # Euclidean distance → similarity score
            distance = self.euclidean_distance(embedding1, embedding2)
            # Convert distance to similarity: 1 / (1 + distance)
            similarity = 1 / (1 + distance)
        
        elif self.similarity_metric == 'manhattan':
            # Manhattan distance → similarity score
            distance = self.manhattan_distance(embedding1, embedding2)
            # Convert distance to similarity: 1 / (1 + distance)
            similarity = 1 / (1 + distance)
        
        else:
            raise ValueError(f"Unknown metric: {self.similarity_metric}")
        
        return float(similarity)
    
    def find_best_match(self, query_embedding, database_embeddings):
        """
        Find best match untuk query embedding dari database.
        
        Args:
            query_embedding (numpy.ndarray): Embedding wajah yang mau dikenali
            database_embeddings (dict): {user_id: embedding} dari database
        
        Returns:
            dict: {
                'user_id': best_match_id atau None,
                'similarity': best_score,
                'is_match': True/False,
                'all_scores': {user_id: score, ...}
            }
        
        Example:
            >>> matcher = FaceMatcher(similarity_metric='cosine', threshold=0.6)
            >>> result = matcher.find_best_match(query_emb, db_embeddings)
            >>> if result['is_match']:
            ...     print(f"Match: {result['user_id']} ({result['similarity']:.2%})")
        """
        if not database_embeddings:
            return {
                'user_id': None,
                'similarity': 0.0,
                'is_match': False,
                'all_scores': {},
                'message': 'Database kosong'
            }
        
        # Compute similarity untuk semua users
        all_scores = {}
        best_user_id = None
        best_score = -1.0
        
        for user_id, db_embedding in database_embeddings.items():
            try:
                # Compute similarity
                similarity = self.compute_similarity(query_embedding, db_embedding)
                all_scores[user_id] = similarity
                
                # Track best match
                if similarity > best_score:
                    best_score = similarity
                    best_user_id = user_id
                
                # Early stopping jika sudah ketemu match dengan confidence tinggi
                if similarity > 0.95:
                    break
                    
            except Exception as e:
                warnings.warn(f"Error computing similarity for {user_id}: {e}", UserWarning)
                all_scores[user_id] = 0.0
        
        # Determine match based on threshold
        is_match = best_score >= self.threshold
        
        return {
            'user_id': best_user_id if is_match else None,
            'similarity': best_score,
            'is_match': is_match,
            'all_scores': all_scores,
            'threshold_used': self.threshold
        }
    
    def batch_match(self, query_embeddings, database_embeddings):
        """
        Match multiple queries sekaligus (efficient batch processing).
        
        Args:
            query_embeddings (list): List of query embeddings
            database_embeddings (dict): {user_id: embedding}
        
        Returns:
            list: List of match results (same format as find_best_match)
        """
        results = []
        
        for query_emb in query_embeddings:
            result = self.find_best_match(query_emb, database_embeddings)
            results.append(result)
        
        return results
    
    def set_threshold(self, threshold):
        """
        Dynamically update threshold.
        
        Args:
            threshold (float): New threshold value [0, 1]
        
        Raises:
            ValueError: Jika threshold di luar range [0, 1]
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold harus antara 0.0 dan 1.0, got {threshold}")
        
        self.threshold = threshold
        print(f"✓ Threshold updated to {threshold}")
    
    def calibrate_threshold(self, positive_pairs, negative_pairs):
        """
        ADVANCED: Auto-determine optimal threshold menggunakan ROC curve.
        
        Args:
            positive_pairs (list): List of (emb1, emb2) yang seharusnya match
            negative_pairs (list): List of (emb1, emb2) yang seharusnya tidak match
        
        Returns:
            dict: {
                'optimal_threshold': float,
                'accuracy': float,
                'fpr': float (False Positive Rate),
                'tpr': float (True Positive Rate),
                'auc': float (Area Under Curve)
            }
        """
        # Compute similarities untuk positive pairs
        positive_scores = []
        for emb1, emb2 in positive_pairs:
            score = self.compute_similarity(emb1, emb2)
            positive_scores.append(score)
        
        # Compute similarities untuk negative pairs
        negative_scores = []
        for emb1, emb2 in negative_pairs:
            score = self.compute_similarity(emb1, emb2)
            negative_scores.append(score)
        
        # Create labels: 1 for positive, 0 for negative
        y_true = [1] * len(positive_scores) + [0] * len(negative_scores)
        y_scores = positive_scores + negative_scores
        
        # Compute ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        # Find optimal threshold (maximize TPR - FPR)
        optimal_idx = np.argmax(tpr - fpr)
        optimal_threshold = thresholds[optimal_idx]
        
        # Compute metrics at optimal threshold
        optimal_fpr = fpr[optimal_idx]
        optimal_tpr = tpr[optimal_idx]
        
        # Compute accuracy
        predictions = [1 if score >= optimal_threshold else 0 for score in y_scores]
        accuracy = np.mean(np.array(predictions) == np.array(y_true))
        
        print(f"\n{'='*60}")
        print(f"THRESHOLD CALIBRATION RESULTS")
        print(f"{'='*60}")
        print(f"Optimal Threshold: {optimal_threshold:.3f}")
        print(f"Accuracy: {accuracy:.2%}")
        print(f"True Positive Rate (TPR): {optimal_tpr:.2%}")
        print(f"False Positive Rate (FPR): {optimal_fpr:.2%}")
        print(f"AUC: {roc_auc:.3f}")
        print(f"{'='*60}")
        
        # Update threshold
        self.set_threshold(optimal_threshold)
        
        return {
            'optimal_threshold': float(optimal_threshold),
            'accuracy': float(accuracy),
            'tpr': float(optimal_tpr),
            'fpr': float(optimal_fpr),
            'auc': float(roc_auc)
        }
    
    def get_similarity_statistics(self, all_scores):
        """
        Compute statistics dari similarity scores untuk analysis.
        
        Args:
            all_scores (dict): {user_id: similarity_score}
        
        Returns:
            dict: Statistics (mean, std, min, max, etc.)
        """
        if not all_scores:
            return {}
        
        scores = list(all_scores.values())
        
        stats = {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores),
            'median': np.median(scores),
            'count': len(scores)
        }
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize matcher
    matcher = FaceMatcher(
        similarity_metric='cosine',
        threshold=0.6
    )
    
    # Create dummy embeddings untuk testing
    np.random.seed(42)
    
    # Query embedding
    query_emb = np.random.rand(1280)
    query_emb = query_emb / np.linalg.norm(query_emb)
    
    # Database embeddings
    db_embeddings = {}
    for i in range(5):
        emb = np.random.rand(1280)
        emb = emb / np.linalg.norm(emb)
        db_embeddings[f'user_{i:03d}'] = emb
    
    # Add similar embedding untuk testing match
    similar_emb = query_emb + np.random.rand(1280) * 0.1
    similar_emb = similar_emb / np.linalg.norm(similar_emb)
    db_embeddings['user_target'] = similar_emb
    
    # Find best match
    result = matcher.find_best_match(query_emb, db_embeddings)
    
    print(f"\n{'='*60}")
    print(f"FACE MATCHING RESULT")
    print(f"{'='*60}")
    print(f"Match Found: {result['is_match']}")
    if result['is_match']:
        print(f"User ID: {result['user_id']}")
        print(f"Similarity: {result['similarity']:.2%}")
    else:
        print(f"Best Score: {result['similarity']:.2%} (below threshold {result['threshold_used']})")
    
    print(f"\n{'='*60}")
    print(f"ALL SCORES:")
    print(f"{'='*60}")
    for user_id, score in sorted(result['all_scores'].items(), key=lambda x: x[1], reverse=True):
        print(f"{user_id}: {score:.4f}")
    
    # Statistics
    stats = matcher.get_similarity_statistics(result['all_scores'])
    print(f"\n{'='*60}")
    print(f"STATISTICS:")
    print(f"{'='*60}")
    print(f"Mean: {stats['mean']:.4f}")
    print(f"Std: {stats['std']:.4f}")
    print(f"Min: {stats['min']:.4f}")
    print(f"Max: {stats['max']:.4f}")
    
    # Test different thresholds
    print(f"\n{'='*60}")
    print(f"THRESHOLD TESTING:")
    print(f"{'='*60}")
    for threshold in [0.5, 0.6, 0.7, 0.8]:
        matcher.set_threshold(threshold)
        result = matcher.find_best_match(query_emb, db_embeddings)
        print(f"Threshold {threshold}: Match = {result['is_match']}, Best = {result['similarity']:.4f}")
