from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


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
        User, username=username
    )
    following = request.user.is_authenticated and Follow.objects.filter(
        author=post_author,
        user=request.user
    ).exists()
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


def post_view(request, username, post_id):
    """Возвращает страницу просмотра записи с комментариями."""
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related('comments'),
        pk=post_id, author__username=username
    )
    following = request.user.is_authenticated and Follow.objects.filter(
        author=post.author,
        user=request.user
    ).exists()
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'post': post,
            'comments': post.comments.all(),
            'form': form,
            'following': following,
        }
    )


@login_required
def add_comment(request, username, post_id):
    """Добавляет комментарий к посту."""
    if request.method == 'POST':
        post = get_object_or_404(
            Post.objects.select_related('author'),
            pk=post_id, author__username=username
        )
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    """Возвращает страницу редактирования записи."""
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(
        Post, pk=post_id, author__username=username
    )
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(
            'post', username=username, post_id=post_id
        )
    return render(request, 'post_edit.html',
                  {'form': form, 'username': username, 'post': post})


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {
            'page': page,
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
            user=request.user,
            author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect(
        'profile', username=username
    )


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(user=request.user,
                                   author__username=username)
    if follow.exists():
        follow.delete()
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
