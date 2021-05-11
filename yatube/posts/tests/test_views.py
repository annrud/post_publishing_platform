import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Follow, Group, Post, User


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Временная папка для медиа-файлов.
        Запись в тестовую БД.
        """
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(
            username='anna', email='anna@mail.ru'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Группа 1 для проведения тестов.',
        )
        cls.post = Post.objects.create(
            text='Текст поста 1.',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('index'): 'index.html',
            reverse('group_posts',
                    kwargs={'slug': self.group.slug}): 'group.html',
            reverse('profile',
                    kwargs={'username': self.author.username}): 'profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_and_uses_correct_template_for_authorized_client(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('add_comment',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}): 'post.html',
            reverse('new_post'): 'post_new.html',
            reverse('follow_index'): 'follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_for_authorized_author(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.authorized_author.get(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'post_edit.html')

    def test_index_shows_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('page', response.context)
        self.assertGreater(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)

    def test_group_shows_correct_context(self):
        """Шаблон group.html сформирован
        с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertIn('page', response.context)
        self.assertGreater(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_post_not_in_group_2(self):
        """Пост не попал в группу, для
        которой не был предназначен.
        """
        self.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Группа 2 для проведения тестов.',
        )
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group_2.slug}'})
        )
        self.assertIn('page', response.context)
        posts = response.context['page']
        self.assertNotIn(self.post, posts)

    def test_post_new_shows_correct_context(self):
        """Шаблон post_new.html
         сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('new_post')
        )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_shows_correct_context(self):
        """Шаблон profile.html
        сформирован с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.author.username})
        )
        self.assertIn('post_author', response.context)
        post_author = response.context['post_author']
        self.assertIsInstance(post_author, User)
        self.assertIn('following', response.context)
        self.assertIn('page', response.context)
        page = response.context['page']
        self.assertGreater(len(page), 0)
        post = page[0]
        self.assertEqual(post_author, self.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(page.paginator.count, 1)

    def test_add_comment_shows_correct_context(self):
        """Шаблон post.html сформирован
         с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('add_comment',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
        form_field = response.context['form'].fields['text']
        self.assertIsInstance(form_field, forms.fields.CharField)
        self.assertIn('post', response.context)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(post.author.posts.count(), 1)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit.html
         сформирован с правильным контекстом.
         """
        response = self.authorized_author.get(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        form_fields_filled = {
            'group': self.group.id,
            'text': self.post.text,
            'image': self.post.image,
        }
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('username', response.context)
        self.assertIsInstance(response.context['username'], str)
        self.assertIn('post', response.context)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.group.id, form_fields_filled['group'])
        self.assertEqual(post.text, form_fields_filled['text'])
        self.assertEqual(post.image, form_fields_filled['image'])
        for value, expected in form_fields_filled.items():
            with self.subTest(value=value):
                form_field = response.context['form'].initial[value]
                self.assertEqual(form_field, expected)

    def test_follow_and_unfollow_exist(self):
        """Авторизованный пользователь может
         подписываться на автора поста
         и отписываться от него.
        """
        response = self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        follow = Follow.objects.filter(user=self.user, author=self.author)
        self.assertIs(follow.exists(), True)
        response = self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIs(follow.exists(), False)

    def test_follow_shows_correct_context(self):
        """Шаблон follow.html
        сформирован с правильным контекстом.
        """
        authorized_client_2 = Client()
        user_2 = User.objects.create_user(username='Vladimir')
        authorized_client_2.force_login(user_2)
        authorized_client_2.get(
            reverse('profile_follow',
                    kwargs={'username': self.author.username}))
        response = authorized_client_2.get(reverse('follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('page', response.context)
        self.assertGreater(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page']), 0)
