# Yatube

*Yatube - django-проект социальной сети - платформы для публикаций постов.*<br>

*В проекте реализовано:*
- *форма создания учётной записи*
- *форма для публикации поста* 
- *выбор сообщества*
- *редактирование поста*
- *подписка на любимых авторов* 
- *комментарии к постам*
- *админка* 

Запуск проекта:
1. Склонируйте репозиторий в рабочую директорию:<br>
```git clone https://github.com/annrud/post_publishing_platform.git```
2. Установите и активируйте виртуальное окружение:<br>
```python -m venv venv```<br>
```source venv/bin/activate```
3. Установите необходимые зависимости:<br>
```pip install -r requirements.txt```
4. Создайте файл .env c переменными окружения 'SECRET_KEY' и 'DEBUG'=True (режим отладкки включён).
   Для получения 'SECRET_KEY':<br>
 - запустите ```python manage.py shell```
 - напишите:<br>
 ```from django.core.management.utils import get_random_secret_key```<br>
 ```print(get_random_secret_key())```<br>
 ```exit()```
5. Выполните миграции:<br>
```python manage.py migrate```
6. Создайте суперюзера:<br>
 ```python manage.py createsuperuser```
7. Запустите локальный сервер:
```python manage.py runserver```
8. Приложение доступно по адресу http://127.0.0.1:8000/ 
9. Админка сайта доступна на странице http://127.0.0.1:8000/admin