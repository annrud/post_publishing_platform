from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Запись в тестовую БД."""
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='anna', email='anna@mail.ru'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Группа для проведения тестов.',
        )
        cls.post = Post.objects.create(
            text='Тест поста тут.',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        """Неавторизованный пользователь,
        авторизованный пользователь,
        авторизованный автор поста.
        """
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Galina')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_urls_exists_and_uses_correct_template_for_guest_client(self):
        """Страница доступна любому пользователю,
        URL-адрес использует соответствующий шаблон.
         """
        templates_url_names = {
            '/': 'index.html',
            f'/group/{self.group.slug}/': 'group.html',
            f'/{self.author.username}/': 'profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_url_exists_and_uses_correct_template_for_authorized_client(self):
        """Страница доступна авторизованному пользователю,
        URL-адрес использует соответствующий шаблон.
        """
        templates_url_names = {
            '/new/': 'post_new.html',
            f'/{self.author.username}/{self.post.id}/comment/': 'post.html',
            '/follow/': 'follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_for_authorized_author(self):
        """Страница редактирования поста доступна
        авторизованному автору поста,
        URL-адрес использует соответствующий шаблон.
        """
        response = self.authorized_author.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'post_edit.html')

    def test_url_redirects_correctly_guest_client(self):
        """Страница перенаправит неавторизованного
        пользователя на страницу логина.
        """
        url_names = {
            '/new/': f'{reverse("login")}?next=/new/',
            f'/{self.author.username}/{self.post.id}/edit/':
                f'{reverse("login")}?next=/{self.author.username}'
                f'/{self.post.id}/edit/',
            f'/{self.author.username}/{self.post.id}/comment/':
                f'{reverse("login")}?next=/{self.author.username}'
                f'/{self.post.id}/comment/',
            '/follow/': f'{reverse("login")}?next=/follow/',
            f'/{self.author.username}/follow/':
                f'{reverse("login")}?next=/{self.author.username}/follow/',
            f'/{self.author.username}/unfollow/':
                f'{reverse("login")}?next=/{self.author.username}/unfollow/',
        }
        for address, redirection in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, redirection)

    def test_url_redirects_correctly_authorized_client(self):
        """Страница верно перенаправит авторизованного пользователя."""
        url_names = {
            f'/{self.author.username}/{self.post.id}/edit/':
                f'/{self.author.username}/{self.post.id}/comment/',
            f'/{self.author.username}/follow/': f'/{self.author.username}/',
            f'/{self.author.username}/unfollow/': f'/{self.author.username}/'
        }
        for address, redirection in url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, redirection)

    def test_url_404(self):
        response = self.guest_client.get('404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
