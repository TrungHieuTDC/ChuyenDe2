from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Group

@receiver(post_save, sender=Post)
def auto_approve_post(sender, instance, created, **kwargs):
    # Kiểm tra xem tính năng duyệt bài viết có được bật hay không
    if instance.group.post_approval_enabled and created and not instance.is_approved:
        # Nếu tính năng duyệt bài viết đang bật và bài viết là mới được tạo và chưa được duyệt, tự động duyệt bài viết
        instance.is_approved = True
        instance.save()

