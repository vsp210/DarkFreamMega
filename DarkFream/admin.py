from .config import DarkFreamConfig
from peewee import *
from functools import wraps
from .orm import User
from .auth import AdminAuth
from .global_config import get_user_model


class DarkAdmin:
    def __init__(self, app):
        self.app = app
        self.models = {}
        self.base_url = '/admin/'
        self.auth = AdminAuth(app)
        self.user_model = get_user_model() or User
        print("Admin user model:", self.user_model)
        self.register_routes()

    def register_model(self, model):
        self.models[model.__name__] = model
        return model

    def get_related_objects(self, field):
        if isinstance(field, ForeignKeyField):
            return field.rel_model.select()
        return None


    def register_routes(self):

        for path, methods in self.app.routes.items():
            if path.startswith(self.base_url) and path not in [f'{self.base_url}login', f'{self.base_url}logout']:
                for method, handler in methods.items():
                    self.app.routes[path][method] = self.auth.login_required(handler)

        @self.app.route(f'{self.base_url}')
        @self.auth.login_required
        def admin_index(data):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                current_user = self.auth.get_current_user(cookie_parts[1])
            else:
                current_user = None

            if current_user.user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')

            return 200, {
                'template': 'admin/index.html',
                'models': self.models,
                'base_url': self.base_url,
                'current_user': current_user.user
            }, 'text/html'

        @self.app.route(f'{self.base_url}<model_name>')
        @self.auth.login_required
        def admin_model_list(data=None, model_name=None):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                current_user = self.auth.get_current_user(cookie_parts[1])
            else:
                current_user = None

            if current_user.user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user, 'message': "Model not found",
                                                                 'models': self.models,
                                                                 'base_url': self.base_url
                                                                }), 'text/html'

            items = model.select()
            return 200, self.app.render_with_cache('admin/list.html', {
                'model': model,
                'models': self.models,
                'items': items,
                'base_url': self.base_url,
                'current_user': current_user.user
            }), 'text/html'


        @self.app.route(f'{self.base_url}<model_name>/create', methods=['GET', 'POST'])
        @self.auth.login_required
        def admin_model_create(data=None, model_name=None):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                current_user = self.auth.get_current_user(cookie_parts[1])
            else:
                current_user = None

            if current_user.user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user, 'message': f"Model {model_name} not found",
                                                                            'models': self.models,
                                                                 'base_url': self.base_url
                                                                }), 'text/html'

            if data['method'] == 'POST':
                try:
                    new_item = model()
                    for field_name, field in model._meta.fields.items():
                        if field_name != 'id':
                            if isinstance(field, ForeignKeyField) and field_name in data['data']:
                                related_id = int(data['data'][field_name][0])
                                related_obj = field.rel_model.get_by_id(related_id)
                                setattr(new_item, field_name, related_obj)
                            elif isinstance(field, BooleanField):
                                value = bool(int(data['data'].get(field_name, ['0'])[0]))
                                setattr(new_item, field_name, value)
                            elif field_name in data['data']:
                                if isinstance(new_item, self.user_model) and field_name == 'password':
                                    hashed_password = self.user_model.hash_password(data['data'][field_name][0])
                                    setattr(new_item, field_name, hashed_password)
                                else:
                                    setattr(new_item, field_name, data['data'][field_name][0])
                    new_item.save()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 400, self.app.render_with_cache('admin/error.html', {
                        'error_code': 400,
                        'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Error creating object: {str(e)}",
                    'models': self.models,
                    'base_url': self.base_url
                }), 'text/html'

            related_objects = {}
            for field_name, field in model._meta.fields.items():
                if isinstance(field, ForeignKeyField):
                    related_objects[field_name] = self.get_related_objects(field)

            return 200, self.app.render_with_cache('admin/edit.html', {
                'model': model,
                'item': None,
                'models': self.models,
                'base_url': self.base_url,
                'related_objects': related_objects,
                'current_user': current_user.user
            }), 'text/html'

        @self.app.route(f'{self.base_url}<model_name>/edit/<item_id>', methods=['GET', 'POST'])
        @self.auth.login_required
        def admin_model_edit(data=None, model_name=None, item_id=None):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                current_user = self.auth.get_current_user(cookie_parts[1])
            else:
                current_user = None

            if current_user.user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Model {model_name} not found",
                    'models': self.models,
                    'base_url': self.base_url
                }), 'text/html'

            try:
                item_id = int(item_id)
                item = model.get(id=item_id)
            except Exception as e:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user, 'message': f"Item not found: {str(e)}",
                                                                 'base_url': self.base_url,
                                                                 'models': self.models
                                                                }), 'text/html'

            if data['method'] == 'POST':
                try:
                    for field_name, field in model.get_fields():
                        if field_name in data['data']:
                            if isinstance(field, ForeignKeyField):
                                related_id = int(data['data'][field_name][0])
                                related_obj = field.rel_model.get_by_id(related_id)
                                setattr(item, field_name, related_obj)
                            elif isinstance(field, BooleanField):
                                values = data['data'].get(field_name, ['0'])
                                value = bool(int(values[-1]))
                                setattr(item, field_name, value)
                            else:
                                if isinstance(item, self.user_model) and field_name == 'password':
                                    if data['data'][field_name][0] != item.password:
                                        hashed_password = self.user_model.hash_password(data['data'][field_name][0])
                                        setattr(item, field_name, hashed_password)
                                else:
                                    setattr(item, field_name, data['data'][field_name][0])

                    item.save()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 400, self.app.render_with_cache('admin/error.html', {
                        'error_code': 400,
                        'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Error updating object: {str(e)}",
                    'models': self.models,
                    'base_url': self.base_url
                }), 'text/html'

            related_objects = {}
            for field_name, field in model.get_fields():
                if isinstance(field, ForeignKeyField):
                    related_objects[field_name] = self.get_related_objects(field)

            return 200, self.app.render_with_cache('admin/edit.html', {
                'model': model,
                'item': item,
                'models': self.models,
                'base_url': self.base_url,
                'related_objects': related_objects,
                'current_user': current_user.user
            }), 'text/html'

        @self.app.route(f'{self.base_url}<model_name>/delete/<item_id>', methods=['GET', 'POST'])
        @self.auth.login_required
        def admin_model_delete(data=None, model_name=None, item_id=None):
            cookie = data['headers'].get('Cookie', '')
            cookie_parts = cookie.split('=')
            if len(cookie_parts) > 1:
                current_user = self.auth.get_current_user(cookie_parts[1])
            else:
                current_user = None

            if current_user.user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Model {model_name} not found",
                    'models': self.models,
                    'base_url': self.base_url
                }), 'text/html'
            try:
                item_id = int(item_id)
                item = model.get_by_id(item_id)
            except ValueError:
                return 400, self.app.render_with_cache('admin/error.html', {
                    'error_code': 400,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Invalid item ID: {item_id}",
                    'base_url': self.base_url,
                    'models': self.models
                }), 'text/html'
            except model.DoesNotExist:
                return 404, self.app.render_with_cache('admin/error.html', {
                    'error_code': 404,
                    'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                    'message': f"Item with id {item_id} not found",
                    'base_url': self.base_url,
                    'models': self.models
                }), 'text/html'

            if data['method'] == 'POST':
                try:
                    item.delete_instance()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 500, self.app.render_with_cache('admin/error.html', {
                        'error_code': 500,
                        'current_user': self.auth.get_current_user(cookie_parts[1]).user,
                        'message': f"Error deleting object: {str(e)}",
                        'base_url': self.base_url,
                        'models': self.models
                    }), 'text/html'
            return 200, self.app.render_with_cache('admin/delete_confirm.html', {
                'model': model,
                'item': item,
                'base_url': self.base_url,
                'models': self.models,
                'current_user': current_user.user
                }), 'text/html'
