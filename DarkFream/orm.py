import bcrypt
from peewee import *

conn = SqliteDatabase('darkfream.db')

class DarkModel(Model):
    class Meta:
        database = conn

    @classmethod
    def get_fields(cls):
        return [(field_name, field) for field_name, field in cls._meta.fields.items()
                if field_name != 'id']

    def get_field_values(self):
        return {field_name: getattr(self, field_name) for field_name, _ in self.get_fields()}

class User(DarkModel):
    username = CharField(unique=True)
    password = CharField()
    is_admin = BooleanField(default=False)

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except ValueError:
            return False
