from django.urls import path,re_path
from . import views

app_name ="social_network"
urlpatterns = [
    #group
    path('group', views.group, name="group"),
    path('group/<slug:slug>/', views.group_detail, name='group_detail'),
    path('group/<slug:slug>/join/', views.join_group, name='join_group'),
    path('group/<slug:slug>/leave/', views.leave_group, name='leave_group'),
    path('like_post/', views.like_post, name='like_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('delete-video/<int:video_id>/', views.delete_video, name='delete_video'),
    path('add_comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('add_reply/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('like_reply/<int:reply_id>/', views.like_reply, name='like_reply'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('group_create/', views.group_create, name='group_create'),
    path('pending/<slug:slug>/', views.pending_users_in_group, name='pending'),
    path('approve_member/', views.approve_join_group, name='approve_join_group'),
    path('reject/', views.reject_join_group, name='reject_join_group'),
    path('disband_group/<slug:slug>/', views.disband_group, name='disband_group'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete_reply/<int:reply_id>/', views.delete_reply, name='delete_reply'),
    path('edit_comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('edit_reply/<int:reply_id>/', views.edit_reply, name='edit_reply'),
    path('detail_image/<int:image_id>/', views.detail_image, name='detail_image'),
    path('detail_image_profile/<int:image_id>/', views.detail_image_profile, name='detail_image_profile'),
    path('detail_image_comment/<int:image_id>/', views.detail_image_comment, name='detail_image_comment'),
    path('hide_post/<int:post_id>/', views.hide_post, name='hide_post'),
    path('search_post/<slug:slug>/', views.search_post, name='search_post'),
    path('close_comment/<int:post_id>/', views.close_comment, name='close_comment'),
    path('open_comment/<int:post_id>/', views.open_comment, name='open_comment'),
    path('group_member/<int:group_id>/', views.group_members, name='group_members'),
    path('kick_member/', views.kick_member, name='kick_member'),
    path('ban_member/', views.ban_member, name='ban_member'),
    path('unban_member/', views.unban_member, name='unban_member'),
    path('post_detail/<int:post_id>/', views.post_detail, name='post_detail'),
    path('admin_groups/', views.user_admin_groups, name='user_admin_groups'),
    path('group/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('pending_posts/<int:group_id>/', views.get_pending_posts, name='get_pending_posts'),
    path('approve_post/<int:post_id>/', views.approve_post, name='approve_post'),
    path('reject_post/<int:post_id>/', views.reject_post, name='reject_post'),
    path('group/<int:group_id>/user/<int:user_id>/posts/', views.user_posts_in_group, name='user_posts_in_group'),
    #society
    
    path('save_post/<int:post_id>/', views.save_post, name='save_post'),
    path('unsave_post/<int:post_id>/', views.unsave_post, name='unsave_post'),
    path('saved_posts/', views.saved_posts, name='saved_posts'),
    path('search/', views.search, name='search'),

    #user 
    path("register/", views.Register, name="register"),
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),
    # path("profile/", views.profile_user, name="profile"),
    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path("all_notifications/", views.all_notifications, name="all_notifications"),
    path("delete_notification/<int:notification_id>/", views.delete_notification, name="delete_notification"),
    # path("add_comment_user/<int:post_id>/", views.add_comment_user, name="add_comment_user"),

    #chat
    path("", views.index, name="index"),
    # path("<str:room_name>/", views.room, name="room"),
    
]