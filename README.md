# DarkFream
Мой собственный фреймворк DarkFream.

## Привет я молодой 14 летний программист который пытается создавать невозможное


#### DarkFream - Мой собственный фреймворк основанный на идеи создать что-то интересное
DarkFream - это фреймворк который позволяет создавать очень простые веб-приложения


#### DarkFream - Основные функции:
+ **Создание моделей** - Создание моделей для базы данных очень схожая с фреймворком Django но имеет меньший функционал например:
- **CharField**
- **TextField**
- **IntegerField**

+ **Работа с шаблонами** - Работа с шаблонами похожая с Django или Flask например:
- **render** (рендерит шаблон)
- **redirect** (изменяет ваш url)

### Запуск проекта

- для запуска требуется слонировать репозиторий командой:
```git clone https://github.com/vsp210/DarkFreamMega.git```
- затем рекомендую создать виртуальное окружение venv (для изоляции зависимостей)
~~~bash
py -* -m venv venv
source venv/Scripts/activate
~~~
где * — ваша версия Python
- перейдите в папку:
~~~bash
cd DarkFreamMega
~~~
- затем установите зависимости командой:
~~~bash
pip install -r requirements.txt
~~~


### Пример создания простой сот сети для постов:

- DarkFreamMega/app.py:
~~~python
from DarkFream.app import *
from DarkFream.auth import Auth
from DarkFream.orm import *
from models import Post


app = DarkHandler.initialize()
auth = Auth(app)
app.admin.register_model(Post)

@app.route('/', methods=['GET'])
def list_posts(data=None):
    posts = Post.select()
    return app.render('posts/list.html', {'posts': posts})

@app.route('/posts/create', methods=['GET', 'POST'])
@auth.login_required('/login')
def create_post(data=None):
    if data['method'] == 'POST':
        title = data['data'].get('title', [''])[0]
        content = data['data'].get('content', [''])[0]
        session = auth.get_current_user(data)

        if session:
            author = session.user
            new_post = Post(title=title, content=content, author=author)
            new_post.save()
            return app.redirect('/')

    return app.render('posts/create.html')

@app.route('/posts/<id>', methods=['GET'])
def view_post(data=None, id=None):
    post = Post.get_by_id(id)
    return app.render('posts/view.html', {'post': post})

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_post(data=None, id=None):
    post = Post.get_by_id(id)

    if data['method'] == 'POST':
        post.title = data['data'].get('title', [''])[0]
        post.content = data['data'].get('content', [''])[0]
        post.save()
        return app.redirect('/posts')

    return app.render('posts/edit.html', {'post': post})

@app.route('/delete/<id>', methods=['POST'])
def delete_post(data=None, id=None):
    post = Post.get_by_id(id)
    post.delete_instance()
    return app.redirect('/posts')

@app.route('/login', methods=['GET', 'POST'])
def login(data=None):
    if data['method'] == 'POST':
        user = auth.login(data)
        if user is not None:
            return user
    return app.render('posts/login.html')

if __name__ == '__main__':
    migrate([Post])
    app.run()
~~~

- DarkFreamMega/templates/login.html:
~~~html
{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card mt-5">
            <div class="card-header">
                <h3 class="text-center">Login</h3>
            </div>
            <div class="card-body">
                {% if error_message %}
                    <div class="alert alert-danger" role="alert">
                        {{ error_message }}
                    </div>
                {% endif %}
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Login</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
~~~

- DarkFreamMega/templates/edit.html:
~~~html
{% extends "base.html" %}
{% block title %}Edit Post{% endblock %}

{% block content %}
<h1>Edit Post</h1>
<form method="POST">
    <div>
        <label for="title">Title</label>
        <input type="text" name="title" value="{{ post.title }}" required>
    </div>
    <div>
        <label for="content">Content</label>
        <textarea name="content" required>{{ post.content }}</textarea>
    </div>
    <button type="submit">Save</button>
</form>
<a href="/">Back to list</a>
{% endblock %}
~~~

- DarkFreamMega/templates/list.html:
~~~html
{% extends "base.html" %}
{% block title %}Posts{% endblock %}

{% block content %}
<h1>Posts</h1>
<a href="/create" class="btn btn-primary">Create New Post</a>
<table class="table">
    <thead>
        <tr>
            <th>Title</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for post in posts %}
        <tr>
            <td><a href="/posts/{{ post.id }}" class="post-link">{{ post.title }}</a></td>
            <td>
                <a href="/edit/{{ post.id }}" class="btn btn-warning">Edit</a>
                <form action="/delete/{{ post.id }}" method="POST" style="display:inline;">
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
~~~

- DarkFreamMega/templates/view.html:
~~~html
{% extends "base.html" %}
{% block title %}{{ post.title }}{% endblock %}

{% block content %}
<h1>{{ post.title }}</h1>
<p>{{ post.content }}</p>
<a href="/">Back to list</a>
<a href="/edit/{{ post.id }}">Edit</a>
<form action="/delete/{{ post.id }}" method="POST" style="display:inline;">
    <button type="submit">Delete</button>
</form>
{% endblock %}
~~~

- DarkFreamMega/templates/base.html:
~~~html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Posts{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .navbar {
            margin-bottom: 20px;
        }
        .content {
            padding: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">Post Management</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="">Posts</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/create">Create Post</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="content">
            {% block content %}{% endblock %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
~~~

### Пояснение:
В этом примере мы создали пример простого приложения постов
- ##### В файле `app.py` мы создали приложение DarkFream, добавили маршруты:
- `/` первая страница со всеми постами
- `/create` страница создания поста (можно зайти еслси пользователь вошол в систему)
- `/posts/<id>` страница просмотра определёного поста
- `/edit/<id>` страница редактирования постов
- `delete/<id>` страница удаления поста
- `/login/` страница для входа в систему

### Примечание:
В этом примере мы использовали функцию `migrate([Post])` которая встроеная в DarkFream и нужна для создания бд с моделью User (Рекомендую всегда вставлять эту строчку).
Также в DarkFream присутствует встроеная админка доступная по адресу `/admin/`

### Контакты
- **ВКонтакте**: https://vk.com/vsp210
- **Телеграм**: https://t.me/vsp210
- **Электронная почта**: vsp210@gmail.com
- **Проект на pypi.org**: https://pypi.org/project/DarkFream/1.1.8/

### DarkFream - Мой собственный фреймворк с открытым исходным кодом

## Предупреждаю!
## После любых изменений несчитая шаблонов нужно перезапускать сервер

##### Версия 2 (beta)

#### Список изменений:
- ##### Улучшена скорость
- ##### Добавлена возможность создания большой кастомизации
- ##### системы шифрования данных через сессии
- ##### Добавлена возможность создания кастомных шаблонов
