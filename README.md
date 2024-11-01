# DarkFream
Мой собственный фреймворк DarkFream.

## Привет я молодой 14 летний программист который патается создавать невозможное


#### DarkFream - Мой собственный фреймворк основаный на идеи создать что то интересное
DarkFream - это фреймворк который позволяет создавать крайне простые веб-приложения


#### DarkFream - Основные функции:
+ **Создание моделей** - Создание моделей для базы данных крайне схожая с фреймворком Django но имеет меньший функционал например:
- **CharField**
- **TextField**
- **IntegerField**

+ **Работа с шаблонами** - Работа с шаблонами похожая с Django или Flask например:
- **render** (рендерит шаблон)
- **redirect** (изменяет ваш url)

### Запуск проекта

- для запуска требуется слонировать репозиторий командой:
```git clone https://github.com/vsp210/DarkFreamMega.git```
- затем рекомендую создать venv
~~~bash
py -* -m venv venv
source venv/Scripts/activate
~~~
где * - ваша версия пайтона
- перейдите в папку:
~~~bash
cd DarkFreamMega
~~~
- затем установите зависимости командой:
~~~bash
pip install -r requirements.txt
~~~


### Пример создания простого калькулятора:

- DarkFreamMega/app.py:
~~~python
from DarkFream.app import *
from DarkFream.orm import *
from DarkFream.auth import Auth

app = DarkHandler.darkfream
auth = Auth(app)


@app.route('/')
@auth.login_required('/login/')
def index(data=None):
    return 'Hello, World!'

@app.route('/login/', methods=['GET', 'POST'])
def login(data=None):
    if data['method'] == 'POST':
        return auth.login(data)
    return app.render('login.html')

@app.route('/logout/', methods=['GET', 'POST'])
@auth.login_required('/login/')
def logout(data=None):
    return auth.logout(data)

@app.route('/test/<id>', methods=['GET', 'POST'])
def test(data=None, id=None):
    return 'Test: ' + id

if __name__ == "__main__":
    migrate([User])
    run()
~~~

- DarkFreamMega/templates/login.html:
~~~html
<!DOCTYPE html>
<html>
    <head>
        <title>Login</title>
        <meta charset="UTF-8"> <!-- Рекомендую использовать эту строчку для избежания ошибки кодировки -->
    </head>
    <body>
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
    </body>
</html>
~~~

### Пояснение:
В этом примере мы создали пример калькулятора
- ##### В файле `app.py` мы создали приложение DarkFream, добавили маршруты:
- `/` первая страница на которую можно зайти еслси пользователь вошол в систему
- `/login/` для входа в систему
- `/logout/` для выхода из системы
- `/test/<id>` для вывода id
- ##### В файле `templates/login.html` мы создали форму для входа в систему


### Примечание:
В этом примере мы использовали функцию `migrate([User])` которая встроеная в DarkFream и нужна для создания бд с моделью User (Рекомендую всегда вставлять эту строчку).
Также в DarkFream присутствует встроеная админка доступная по адресу `/admin/` (если вы выполнили команду `migrate([User])` то в бд будет пользователь админ с логином admin и паролем admin)

### Контакты
- **ВКонтакте**: https://vk.com/vsp210
- **Телеграм**: https://t.me/vsp210
- **Электронная почта**: vsp210@gmail.com

### DarkFream - Мой собственный фреймворк с открытым исходным кодом

## Предупреждаю!
## После любых изменений несчитая шаблонов нужно перезапускать сервер

##### Версия 1 (release)
