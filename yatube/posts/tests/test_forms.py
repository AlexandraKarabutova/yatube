from ..forms import PostForm
from ..models import Group, Post
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.auth = User.objects.create_user(username='Author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=PostFormTests.auth,
            text='Тестовый текст',
            group=PostFormTests.group,
        )

        cls.form = PostForm()

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.auth)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст поста',
            'group': PostFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Тестовый текст поста')
        self.assertContains(response, PostFormTests.group.id)
        self.assertRedirects(
            response,
            f'/profile/{PostFormTests.auth.username}/',
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text='Тестовый текст поста',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            'text': 'Измененный текст поста',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=(f'{PostFormTests.post.pk}',)
            ),
            form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'/posts/{PostFormTests.post.pk}/',
        )
        response_post_detail = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostFormTests.post.pk}'}
            )
        )
        self.assertContains(response_post_detail, 'Измененный текст поста')
