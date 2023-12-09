from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.models import User,Group
from django.urls import reverse
from django.contrib.auth  import authenticate,  login, logout
from .models import *
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect 
from django.http import JsonResponse
from django.db.models import Count
from django.views import generic
from django.views.generic import RedirectView
from django.db.utils import IntegrityError
from .form import *
from django.utils import timezone
from django.utils.timesince import timesince
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
import json
from social_profile.models import *
from social_network.models import *
# Create your views here.
def delete_fanpage(request, slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    fanpages = Fanpage.objects.all()
    fanpage.delete()
    return render(request, 'fanpages/fanpage.html', {'fanpages': fanpages})
def toggle_like(request, fanpage_id):
    fanpage = get_object_or_404(Fanpage, id=fanpage_id)
    user = request.user
    if user == fanpage.user:
        # Admin không thể like fanpage của mình
        return JsonResponse({'status': 'error', 'message': 'Admins cannot like their own fanpages'})
    # Kiểm tra xem người dùng đã like fanpage hay chưa
    user_already_likes = UserLikeFanpage.objects.filter(user=user, fanpage=fanpage).exists()

    if user_already_likes:
        # Người dùng đã like fanpage, hủy like
        UserLikeFanpage.objects.filter(user=user, fanpage=fanpage).delete()
        fanpage.likes_count -= 1
        fanpage.save()
        return JsonResponse({'status': 'unliked', 'count': fanpage.likes_count})
    else:
        # Người dùng chưa like fanpage, thêm like
        UserLikeFanpage.objects.create(user=user, fanpage=fanpage)
        fanpage.likes_count += 1
        fanpage.save()
        return JsonResponse({'status': 'liked', 'count': fanpage.likes_count})
def open_fanpage(request, slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    if request.method == 'POST':
        is_hidden = request.POST.get('is_hidden')
        if not is_hidden:
            fanpage.is_hidden = False
            fanpage.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def close_fanpage(request, slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    if request.method == 'POST':
        is_hidden = request.POST.get('is_hidden')
        if is_hidden:
            fanpage.is_hidden = True
            fanpage.save()
        else:
           fanpage.is_hidden = False
           fanpage.save() 
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def remove_admin(fanpage, user):
    fanpage.admins.remove(user)
def remove_admin_management(request,slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    friends = Friendship.objects.filter(friend=request.user, is_friend=True, is_blocking=False).select_related('friend__profile')
    admins = fanpage.admins.all()
    admin_ids = admins.values_list('id', flat=True)
    if request.method == 'POST':
        selected_user_id = request.POST.get('admin')  
        if selected_user_id:
            selected_user = User.objects.get(id=selected_user_id)
            remove_admin(fanpage, selected_user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def set_admin(fanpage, user):
    fanpage.admins.add(user)
def admin_management(request,slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    friends = Friendship.objects.filter(friend=request.user, is_friend=True, is_blocking=False).select_related('friend__profile')
    admins = fanpage.admins.all()
    admin_ids = admins.values_list('id', flat=True)
    if request.method == 'POST':
        selected_user_id = request.POST.get('admin')  
        if selected_user_id:
            selected_user = User.objects.get(id=selected_user_id)
            set_admin(fanpage, selected_user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def edit_fanpage(request, slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    friends = Friendship.objects.filter(friend=request.user, is_friend=True, is_blocking=False).select_related('friend__profile')
    admins = fanpage.admins.all()
    admin_ids = admins.values_list('id', flat=True)
    if request.method == 'POST': 
        name = request.POST.get('name')
        description = request.POST.get('description')
        avatar = request.FILES.get('avatar')
        background = request.FILES.get('background')
        if avatar:
            fanpage.avatar = avatar
        if background:
            fanpage.cover_image = background    
        fanpage.name = name
        fanpage.description = description
        fanpage.save()
        messages.success(request, 'Profile updated successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'fanpages/fanpage-edit.html', {'fanpage': fanpage,'friends':friends,'admins':admins,'admin_ids':admin_ids})
def save_post_fanpage(request, post_id):
    post = get_object_or_404(FanpagePost, id=post_id)
    fanpage = post.fanpage 
    user_profile = get_object_or_404(Profile, user=request.user)
    user_profile.saved_posts_fanpage.add(fanpage) 
    user_profile.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def hide_post(request, post_id):
    post = get_object_or_404(FanpagePost, id=post_id)
    post.hidden_for_users.add(request.user)
    post.save()
    return JsonResponse({'status': 'success'})
def delete_image(request, image_id):
    image = get_object_or_404(PostImageFanpage, id=image_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_video(request, video_id):
    image = get_object_or_404(PostVideoFanpage, id=video_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_post(request, post_id):
    post = get_object_or_404(FanpagePost, id=post_id)
    post.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def edit_post(request, post_id):
    post = get_object_or_404(FanpagePost, id=post_id)
    group = post.fanpage
    slug = group.slug
    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        image_form = PostImageEditForm(request.POST, request.FILES)
        if post_form.is_valid():
            # Lưu thông tin chỉnh sửa bài viết
            post_form.save()
           # Lấy tất cả hình ảnh cũ của post
            existing_images = post.postimagefanpage_set.all()
            existing_videos = post.videos.all()
            # Lấy hình ảnh từ input file
            new_images = request.FILES.getlist('image')
            new_videos = request.FILES.getlist('video')
            for video in new_videos:
                if not existing_videos.filter(video=video).exists():
                    post_video = PostVideoFanpage(post=post, video=video)
                    post_video.save()  
            for image in new_images:
                if not existing_images.filter(image=image).exists():
                    post_image = PostImageFanpage(post=post, image=image)
                    post_image.save()
            return HttpResponseRedirect(reverse("social_fanpage:fanpage_detail", kwargs={"slug":slug}))

    else:
        post_form = PostForm(instance=post)
        image_form = PostImageEditForm()

    return render(request, 'fanpages/fanpage-edit.html', {'post_form': post_form, 'image_form': image_form, 'post': post,'group': group})

@login_required
def like_post(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        is_liked = request.POST.get('is_liked')
        user = request.user
        notification_html=""
        try:
            post = get_object_or_404(FanpagePost, pk=post_id)
            is_post_owner = post.user == user

            if is_liked and is_liked == 'true':
                LikePostFanpage.objects.filter(post=post, user=user).delete()
                # LikeNotification.objects.filter(user_owner=post.user, post=post, user_liker=user, group=post.group).delete()
                message = 'Unliked successfully'
            else:
                like, created = LikePostFanpage.objects.get_or_create(post=post, user=user)
                message = 'Liked successfully' if created else 'You already liked this post.'
            #     if not is_post_owner:
            #         notification = LikeNotification.objects.create(
            #             user_owner=post.user,  
            #             user_liker=user,
            #             post=post,
            #             group=post.group
            #         )
            #         notification_html = render_to_string('society/notification_item.html', {'notification': notification}, request=request)
            # print(notification_html)
            current_likes = post.likes.count()

            # Return the notification_html in the response
            return JsonResponse({'message': message, 'likes': current_likes, 'notification_html': notification_html, 'is_owner': is_post_owner})


        except Exception as e:
            print(f'Error occurred: {e}')
            return JsonResponse({'error': 'Error occurred while processing the request.'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# def get_notifications(request):
#     try:
#         user = request.user
#         # notifications = LikeNotification.objects.filter(user_owner=user, is_read=False)
#         # current_notification_count = LikeNotification.objects.filter(user_owner=user).count()
#         # serialized_notifications = [
#         #     {
#         #         'user_liker_last_name': notification.user_liker.last_name,
#         #         'post_content': notification.post.content,
#         #         'group_name': notification.group.name,
#         #         'avatar':notification.user_liker.profile.avatar.url,
#         #         'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
#         #         'is_read': notification.is_read, 
#         #         'post_id':notification.post.id,
#         #     }
#         #     for notification in notifications
#         # ]

#         # updated_notification_count = current_notification_count + len(serialized_notifications) 

#         # notifications.update(is_read=True)

#         return JsonResponse({'notifications': serialized_notifications, 'notification_count': updated_notification_count})
#     except Exception as e:
#         print(f'Error in get_notifications: {e}')
#         return JsonResponse({'error': 'Internal Server Error'}, status=500)

# def all_notifications(request):
#     notifications = LikeNotification.objects.filter(user_owner=request.user).order_by('-created_at')
#     return render(request, "users/user_notification.html",{'notifications':notifications})
# def delete_notification(request, notification_id):
#     notification = get_object_or_404(LikeNotification, pk=notification_id)
#     notification.delete()
#     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def like_reply(request, reply_id):
    reply = ReplyCommentFanpage.objects.get(id=reply_id)
    user = request.user
    already_liked = ReplyLikeFanpage.objects.filter(user=user, reply=reply).exists()

    if not already_liked:
        like = ReplyLikeFanpage(user=user, reply=reply)
        like.save()
    else:
        like = ReplyLikeFanpage.objects.get(user=user, reply=reply)
        like.delete()

    likes_count = ReplyLikeFanpage.objects.filter(reply=reply).count()
    return JsonResponse({'liked': not already_liked,'likes': likes_count})
def like_comment(request, comment_id):
    comment = CommentFanpage.objects.get(id=comment_id)
    user = request.user
    already_liked = LikeCommentFanpage.objects.filter(user=user, comment=comment).exists()
    if not already_liked:
        like = LikeCommentFanpage(user=user, comment=comment)
        like.save()
    else:
        like = LikeCommentFanpage.objects.get(user=user, comment=comment)
        like.delete()
    likes_count = LikeCommentFanpage.objects.filter(comment=comment).count()
    return JsonResponse({'liked': not already_liked, 'likes': likes_count})
@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')  
        if content:
            post = FanpagePost.objects.get(id=post_id)  
            user = request.user
            comment, created = CommentFanpage.objects.get_or_create(user=user, post=post, content=content)
            # Xử lý ảnh
            image_files = request.FILES.getlist('image_comment')
            for image_file in image_files:
                CommentImageFanpage.objects.create(comment=comment, image=image_file)
            # Xử lý video
            video_files = request.FILES.getlist('video_comment')
            for video_file in video_files:
                CommentVideoFanpage.objects.create(comment=comment, video=video_file)

            if content or image_files or video_files:
                created_at = comment.created_at
                now = timezone.now()
                time_difference = timesince(created_at, now)
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'success'})
    else:
        return render(request, "errors/pages-error-500.html")

@login_required
def delete_comment(request, comment_id):
    try:
        comment = CommentFanpage.objects.get(pk=comment_id)
        if comment.user == request.user or request.user.is_staff:
            comment.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except CommentFanpage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'}) 
def close_comment(request, post_id):
    post = get_object_or_404(FanpagePost, pk=post_id)
    post.comments_closed = True
    post.save()
    return JsonResponse({'success': True})
def open_comment(request, post_id):
    post = get_object_or_404(FanpagePost, pk=post_id)
    post.comments_closed = False
    post.save()
    return JsonResponse({'success': True})  
@login_required
def delete_reply(request, reply_id):
    try:
        reply = ReplyCommentFanpage.objects.get(pk=reply_id)
        if reply.user == request.user:
            reply.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except CommentFanpage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'})  
def edit_comment(request, comment_id):
    comment = get_object_or_404(CommentFanpage, id=comment_id)
    if request.method == 'POST':
        new_content = request.POST.get('new_content')
        comment.content = new_content
        comment.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
def edit_reply(request, reply_id):
    reply = get_object_or_404(ReplyCommentFanpage, id=reply_id)

    if request.method == 'POST':
        new_content = request.POST.get('new_content')

        # Perform the update logic here
        reply.content = new_content
        reply.save()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
@login_required
def add_reply(request, comment_id):
    if request.method == 'POST': 
        parent_comment = CommentFanpage.objects.get(pk=comment_id)
        reply_text = request.POST.get('reply_content')
        if reply_text:
            ReplyCommentFanpage.objects.create(user=request.user, text=reply_text, parent=parent_comment)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})
def detail_image_post(request, image_id):
    image = PostImageFanpage.objects.get(id=image_id)
    post = image.post
    post_images = PostImageFanpage.objects.filter(post=post)
    return render(request, 'fanpages/detail-image-post.html', {'image': image, 'post_images': post_images})
def detail_image_comment(request, image_id):
    image = CommentImageFanpage.objects.get(id=image_id)
    comment = image.comment
    comment_images = CommentImageFanpage.objects.filter(comment=comment)
    return render(request, 'fanpages/detail-image-comment.html', {'image': image, 'post_images': comment_images})
def detail_image_profile(request, user_id, image_id):
    user = get_object_or_404(User, id=user_id)
    user_posts = FanpagePost.objects.filter(user=user)
    profile_images = PostImageFanpage.objects.filter(post__in=user_posts)
    
    user_album, created = AlbumFanpage.objects.get_or_create(user=user)
    user_album.images.set(profile_images)
    
    image = get_object_or_404(PostImageFanpage, id=image_id)
    images_in_album = user_album.images.all()
    return render(request, 'fanpages/detail_image-profile.html', {'profile_images': profile_images, 'images_in_album': images_in_album, 'image': image})

def fanpage_post(request,slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    if request.method == 'POST':
        content = request.POST.get('content')
        images = request.FILES.getlist('image')
        text_form = PostForm({'content': content})
        image_form = PostImageForm(request.POST, request.FILES)
        video_form = VideoForm(request.POST, request.FILES)
        if text_form.is_valid():
            post = FanpagePost(fanpage=fanpage,content=content,user=request.user)
            post.save() 
            for image in images:
                post_image = PostImageFanpage(post=post, image=image)
                post_image.save()
            for video in video_form.files.getlist('video'):
                post_video = PostVideoFanpage(post=post, video=video)
                post_video.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def fanpage_list(request):
    fanpages = Fanpage.objects.all()
    return render(request, 'fanpages/fanpage.html', {'fanpages': fanpages})
def fanpage_detail(request, slug):
    fanpage = get_object_or_404(Fanpage, slug=slug)
    latest_posts = FanpagePost.objects.filter(fanpage=fanpage).order_by('-created_at')
    admins = FanpagePost.objects.values_list('user', flat=True).distinct()
    user_album, created = AlbumFanpage.objects.get_or_create(user=fanpage.user)
    profile_images = PostImageFanpage.objects.filter(post__in=latest_posts)
    user_album.images.set(profile_images)
    images_in_album = user_album.images.all()
    videos = PostVideoFanpage.objects.filter(post__in=latest_posts)
    all_admins = fanpage.admins.all()
    admin_ids = all_admins.values_list('id', flat=True)
    context = {
        'fanpage':fanpage,
        'latest_posts':latest_posts,
        'admins':admins,
        'images_in_album':images_in_album,
        'videos':videos,
        'admin_ids':admin_ids
    }
    return render(request, 'fanpages/fanpage-detail.html', context)
@login_required
def fanpage_create(request):
    if request.method == 'POST':
        form = FanPageForm(request.POST,request.FILES)
        if form.is_valid():
            fanpage = form.save(commit=False)
            fanpage.user = request.user
            fanpage.slug = form.cleaned_data['name']  
            fanpage.save()
            return HttpResponseRedirect(reverse("social_fanpage:fanpage_detail", kwargs={"slug": fanpage.slug}))
    else:
        form = FanPageForm()
    return render(request, 'fanpages/fanpage-create.html', {'form': form})
