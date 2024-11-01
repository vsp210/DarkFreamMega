from peewee import *
from functools import wraps
from .orm import User
from .auth import AdminAuth


def login_required(func):
    @wraps(func)
    def wrapper(data, *args, **kwargs):
        if 'user_id' not in data.get('session', {}):
            return (302, '', {
                'Location': '/admin/login',
                'Content-Type': 'text/html'
            })
        return func(data, *args, **kwargs)
    return wrapper

class DarkAdmin:
    def __init__(self, app):
        self.app = app
        self.models = {}
        self.base_url = '/admin/'
        self.auth = AdminAuth(app)
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


        base_url = self.base_url
        models = self.models

        @self.app.route(f'{self.base_url}')
        @login_required
        def admin_index(data):
            current_user = self.auth.get_current_user(data.get('session', {}))
            if current_user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            return 200, {
                'template': 'admin/index.html',
                'models': self.models,
                'base_url': self.base_url,
                'session': data.get('session', {}),
                'current_user': current_user
            }, 'text/html'

        @self.app.route(f'{self.base_url}<model_name>')
        @login_required
        def admin_model_list(data=None, model_name=None):
            current_user = self.auth.get_current_user(data.get('session', {}))
            if current_user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render('admin/error.html', {'message': "Model not found",
                                                                 'base_url': self.base_url,
                                                                 'session': data.get('session', {})
                                                                }), 'text/html'

            items = model.select()
            current_user = self.auth.get_current_user(data.get('session', {}))

            return 200, {
                'template': 'admin/list.html',
                'model': model,
                'items': items,
                'base_url': self.base_url,
                'current_user': current_user
            }, 'text/html'


        @self.app.route(f'{self.base_url}<model_name>/create', methods=['GET', 'POST'])
        @login_required
        def admin_model_create(data=None, model_name=None):
            current_user = self.auth.get_current_user(data.get('session', {}))
            if current_user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render('admin/error.html', {'message': f"Model {model_name} not found",
                                                                 'base_url': self.base_url,
                                                                 'session': data.get('session', {})
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
                                if isinstance(new_item, User) and field_name == 'password':
                                    hashed_password = User.hash_password(data['data'][field_name][0])
                                    setattr(new_item, field_name, hashed_password)
                                else:
                                    setattr(new_item, field_name, data['data'][field_name][0])
                    new_item.save()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 400, f"Error creating object: {str(e)}", 'text/html'

            related_objects = {}
            for field_name, field in model._meta.fields.items():
                if isinstance(field, ForeignKeyField):
                    related_objects[field_name] = self.get_related_objects(field)

            current_user = self.auth.get_current_user(data.get('session', {}))
            return 200, self.app.render('admin/edit.html', {
                'model': model,
                'item': None,
                'base_url': self.base_url,
                'related_objects': related_objects,
                'session': data.get('session', {}),
                'current_user': current_user
            }), 'text/html'

        @self.app.route(f'{self.base_url}<model_name>/edit/<item_id>', methods=['GET', 'POST'])
        @login_required
        def admin_model_edit(data=None, model_name=None, item_id=None):
            current_user = self.auth.get_current_user(data.get('session', {}))
            if current_user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render('admin/error.html', {
                    'message': f"Model {model_name} not found",
                    'base_url': self.base_url,
                    'session': data.get('session', {})
                }), 'text/html'

            try:
                item_id = int(item_id)
                item = model.get(id=item_id)
            except Exception as e:
                return 404, self.app.render('admin/error.html', {'message': f"Item not found: {str(e)}",
                                                                 'base_url': self.base_url,
                                                                 'session': data.get('session', {})
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
                                value = bool(int(data['data'].get(field_name, ['0'])[0]))
                                print(value)
                                if value == False:
                                    value = bool(int(data['data'].get(field_name, ['0'])[1]))
                                setattr(item, field_name, value)
                            else:
                                if isinstance(item, User) and field_name == 'password':
                                    if data['data'][field_name][0] != item.password:
                                        hashed_password = User.hash_password(data['data'][field_name][0])
                                        setattr(item, field_name, hashed_password)
                                else:
                                    setattr(item, field_name, data['data'][field_name][0])

                    item.save()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 400, self.app.render('admin/error.html', {
                    'message': f"Error updating object: {str(e)}",
                    'base_url': self.base_url,
                    'session': data.get('session', {})
                }), 'text/html'

            related_objects = {}
            for field_name, field in model.get_fields():
                if isinstance(field, ForeignKeyField):
                    related_objects[field_name] = self.get_related_objects(field)

            current_user = self.auth.get_current_user(data.get('session', {}))
            return 200, self.app.render('admin/edit.html', {
                'model': model,
                'item': item,
                'base_url': self.base_url,
                'related_objects': related_objects,
                'session': data.get('session', {}),
                'current_user': current_user
            }), 'text/html'

        @self.app.route(f'{self.base_url}<model_name>/delete/<item_id>', methods=['GET', 'POST'])
        @login_required
        def admin_model_delete(data=None, model_name=None, item_id=None):
            current_user = self.auth.get_current_user(data.get('session', {}))
            if current_user.is_admin == False:
                return self.app.redirect(f'{self.base_url}logout')
            model = self.models.get(model_name)
            if not model:
                return 404, self.app.render('admin/error.html', {
                    'message': f"Model {model_name} not found",
                    'base_url': self.base_url,
                    'session': data.get('session', {})
                }), 'text/html'

            try:
                item_id = int(item_id)
                item = model.get_by_id(item_id)
            except ValueError:
                return 400, self.app.render('admin/error.html', {
                    'message': f"Invalid item ID: {item_id}",
                    'base_url': self.base_url,
                    'session': data.get('session', {})
                }), 'text/html'
            except model.DoesNotExist:
                return 404, self.app.render('admin/error.html', {
                    'message': f"Item with id {item_id} not found",
                    'base_url': self.base_url,
                    'session': data.get('session', {})
                }), 'text/html'

            if data['method'] == 'POST':
                try:
                    item.delete_instance()
                    return self.app.redirect(f'{self.base_url}{model_name}')
                except Exception as e:
                    return 500, self.app.render('admin/error.html', {
                        'message': f"Error deleting object: {str(e)}",
                        'base_url': self.base_url,
                        'session': data.get('session', {})
                    }), 'text/html'
            current_user = self.auth.get_current_user(data.get('session', {}))
            return 200, self.app.render('admin/delete_confirm.html', {
                'model': model,
                'item': item,
                'base_url': self.base_url,
                'session': data.get('session', {}),
                'current_user': current_user
                }), 'text/html'
