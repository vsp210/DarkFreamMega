import smtplib
from email.message import EmailMessage
import math
import os
from pathlib import Path

class Request:
    def __init__(self, scope, receive):
        self.scope = scope
        self.receive = receive
        self.path = self.scope.get('path', '/')
        self.method = self.scope.get('method', 'GET')
        self.headers = self.parse_headers(self.scope.get('headers', []))
        self.query_params = {}
        self.body = None

    def parse_headers(self, headers):
        return {k.decode('utf-8').lower(): v.decode('utf-8')
                for k, v in headers}

    async def get_body(self):
        if self.body is None:
            body = b''
            more_body = True

            while more_body:
                message = await self.receive()
                body += message.get('body', b'')
                more_body = message.get('more_body', False)

            self.body = body

        return self.body

    @property
    def content_type(self):
        return self.headers.get('content-type')

    @property
    def content_length(self):
        return int(self.headers.get('content-length', 0))

class StaticFiles:
    def __init__(self, directory):
        self.directory = directory

    def __call__(self, request):
        file_path = request.path.replace('/static/', '', 1)
        full_path = os.path.join(self.directory, file_path)

        try:
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    content = f.read()

                content_type = self.get_content_type(full_path)

                return content, 200, content_type
            else:
                return "File not found", 404, 'text/plain'
        except Exception as e:
            print(f"Error serving static file: {e}")
            return "Internal server error", 500, 'text/plain'

    def get_content_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.html': 'text/html',
        }
        return content_types.get(ext, 'application/octet-stream')


def log(x: float, base: float = math.e) -> float:
    """Returns the logarithm of x with the given base"""
    return math.log(x, base)

def sqrt(x: float) -> float:
    """Returns the square root of x"""
    return math.sqrt(x)

def tan(x: float) -> float:
    """Returns the tangent of x"""
    return math.tan(x)

def cos(x: float) -> float:
    """Returns the cosine of x"""
    return math.cos(x)

def sin(x: float) -> float:
    """Returns the sine of x"""
    return math.sin(x)

def calculator(input_str: str) -> float:
    """This function takes a string of numbers as input, evaluates the expression, and returns the result."""
    numbers = input_str.split()

    if len(numbers) != 3:
        raise ValueError("Invalid input string. It should contain exactly two numbers and an operator.")

    operator = numbers[1]
    num1, num2 = float(numbers[0]), float(numbers[2])

    if operator == "+":
        result = num1 + num2
    elif operator == "-":
        result = num1 - num2
    elif operator == "*":
        result = num1 * num2
    elif operator == "/":
        if num2 == 0:
            raise ZeroDivisionError("Cannot divide by zero!")
        result = num1 / num2
    elif operator == "**":
        result = num1 ** num2
    elif operator == "%":
        result = num1 % num2
    elif operator == "//":
        if num2 == 0:
            raise ZeroDivisionError("Cannot divide by zero!")
        result = num1 // num2
    else:
        raise ValueError("Invalid operator. Supported operators are +, -, *, /, **, %, //.")

    return result


def send_email(sender_email, password, recipient_email, subject, body, host, port):
    if not sender_email and not password:
        return "Sender's email and password are required."

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()


def send_html_email(sender_email, password, recipient_email, subject, html_body, host, port):
    if not sender_email and not password:
        return "Sender's email and password are required."

    msg = EmailMessage()
    msg.set_content(html_body, subtype='html')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    server = smtplib.SMTP_SSL(host, port)
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()



class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.hooks = {}

    def register_plugin(self, plugin_name: str, plugin_class: object) -> None:
        """Регистрация нового плагина"""
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} already registered")
        self.plugins[plugin_name] = plugin_class
        print(f"Plugin '{plugin_name}' registered successfully")

    def unregister_plugin(self, plugin_name: str) -> None:
        """Удаление плагина"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            print(f"Plugin '{plugin_name}' unregistered successfully")

    def get_plugin(self, plugin_name: str) -> object:
        """Получение плагина по имени"""
        return self.plugins.get(plugin_name)

    def register_hook(self, hook_name: str, callback: callable) -> None:
        """Регистрация хука (точки расширения)"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> list:
        """Выполнение всех callback-функций для определенного хука"""
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                results.append(callback(*args, **kwargs))
        return results


class BasePlugin:
    def __init__(self, app):
        self.app = app

    def initialize(self):
        """Метод инициализации плагина"""
        pass

    def cleanup(self):
        """Метод очистки при отключении плагина"""
        pass

class PluginConfig:
    def __init__(self):
        self.enabled_plugins = set()
        self.plugin_settings = {}

    def enable_plugin(self, plugin_name: str) -> None:
        self.enabled_plugins.add(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        self.enabled_plugins.discard(plugin_name)

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        return plugin_name in self.enabled_plugins

    def set_plugin_setting(self, plugin_name: str, key: str, value: any) -> None:
        if plugin_name not in self.plugin_settings:
            self.plugin_settings[plugin_name] = {}
        self.plugin_settings[plugin_name][key] = value
