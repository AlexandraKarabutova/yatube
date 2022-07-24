import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=PostPagesTests.author,
            text='Тестовый длинный пост с группой',
            group=PostPagesTests.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.author = Client()
        self.author.force_login(PostPagesTests.author)

        self.guest_client = Client()

        self.user = User.objects.create_user(username='Not_Author')
        self.authorised_user = Client()
        self.authorised_user.force_login(self.user)

        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostPagesTests.group.slug}'}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': f'{PostPagesTests.author.username}'}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostPagesTests.post.pk}'}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostPagesTests.post.pk}'}
                    ): 'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostPagesTests.post.text,
            first_object.group: PostPagesTests.post.group,
            first_object.author: PostPagesTests.post.author,
            first_object.pub_date: PostPagesTests.post.pub_date,
            first_object.image: PostPagesTests.post.image,
        }
        for value, expected in context_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_index_page_cache(self):
        """Список постов на главной странице сайта хранится в кэше."""
        post_cache = Post.objects.create(
            author=PostPagesTests.author,
            text='Тестовый пост, который должен сохраниться в кэше',
        )
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertContains(response, first_object.text)
        self.assertEqual(first_object.text, post_cache.text)
        count_page_obj = len(response.context['page_obj'])
        self.assertEqual(count_page_obj, 2)
        post_cache.delete()
        self.assertEqual(first_object.text, post_cache.text)
        self.assertEqual(len(response.context['page_obj']), 2)
        cache.clear()
        response_new = self.guest_client.get(reverse('posts:index'))
        second_object = response_new.context['page_obj'][0]
        count_page_obj = len(response_new.context['page_obj'])
        self.assertEqual(count_page_obj, 1)
        self.assertNotEqual(second_object.text, first_object.text)
        self.assertNotContains(response_new, first_object.text)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.group.slug}'}
            )
        )
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostPagesTests.post.text,
            first_object.group: PostPagesTests.post.group,
            first_object.author: PostPagesTests.post.author,
            first_object.pub_date: PostPagesTests.post.pub_date,
            first_object.image: PostPagesTests.post.image,
        }
        for value, expected in context_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        Post.objects.create(
            author=PostPagesTests.author,
            text='Тестовый длинный пост без группы',
        )
        count_page_obj = len(response.context['page_obj'])
        self.assertEqual(count_page_obj, 1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.author.username}'})
        )
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostPagesTests.post.text,
            first_object.group: PostPagesTests.post.group,
            first_object.author: PostPagesTests.post.author,
            first_object.pub_date: PostPagesTests.post.pub_date,
            first_object.image: PostPagesTests.post.image,
        }
        for value, expected in context_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_id_page_show_correct_context(self):
        """Шаблон post_id сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostPagesTests.post.pk}'}
                    )
        )
        first_object = response.context['post']
        context_names = {
            first_object.text: PostPagesTests.post.text,
            first_object.group: PostPagesTests.post.group,
            first_object.author: PostPagesTests.post.author,
            first_object.pub_date: PostPagesTests.post.pub_date,
            first_object.image: PostPagesTests.post.image,
        }
        for value, expected in context_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTests.post.pk}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.author.get(
            reverse('posts:create_post')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_follow_index_show_correct_context(self):
        """Новая запись появляется в follow_index тех,
        кто подписан на этого автора."""
        Follow.objects.create(author=PostPagesTests.author, user=self.user)
        response = self.authorised_user.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        response_new = self.author.get(reverse('posts:follow_index'))
        self.assertNotContains(response_new, PostPagesTests.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        POST_QUANTITY: int = 13
        Post.objects.bulk_create(
            Post(
                author=PaginatorViewsTest.author,
                group=PaginatorViewsTest.group,
                text=f'Тестовый пост {i}')
            for i in range(POST_QUANTITY)
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        cache.clear()

    def test_first_page_contains_ten_posts(self):
        """Проверка: количество постов на первой странице равно 10."""
        POST_LIMIT: int = 10
        responses_paginator = [
            self.guest_client.get(reverse('posts:index')),
            self.guest_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': f'{PaginatorViewsTest.group.slug}'}
                )
            ),
            self.guest_client.get(
                reverse(
                    'posts:profile',
                    kwargs={
                        'username': f'{PaginatorViewsTest.author.username}'
                    }
                )
            )
        ]
        for response in responses_paginator:
            self.assertEqual(len(response.context['page_obj']), POST_LIMIT)

    def test_second_page_contains(self):
        """Проверка: на второй странице должно быть три поста."""
        page_number = {'page': 2}
        responses_paginator = [
            self.guest_client.get(
                reverse('posts:index'), page_number
            ),
            self.guest_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': f'{PaginatorViewsTest.group.slug}'}
                ), page_number
            ),
            self.guest_client.get(
                reverse(
                    'posts:profile',
                    kwargs={
                        'username': f'{PaginatorViewsTest.author.username}'
                    }
                ), page_number
            )
        ]
        for response in responses_paginator:
            self.assertEqual(len(response.context['page_obj']), 3)
