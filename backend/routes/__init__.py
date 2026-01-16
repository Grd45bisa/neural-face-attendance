"""Routes package initialization."""

from .auth import init_auth_routes
from .user import init_user_routes
from .face import init_face_routes
from .attendance import init_attendance_routes

__all__ = [
    'init_auth_routes',
    'init_user_routes',
    'init_face_routes',
    'init_attendance_routes'
]
