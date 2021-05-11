from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_accessible_by_name_and_use_correct_template(self):
        """URL, генерируемый при помощи name, доступен,
        URL-адрес использует соответствующий шаблон.
        """
        templates_pages_names = {
            'author.html': reverse('about:author'),
            'tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
