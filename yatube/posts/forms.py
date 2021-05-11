from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': _('Текст поста'),
            'group': _('Сообщество'),
            'image': _('Изображение'),
        }
        help_texts = {
            'text': _('Не более 3000 символов.'),
            'image': _('Загрузите изображение.'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': _('Комментарий'),
        }
        help_texts = {
            'text': _('Не более 1000 символов.'),
        }
