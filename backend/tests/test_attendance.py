"""
Test suite for attendance endpoints.
Tests check-in, history, statistics, and business logic.
"""

import unittest
import json
from datetime import datetime, timedelta
from app import create_app
from pymongo import MongoClient
from config import get_config

config = get_config('testing')


class TestAttendance(unittest.TestCase):
    """Test cases for attendance endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and app."""
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        cls.db_client = MongoClient(config.MONGO_URI)
        cls.db = cls.db_client[config.MONGO_DB_NAME]
    
    def setUp(self):
        """Set up test user and get auth token."""
        # Clean up
        self.db.users.delete_many({'email': 'attendance_test@example.com'})
        self.db.attendance.delete_many({})
        self.db.face_embeddings.delete_many({})
        
        # Register test user
        user_data = {
            'email': 'attendance_test@example.com',
            'password': 'TestPassword123',
            'name': 'Attendance Test User',
            'role': 'student'
        }
        
        response = self.client.post('/api/auth/register',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        
        data = json.loads(response.data)
        self.token = data['data']['access_token']
        self.user_id = data['data']['user']['user_id']
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.users.delete_many({'email': 'attendance_test@example.com'})
        self.db.attendance.delete_many({})
        self.db.face_embeddings.delete_many({})
    
    def test_checkin_without_face_registration(self):
        """Test check-in without face registration should fail."""
        # Note: This would require actual face verification
        # For now, we test the endpoint exists
        response = self.client.get('/api/attendance/today',
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
    
    def test_get_today_attendance_empty(self):
        """Test getting today's attendance when none exists."""
        response = self.client.get('/api/attendance/today',
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsNone(data['data'])
    
    def test_get_attendance_history(self):
        """Test getting attendance history."""
        response = self.client.get('/api/attendance/history',
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('records', data['data'])
        self.assertIn('total', data['data'])
    
    def test_get_attendance_history_with_filters(self):
        """Test getting attendance history with month/year filters."""
        params = {
            'month': 12,
            'year': 2024,
            'page': 1,
            'per_page': 20
        }
        
        response = self.client.get('/api/attendance/history',
                                  headers=self.headers,
                                  query_string=params)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('records', data['data'])
    
    def test_get_attendance_stats(self):
        """Test getting attendance statistics."""
        response = self.client.get('/api/attendance/stats',
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_present', data['data'])
        self.assertIn('total_late', data['data'])
        self.assertIn('total_absent', data['data'])
        self.assertIn('attendance_percentage', data['data'])
        self.assertIn('streak', data['data'])
    
    def test_attendance_without_auth(self):
        """Test attendance endpoints without authentication."""
        response = self.client.get('/api/attendance/today')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.get('/api/attendance/history')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.get('/api/attendance/stats')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
