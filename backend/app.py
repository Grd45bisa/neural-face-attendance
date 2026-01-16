"""
Flask Backend API for Face Recognition Attendance System.
Main application entry point.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from config import get_config
from routes import (
    init_auth_routes,
    init_user_routes,
    init_face_routes,
    init_attendance_routes
)


def create_app(config_name=None):
    """
    Create and configure Flask application.
    
    Args:
        config_name (str): Configuration name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Create upload folders
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'faces'), exist_ok=True)
    os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'attendance'), exist_ok=True)
    
    # Connect to MongoDB
    try:
        mongo_client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.server_info()
        db = mongo_client[config.MONGO_DB_NAME]
        app.logger.info(f"Connected to MongoDB: {config.MONGO_DB_NAME}")
    except ConnectionFailure as e:
        app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    # Store db in app context
    app.db = db
    
    # Register blueprints
    app.register_blueprint(init_auth_routes(db))
    app.register_blueprint(init_user_routes(db))
    app.register_blueprint(init_face_routes(db))
    app.register_blueprint(init_attendance_routes(db))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'error': str(error)
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"Internal error: {str(error)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(error) if app.config['DEBUG'] else 'An error occurred'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions."""
        app.logger.error(f"Unhandled exception: {str(error)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
            'error': str(error) if app.config['DEBUG'] else 'Please contact support'
        }), 500
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        try:
            # Check MongoDB connection
            mongo_client.server_info()
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '1.0.0'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 503
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information."""
        return jsonify({
            'name': 'Face Recognition Attendance API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'auth': '/api/auth',
                'user': '/api/user',
                'face': '/api/face',
                'attendance': '/api/attendance'
            },
            'documentation': 'See README.md for API documentation'
        }), 200
    
    return app


if __name__ == '__main__':
    # Create app
    app = create_app()
    
    # Get configuration
    config = get_config()
    
    # Run server
    print("=" * 60)
    print("Face Recognition Attendance API")
    print("=" * 60)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug mode: {config.DEBUG}")
    print(f"MongoDB: {config.MONGO_URI}{config.MONGO_DB_NAME}")
    print(f"Server: http://localhost:5000")
    print("=" * 60)
    print("Registered Routes:")
    print(app.url_map)
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )
