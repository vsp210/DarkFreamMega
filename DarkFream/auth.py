from datetime import datetime, timedelta
import json
from pprint import pprint
import uuid

from .config import DarkFreamConfig
from .orm import User, Session
from .global_config import get_user_model

class AdminAuth:
    def __init__(self, app):
        self.app = app
        self.base_url = '/admin/'
        self.user_model = get_user_model() or User
        print("AdminAuth user model:", self.user_model)
        self.register_routes()

    def register_routes(self):
        self.app.route(f'{self.base_url}login', methods=['GET', 'POST'])(self.login)
        self.app.route(f'{self.base_url}logout')(self.logout)

    def login(self, data):
        cookie = data['headers'].get('Cookie', '')
        cookie_parts = cookie.split('=')
        if len(cookie_parts) > 1:
            logging = self.get_current_user(cookie_parts[1])
        else:
            logging = None
        if logging:
            session = data['headers']['Cookie'].split('=')[1]
            return 302, '', {
                'Location': self.base_url,
                'Content-Type': 'text/html',
                'Set-Cookie': f'session={session}; Path=/'
            }

        if data['method'] == 'POST':
            username = data['data'].get('username', [''])[0]
            password = data['data'].get('password', [''])[0]
            try:
                user = self.user_model.get(self.user_model.username == username)
                if user.verify_password(password):
                    session_id = str(uuid.uuid4())
                    expires_at = datetime.utcnow() + timedelta(days=1)

                    Session.create(session_id=session_id, user=user, expires_at=expires_at)

                    data['session'] = data.get('session', {})
                    data['session']['session_id'] = session_id
                    return 302, '', {
                        'Location': self.base_url,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={session_id}; Path=/; HttpOnly; Expires={expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT")}'
                    }
                else:
                    error_message = 'Invalid username or password'
            except User.DoesNotExist:
                error_message = 'Invalid username or password'

            return 200, {
                'template': 'admin/login.html',
                'error_message': error_message,
                'base_url': self.base_url,
                'session': data.get('session', {})
            }, 'text/html'

        return 200, {
            'template': 'admin/login.html',
            'base_url': self.base_url,
            'session': data.get('session', {})
        }, 'text/html'

    def logout(self, data):
        cookie = data['headers'].get('Cookie', '')
        cookie_parts = cookie.split('=')
        if len(cookie_parts) > 1:
            session = self.get_current_user(cookie_parts[1])
        else:
            session = None
        if session:
            try:
                Session.delete().where(Session.user == session.user).execute()
            except self.user_model.DoesNotExist:
                print(f"User {session.user.username} does not exist during logout.")
        data['session'] = {}
        return 302, '', {
            'Location': f'{self.base_url}login',
            'Content-Type': 'text/html',
            'Set-Cookie': 'session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        }


    def login_required(self, func):
        @wraps(func)
        def wrapper(data, *args, **kwargs):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                logging = self.get_current_user(cookie_parts[1])
            else:
                logging = None
            if logging is None:
                return (302, '', {
                    'Location': '/admin/login',
                    'Content-Type': 'text/html'
                })
            return func(data, *args, **kwargs)
        return wrapper


    def authotization(self, username, password=None, hash_password=None):
        if hash_password is not None:
            user = User.get(username = username, password = User.hash_password(password))
        else: user = User.get(username = username, password = hash_password)
        if user:
            return user.id
        return None


    def get_current_user(self, session_id):
        if session_id:
            try:
                session_obj = Session.get(Session.session_id == session_id)
                if session_obj.expires_at > datetime.utcnow():
                    return session_obj
            except Session.DoesNotExist:
                return None
        return None


from functools import wraps

class Auth:
    base_url = '/'

    def __init__(self, app):
        self.app = app
        self.user_model = get_user_model() or User
        print("Auth user model:", self.user_model)

    def login(self, data, redirect_uri=None):
        logging = self.get_current_user(data)
        redirect = redirect_uri or self.base_url
        if logging:
            session = data['headers']['Cookie'].split('=')[1]
            return 302, '', {
                'Location': redirect,
                'Content-Type': 'text/html',
                'Set-Cookie': f'session={session}; Path=/'
            }

        if data['method'] == 'POST':
            username = data['data'].get('username', [''])[0]
            password = data['data'].get('password', [''])[0]
            try:
                user = self.user_model.get(self.user_model.username == username)
                if user.verify_password(password):
                    session_id = str(uuid.uuid4())
                    expires_at = datetime.utcnow() + timedelta(days=1)

                    Session.create(session_id=session_id, user=user, expires_at=expires_at)

                    data['session'] = data.get('session', {})
                    data['session']['session_id'] = session_id
                    return 302, '', {
                        'Location': redirect,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={session_id}; Path=/; HttpOnly; Expires={expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT")}'
                    }
                else:
                    print('Invalid username or password')
            except User.DoesNotExist:
                print('Invalid username or password')

    def logout(self, data):
        cookie = data['headers'].get('Cookie', '')
        cookie_parts = cookie.split('=')
        if len(cookie_parts) > 1:
            session = self.get_current_user(cookie_parts[1])
        else:
            session = None
        if session:
            try:
                Session.delete().where(Session.user == session.user).execute()
            except self.user_model.DoesNotExist:
                print(f"User {session.user.username} does not exist during logout.")
        data['session'] = {}
        return 302, '', {
            'Location': f'{self.base_url}login',
            'Content-Type': 'text/html',
            'Set-Cookie': 'session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        }


    @classmethod
    def login_required(cls, redirect_url=None):
        def decorator(func):
            @wraps(func)
            def wrapper(data, *args, **kwargs):
                if cls.get_current_user(data) is None:
                    redirect_to = redirect_url or f'{cls.base_url}login'
                    return (302, '', {
                        'Location': redirect_to,
                        'Content-Type': 'text/html'
                    })
                return func(data, *args, **kwargs)
            return wrapper
        return decorator


    def authotization(self, username, password=None, hash_password=None):
        if hash_password is not None:
            user = User.get(username = username, password = User.hash_password(password))
        else: user = User.get(username = username, password = hash_password)
        if user:
            return user.id
        return None


    @classmethod
    def get_current_user(cls, data):
        if data is None:
            return None
        cookie = data['headers'].get('Cookie', '')
        cookie_parts = cookie.split('=')
        if cookie_parts:
            try:
                if cookie_parts[0] == 'session':
                    session_obj = Session.get(Session.session_id == cookie_parts[1])
                    if session_obj.expires_at > datetime.utcnow():
                        return session_obj
            except Session.DoesNotExist:
                return None
        return None
