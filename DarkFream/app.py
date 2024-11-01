import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
import urllib.parse
from .admin import DarkAdmin
from .orm import *

class DarkFream:
    def __init__(self):
        self.routes = {}
        framework_templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        user_templates_dir = os.path.join(os.getcwd(), 'templates')
        self.env = Environment(loader=ChoiceLoader([
            FileSystemLoader(user_templates_dir),
            FileSystemLoader(framework_templates_dir)
        ]))
        self.env.globals['getattr'] = getattr
        self.admin = DarkAdmin(self)

    def route(self, path, methods=['GET']):
        path_regex = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', path)
        path_regex = f'^{path_regex}$'

        def wrapper(func):
            if path_regex not in self.routes:
                self.routes[path_regex] = {}
            for method in methods:
                self.routes[path_regex][method] = func
            return func
        return wrapper

    def route_404(self, func):
        self.routes['404'] = func
        return func

    def handle_request(self, path, method='GET', data=None):
        for pattern, methods in self.routes.items():
            match = re.match(pattern, path)
            if match and method in methods:
                kwargs = match.groupdict()
                result = methods[method](data, **kwargs)

                if isinstance(result, tuple):
                    if len(result) == 3:
                        status_code, response_body, content_type = result
                        if isinstance(content_type, dict):
                            return status_code, response_body, content_type
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
                    return status_code, self.render(response_body.get('template', 'admin/base.html'), context), content_type

        if '404' in self.routes:
            response_body = self.routes['404'](data)
            return 404, response_body, 'text/html'

        return 404, "404 Not Found", 'text/html'

    def render(self, template_name, context={}):
        template = self.env.get_template(template_name)
        return template.render(context)

    def render_code(self, status_code, message, template_name=None, context=None):
        if template_name is not None:
            context = {'status_code': status_code,
                       'message': message}
            return self.render(template_name, context)
        return (status_code, message)

    def redirect(self, path, method='GET'):
        return (302, '', {
            'Location': path,
            'Content-Type': 'text/html'
        })


    # API эндпоинты

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
                return self.json_response(500, {"error": str(e)})
        return wrapper

    def json_response(self, status_code, data):
        import json
        return (status_code, json.dumps(data), 'application/json')



class DarkHandler(BaseHTTPRequestHandler):
    darkfream = DarkFream()

    def do_POST(self):
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
        request_data = {
            'method': 'GET',
            'path': self.path,
            'headers': dict(self.headers),
            'data': {},
            'session': self.parse_session()
        }

        status_code, response, content_type = self.darkfream.handle_request(self.path, method='GET', data=request_data)

        self.send_response(status_code)
        if isinstance(content_type, dict):
            for header, value in content_type.items():
                self.send_header(header, value)
        else:
            self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        client_ip = self.headers.get('X-Forwarded-For', self.headers.get('X-Real-IP', self.client_address[0]))
        print(f'{client_ip} - {self.client_address[0]} - - [{self.log_date_time_string()}] - %s' % (format%args))


def run(server_address='', port=8000):
    httpd = HTTPServer((server_address, port), DarkHandler)
    print(f'Serving on port {port}...')
    httpd.serve_forever()

from .orm import User
DarkHandler.darkfream.admin.register_model(User)

def migrate(models=[]):

    conn.connect()
    conn.create_tables(models)
    if not User.select().exists():
        User.create(
            username='admin',
            password=User.hash_password('admin')
        )
    conn.close()
