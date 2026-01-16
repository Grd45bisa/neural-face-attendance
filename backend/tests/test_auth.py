"""
Test suite for authentication endpoints.
Tests user registration, login, logout, and token refresh.
"""

import unittest
import json
from app import create_app
from pymongo import MongoClient
from config import get_config

config = get_config('testing')


class TestAuth(unittest.TestCase):
    """Test cases for authentication endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and app."""
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        cls.db_client = MongoClient(config.MONGO_URI)
        cls.db = cls.db_client[config.MONGO_DB_NAME]
    
    def setUp(self):
        """Clear test data before each test."""
        self.db.users.delete_many({'email': {'$regex': 'test.*@example.com'}})
        self.test_user = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'name': 'Test User',
            'role': 'student'
        }
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.users.delete_many({'email': {'$regex': 'test.*@example.com'}})
    
    def test_register_success(self):
        """Test successful user registration."""
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(self.test_user),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('access_token', data['data'])
        self.assertIn('refresh_token', data['data'])
        self.assertEqual(data['data']['user']['email'], self.test_user['email'])
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Register first user
        self.client.post('/api/auth/register',
                        data=json.dumps(self.test_user),
                        content_type='application/json')
        
        # Try to register again with same email
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(self.test_user),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        invalid_user = self.test_user.copy()
        invalid_user['email'] = 'invalid-email'
        
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(invalid_user),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_register_weak_password(self):
        """Test registration with weak password."""
        weak_user = self.test_user.copy()
        weak_user['password'] = '123'
        
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(weak_user),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_login_success(self):
        """Test successful login."""
        # Register user first
        self.client.post('/api/auth/register',
                        data=json.dumps(self.test_user),
                        content_type='application/json')
        
        # Login
        login_data = {
            'email': self.test_user['email'],
            'password': self.test_user['password']
        }
        response = self.client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('access_token', data['data'])
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register user first
        self.client.post('/api/auth/register',
                        data=json.dumps(self.test_user),
                        content_type='application/json')
        
        # Login with wrong password
        login_data = {
            'email': self.test_user['email'],
            'password': 'WrongPassword123'
        }
        response = self.client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'Password123'
        }
        response = self.client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_token_refresh(self):
        """Test token refresh."""
        # Register and get tokens
        register_response = self.client.post('/api/auth/register',
                                            data=json.dumps(self.test_user),
                                            content_type='application/json')
        
        tokens = json.loads(register_response.data)['data']
        refresh_token = tokens['refresh_token']
        
        # Refresh token
        response = self.client.post('/api/auth/refresh',
                                   data=json.dumps({'refresh_token': refresh_token}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data['data'])
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = self.client.get('/api/user/profile')
        self.assertEqual(response.status_code, 401)
    
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        # Register and get token
        register_response = self.client.post('/api/auth/register',
                                            data=json.dumps(self.test_user),
                                            content_type='application/json')
        
        token = json.loads(register_response.data)['data']['access_token']
        
        # Access protected endpoint
        response = self.client.get('/api/user/profile',
                                   headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
