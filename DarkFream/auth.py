# DarkFream/DarkFream/auth.py
import json
from .orm import User

class AdminAuth:
    def __init__(self, app):
        self.app = app
        self.base_url = '/admin/'
        self.register_routes()

    def register_routes(self):
        self.app.route(f'{self.base_url}login', methods=['GET', 'POST'])(self.login)
        self.app.route(f'{self.base_url}logout')(self.logout)

    def login(self, data):
        logging = self.get_current_user(data.get('session', {}))
        if logging:
            return 302, '', {
                'Location': self.base_url,
                'Content-Type': 'text/html',
                'Set-Cookie': f'session={json.dumps(data["session"])}; Path=/'
            }
        if data['method'] == 'POST':
            username = data['data'].get('username', [''])[0]
            password = data['data'].get('password', [''])[0]
            try:
                user = User.get(User.username == username)
                if user.verify_password(password):
                    data['session'] = data.get('session', {})
                    data['session']['user_id'] = user.id
                    return 302, '', {
                        'Location': self.base_url,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={json.dumps(data["session"])}; Path=/'
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
        data['session'] = {}
        return 302, '', {
            'Location': f'{self.base_url}login',
            'Content-Type': 'text/html',
            'Set-Cookie': 'session={}; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        }

    def login_required(self, location='/admin/login'):
        def decorator(func):
            def wrapper(data, *args, **kwargs):
                if 'user_id' not in data.get('session', {}):
                    location_to_redirect = location or f'{self.base_url}login'
                    return (302, '', {
                        'Location': location_to_redirect,
                        'Content-Type': 'text/html'
                    })
                return func(data, *args, **kwargs)
            return wrapper
        return decorator

    def authotization(self, username, password):
        user = User.get(username = username, password = User.hash_password(password))
        if user:
            return user.id
        return None


    def get_current_user(self, session):
        user_id = session.get('user_id')
        if user_id:
            try:
                return User.get_by_id(user_id)
            except User.DoesNotExist:
                return None
        return None


from functools import wraps

class Auth:
    base_url = '/'

    def __init__(self, app):
        self.app = app

    @classmethod
    def login_required(cls, redirect_url=None):
        def decorator(func):
            @wraps(func)
            def wrapper(data, *args, **kwargs):
                if 'user_id' not in data.get('session', {}):
                    redirect_to = redirect_url or f'{cls.base_url}login'
                    return (302, '', {
                        'Location': redirect_to,
                        'Content-Type': 'text/html'
                    })
                return func(data, *args, **kwargs)
            return wrapper
        return decorator

    def login(self, data):
        if data['method'] == 'POST':
            username = data['data'].get('username', [''])[0]
            password = data['data'].get('password', [''])[0]
            try:
                user = User.get(User.username == username)
                if user.verify_password(password):
                    data['session'] = data.get('session', {})
                    data['session']['user_id'] = user.id
                    return 302, '', {
                        'Location': self.base_url,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={json.dumps(data["session"])}; Path=/'
                    }
                else:
                    error_message = 'Invalid username or password'
            except User.DoesNotExist:
                error_message = 'Invalid username or password'

            return error_message

        return True

    def logout(self, data, redirect_url=None):
        data['session'] = {}
        return 302, '', {
            'Location': f'{redirect_url if redirect_url is not None else self.base_url}login',
            'Content-Type': 'text/html',
            'Set-Cookie': 'session={}; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        }

    def get_current_user(self, session):
        user_id = session.get('user_id')
        if user_id:
            return User.get_or_none(User.id == user_id)
        return None
