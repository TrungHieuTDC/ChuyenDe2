from django.db import models
from django.contrib.auth.models import User
from autoslug import AutoSlugField
from django.utils import timezone
from social_profile.models import PostUser
# Create your models here.
  
class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = AutoSlugField(unique=True, populate_from='name')
    posts = models.ManyToManyField('Post', related_name='groups')
    members = models.ManyToManyField(User, through='Membership')
    visits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='group_avatars/', null=True, blank=True) 
    background_image = models.ImageField(upload_to='group_backgrounds/', null=True, blank=True)
    admins = models.ManyToManyField(User, related_name='admin_groups')
    access = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='Public')
    requires_approval = models.BooleanField(default=False)
    post_approval_enabled = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_posts', default=1) 
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  
    created_at = models.DateTimeField(default=timezone.now)
    hidden_for_users = models.ManyToManyField(User, blank=True, related_name='hidden_posts')
    comments_closed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    def __str__(self):
        return self.title
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images/')
class PostVideo(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='post_videos/')
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    

class CommentImage(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='comment_images/', blank=True, null=True)

class CommentVideo(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='comment_videos/', blank=True, null=True)
    
class LikeComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name='likes', on_delete=models.CASCADE)
class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey(Comment, related_name='replies', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

class ReplyLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, related_name='likes', on_delete=models.CASCADE)
class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('banned', 'Banned'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    def __str__(self):
        return f'{self.user.username} - {self.group.name}'
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,blank = True,null = True)
    avatar = models.ImageField(upload_to="profile_pics",blank=True,null=True)
    background_avatar = models.ImageField(upload_to="background_pics",blank=True,null=True)
    bio = models.TextField()
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    saved_posts = models.ManyToManyField('Post', related_name='saved_by_profiles')
    saved_posts_user = models.ManyToManyField('social_profile.PostUser', related_name='saved_by_profiles_user')
    saved_posts_fanpage = models.ManyToManyField('social_fanpage.Fanpage', related_name='saved_by_profiles_fanpage')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    social_link = models.URLField(max_length=200, blank=True, null=True)
    interested = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=20, blank=True, null=True)
    marital_choices = [
        ('single', 'Single'),
        ('dating', 'Dating'),
        ('married', 'Married'),
    ]
    marital = models.CharField(max_length=10, choices=marital_choices, blank=True, null=True)
    def __str__(self):
        return str(self.user)
class LikeNotification(models.Model):
    user_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_owned')
    user_liker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_liked')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='post_likes')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='group_likes')
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user_liker} liked {self.post.content} in {self.group.name} group"
    
# class LikeNotificationComment(models.Model):
#     user_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_owned_comment')
#     user_liker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_liked_comment')
#     comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='comment_likes')
#     group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='group_likes_comment')
#     created_at = models.DateTimeField(default=timezone.now)
#     is_read = models.BooleanField(default=False)
#     def __str__(self):
#         return f"{self.user_liker} liked {self.post.content} in {self.group.name} group"

    