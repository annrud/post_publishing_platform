import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
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

    def checking_post_content(self, post, response):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group, self.group)
        self.assertContains(response, '<img')

    def checking_profile_content(self, response):
        self.assertIn('following', response.context)
        self.assertIsInstance(response.context['following'], bool)
        self.assertIn('post_author', response.context)
        post_author = response.context['post_author']
        self.assertIsInstance(post_author, User)
        self.assertIn('page', response.context)
        page = response.context['page']
        self.assertGreater(len(page), 0)
        post = page[0]
        self.assertIsInstance(post, Post)
        self.checking_post_content(post, response)
        self.assertEqual(page.paginator.count, 1)

    def checking_post_page_content(self, response):
        self.assertIn('form', response.context)
        self.assertIn('post', response.context)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.checking_post_content(post, response)
        self.assertEqual(post.author.posts.count(), 1)

    def test_urls_exists_and_uses_correct_template_for_guest_client(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('index'): 'index.html',
            reverse('group_posts',
                    kwargs={'slug': self.group.slug}): 'group.html',
            reverse('profile',
                    kwargs={'username': self.author.username}): 'profile.html',
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}): 'post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_and_uses_correct_template_for_authorized_client(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
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
        self.assertIn('page', response.context)
        self.assertIsInstance(response.context['page'], Page)
        self.assertGreater(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertIsInstance(post, Post)
        self.checking_post_content(post, response)

    def test_group_shows_correct_context(self):
        """Шаблон group.html сформирован
        с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertIn('page', response.context)
        self.assertIsInstance(response.context['page'], Page)
        self.assertGreater(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertIsInstance(post, Post)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.checking_post_content(post, response)

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
        self.assertIsInstance(response.context['page'], Page)
        posts = response.context['page']
        self.assertNotIn(self.post, posts)

    def test_post_new_shows_correct_form(self):
        """Шаблон post_new.html выводит
        правильную форму создания поста.
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

    def test_profile_shows_correct_context_for_guest_client(self):
        """Шаблон profile.html для анонимного пользователя
        сформирован с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.author.username})
        )
        self.assertEqual(response.context['following'], False)
        self.checking_profile_content(response)

    def test_profile_shows_correct_context_for_authorized_client(self):
        """Шаблон profile.html для авторизованного пользователя
        сформирован с правильным контекстом.
        """
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.author.username}))
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.author.username})
        )
        self.assertEqual(response.context['following'], True)
        self.checking_profile_content(response)

    def test_post_shows_correct_context_for_guest_client(self):
        """Шаблон post.html для анонимного пользователя
        сформирован с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], CommentForm)
        self.checking_post_page_content(response)

    def test_post_shows_correct_context_for_authorized_client(self):
        """Шаблон post.html для авторизованного пользователя
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], CommentForm)
        form_field = response.context['form'].fields['text']
        self.assertIsInstance(form_field, forms.fields.CharField)
        self.checking_post_page_content(response)

    def test_can_add_comment(self):
        """В шаблон post.html авторизованный пользователь
        может добавить комментарий.
        """
        comments_count = self.post.comments.count()
        form_data = {'text': 'Это новый комментарий'}
        response = self.authorized_client.post(
            reverse('add_comment',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             reverse('post',
                                     kwargs={'username': self.author.username,
                                             'post_id': self.post.id}))
        self.assertNotEqual(comments_count, self.post.comments.count())

    def test_can_not_add_comment(self):
        """В шаблон post.html анонимный пользователь
        не может добавить комментарий.
        """
        comments_count = self.post.comments.count()
        form_data = {'text': 'Это новый комментарий'}
        response = self.guest_client.post(
            reverse('add_comment',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'{reverse("login")}?next=/{self.author.username}'
                             f'/{self.post.id}/comment/')
        self.assertEqual(comments_count, self.post.comments.count())

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

    def test_follow_exist(self):
        """Авторизованный пользователь может
         подписываться на автора поста.
        """
        response = self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.author.username}), follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('profile',
                              kwargs={'username': self.author.username})
        )
        follow = Follow.objects.filter(user=self.user, author=self.author)
        self.assertIs(follow.exists(), True)

    def test_unfollow_exist(self):
        """Авторизованный пользователь может
        отписываться от автора поста.
        """
        response = self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': self.author.username}), follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('profile',
                              kwargs={'username': self.author.username})
        )
        follow = Follow.objects.filter(user=self.user, author=self.author)
        self.assertIs(follow.exists(), False)

    def test_follow_shows_followings_of_client(self):
        """Шаблон follow.html содержит
        подписки пользователя.
        """
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.author.username}))
        post_new = Post.objects.create(
            text='Новый пост.',
            author=self.author,
            group=self.group,
            image=self.uploaded
        )
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('page', response.context)
        self.assertIsInstance(response.context['page'], Page)
        self.assertIn(post_new, response.context['page'])

    def test_follow_do_not_show_followings_of_another_client(self):
        """Шаблон follow.html не содержит
        подписки других пользователей.
        """
        post_new = Post.objects.create(
            text='Новый пост.',
            author=self.author,
            group=self.group,
            image=self.uploaded
        )
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('page', response.context)
        self.assertIsInstance(response.context['page'], Page)
        self.assertNotIn(post_new, response.context['page'])
