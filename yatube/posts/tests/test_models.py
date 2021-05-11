from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Запись в тестовую БД."""
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Группа для проведения тестов.'
        )
        cls.post = Post.objects.create(
            text='Текст поста длиннее 15 символов.',
            author=User.objects.create_user(username='Galina'),
            group=cls.group
        )

    def test_str_group(self):
        """__str__ строка модели Group
        совпадает с ожидаемой.
        """
        self.assertEqual(str(self.group), self.group.title)

    def test_str_post(self):
        """__str__ строка модели Post
        совпадает с ожидаемой.
        """
        self.assertEqual(str(self.post), self.post.text[:15])
