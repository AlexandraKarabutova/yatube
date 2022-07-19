from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.generic.edit import DeleteView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    search_query = request.GET.get('search', '')
    if search_query:
        post_list = Post.objects.filter(
            Q(text__icontains=search_query)
            | Q(group__title__icontains=search_query)
            | Q(author__username__icontains=search_query)
            | Q(author__last_name__icontains=search_query)
            | Q(author__first_name__icontains=search_query)
            | Q(comments__author__username__icontains=search_query)
            | Q(comments__text__icontains=search_query)
        )
    else:
        post_list = Post.objects.select_related('group')
    page_obj = paginator(post_list, request)
    context = {'page_obj': page_obj, }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related()
    page_obj = paginator(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(post_list, request)
    if request.user.is_authenticated and Follow.objects.filter(
        user=user,
        author=author
    ).exists():
        following = True
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    form = CommentForm(request.POST or None)
    comments = post.comments
    context = {
        'post': post,
        'author': author,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def create_post(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author_id = request.user.id
            post.save()
            return redirect('posts:profile', request.user.username)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'is_edit': True}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница подписок текущего пользователя"""
    user = request.user
    authors = user.follower.values_list('author', flat=True)
    post_list = Post.objects.filter(author__id__in=authors)
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj,
        'user': user,
    }
    return render(request, 'posts/follow_index.html', context)


@login_required
def profile_follow(request, username):
    """Функция подписки на автора."""
    author = User.objects.get(username=username)
    user = request.user
    if user.id != author.id and user.id not in author.following.values_list(
        'user',
        flat=True
    ):
        Follow.objects.create(author=author, user=user)
    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    """Функция отмены подписки на автора."""
    author = User.objects.get(username=username)
    user = request.user
    follow_relationship = Follow.objects.get(author=author, user=user)
    follow_relationship.delete()
    return redirect('posts:profile', username=author)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'posts/post_delete.html'
    success_url = reverse_lazy('posts:index')
