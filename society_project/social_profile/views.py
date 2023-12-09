from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.models import User,Group
from django.urls import reverse
from django.contrib.auth  import authenticate,  login, logout
from .models import *
from itertools import chain
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
from social_network.form import *
from django.http import HttpResponseServerError
from django.http import HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist
import json
from social_network.models import *
from django.contrib.auth import update_session_auth_hash
# Create your views here.@login_required
def change_background_avatar(request):
    if request.method == 'POST':
        background_image = request.FILES.get('background')
        if background_image:
            request.user.profile.background_avatar = background_image
            request.user.profile.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def friend_request_list(request):
    user = request.user
    friend_requests = Friendship.objects.filter(friend=request.user, is_friend=False, is_following=False, is_blocking=False)
    friend_requests_ids = friend_requests.values_list('user__id', flat=True)
    blocked_list_ids = Friendship.objects.filter(user=request.user, is_blocking=True).values_list('friend__id', flat=True)
    friend_list_ids = Friendship.objects.filter(user=request.user, is_friend=True).values_list('friend__id', flat=True)
    user_city = PlacesUser.objects.filter(user=user).values_list('city', flat=True).first()
    user_company = WorkUser.objects.filter(user=user).values_list('company_name', flat=True).first()
    user_school = EducationUser.objects.filter(user=user).values_list('school_name', flat=True).first()
    user_gender = user.profile.gender
    user_birthdate = user.profile.birthdate.year
    user_interested = user.profile.interested
    potential_friends = User.objects.filter(
        Q(placesuser__city=user_city) |
        Q(workuser__company_name=user_company) |
        Q(educationuser__school_name=user_school) |
        Q(profile__gender=user_gender) |
        Q(profile__birthdate__year=user_birthdate) |
        Q(profile__interested=user_interested)
    ).exclude(id=user.id).exclude(id__in=friend_requests_ids).exclude(id__in=friend_list_ids).exclude(id__in=blocked_list_ids).distinct()
    request.session['potential_friends'] = list(potential_friends.values_list('id', flat=True))
    return render(request, 'users/friend-request.html', {'friend_requests': friend_requests,'potential_friends':potential_friends})
@login_required
def unfollow_user(request, pk):
    user_to_unfollow = get_object_or_404(User, id=pk)
    friendship = Friendship.objects.filter(user=request.user, friend=user_to_unfollow, is_following=True).first()
    if friendship:
        friendship.is_following = False
        friendship.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def follow_user(request, pk):
    user_to_follow = get_object_or_404(User, id=pk)
    friendship, created = Friendship.objects.get_or_create(user=request.user, friend=user_to_follow)
    if friendship:
        friendship.is_following = True
        friendship.save()
    if created:
        friendship.is_following = True
        friendship.save()
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def unfriend_user(request, pk):
    friend_to_unfriend = get_object_or_404(User, id=pk)
    friendship = Friendship.objects.filter(user=request.user, friend=friend_to_unfriend, is_friend=True).first()
    if friendship:
        friendship.delete()
        reciprocal_friendship = Friendship.objects.filter(user=friend_to_unfriend, friend=request.user, is_friend=True).first()
        if reciprocal_friendship:
            reciprocal_friendship.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def unblock_user(request, pk):
    user_to_unblock = get_object_or_404(User, id=pk)
    friend_request = Friendship.objects.filter(user=request.user, friend=user_to_unblock, is_blocking=True).first()

    if friend_request:
        friend_request.is_blocking = False
        friend_request.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def block_user(request, pk):
    user_to_block = get_object_or_404(User, id=pk)
    friend_request, created = Friendship.objects.get_or_create(user=request.user, friend=user_to_block)
    if friend_request.is_friend:
        reciprocal_friendship = Friendship.objects.get(user=user_to_block, friend=request.user, is_friend=True)
        reciprocal_friendship.delete()
    friend_request.is_blocking = True
    friend_request.is_friend = False 
    friend_request.is_following = False 
    friend_request.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def send_friend_request(request, pk):
    friend = get_object_or_404(User, id=pk)
    existing_blocking = Friendship.objects.filter(Q(user=request.user, friend=friend, is_blocking=True) | Q(user=friend, friend=request.user, is_blocking=True)).first()
    if existing_blocking:
        return render(request, "errors/pages-error-friend.html")
    existing_request = Friendship.objects.filter(user=request.user, friend=friend, is_friend=False, is_following=False, is_blocking=False).first()
    if existing_request:
        return render(request, "errors/pages-error-500.html")
    friend_request = Friendship(user=request.user, friend=friend)
    friend_request.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def accept_friend_request(request, pk):
    friend = get_object_or_404(User, id=pk)
    friend_request = Friendship.objects.filter(user=friend, friend=request.user, is_friend=False, is_following=False, is_blocking=False).first()

    if not friend_request:
        return HttpResponseBadRequest("No friend request to accept.")
    friend_request.is_friend = True
    friend_request.is_following = True
    friend_request.save()

    reciprocal_friendship = Friendship(user=request.user, friend=friend, is_friend=True,is_following=True)
    reciprocal_friendship.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def reject_friend_request(request, pk):
    friend = get_object_or_404(User, id=pk)
    friend_request = Friendship.objects.filter(user=friend, friend=request.user, is_friend=False, is_following=False, is_blocking=False).first()

    if not friend_request:
        return HttpResponseBadRequest("No friend request to reject.")
    friend_request.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def add_places_user(request):
    if request.method == 'POST':
        city = request.POST.get('city')
        district = request.POST.get('district')
        year_lived = request.POST.get('year_lived')
        places_user = PlacesUser.objects.create(
            user=request.user,
            city=city,
            district=district,
            year_lived=year_lived
        )
        places_user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/add_places_user.html')
def edit_places_user(request, pk):
    places_user = get_object_or_404(PlacesUser, pk=pk)
    if request.method == 'POST':
        city = request.POST.get('city')
        district = request.POST.get('district')
        year_lived = request.POST.get('year_lived')
        places_user.city = city
        places_user.district = district
        places_user.year_lived = year_lived
        places_user.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/edit_places_user.html', {'places_user': places_user})
def delete_places_user(request, pk):
    places_user = get_object_or_404(PlacesUser, id=pk)
    places_user.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_education_user(request, pk):
    education_user = get_object_or_404(EducationUser, id=pk)
    education_user.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_work_user(request, pk):
    work_user = get_object_or_404(WorkUser, id=pk)
    work_user.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))  # Default to '/' if referer is not available
    
def edit_education_user(request, pk):
    education_user = get_object_or_404(EducationUser, pk=pk)
    if request.method == 'POST':
        school_name = request.POST.get('school_name')
        address = request.POST.get('address')
        end_date = request.POST.get('end_date')
        education_user.school_name = school_name
        education_user.address = address
        education_user.end_date = end_date
        education_user.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/edit_education_user.html', {'education_user': education_user})
def edit_work_user(request, pk):
    work_user = get_object_or_404(WorkUser, pk=pk)
    if request.method == 'POST':
        company_name = request.POST.get('company')
        position = request.POST.get('position')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') 
        work_user.company_name = company_name
        work_user.position = position
        work_user.start_date = start_date
        work_user.end_date = end_date
        work_user.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/edit_work_user.html', {'work_user': work_user})
def add_education_user(request):
    if request.method == 'POST':
        school_name = request.POST.get('school_name')
        address = request.POST.get('address')
        end_date = request.POST.get('end_date')
        education_user = EducationUser.objects.create(
            user=request.user,
            school_name=school_name,
            school_address=address,
            end_date=end_date
        )
        education_user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/add_education_user.html')
def add_work_user(request):
    if request.method == 'POST':
        company_name = request.POST.get('company')
        position = request.POST.get('position')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        work_user = WorkUser.objects.create(
            user=request.user,
            company_name=company_name,
            position=position,
            start_date=start_date,
            end_date=end_date
        )
        work_user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'users/add_work_user.html')
@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        new_password_verify = request.POST.get('new_password_verify')
        user = authenticate(username=request.user.username, password=current_password)
        if user is not None:
            if new_password == new_password_verify:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password successfully changed!')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Incorrect current password.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def edit_profile_user(request, user_id):
    user = get_object_or_404(Profile, user__id=user_id)

    if request.method == 'POST': 
        first_name = request.POST.get('user__first_name')
        last_name = request.POST.get('user__last_name')
        bio = request.POST.get('bio')
        birthdate = request.POST.get('birthdate')
        gender = request.POST.get('gender')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        social_link = request.POST.get('social_link')
        interested = request.POST.get('interested')
        language = request.POST.get('language')
        marital = request.POST.get('marital')
        avatar = request.FILES.get('avatar')
        if avatar:
            user.avatar = avatar
        user.user.first_name = first_name
        user.user.last_name = last_name
        user.bio = bio
        user.birthdate = birthdate
        user.gender = gender
        user.mobile = mobile
        user.address = address
        user.social_link = social_link
        user.interested = interested
        user.language = language
        user.marital = marital

        user.save()
        messages.success(request, 'Profile updated successfully.')
        return HttpResponseRedirect(reverse('social_profile:profile'))

    return render(request, 'users/profile-edit.html', {'user': user})
def post_detail_user(request, post_image_id):
    post_image = get_object_or_404(PostImageUser, id=post_image_id)
    post = post_image.post
    comments = CommentUser.objects.filter(post=post)
    # like_notification = LikeNotification.objects.filter(post=post, is_read=False).first()
    
    # if like_notification:
    #     like_notification.is_read = True
    #     like_notification.save()

    return render(request, "users/post-detail-user.html", {'post': post, 'comments': comments})
def delete_image_from_album(request, album_id, image_id):
    album = get_object_or_404(Album, id=album_id)
    image_to_delete = get_object_or_404(PostImageUser, id=image_id, albums=album)
    post_image_to_delete = get_object_or_404(PostImageUser, id=image_id)
    album.images.remove(post_image_to_delete)
    album.save()
    post_image_to_delete.image.delete()
    return JsonResponse({'message': 'Image deleted successfully'})
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
def detail_image_profile(request, user_id, image_id):
    user = get_object_or_404(User, id=user_id)
    user_posts = PostUser.objects.filter(user=user)
    profile_images = PostImageUser.objects.filter(post__in=user_posts)
    
    user_album, created = Album.objects.get_or_create(user=user)
    user_album.images.set(profile_images)
    
    image = get_object_or_404(PostImageUser, id=image_id)
    images_in_album = user_album.images.all()
    
    return render(request, 'users/detail_image-profile.html', {'profile_images': profile_images, 'images_in_album': images_in_album, 'image': image})


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
        privacy = request.POST.get('privacy')
        if post_form.is_valid():
            post.privacy = privacy
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
    comment = CommentUser.objects.get(pk=comment_id)
    comment.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
        privacy = request.POST.get('privacy')
        if text_form.is_valid():
            # Tạo bài viết với nội dung và gán user và group
            post = PostUser( content=content,user=request.user,privacy=privacy)
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
    profile_images = PostImageUser.objects.filter(post__in=user_posts)
    user_album, created = Album.objects.get_or_create(user=request.user)
    user_album.images.set(profile_images)
    images_in_album = user_album.images.all()
    blocked_users = Friendship.objects.filter(user=user, is_blocking=True)
    user_album = Album.objects.get(user=request.user)
    work_users = WorkUser.objects.filter(user=request.user)
    education_users = EducationUser.objects.filter(user=request.user)
    places_users = PlacesUser.objects.filter(user=request.user)
    places_user_latest = places_users.order_by('-year_lived').first()
    friend_requests_received = Friendship.objects.filter(friend=request.user, is_friend=False, is_following=False, is_blocking=False)
    friend_requests_sent = Friendship.objects.filter(user=request.user, is_friend=False, is_following=False, is_blocking=False)
    friends = Friendship.objects.filter(friend=request.user, is_friend=True, is_blocking=False).select_related('friend__profile')
    following_users = Friendship.objects.filter(user=request.user, is_following=True)
    following_user_ids = following_users.values_list('user__id', flat=True)
    recently_friends = Friendship.objects.filter(user=user, is_friend=True).order_by('-created_at')[:10]
    friend_posts = FriendPost.objects.filter(friend_user=user)
    all_posts = sorted(
        chain(user_posts, friend_posts),
        key=lambda post: post.created_at,
        reverse=True
    )
    context = {
        'user': user,
        'user_posts':user_posts,
        'comments':comments,
        'images_in_album':images_in_album,
        'user_album':user_album,
        'work_users':work_users,
        'education_users':education_users,
        'places_users':places_users,
        'places_user_latest':places_user_latest,
        'friend_requests_received':friend_requests_received,
        'friend_requests_sent':friend_requests_sent,
        'friends':friends,
        'blocked_users':blocked_users,
        'following_users':following_users,
        'recently_friends':recently_friends,
        'following_user_ids':following_user_ids,
        'all_posts':all_posts,
    }
    return render(request, 'users/profile.html', context)
class CombinedPost:
    def __init__(self, post, created_at):
        self.post = post
        self.created_at = created_at
def newsfeed(request):

    following_friends = Friendship.objects.filter(user=request.user, is_following=True)
    following_friends_ids = following_friends.values_list('friend', flat=True)
    newsfeed_posts = PostUser.objects.filter(user__in=following_friends_ids, privacy='public')
    newsfeed_posts_friend = PostUser.objects.filter(user__in=following_friends_ids, privacy='friend')
    all_newsfeed_posts = newsfeed_posts | newsfeed_posts_friend
    user_memberships = Membership.objects.filter(user=request.user)
    user_groups = user_memberships.values_list('group', flat=True)
    group_posts = Post.objects.filter(group__in=user_groups)
   
   
    context = {
        'group_posts':group_posts,
        'all_newsfeed_posts':all_newsfeed_posts,

    }
    return render(request, 'society/newsfeed.html', context)
def view_profile_user(request, pk):
    user = get_object_or_404(User, id=pk)
    profile = get_object_or_404(Profile, user=user)
    is_friend = Friendship.objects.filter(user=request.user, friend=user, is_friend=True).exists()
    user_posts = PostUser.objects.filter(user=user).order_by('-created_at')
    comments = CommentUser.objects.filter(post__in=user_posts).order_by('-created_at')
    profile_images = PostImageUser.objects.filter(post__in=user_posts)
    user_album, created = Album.objects.get_or_create(user=user)
    user_album.images.set(profile_images)
    images_in_album = user_album.images.all()
    work_users = WorkUser.objects.filter(user=user)
    education_users = EducationUser.objects.filter(user=user)
    places_users = PlacesUser.objects.filter(user=user)
    places_user_latest = places_users.order_by('-year_lived').first()
    friends = Friendship.objects.filter(friend=user, is_friend=True, is_blocking=False).select_related('friend__profile')
    following_users = Friendship.objects.filter(user=user, is_following=True)
    following_user_ids = following_users.values_list('user__id', flat=True)
    recently_friends = Friendship.objects.filter(user=user, is_friend=True).order_by('-created_at')[:10]
    is_user_friend = friends.filter(user=request.user).exists()
    public_posts = user_posts.filter(privacy='public')
    friend_posts = user_posts.filter(Q(privacy='friend') | Q(privacy='public'))
    private_posts = user_posts.filter(Q(privacy='friend') | Q(privacy='public')| Q(privacy='private'))
    if request.method == 'POST':
        content = request.POST.get('content')
        images = request.FILES.getlist('image')
        text_form = PostTextForm({'content': content})
        image_form = PostImageForm(request.POST, request.FILES)
        video_form = VideoForm(request.POST, request.FILES)
        if text_form.is_valid():
            post = PostUser( content=content,user=request.user)
            post.save() 
            for image in images:
                post_image = PostImageUser(post=post, image=image)
                post_image.save()
            for video in video_form.files.getlist('video'):
                post_video = PostVideoUser(post=post, video=video)
                post_video.save()
            user_friend = get_object_or_404(User, id=pk)
            friend_post = FriendPost(post=post, user=request.user, friend_user=user_friend)
            friend_post.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    friend_posts_profile = FriendPost.objects.filter(friend_user=user)
    all_posts = sorted(
        chain(friend_posts_profile, friend_posts),
        key=lambda post: post.created_at,
        reverse=True
    )
    context = {
        'user': user,
        'profile': profile,
        'is_friend': is_friend,
        'user_posts':user_posts,
        'comments':comments,
        'images_in_album':images_in_album,
        'user_album':user_album,
        'work_users':work_users,
        'education_users':education_users,
        'places_users':places_users,
        'places_user_latest':places_user_latest,
        'friends':friends,
        'following_users':following_users,
        'following_user_ids':following_user_ids,
        'recently_friends':recently_friends,
        'is_user_friend':is_user_friend,
        'public_posts':public_posts,
        'friend_posts':friend_posts,
        'private_posts':private_posts,
        'all_posts':all_posts,
        'is_friend_post': isinstance(friend_posts_profile, FriendPost),
    }
    return render(request, 'users/friend-profile.html', context)
    
