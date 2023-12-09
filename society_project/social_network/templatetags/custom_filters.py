from django import template
from django.utils.timesince import timesince
from django.utils import timezone
from social_profile.models import FriendPost
register = template.Library()

@register.filter
def custom_timesince(value):
    now = timezone.now()
    time_difference = now - value
    if time_difference.days > 0:
        return f'{time_difference.days} day'
    elif time_difference.seconds < 3600:
        return f'{time_difference.seconds // 60} minutes'
    else:
        return f'{time_difference.seconds // 3600} hours'

@register.filter
def unique_users(comments):
    user_list = []
    unique_comments = []
    for comment in comments:
        if comment.user not in user_list:
            user_list.append(comment.user)
            unique_comments.append(comment)
    return unique_comments

@register.filter(name='is_friend_post')
def is_friend_post(post):
    return isinstance(post, FriendPost)