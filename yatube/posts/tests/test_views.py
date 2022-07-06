from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()


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
        cls.post = Post.objects.create(
            author=PostPagesTests.author,
            text='Тестовый длинный пост с группой',
            group=PostPagesTests.group,
        )

    def setUp(self):
        super().setUp()
        self.author = Client()
        self.author.force_login(PostPagesTests.author)
        self.guest_client = Client()

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
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.group, PostPagesTests.post.group)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.group.slug}'}
            )
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.group, PostPagesTests.post.group)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)
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
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.group, PostPagesTests.post.group)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)

    def test_post_id_page_show_correct_context(self):
        """Шаблон post_id сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostPagesTests.post.pk}'}
                    )
        )
        first_object = response.context['post']
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.group, PostPagesTests.post.group)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)

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
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.author.get(
            reverse('posts:create_post')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


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

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        responses_paginator = [
            self.guest_client.get(
                reverse('posts:index') + '?page=2'
            ),
            self.guest_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': f'{PaginatorViewsTest.group.slug}'}
                ) + '?page=2'
            ),
            self.guest_client.get(
                reverse(
                    'posts:profile',
                    kwargs={
                        'username': f'{PaginatorViewsTest.author.username}'
                    }
                ) + '?page=2'
            )
        ]
        for response in responses_paginator:
            self.assertEqual(len(response.context['page_obj']), 3)
