import bcrypt
from peewee import *

from .global_config import get_round

conn = SqliteDatabase('darkfream.db')

class DarkModel(Model):
    """Базовая модель для всех моделей в приложении.

    Attributes:
        Meta: Настройки базы данных.
    """

    class Meta:
        database = conn

    @classmethod
    def get_fields(cls):
        """Получает все поля модели, кроме поля 'id'.

        Returns:
            list: Список кортежей с именами полей и их определениями.
        """
        return [(field_name, field) for field_name, field in cls._meta.fields.items()
                if field_name != 'id']

    @classmethod
    def get_field_values(cls):
        """Получает значения всех полей модели.

        Returns:
            dict: Словарь с именами полей и их значениями.
        """
        return {field_name: getattr(cls, field_name) for field_name, _ in cls.get_fields()}

    def __str__(self):
        """Возвращает строковое представление модели.

        Returns:
            str: Имя или заголовок модели, если они существуют, иначе строка с именем класса и ID.
        """
        if hasattr(self, 'name'):
            return str(self.name)
        elif hasattr(self, 'title'):
            return str(self.title)
        else:
            return f"{self.__class__.__name__}#{self.id}"


class User(DarkModel):
    """Модель пользователя.

    Attributes:
        username (CharField): Уникальное имя пользователя.
        password (CharField): Хэшированный пароль пользователя.
        is_admin (BooleanField): Указывает, является ли пользователь администратором.
    """

    username = CharField(unique=True)
    password = CharField()
    is_admin = BooleanField(default=False)

    @staticmethod
    def hash_password(password):
        """Хэширует пароль пользователя.

        Args:
            password (str): Пароль для хэширования.

        Returns:
            str: Хэшированный пароль.
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=get_round())).decode('utf-8')

    def verify_password(self, password):
        """Проверяет, соответствует ли введенный пароль хэшированному паролю.

        Args:
            password (str): Введенный пароль для проверки.

        Returns:
            bool: True, если пароли совпадают, иначе False.
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except ValueError:
            return False

    def __str__(self):
        """Возвращает имя пользователя.

        Returns:
            str: Имя пользователя.
        """
        return self.username


class Session(DarkModel):
    """Модель сессии пользователя.

    Attributes:
        session_id (CharField): Уникальный идентификатор сессии.
        user (ForeignKeyField): Внешний ключ на модель пользователя.
        expires_at (DateTimeField): Время истечения сессии.
    """

    session_id = CharField(unique=True)
    user = ForeignKeyField(User, backref='sessions')
    expires_at = DateTimeField()
