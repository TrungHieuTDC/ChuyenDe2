from django.contrib import admin
from .models import Profile,Group,Membership,Post,PostImage,Like,Comment,PostVideo,CommentImage,CommentVideo,LikeNotification
# Register your models here.
class InfoAppModel(admin.ModelAdmin):
    fields = ('user', 'birthdate', 'gender','bio','avatar','mobile','address','social_link','interested','language','marital','background_avatar')
    search_fields = ('user','gender')
    list_display = ('user','birthdate','gender','avatar','mobile','address','social_link','interested','language','marital','background_avatar')
    # Cấu hình liên kết cho trường 'name'
    list_display_links = ('user',)
    list_editable = ('birthdate', 'gender')
class InfoGroup(admin.ModelAdmin):
    fields = ('name','description','avatar','background_image','admins','access','post_approval_enabled')
    list_display = ('name','description','avatar','background_image','get_admins','access','post_approval_enabled')
    def get_admins(self, obj):
        return ", ".join([admin.username for admin in obj.admins.all()])
    get_admins.short_description = "Admins"
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'display_images')  # Thêm 'display_images' vào list_display

    def display_images(self, obj):
        # Tạo một chuỗi HTML để hiển thị các hình ảnh
        images_html = ""
        for image in obj.post.postimage_set.all():
            images_html += f'<img src="{image.image.url}" alt="Post Image" width="100" />'

        return images_html

    display_images.short_description = 'Images' 
admin.site.register(Profile,InfoAppModel)
admin.site.register(Group,InfoGroup)
admin.site.register(Membership)
admin.site.register(Post)
admin.site.register(PostImage, PostImageAdmin)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(PostVideo)
admin.site.register(CommentImage)
admin.site.register(CommentVideo)
admin.site.register(LikeNotification)
