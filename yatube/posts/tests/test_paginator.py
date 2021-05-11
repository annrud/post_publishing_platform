from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Запись в тестовую БД."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='anna',
                                            email='anna@mail.ru')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Группа 1 для проведения тестов.',
        )
        for i in range(13):
            Post.objects.create(
                text=f'Текст поста {i}.',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        """Неавторизованный клиент."""
        self.guest_client = Client()
        cache.clear()

    def test_page_contains_correct_number_records(self):
        """Первая страница содержит 10 постов,
        вторая страница - 3 поста.
        """
        url_names = (
            reverse('index'),
            reverse('group_posts', kwargs={'slug': self.group.slug}),
            reverse('profile', kwargs={'username': self.user.username}),
        )
        for address in url_names:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(len(
                    response.context.get('page').object_list), 10
                )
        for address in url_names:
            with self.subTest():
                response = self.guest_client.get(address + '?page=2')
                self.assertEqual(len(
                    response.context.get('page').object_list), 3
                )
