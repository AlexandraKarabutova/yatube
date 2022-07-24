from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов /about/author/ и /about/tech/."""
        response_author = self.guest_client.get('/about/author/')
        response_tech = self.guest_client.get('/about/tech/')
        static_urls = {
            response_author.status_code: HTTPStatus.OK,
            response_tech.status_code: HTTPStatus.OK,
        }
        for value, expected in static_urls.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов /about/author/ и /about/tech/."""
        response_author = self.guest_client.get('/about/author/')
        response_tech = self.guest_client.get('/about/tech/')
        static_templates = {
            response_author: 'about/author.html',
            response_tech: 'about/tech.html',
        }
        for value, expected in static_templates.items():
            with self.subTest(value=value):
                self.assertTemplateUsed(value, expected)
