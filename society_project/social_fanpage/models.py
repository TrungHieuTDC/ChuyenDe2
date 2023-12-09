from django.db import models
from django.contrib.auth.models import User
from autoslug import AutoSlugField
from django.utils import timezone
class Fanpage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(unique=True, populate_from='name', default='default-slug')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    likes_count = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='fanpage_avatars/', null=True, blank=True) 
    cover_image = models.ImageField(upload_to='fanpage_covers/', null=True, blank=True)
    admins = models.ManyToManyField(User, related_name='admin_of_pages', blank=True)
    is_hidden = models.BooleanField(default=False)
    def __str__(self):
        return self.name
class UserLikeFanpage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_fanpages')
    fanpage = models.ForeignKey('Fanpage', on_delete=models.CASCADE)
class FanpageLike(models.Model):
    fanpage = models.ForeignKey(Fanpage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} likes {self.fanpage.name}"
class FanpagePost(models.Model):
    fanpage = models.ForeignKey(Fanpage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    hidden_for_users = models.ManyToManyField(User, blank=True, related_name='hidden_posts_fanpage')
    comments_closed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username}'s post on {self.fanpage.name}"
class PostImageFanpage(models.Model):
    post = models.ForeignKey(FanpagePost, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images_fanpage/')
class PostVideoFanpage(models.Model):
    post = models.ForeignKey(FanpagePost, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='post_videos_fanpage/')
class CommentFanpage(models.Model):
    post = models.ForeignKey(FanpagePost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    

class CommentImageFanpage(models.Model):
    comment = models.ForeignKey(CommentFanpage, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='comment_images_fanpage/', blank=True, null=True)

class CommentVideoFanpage(models.Model):
    comment = models.ForeignKey(CommentFanpage, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='comment_videos_fanpage/', blank=True, null=True)
    
class LikeCommentFanpage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(CommentFanpage, related_name='likes', on_delete=models.CASCADE)
class ReplyCommentFanpage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey(CommentFanpage, related_name='replies', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    
class LikePostFanpage(models.Model):
    post = models.ForeignKey(FanpagePost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

class ReplyLikeFanpage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(ReplyCommentFanpage, related_name='likes', on_delete=models.CASCADE)
class AlbumFanpage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='album_fanpage')
    name = models.CharField(max_length=255, default='Fanpage Album')
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.ManyToManyField(PostImageFanpage, related_name='albums_fanpage')
    def __str__(self):
        return self.name  