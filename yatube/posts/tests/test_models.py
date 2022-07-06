from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()
POST_LIMIT: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostModelTest.user,
            text='Тестовый длинный пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_group_name = group.title
        post = PostModelTest.post
        expected_post_name = post.text[:POST_LIMIT]
        object_names = {
            expected_group_name: str(group),
            expected_post_name: str(post),
        }
        for value, expected in object_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
