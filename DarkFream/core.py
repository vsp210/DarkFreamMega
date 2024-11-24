import smtplib
from email.message import EmailMessage
import math
import os
from pathlib import Path

class Request:
    """Класс для обработки HTTP-запросов.

    Attributes:
        scope (dict): Контекст запроса.
        receive (callable): Функция для получения данных запроса.
        path (str): Путь запроса.
        method (str): Метод HTTP (например, GET, POST).
        headers (dict): Заголовки запроса.
        query_params (dict): Параметры запроса.
        body (bytes): Тело запроса.
    """
    def __init__(self, scope, receive):
        """Инициализация объекта Request.

        Args:
            scope (dict): Контекст запроса.
            receive (callable): Функция для получения данных запроса.
        """
        self.scope = scope
        self.receive = receive
        self.path = self.scope.get('path', '/')
        self.method = self.scope.get('method', 'GET')
        self.headers = self.parse_headers(self.scope.get('headers', []))
        self.query_params = {}
        self.body = None

    def parse_headers(self, headers):
        """Парсит заголовки запроса.

        Args:
            headers (list): Список заголовков.

        Returns:
            dict: Словарь заголовков с ключами в нижнем регистре.
        """
        return {k.decode('utf-8').lower(): v.decode('utf-8')
                for k, v in headers}

    async def get_body(self):
        """Получает тело запроса.

        Returns:
            bytes: Тело запроса.
        """
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
        """Возвращает тип контента из заголовков запроса."""
        return self.headers.get('content-type')

    @property
    def content_length(self):
        """Возвращает длину контента из заголовков запроса."""
        return int(self.headers.get('content-length', 0))

class StaticFiles:
    """Класс для обслуживания статических файлов.

    Attributes:
        directory (str): Директория, из которой будут обслуживаться файлы.
    """
    def __init__(self, directory):
        """Инициализация объекта StaticFiles.

        Args:
            directory (str): Директория для статических файлов.
        """
        self.directory = directory

    def __call__(self, request):
        """Обрабатывает HTTP-запрос для статического файла.

        Args:
            request (Request): Объект запроса.

        Returns:
            tuple: Содержимое файла, статус ответа и тип контента.
        """
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
        """Возвращает тип контента на основе расширения файла.

        Args:
            path (str): Путь к файлу.

        Returns:
            str: Тип контента.
        """
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
    """Возвращает логарифм x с заданным основанием.

    Args:
        x (float): Число, для которого вычисляется логарифм.
        base (float): Основание логарифма (по умолчанию e).

    Returns:
        float: Логарифм числа x.
    """
    return math.log(x, base)

def sqrt(x: float) -> float:
    """Возвращает квадратный корень из x.

    Args:
        x (float): Число, из которого нужно извлечь корень.

    Returns:
        float: Квадратный корень числа x.
    """
    return math.sqrt(x)

def tan(x: float) -> float:
    """Возвращает тангенс угла x.

    Args:
        x (float): Угол в радианах.

    Returns:
        float: Тангенс угла x.
    """
    return math.tan(x)

def cos(x: float) -> float:
    """Возвращает косинус угла x.

    Args:
        x (float): Угол в радианах.

    Returns:
        float: Косинус угла x.
    """
    return math.cos(x)

def sin(x: float) -> float:
    """Возвращает синус угла x.

    Args:
        x (float): Угол в радианах.

    Returns:
        float: Синус угла x.
    """
    return math.sin(x)

def calculator(input_str: str) -> float:
    """Вычисляет результат математического выражения.

    Args:
        input_str (str): Строка, содержащая два числа и оператор.

    Returns:
        float: Результат вычисления.

    Raises:
        ValueError: Если строка не содержит два числа и оператора.
        ZeroDivisionError: Если происходит деление на ноль.
    """
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
    """Отправляет электронное письмо.

    Args:
        sender_email (str): Адрес электронной почты отправителя.
        password (str): Пароль отправителя.
        recipient_email (str): Адрес электронной почты получателя.
        subject (str): Тема письма.
        body (str): Текст письма.
        host (str): Хост SMTP-сервера.
        port (int): Порт SMTP-сервера.

    Returns:
        None
    """
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
    """Отправляет HTML-форматированное электронное письмо.

    Args:
        sender_email (str): Адрес электронной почты отправителя.
        password (str): Пароль отправителя.
        recipient_email (str): Адрес электронной почты получателя.
        subject (str): Тема письма.
        html_body (str): HTML-содержимое письма.
        host (str): Хост SMTP-сервера.
        port (int): Порт SMTP-сервера.

    Returns:
        None
    """
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
    """Класс для управления плагинами.

    Attributes:
        plugins (dict): Словарь зарегистрированных плагинов.
        hooks (dict): Словарь хуков для расширения функциональности.
    """
    def __init__(self):
        """Инициализация объекта PluginManager."""
        self.plugins = {}
        self.hooks = {}

    def register_plugin(self, plugin_name: str, plugin_class: object) -> None:
        """Регистрация нового плагина.

        Args:
            plugin_name (str): Имя плагина.
            plugin_class (object): Класс плагина.

        Raises:
            ValueError: Если плагин с таким именем уже зарегистрирован.
        """
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} already registered")
        self.plugins[plugin_name] = plugin_class
        print(f"Plugin '{plugin_name}' registered successfully")

    def unregister_plugin(self, plugin_name: str) -> None:
        """Удаление плагина.

        Args:
            plugin_name (str): Имя плагина для удаления.
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            print(f"Plugin '{plugin_name}' unregistered successfully")

    def get_plugin(self, plugin_name: str) -> object:
        """Получение плагина по имени.

        Args:
            plugin_name (str): Имя плагина.

        Returns:
            object: Класс плагина или None, если плагин не найден.
        """
        return self.plugins.get(plugin_name)

    def register_hook(self, hook_name: str, callback: callable) -> None:
        """Регистрация хука (точки расширения).

        Args:
            hook_name (str): Имя хука.
            callback (callable): Функция обратного вызова для хука.
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> list:
        """Выполнение всех callback-функций для определенного хука.

        Args:
            hook_name (str): Имя хука.
            *args: Аргументы для передачи в функции обратного вызова.
            **kwargs: Именованные аргументы для передачи в функции обратного вызова.

        Returns:
            list: Список результатов выполнения функций обратного вызова.
        """
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                results.append(callback(*args, **kwargs))
        return results


class BasePlugin:
    """Базовый класс для создания плагинов.

    Attributes:
        app: Ссылка на приложение, к которому подключен плагин.
    """
    def __init__(self, app):
        """Инициализация базового плагина.

        Args:
            app: Ссылка на приложение.
        """
        self.app = app

    def initialize(self):
        """Метод инициализации плагина"""
        pass

    def cleanup(self):
        """Метод очистки при отключении плагина"""
        pass

class PluginConfig:
    """Класс для управления конфигурацией плагинов.

    Attributes:
        enabled_plugins (set): Множество включенных плагинов.
        plugin_settings (dict): Настройки для плагинов.
    """
    def __init__(self):
        """Инициализация объекта PluginConfig."""
        self.enabled_plugins = set()
        self.plugin_settings = {}

    def enable_plugin(self, plugin_name: str) -> None:
        """Включает плагин.

        Args:
            plugin_name (str): Имя плагина для включения.
        """
        self.enabled_plugins.add(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        """Отключает плагин.

        Args:
            plugin_name (str): Имя плагина для отключения.
        """
        self.enabled_plugins.discard(plugin_name)

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Проверяет, включен ли плагин.

        Args:
            plugin_name (str): Имя плагина.

        Returns:
            bool: True, если плагин включен, иначе False.
        """
        return plugin_name in self.enabled_plugins

    def set_plugin_setting(self, plugin_name: str, key: str, value: any) -> None:
        """Устанавливает настройку для указанного плагина.

        Args:
            plugin_name (str): Имя плагина.
            key (str): Ключ настройки.
            value (any): Значение настройки.
        """
        if plugin_name not in self.plugin_settings:
            self.plugin_settings[plugin_name] = {}
        self.plugin_settings[plugin_name][key] = value
