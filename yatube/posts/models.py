from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель сообщества."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    """Модель поста в сообществе."""
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name='posts', blank=True, null=True)
    image = models.ImageField(upload_to='media/', blank=True, null=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        default_related_name = 'posts'
        ordering = ['-pub_date']


class Comment(models.Model):
    """Модель комментария к посту."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True)


class Follow(models.Model):
    """Модель подписки на автора поста."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')
