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
from django.utils import timezone
from django.utils.timesince import timesince
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from social_network.models import Profile
from .form import *
import json
# Create your views here.@login_required
def detail_image_post(request, image_id):
    image = PostImageUser.objects.get(id=image_id)
    post = image.post
    post_images = PostImageUser.objects.filter(post=post)
    return render(request, 'users/detail-image-post.html', {'image': image, 'post_images': post_images})
def detail_image_comment(request, image_id):
    image = CommentImageUser.objects.get(id=image_id)
    comment = image.comment
    comment_images = CommentImageUser.objects.filter(comment=comment)
    return render(request, 'users/detail-image-comment.html', {'image': image, 'post_images': comment_images})
def detail_image_profile(request, image_id):
    image = PostImageUser.objects.get(id=image_id)
    post = image.post
    profile_images = PostImageUser.objects.filter(post=post)
    return render(request, 'users/detail_image-profile.html', {'image': image, 'profile_images': profile_images})
def close_comment_user(request, post_id):
    post = get_object_or_404(PostUser, pk=post_id)
    post.comments_closed = True
    post.save()
    return JsonResponse({'success': True})
def open_comment_user(request, post_id):
    post = get_object_or_404(PostUser, pk=post_id)
    post.comments_closed = False
    post.save()
    return JsonResponse({'success': True})  
@login_required
def delete_post_user(request, post_id):
    post = get_object_or_404(PostUser, id=post_id)
    post.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def hide_post_user(request, post_id):
    post = get_object_or_404(PostUser, id=post_id)
    post.hidden_for_users.add(request.user)
    post.save()
    return JsonResponse({'status': 'success'})
def delete_image(request, image_id):
    image = get_object_or_404(PostImageUser, id=image_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_video(request, video_id):
    image = get_object_or_404(PostVideoUser, id=video_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def edit_post_user(request, post_id):
    post = get_object_or_404(PostUser, id=post_id)
    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        image_form = PostImageEditForm(request.POST, request.FILES)
        if post_form.is_valid():
            post_form.save()
            existing_images = post.postimageuser_set.all()
            existing_videos = post.videos_user.all()
            new_images = request.FILES.getlist('image')
            new_videos = request.FILES.getlist('video')
            for image in new_images:
                if not existing_images.filter(image=image).exists():
                    post_image = PostImageUser(post=post, image=image)
                    post_image.save()
            for video in new_videos:
                if not existing_videos.filter(video=video).exists():
                    post_video = PostVideoUser(post=post, video=video)
                    post_video.save()       
            return HttpResponseRedirect(reverse('social_profile:profile'))

    else:
        post_form = PostForm(instance=post)
        image_form = PostImageEditForm()

    return render(request, 'users/post-edit.html', {'post_form': post_form, 'image_form': image_form, 'post': post})
def save_post_user(request, post_id):
    post = get_object_or_404(PostUser, id=post_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    user_profile.saved_posts_user.add(post)
    user_profile.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def unsave_post_user(request, post_id):
    post = get_object_or_404(PostUser, id=post_id)
    request.user.profile.saved_posts.remove(post)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def edit_reply_user(request, reply_id):
    reply = get_object_or_404(ReplyUser, id=reply_id)
    if request.method == 'POST':
        new_content = request.POST.get('new_content')
        reply.text = new_content
        reply.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
@login_required
def delete_reply_user(request, reply_id):
    try:
        reply = ReplyUser.objects.get(pk=reply_id)
        if reply.user == request.user:
            reply.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except CommentUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'})  
@login_required
def delete_comment_user(request, comment_id):
    try:
        comment = CommentUser.objects.get(pk=comment_id)
        if comment.user == request.user:
            comment.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except CommentUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'}) 
def edit_comment_user(request, comment_id):
    comment = get_object_or_404(CommentUser, id=comment_id)

    if request.method == 'POST':
        new_content = request.POST.get('new_content')
        comment.content = new_content
        comment.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
@login_required
def like_reply_user(request, reply_id):
    reply = ReplyUser.objects.get(id=reply_id)
    user = request.user
    already_liked = ReplyLikeUser.objects.filter(user=user, reply=reply).exists()

    if not already_liked:
        like = ReplyLikeUser(user=user, reply=reply)
        like.save()
    else:
        like = ReplyLikeUser.objects.get(user=user, reply=reply)
        like.delete()

    likes_count = ReplyLikeUser.objects.filter(reply=reply).count()
    return JsonResponse({'liked': not already_liked,'likes': likes_count})
@login_required
def add_reply_user(request, comment_id):
    if request.method == 'POST': 
        parent_comment = CommentUser.objects.get(pk=comment_id)
        reply_text = request.POST.get('reply_content')
        if reply_text:
            ReplyUser.objects.create(user=request.user, text=reply_text, parent=parent_comment)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})
@login_required
def like_post_user(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        is_liked = request.POST.get('is_liked')
        user = request.user
        notification_html=""
        print(f"post_id: {post_id}")
        try:
            post = get_object_or_404(PostUser, id=post_id)
            is_post_owner = post.user == user

            if is_liked and is_liked == 'true':
                LikeUser.objects.filter(post=post, user=user).delete()
                # LikeNotification.objects.filter(user_owner=post.user, post=post, user_liker=user, group=post.group).delete()
                message = 'Unliked successfully'
            else:
                like, created = LikeUser.objects.get_or_create(post=post, user=user)
                message = 'Liked successfully' if created else 'You already liked this post.'
            #     if not is_post_owner:
            #         notification = LikeNotification.objects.create(
            #             user_owner=post.user,  # Ensure that user_owner is set to the post owner
            #             user_liker=user,
            #             post=post,
            #             group=post.group
            #         )

            #         # Get the rendered HTML for the new notification
            #         notification_html = render_to_string('society/notification_item.html', {'notification': notification}, request=request)
            # print(notification_html)
            current_likes = post.likes_user.count()
            # Return the notification_html in the response
            return JsonResponse({'message': message, 'likes': current_likes, 'notification_html': notification_html, 'is_owner': is_post_owner})


        except Exception as e:
            print(f'Error occurred: {e}')
            return JsonResponse({'error': 'Error occurred while processing the request.'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
@login_required
def like_comment_user(request, comment_id):
    comment = CommentUser.objects.get(id=comment_id)
    user = request.user
    already_liked = LikeCommentUser.objects.filter(user=user, comment=comment).exists()
    if not already_liked:
        like = LikeCommentUser(user=user, comment=comment)
        like.save()
    else:
        like = LikeCommentUser.objects.get(user=user, comment=comment)
        like.delete()
    likes_count = LikeCommentUser.objects.filter(comment=comment).count()
    return JsonResponse({'liked': not already_liked, 'likes': likes_count})
@login_required
def add_comment_user(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')  
        if content:
            post = PostUser.objects.get(id=post_id)  
            user = request.user
            comment, created = CommentUser.objects.get_or_create(user=user, post=post, content=content)
            # Xử lý ảnh
            image_files = request.FILES.getlist('image_comment')
            for image_file in image_files:
                CommentImageUser.objects.create(comment=comment, image=image_file)
            # Xử lý video
            video_files = request.FILES.getlist('video_comment')
            for video_file in video_files:
                CommentVideoUser.objects.create(comment=comment, video=video_file)

            if content or image_files or video_files:
                created_at = comment.created_at
                now = timezone.now()
                time_difference = timesince(created_at, now)
                return JsonResponse({'status': 'success'}) 
        return JsonResponse({'status': 'success'})
    else:
        return render(request, "errors/pages-error-500.html")
@login_required
def post_user(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        images = request.FILES.getlist('image')
        text_form = PostTextForm({'content': content})
        image_form = PostImageForm(request.POST, request.FILES)
        video_form = VideoForm(request.POST, request.FILES)
        if text_form.is_valid():
            # Tạo bài viết với nội dung và gán user và group
            post = PostUser( content=content,user=request.user)
            post.save()  # Lưu bài viết trước
            for image in images:
                post_image = PostImageUser(post=post, image=image)
                post_image.save()
            for video in video_form.files.getlist('video'):
                post_video = PostVideoUser(post=post, video=video)
                post_video.save()
            return HttpResponseRedirect(reverse('social_profile:profile'))
@login_required
def profile_user(request):
    user_posts = PostUser.objects.filter(user=request.user).order_by('-created_at')
    comments = CommentUser.objects.filter(post__in=user_posts).order_by('-created_at')
    user = User.objects.get(username=request.user.username)
    return render(request, 'users/profile.html', {'user': user,'user_posts':user_posts,'comments':comments,})
