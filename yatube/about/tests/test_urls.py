from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адреса."""
        url_addresses = (
            '/about/author/',
            '/about/tech/'
        )
        for url_address in url_addresses:
            with self.subTest():
                response = self.guest_client.get(url_address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
