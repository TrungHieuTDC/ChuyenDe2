from django.db import models

from django.contrib.auth.models import User
from autoslug import AutoSlugField
from django.utils import timezone
# Create your models here.
# Create your models here.
class PostUser(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  
    created_at = models.DateTimeField(default=timezone.now)
    hidden_for_users = models.ManyToManyField(User, blank=True, related_name='hidden_posts_user')
    comments_closed = models.BooleanField(default=False)
    PUBLIC = 'public'
    FRIEND = 'friend'
    PRIVATE = 'private'

    PRIVACY_CHOICES = [
    (PUBLIC, 'Public'),
    (FRIEND, 'Friend'),
    (PRIVATE, 'Private'),
    ]
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default=PUBLIC)
    def __str__(self):
        return self.content
class FriendPost(models.Model):
    post = models.ForeignKey(PostUser, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_posts')
    friend_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_posts')
    created_at = models.DateTimeField(default=timezone.now)
class PostImageUser(models.Model):
    post = models.ForeignKey(PostUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images_user/')
class PostVideoUser(models.Model):
    post = models.ForeignKey(PostUser, on_delete=models.CASCADE, related_name='videos_user')
    video = models.FileField(upload_to='post_videos_user/')
class CommentUser(models.Model):
    post = models.ForeignKey(PostUser, on_delete=models.CASCADE, related_name='comments_user')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
class CommentImageUser(models.Model):
    comment = models.ForeignKey(CommentUser, on_delete=models.CASCADE, related_name='images_user')
    image = models.ImageField(upload_to='comment_images_user/', blank=True, null=True)

class CommentVideoUser(models.Model):
    comment = models.ForeignKey(CommentUser, on_delete=models.CASCADE, related_name='videos_user')
    video = models.FileField(upload_to='comment_videos_user/', blank=True, null=True)
    
class LikeCommentUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(CommentUser, related_name='likes_user', on_delete=models.CASCADE)
class ReplyUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey(CommentUser, related_name='replies_user', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    
class LikeUser(models.Model):
    post = models.ForeignKey(PostUser, on_delete=models.CASCADE, related_name='likes_user')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

class ReplyLikeUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(ReplyUser, related_name='likes_user', on_delete=models.CASCADE)
class Album(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='album')
    name = models.CharField(max_length=255, default='User Album')
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.ManyToManyField(PostImageUser, related_name='albums')
    def __str__(self):
        return self.name  
class WorkUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.company_name}"
class EducationUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    school_name = models.CharField(max_length=255)
    school_address = models.TextField()
    end_date = models.DateField(null=True, blank=True)  
    def __str__(self):
        return f"{self.user.username}'s Education at {self.school_name}"
class PlacesUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    year_lived = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.city}, {self.district} ({self.year_lived})"
class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_of')
    is_friend = models.BooleanField(default=False)
    is_following = models.BooleanField(default=False)
    is_blocking = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def is_blocked_by(self, user):
        return self.is_blocking and self.user == user
    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"
    def has_sent_friend_request(user, friend):
        return Friendship.objects.filter(user=user, friend=friend, is_friend=False, is_following=False, is_blocking=False).exists()