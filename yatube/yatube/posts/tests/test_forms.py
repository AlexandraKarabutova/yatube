import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.auth)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст поста',
            'group': PostFormTests.group.id,
            'image': uploaded,
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
                image='posts/small.gif',
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


class CommentFormTests(TestCase):
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
            author=CommentFormTests.auth,
            text='Тестовый текст',
            group=CommentFormTests.group,
        )

        cls.form = CommentForm()

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTests.auth)
        self.guest_client = Client()
        self.form_data = {
            'text': 'Текст комментария'
        }

    def test_add_comment(self):
        """Только авторизованный пользователь может комментировать пост,
        комментарий появляется на странице поста."""
        response = self.authorized_client.post(
            reverse(
                'posts:post_detail',
                args=(f'{CommentFormTests.post.pk}',)
            ),
            self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Текст комментария')

    def test_add_comment_guest(self):
        """Неавторизованный пользователь не сможет добавить комментарий."""
        response = self.guest_client.post(
            reverse(
                'posts:post_detail',
                args=(f'{CommentFormTests.post.pk}',)
            ),
            self.form_data
        )
        self.assertNotContains(response, 'Текст комментария')
        self.assertFalse(
            Comment.objects.filter(text='Текст комментария').exists()
        )


class FollowFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='Author')
        cls.post = Post.objects.create(
            author=FollowFormTests.auth,
            text='Тестовый текст',
        )

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='Not_Author')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_follow_response(self):
        """Авторизованный пользователь может подписаться
        на других пользователей."""
        response = self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{FollowFormTests.auth.username}'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_follow_count(self):
        """При подписке на пользователя создается объект класса Follow."""
        count = Follow.objects.count()
        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{FollowFormTests.auth.username}'}
            )
        )
        self.assertEqual(Follow.objects.count(), count + 1)

    def test_unfollow_response(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.user,
            author=FollowFormTests.auth
        )
        count = Follow.objects.count()
        response = self.authorized_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': f'{FollowFormTests.auth.username}'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), count - 1)
