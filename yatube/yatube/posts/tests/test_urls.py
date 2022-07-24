from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostsURLTests.author,
            text='Тестовый длинный пост',
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()

        self.user = User.objects.create_user(username='Not_Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author = Client()
        self.author.force_login(PostsURLTests.author)

        cache.clear()

    def test_posts_url_exists_at_desired_location(self):
        """Проверка доступности адресов
        '/', '/group/<slug>/',
        '/profile/<username>/',
        '/posts/<post_id>/',
        '/unexisting_page/'."""
        urls = [
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            f'/profile/{PostsURLTests.author.username}/',
            f'/posts/{PostsURLTests.post.pk}/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response_unexisting_page = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response_unexisting_page.status_code,
            HTTPStatus.NOT_FOUND
        )

    def test_create_url_exists_at_desired_location(self):
        """Страница '/create/' доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница '/create/' перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_exists_at_desired_location(self):
        """Страница '/posts/<post_id>/edit/' доступна автору поста."""
        response = self.author.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirect_not_auth_on_post_id(self):
        """Страница '/posts/<post_id>/edit/'
        перенаправит неавтора поcта на страницу 'post_detail'."""
        response = self.authorized_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{PostsURLTests.post.pk}/')

    def test_posts_url_uses_correct_template(self):
        """Проверка шаблонов для адресов index,
        group_slug, profile, post_id, create, edit."""
        response_index = self.guest_client.get('/')
        response_group = self.guest_client.get(
            f'/group/{PostsURLTests.group.slug}/'
        )
        response_profile = self.guest_client.get(
            f'/profile/{PostsURLTests.author.username}/'
        )
        response_post_id = self.guest_client.get(
            f'/posts/{PostsURLTests.post.pk}/'
        )
        response_create = self.authorized_client.get('/create/')
        response_edit = self.author.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        response_follow_index = self.authorized_client.get('/follow/')
        posts_templates = {
            response_index: 'posts/index.html',
            response_group: 'posts/group_list.html',
            response_profile: 'posts/profile.html',
            response_post_id: 'posts/post_detail.html',
            response_create: 'posts/create_post.html',
            response_edit: 'posts/create_post.html',
            response_follow_index: 'posts/follow_index.html',
        }
        for value, expected in posts_templates.items():
            with self.subTest(value=value):
                self.assertTemplateUsed(value, expected)
