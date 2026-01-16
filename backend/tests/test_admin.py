"""
Test suite for admin endpoints.
Tests admin-only access and user management.
"""

import unittest
import json
from app import create_app
from pymongo import MongoClient
from config import get_config

config = get_config('testing')


class TestAdmin(unittest.TestCase):
    """Test cases for admin endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and app."""
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        cls.db_client = MongoClient(config.MONGO_URI)
        cls.db = cls.db_client[config.MONGO_DB_NAME]
    
    def setUp(self):
        """Set up admin and regular user."""
        # Clean up
        self.db.users.delete_many({'email': {'$regex': 'admin_test.*@example.com'}})
        
        # Create admin user
        admin_data = {
            'email': 'admin_test@example.com',
            'password': 'AdminPassword123',
            'name': 'Admin User',
            'role': 'admin'
        }
        
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(admin_data),
                                   content_type='application/json')
        
        data = json.loads(response.data)
        self.admin_token = data['data']['access_token']
        self.admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create regular user
        user_data = {
            'email': 'admin_test_student@example.com',
            'password': 'StudentPassword123',
            'name': 'Student User',
            'role': 'student'
        }
        
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        
        data = json.loads(response.data)
        self.student_token = data['data']['access_token']
        self.student_headers = {'Authorization': f'Bearer {self.student_token}'}
        self.student_user_id = data['data']['user']['user_id']
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.users.delete_many({'email': {'$regex': 'admin_test.*@example.com'}})
    
    def test_admin_get_users(self):
        """Test admin can get all users."""
        response = self.client.get('/api/admin/users',
                                  headers=self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_student_cannot_access_admin_endpoint(self):
        """Test student cannot access admin endpoints."""
        response = self.client.get('/api/admin/users',
                                  headers=self.student_headers)
        
        self.assertEqual(response.status_code, 403)
    
    def test_admin_get_users_with_filters(self):
        """Test admin can filter users."""
        params = {
            'role': 'student',
            'page': 1,
            'per_page': 10
        }
        
        response = self.client.get('/api/admin/users',
                                  headers=self.admin_headers,
                                  query_string=params)
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_get_daily_attendance(self):
        """Test admin can get daily attendance."""
        response = self.client.get('/api/admin/attendance/daily',
                                  headers=self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('statistics', data['data'])
        self.assertIn('records', data['data'])
    
    def test_admin_get_attendance_report(self):
        """Test admin can get attendance report."""
        params = {
            'month': 12,
            'year': 2024
        }
        
        response = self.client.get('/api/admin/attendance/report',
                                  headers=self.admin_headers,
                                  query_string=params)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('report', data['data'])
    
    def test_admin_delete_user(self):
        """Test admin can delete user."""
        response = self.client.delete(f'/api/admin/users/{self.student_user_id}',
                                     headers=self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
    
    def test_student_cannot_delete_user(self):
        """Test student cannot delete users."""
        response = self.client.delete(f'/api/admin/users/{self.student_user_id}',
                                     headers=self.student_headers)
        
        self.assertEqual(response.status_code, 403)
    
    def test_admin_update_user(self):
        """Test admin can update user."""
        update_data = {
            'name': 'Updated Name',
            'class_name': 'XII-IPA-1'
        }
        
        response = self.client.put(f'/api/admin/users/{self.student_user_id}',
                                  headers=self.admin_headers,
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
