from django.contrib import admin
from social_fanpage.models import *
# Register your models here.
admin.site.register(Fanpage)
admin.site.register(FanpagePost)
admin.site.register(PostImageFanpage)
admin.site.register(PostVideoFanpage)
admin.site.register(ReplyLikeFanpage)
admin.site.register(ReplyCommentFanpage)