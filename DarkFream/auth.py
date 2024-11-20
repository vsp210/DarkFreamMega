import json
from .config import DarkFreamConfig
from .orm import User
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
                user = self.user_model.get(self.user_model.username == username)
                if user.verify_password(password):
                    data['session'] = data.get('session', {})
                    user_info = f"{user.id}:{user.password}"
                    data['session']['user'] = user_info
                    return 302, '', {
                        'Location': self.base_url,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={json.dumps(data["session"])}; Path=/'
                    }
                else:
                    error_message = 'Invalid username or password'
                    print(error_message)
            except User.DoesNotExist:
                error_message = 'Invalid username or password'
                print(error_message)


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
                if 'user' not in data.get('session', {}):
                    location_to_redirect = location or f'{self.base_url}login'
                    return (302, '', {
                        'Location': location_to_redirect,
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


    def get_current_user(self, session):
        user_id = session.get('user')
        if user_id:
            try:
                return self.user_model.get_by_id(user_id.split(':')[0])
            except self.user_model.DoesNotExist:
                return None
        return None


from functools import wraps

class Auth:
    base_url = '/'

    def __init__(self, app):
        self.app = app
        self.user_model = get_user_model() or User
        print("Auth user model:", self.user_model)

    @classmethod
    def login_required(cls, redirect_url=None):
        def decorator(func):
            @wraps(func)
            def wrapper(data, *args, **kwargs):
                if 'user' not in data.get('session', {}):
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
                user = self.user_model.get(self.user_model.username == username)
                if user.verify_password(password):
                    data['session'] = data.get('session', {})
                    user_info = f"{user.id}:{user.password}"
                    data['session']['user'] = user_info
                    return 302, '', {
                        'Location': self.base_url,
                        'Content-Type': 'text/html',
                        'Set-Cookie': f'session={json.dumps(data["session"])}; Path=/'
                    }
                else:
                    error_message = 'Invalid username or password'
            except self.user_model.DoesNotExist:
                error_message = 'Invalid username or password'

            return error_message

        return True

    def logout(self, data, redirect_url=None):
        print(data['session'])
        data['session'] = {}
        return 302, '', {
            'Location': f'{redirect_url if redirect_url is not None else self.base_url}login',
            'Content-Type': 'text/html',
            'Set-Cookie': 'session={}; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        }

    def get_current_user(self, session):
        user_id = session.get('user')
        if user_id:
            return self.user_model.get_or_none(self.user_model.id == user_id.split(':')[0])
        return None
