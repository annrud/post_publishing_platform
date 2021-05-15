from http import HTTPStatus

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class CacheTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CacheTestCase, cls).setUpClass()
        """Запись в тестовую БД."""
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
        """Неавторизованный пользователь"""
        self.guest_client = Client()

    def test_cache_index(self):
        response_1 = self.guest_client.get(reverse('index'))
        key = make_template_fragment_key('index_page')
        result = cache.get(key)
        Post.objects.create(
            text='Тест поста №2.',
            author=self.author,
        )
        response_2 = self.guest_client.get(reverse('index'))
        self.assertIn('page', response_1.context)
        self.assertEqual(response_1.status_code, HTTPStatus.OK)
        self.assertEqual(response_2.status_code, HTTPStatus.OK)
        self.assertNotEqual(result, None)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(reverse('index'))
        self.assertEqual(response_3.status_code, HTTPStatus.OK)
        self.assertNotEqual(response_1.content, response_3.content)
