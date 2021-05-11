from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    """Возвращает главную страницу."""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, }
    )


def group_posts(request, slug):
    """Возвращает страницу сообщества с постами."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {
            'group': group,
            'page': page,
        }
    )


@login_required
def new_post(request):
    """Возвращает страницу создания новой записи."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'post_new.html', {'form': form})


def profile(request, username):
    """Возвращает страницу профайла автора со всеми его постами."""
    post_author = get_object_or_404(
        User.objects.prefetch_related('following', 'follower'),
        username=username
    )
    following = Follow.objects.filter(author=post_author).first()
    post_list = post_author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            'post_author': post_author,
            'page': page,
            'following': following,
        }
    )


@login_required
def add_comment(request, username, post_id):
    """Возвращает страницу комментария записи."""
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related('comments'),
        pk=post_id, author__username=username
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('add_comment', username=username, post_id=post_id)
    return render(request, 'post.html', {'form': form, 'post': post})


@login_required
def post_edit(request, username, post_id):
    """Возвращает страницу редактирования записи."""
    if request.user.username != username:
        return redirect('add_comment', username=username, post_id=post_id)
    post = get_object_or_404(
        Post, pk=post_id, author__username=username
    )
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(
            'add_comment', username=username, post_id=post_id
        )
    return render(request, 'post_edit.html',
                  {'form': form, 'username': username, 'post': post})


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__in=request.user.follower.values('author'))
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {
            'page': page
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(
            user=request.user,
            author=author).exists() and author != request.user:
        Follow.objects.create(user=request.user, author=author)
        cache.delete(make_template_fragment_key('follow_page',
                                                [request.user.username]))
    return redirect(
        'profile', username=username
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
        cache.delete(make_template_fragment_key('follow_page',
                                                [request.user.username]))
    return redirect(
        'profile', username=username
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
