from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PostUser)
admin.site.register(PostImageUser)
admin.site.register(PostVideoUser)
admin.site.register(CommentUser)
admin.site.register(CommentImageUser)
admin.site.register(CommentVideoUser)
admin.site.register(LikeUser)
admin.site.register(Album)
admin.site.register(WorkUser)
admin.site.register(EducationUser)
admin.site.register(PlacesUser)
admin.site.register(Friendship)
admin.site.register(FriendPost)