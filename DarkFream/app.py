import json
import os
from pprint import pprint
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
import urllib.parse

from .core import PluginConfig, PluginManager, Request
from .admin import DarkAdmin
from .orm import User, Session, conn



class DarkFream:
    def __init__(self):
        self.routes = {}
        self.static_handlers = {}
        framework_templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        user_templates_dir = os.path.join(os.getcwd(), 'templates')
        self.env = Environment(loader=ChoiceLoader([
            FileSystemLoader(user_templates_dir),
            FileSystemLoader(framework_templates_dir)
        ]))
        self.env.globals['getattr'] = getattr
        self.admin = DarkAdmin(self)
        self.plugin_manager = PluginManager()
        self.plugin_config = PluginConfig()

    def mount(self, prefix, handler, name=None):
        self.static_handlers[prefix] = handler

    def load_plugins(self):
        for plugin_name in self.plugin_config.enabled_plugins:
            plugin_class = self.plugin_manager.get_plugin(plugin_name)
            if plugin_class:
                plugin = plugin_class(self)
                plugin.initialize()

    def route(self, path, methods=['GET']):
        path_regex = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', path)
        path_regex = f'^{path_regex}$'

        def wrapper(func):
            if path_regex not in self.routes:
                self.routes[path_regex] = {}

            if '*' in methods:
                self.routes[path_regex]['*'] = func
            else:
                for method in methods:
                    self.routes[path_regex][method] = func

            return func
        return wrapper

    def route_404(self, func):
        self.routes['404'] = func
        return func

    def handle_request(self, path, method='GET', data=None):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Credentials': 'true'
        }

        if method == 'OPTIONS':
            return 204, '', headers

        for pattern, methods in self.routes.items():
            match = re.match(pattern, path)
            if match and (method in methods or '*' in methods):
                kwargs = match.groupdict()
                result = methods.get(method, methods.get('*'))(data, **kwargs)

                if isinstance(result, tuple):
                    if len(result) == 3:
                        status_code, response_body, content_type = result
                        if isinstance(content_type, dict):
                            content_type.update(headers)
                    elif len(result) == 2:
                        status_code, response_body = result
                        content_type = 'text/html'
                    else:
                        raise ValueError(f"Invalid return value from route handler: {result}")
                else:
                    status_code = 200
                    response_body = result
                    content_type = 'text/html'

                if content_type == 'application/json':
                    return status_code, response_body, content_type

                if isinstance(response_body, str):
                    return status_code, response_body, content_type

                if isinstance(response_body, dict):
                    context = response_body
                    if 'session' not in context:
                        context['session'] = data.get('session', {})
                    return status_code, self.render_with_cache(response_body.get('template', 'admin/base.html'), context), content_type

        return 404, "404 Not Found", 'text/html'

    def render(self, template_name, context={}):
        template = self.env.get_template(template_name)
        return template.render(context)

    def render_code(self, status_code, message, template_name=None, context=None):
        if template_name is not None:
            context = {'status_code': status_code,
                    'message': message}
            return self.render_with_cache(template_name, context)
        return (status_code, message)

    def cache_template(self, template_name):
        if not hasattr(self, '_template_cache'):
            self._template_cache = {}
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.env.get_template(template_name)
        return self._template_cache[template_name]

    def render_with_cache(self, template_name, context={}):
        template = self.cache_template(template_name)
        return template.render(context)

    def redirect(self, path, method='GET'):
        return (302, '', {
            'Location': path,
            'Content-Type': 'text/html'
        })


    def api_route(self, path, methods=['GET']):
        def wrapper(func):
            if path not in self.routes:
                self.routes[path] = {}
            for method in methods:
                self.routes[path][method] = self.api_handler(func)
            return func
        return wrapper

    def api_handler(self, func):
        def wrapper(data, *args, **kwargs):
            try:
                result = func(data, *args, **kwargs)
                return self.json_response(200, result)
            except Exception as e:
                print(str(e))
                return self.json_response(500, {"error": str(e)})
        return wrapper

    def json_response(self, status_code, data):
        import json
        return (status_code, json.dumps(data), 'application/json')

    def run(self, server_address='', port=8000):
        self.load_plugins()
        try:
            handler = get_handler() or DarkHandler
            httpd = HTTPServer((server_address, port), handler)
            print(f'Serving on port {port}...')
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Server stopped')

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)
        path = request.path

        for prefix, handler in self.static_handlers.items():
            if path.startswith(prefix):
                response = await handler(request)
                await self.send_response(send, response)
                return

    async def send_response(self, send, response):
        await send({
            "type": "http.response.start",
            "status": int(response["status"].split()[0]),
            "headers": [[k.encode(), v.encode()] for k, v in response.get("headers", {}).items()],
        })
        await send({
            "type": "http.response.body",
            "body": response["body"] if isinstance(response["body"], bytes) else response["body"].encode(),
        })


class DarkHandler(BaseHTTPRequestHandler):
    darkfream = None

    @classmethod
    def initialize(cls, darkfream=None):
        if cls.darkfream is None:
            if darkfream is not None:
                cls.darkfream = darkfream
            else:
                cls.darkfream = DarkFream()
        return cls.darkfream

    def do_POST(self):
        if self.darkfream is None:
            self.darkfream = self.__class__.initialize()
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')

            if 'application/json' in content_type:
                import json
                parsed_data = json.loads(post_data.decode('utf-8'))
            else:
                parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            request_data = {
                'method': 'POST',
                'path': self.path,
                'headers': dict(self.headers),
                'data': parsed_data,
                'session': self.parse_session()
            }

            status_code, response, content_type = self.darkfream.handle_request(self.path, method='POST', data=request_data)

            self.send_response(status_code)
            if isinstance(content_type, dict):
                for header, value in content_type.items():
                    self.send_header(header, value)
            else:
                self.send_header('Content-type', content_type)
            self.end_headers()

            if isinstance(content_type, dict) and 'Location' in content_type:
                return

            self.wfile.write(response.encode('utf-8'))

        except ConnectionAbortedError:
            print('Client connection aborted')
        except Exception as e:
            print(f'Error handling POST request: {str(e)}')

    def do_OPTIONS(self):
        if self.darkfream is None:
            self.darkfream = self.__class__.initialize()
        try:
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()
        except Exception as e:
            print(f'Error handling OPTIONS request: {str(e)}')

    def parse_session(self):
        session_cookie = self.headers.get('Cookie')
        if session_cookie:
            try:
                session_data = session_cookie.split('session=')[1].split(';')[0]
                return json.loads(session_data)
            except:
                pass
        return {}


    def do_GET(self):
        if self.darkfream is None:
            self.darkfream = self.__class__.initialize()
        try:
            for prefix, handler in self.darkfream.static_handlers.items():
                if self.path.startswith(prefix):
                    content, status_code, content_type = handler(Request({'path': self.path}, None))
                    self.send_response(status_code)
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    if isinstance(content, str):
                        self.wfile.write(content.encode('utf-8'))
                    else:
                        self.wfile.write(content)
                    return

            request_data = {
                'method': 'GET',
                'path': self.path,
                'headers': dict(self.headers),
                'data': {},
                'session': self.parse_session()
            }

            status_code, response, content_type = self.darkfream.handle_request(
                self.path, method='GET', data=request_data)

            self.send_response(status_code)
            if isinstance(content_type, dict):
                for header, value in content_type.items():
                    self.send_header(header, value)
            else:
                self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

        except ConnectionAbortedError:
            print('Client connection aborted')

    def log_message(self, format, *args):
        client_ip = self.headers.get('X-Forwarded-For', self.headers.get('X-Real-IP', self.client_address[0]))
        print(f'{client_ip} - {self.client_address[0]} - - [{self.log_date_time_string()}] - %s' % (format%args))





from .global_config import get_user_model, set_user_model, get_handler


def migrate(models=[], custom_user_model=None, initial_admin_data=None):
    models += [User, Session]
    if custom_user_model:
        if not issubclass(custom_user_model, User):
            raise ValueError("Custom user model must inherit from User class")
        set_user_model(custom_user_model)
        print("Setting user model to:", custom_user_model)

    user_model = get_user_model() or User
    handler = get_handler() or DarkHandler
    handler.darkfream.admin.register_model(user_model)
    print("Migrate user model:", user_model)

    default_admin = {
        'username': 'admin',
        'password': 'admin',
        'is_admin': True
    }

    if initial_admin_data and isinstance(initial_admin_data, dict):
        initial_admin_data['is_admin'] = True
        if 'password' in initial_admin_data:
            password = initial_admin_data.pop('password')
            default_admin.update(initial_admin_data)
            default_admin['password'] = password
        else:
            default_admin.update(initial_admin_data)

    conn.connect()
    conn.create_tables(models)

    try:
        if not user_model.select().exists():
            default_admin['password'] = user_model.hash_password(default_admin['password'])
            user_model.create(**default_admin)
            print(f"Created admin user: {default_admin['username']}")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        raise
    finally:
        conn.close()
