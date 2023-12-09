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
#group
def group(request):
    all_users = User.objects.all()
    notifications = LikeNotification.objects.filter(user_owner=request.user).order_by('-created_at')[:5]
    notification_count = notifications.count()
    groups = Group.objects.annotate(num_members=Count('members'), num_posts=Count('posts'))
    for group in groups:
        group.num_posts = Post.objects.filter(group=group).count()
        group.num_members = Membership.objects.filter(group=group,status='approved').count()
    
    members = group.members.all().order_by('membership__joined_at')
    user_groups = Membership.objects.filter(user=request.user).values_list('group', flat=True)
    user_pending_group_ids = Membership.objects.filter(user=request.user, status='Pending').values_list('group', flat=True)
    user_approved_group_ids = Membership.objects.filter(user=request.user, status='approved').values_list('group', flat=True)
    return render(request, "groups/group.html", {"groups": groups, "user_groups": user_groups,"members":members,"user_pending_group_ids":user_pending_group_ids,"user_approved_group_ids":user_approved_group_ids,'all_users':all_users,'notifications':notifications,'notification_count':notification_count})
@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST,request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group = Group.objects.create(
            name=form.cleaned_data['name'],
            description=form.cleaned_data['description'],
            avatar=form.cleaned_data['avatar'],
            background_image=form.cleaned_data['background_image'],
            access = form.cleaned_data['access'],
            post_approval_enabled = form.cleaned_data['post_approval_enabled'])
            group.admins.add(request.user)
            
            return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug": group.slug}))
    else:
        form = GroupForm()
    return render(request, 'groups/group-create.html', {'form': form})
def disband_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect(reverse("social_network:group"))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def search(request):
    search_query = request.GET.get('search', '')
    groups = Group.objects.filter(name__icontains=search_query)

    context = {
        'search_query': search_query,
        'groups': groups
        }
    return render(request, 'society/search.html', context)
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post)
    is_banned = Membership.objects.filter(user=request.user, status='banned').exists()

    like_notification = LikeNotification.objects.filter(post=post, is_read=False).first()
    if like_notification:
        like_notification.is_read = True
        like_notification.save()

    return render(request, "groups/post-detail.html", {'post': post, 'comments': comments, 'is_banned': is_banned})
def group_detail(request, slug):
    group = get_object_or_404(Group, slug=slug)
    groupz = Group.objects.get(slug=slug)
    latest_posts = Post.objects.filter(group=group).order_by('-created_at')
    members = group.members.filter(membership__status='approved').order_by('membership__joined_at')
    approved_memberships = Membership.objects.filter(group=group, status='approved')
    # approved_users = approved_memberships.values_list('user', flat=True)
    is_approved = Membership.objects.filter(group=group, user=request.user, status='approved').exists()
    member_count = members.count()
    text_form = PostTextForm()
    image_form = PostImageForm()
    if group.post_approval_enabled:
        posts = Post.objects.filter(group=group, is_approved=True)
    else:
        posts = Post.objects.filter(group=group)
    group_posts = Post.objects.filter(group__slug=slug).order_by('-created_at')
    comments = Comment.objects.filter(post__group__slug=slug).order_by('-created_at')
    is_banned = Membership.objects.filter(user=request.user, status='banned').exists()
    notifications = LikeNotification.objects.filter(user_owner=request.user).order_by('-created_at')[:5]
    notification_count = notifications.count()
    now = timezone.now()
    group.visits += 1
    group.save()
    comments_by_post = {}
    for post in posts:  
        post.liked = post.likes.filter(user=request.user).exists() 
        post.liked = Like.objects.filter(post=post, user=request.user).exists()
        post.liked_users = [like.user for like in post.likes.all()]
        post_comments = Comment.objects.filter(post=post)
        total_comments = 0
        comments_by_post[post] = post_comments
       
       
    total_reply_count = 0
    for comment in comments:
        total_reply_count += comment.replies.count()
    if request.method == 'POST':
        content = request.POST.get('content')
        images = request.FILES.getlist('image')
        text_form = PostTextForm({'content': content})
        image_form = PostImageForm(request.POST, request.FILES)
        video_form = VideoForm(request.POST, request.FILES)
        if text_form.is_valid():
            # Tạo bài viết với nội dung và gán user và group
            post = Post(title="Title", content=content, group=group, user=request.user)
            if group.post_approval_enabled == False:
                post.is_approved == True
            else:
                post.is_approved == False
            post.save()  # Lưu bài viết trước
            for image in images:
                post_image = PostImage(post=post, image=image)
                post_image.save()
            for video in video_form.files.getlist('video'):
                post_video = PostVideo(post=post, video=video)
                post_video.save()
            return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug": group.slug}))
    context = {
        "group": group,
        "members": members,
        "member_count": member_count,
        'text_form': text_form,
        'image_form': image_form,
        'posts':posts,
        'latest_posts':latest_posts,
        'comments':comments,
        'group_posts': group_posts,
        'posts': posts,
        'now':now,
        'approved_memberships':approved_memberships,
        'is_approved':is_approved,
        'comments_by_post': comments_by_post,
        'total_reply_count':total_reply_count,
        'is_banned': is_banned,
        'notifications':notifications,
        'notification_count':notification_count,
        
    }
    return render(request, "groups/group-detail.html", context)
def group_members(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    members = Membership.objects.filter(group_id=group_id)
    admins = group.admins.all()
    
    context = {
        'group': group,
        'members': members,
        'admins':admins,
    }
    return render(request, 'groups/group-member.html', context)
def edit_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'POST':
        form = EditGroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated successfully.')
            return redirect('social_network:user_admin_groups')
        else:
            messages.error(request, 'Error updating group. Please check the form.')
    else:
        form = EditGroupForm(instance=group)

    return render(request, 'groups/group-edit.html', {'form': form, 'group': group})
def kick_member(request):
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        if membership_id: 
            try:
                membership = Membership.objects.get(id=int(membership_id))
                group = membership.group
                membership.delete()
            except Membership.DoesNotExist: 
                pass

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def user_admin_groups(request):
    admin_groups = Group.objects.filter(admins=request.user).order_by('-created_at')
    groups = admin_groups.annotate(num_members=Count('members'), num_posts=Count('posts'))
    for group in groups:
        group.num_posts = Post.objects.filter(group=group).count()
        group.num_members = Membership.objects.filter(group=group,status='approved').count()
    context = {
        'groups': groups,

    }
    return render(request, 'groups/group-manage.html', context)
def is_admin_groups(request):
    admin_groups = Group.objects.filter(admins=request.user).order_by('-created_at')
    groups = admin_groups.annotate(num_members=Count('members'), num_posts=Count('posts'))
    context = {
        'groups': groups,

    }
    return render(request, 'society/index.html', context)
def ban_member(request):
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        print(f"Membership ID: {membership_id}")
        if membership_id:  
            try:
                membership = Membership.objects.get(id=int(membership_id))
                group = membership.group
                membership.status = 'banned'
                membership.save()
            except Membership.DoesNotExist:
                
                pass

    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) 
def unban_member(request):
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')

        if membership_id:
            try:
                membership = Membership.objects.get(id=int(membership_id))
                group = membership.group
                membership.status = 'approved'
                membership.save()
            except Membership.DoesNotExist:
                pass

    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) 
def user_posts_in_group(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)
    user_posts = Post.objects.filter(group=group, user=user)
    comments = Comment.objects.filter(post__group__id=group_id).order_by('-created_at')
    user_post_images = PostImage.objects.filter(post__in=user_posts)
    membership = Membership.objects.filter(group=group, user=user).first()
    if membership:
        joined_at = membership.joined_at
    else:
        joined_at = group.created_at
    context = {
        'group': group,
        'user': user, 
        'posts': user_posts,
        'comments':comments,
        'images':user_post_images,
        'joined_at': joined_at,
        }
    return render(request, 'groups/group-profile_user.html', context)
def get_pending_posts(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    pending_posts = Post.objects.filter(group=group,is_approved=False)
    context = {'pending_posts': pending_posts,'group':group}
    return render(request, 'groups/post-pending.html', context)
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = True
    post.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = False
    post.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return JsonResponse({'message': 'Bài viết đã được xóa thành công.'})
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    user_profile.saved_posts.add(post)
    user_profile.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def unsave_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    request.user.profile.saved_posts.remove(post)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def saved_posts(request):
    user_profile = request.user.profile
    saved_posts = user_profile.saved_posts.all()
    user_profile_user = request.user.profile
    saved_posts_user = user_profile.saved_posts_user.all()
    saved_posts_fanpage = user_profile.saved_posts_fanpage.all()
    return render(request, 'users/post-save.html', {'saved_posts': saved_posts,'saved_posts_user':saved_posts_user,'saved_posts_fanpage':saved_posts_fanpage})
def search_post(request,slug):
    query = request.GET.get('search')
    if query:
        group = get_object_or_404(Group, slug=slug)
        groupz = Group.objects.get(slug=slug)
        latest_posts = Post.objects.filter(group=group).order_by('-created_at')
        members = group.members.all().order_by('membership__joined_at')
        approved_memberships = Membership.objects.filter(group=group, status='approved')
        # approved_users = approved_memberships.values_list('user', flat=True)
        is_approved = Membership.objects.filter(group=group, user=request.user, status='approved').exists()
        member_count = members.count()
        text_form = PostTextForm()
        image_form = PostImageForm()
        posts = Post.objects.filter(group=group)
        group_posts = Post.objects.filter(group__slug=slug).order_by('-created_at')
        comments = Comment.objects.filter(post__group__slug=slug).order_by('-created_at')
        search_query = Q(content__icontains=query) | Q(user__last_name__icontains=query)  # Tìm kiếm trong nội dung và last name của người dùng
        result_posts = Post.objects.filter(search_query)
        now = timezone.now()
        group.visits += 1
        group.save()
        comments_by_post = {}
        for post in posts:  
            post.liked = post.likes.filter(user=request.user).exists() 
            post.liked = Like.objects.filter(post=post, user=request.user).exists()
            post.liked_users = [like.user for like in post.likes.all()]
            post_comments = Comment.objects.filter(post=post)
            total_comments = 0
            comments_by_post[post] = post_comments
        
        
        total_reply_count = 0
        for comment in comments:
            total_reply_count += comment.replies.count()
        if request.method == 'POST':
            content = request.POST.get('content')
            images = request.FILES.getlist('image')
            text_form = PostTextForm({'content': content})
            image_form = PostImageForm(request.POST, request.FILES)
            video_form = VideoForm(request.POST, request.FILES)
            if text_form.is_valid():
                # Tạo bài viết với nội dung và gán user và group
                post = Post(title="Title", content=content, group=group, user=request.user)
                post.save()  # Lưu bài viết trước
                for image in images:
                    post_image = PostImage(post=post, image=image)
                    post_image.save()
                for video in video_form.files.getlist('video'):
                    post_video = PostVideo(post=post, video=video)
                    post_video.save()
                return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug": group.slug}))
        context = {
            "group": group,
            "members": members,
            "member_count": member_count,
            'text_form': text_form,
            'image_form': image_form,
            'posts':posts,
            'latest_posts':latest_posts,
            'comments':comments,
            'group_posts': group_posts,
            'posts': posts,
            'now':now,
            'approved_memberships':approved_memberships,
            'is_approved':is_approved,
            'comments_by_post': comments_by_post,
            'total_reply_count':total_reply_count,
            'result_posts': result_posts,
            'query': query,    
        }
        return render(request, "groups/group-search.html", context)
    else:
        # Nếu không có query, hiển thị tất cả bài viết
        print("Empty")
        posts = Post.objects.all()
        return render(request, 'blog_search_result.html', {'posts': posts, 'query': query})
@login_required
def hide_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.hidden_for_users.add(request.user)
    post.save()
    return JsonResponse({'status': 'success'})
def delete_image(request, image_id):
    image = get_object_or_404(PostImage, id=image_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def delete_video(request, video_id):
    image = get_object_or_404(PostVideo, id=video_id)
    image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    group = post.group
    slug = group.slug
    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        image_form = PostImageEditForm(request.POST, request.FILES)
        if post_form.is_valid():
            # Lưu thông tin chỉnh sửa bài viết
            post_form.save()
           # Lấy tất cả hình ảnh cũ của post
            existing_images = post.postimage_set.all()
            existing_videos = post.videos.all()
            # Lấy hình ảnh từ input file
            new_images = request.FILES.getlist('image')
            new_videos = request.FILES.getlist('video')
            for video in new_videos:
                if not existing_videos.filter(video=video).exists():
                    post_video = PostVideo(post=post, video=video)
                    post_video.save()  
            for image in new_images:
                if not existing_images.filter(image=image).exists():
                    post_image = PostImage(post=post, image=image)
                    post_image.save()
            return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug":slug}))

    else:
        post_form = PostForm(instance=post)
        image_form = PostImageEditForm()

    return render(request, 'groups/post-edit.html', {'post_form': post_form, 'image_form': image_form, 'post': post,'group': group})

@login_required
def like_post(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        is_liked = request.POST.get('is_liked')
        user = request.user
        notification_html = ""
        try:
            post = get_object_or_404(Post, pk=post_id)
            is_post_owner = post.user == user

            notification = None  # Define notification variable outside the try block

            if is_liked and is_liked == 'true':
                Like.objects.filter(post=post, user=user).delete()
                LikeNotification.objects.filter(user_owner=post.user, post=post, user_liker=user, group=post.group).delete()
                message = 'Unliked successfully'
            else:
                like, created = Like.objects.get_or_create(post=post, user=user)
                message = 'Liked successfully' if created else 'You already liked this post.'
                if not is_post_owner:
                    notification = LikeNotification.objects.create(
                        user_owner=post.user,  
                        user_liker=user,
                        post=post,
                        group=post.group
                    )

            if notification:
                notification_html = render_to_string('society/notification_item.html', {'notification': notification}, request=request)

            current_likes = post.likes.count()

            # Return the notification_html in the response
            return JsonResponse({'message': message, 'likes': current_likes, 'notification_html': notification_html, 'is_owner': is_post_owner})

        except Exception as e:
            import traceback
            traceback.print_exc()  # Print the traceback
            return JsonResponse({'error': f'Error occurred while processing the request: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def get_notifications(request):
    try:
        user = request.user
        notifications = LikeNotification.objects.filter(user_owner=user, is_read=False)
        current_notification_count = LikeNotification.objects.filter(user_owner=user).count()
        serialized_notifications = [
            {
                'user_liker_last_name': notification.user_liker.last_name,
                'post_content': notification.post.content,
                'group_name': notification.group.name,
                'avatar':notification.user_liker.profile.avatar.url,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': notification.is_read, 
                'post_id':notification.post.id,
            }
            for notification in notifications
        ]

        updated_notification_count = current_notification_count + len(serialized_notifications) 

        notifications.update(is_read=True)

        return JsonResponse({'notifications': serialized_notifications, 'notification_count': updated_notification_count})
    except Exception as e:
        print(f'Error in get_notifications: {e}')
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def all_notifications(request):
    notifications = LikeNotification.objects.filter(user_owner=request.user).order_by('-created_at')
    return render(request, "users/user_notification.html",{'notifications':notifications})
def delete_notification(request, notification_id):
    notification = get_object_or_404(LikeNotification, pk=notification_id)
    notification.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def like_reply(request, reply_id):
    reply = Reply.objects.get(id=reply_id)
    user = request.user
    already_liked = ReplyLike.objects.filter(user=user, reply=reply).exists()

    if not already_liked:
        like = ReplyLike(user=user, reply=reply)
        like.save()
    else:
        like = ReplyLike.objects.get(user=user, reply=reply)
        like.delete()

    likes_count = ReplyLike.objects.filter(reply=reply).count()
    return JsonResponse({'liked': not already_liked,'likes': likes_count})
def like_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    user = request.user
    already_liked = LikeComment.objects.filter(user=user, comment=comment).exists()
    if not already_liked:
        like = LikeComment(user=user, comment=comment)
        like.save()
    else:
        like = LikeComment.objects.get(user=user, comment=comment)
        like.delete()
    likes_count = LikeComment.objects.filter(comment=comment).count()
    return JsonResponse({'liked': not already_liked, 'likes': likes_count})
@login_required
# def add_comment(request, post_id):
#     if request.method == 'POST':
#         content = request.POST.get('content') 
#         user = request.user
#         post = Post.objects.get(id=post_id)  
#         is_post_owner = post.user == user 
#         notification_html=""
#         if content:
#             comment, created = Comment.objects.get_or_create(user=user, post=post, content=content)
#             # Xử lý ảnh
#             image_files = request.FILES.getlist('image_comment')
#             for image_file in image_files:
#                 CommentImage.objects.create(comment=comment, image=image_file)
#             # Xử lý video
#             video_files = request.FILES.getlist('video_comment')
#             for video_file in video_files:
#                 CommentVideo.objects.create(comment=comment, video=video_file)

#             if content or image_files or video_files:
#                 created_at = comment.created_at
#                 now = timezone.now()
#                 time_difference = timesince(created_at, now)
#                 return JsonResponse({'status': 'success'})
            
#             notification = LikeNotification.objects.create(
#                         user_owner=post.user,  
#                         user_liker=user,
#                         post=post,
#                         group=post.group
#             ) 
#             notification_html = render_to_string('society/notification_item.html', {'notification': notification}, request=request)
#             return JsonResponse({'message': message, 'status': 'success', 'notification_html': notification_html, 'is_owner': is_post_owner})
#     else:
#         return render(request, "errors/pages-error-500.html")
def add_comment(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content') 
        user = request.user
        post = Post.objects.get(id=post_id)  
        is_post_owner = post.user == user 
        notification_html = ""

        if content:
            comment, created = Comment.objects.get_or_create(user=user, post=post, content=content)
            notification = LikeNotification.objects.create(
            user_owner=post.user,
            user_liker=user,
            post=post,
            group=post.group
            )
            # Xử lý ảnh
            image_files = request.FILES.getlist('image_comment')
            for image_file in image_files:
                CommentImage.objects.create(comment=comment, image=image_file)

            # Xử lý video
            video_files = request.FILES.getlist('video_comment')
            for video_file in video_files:
                CommentVideo.objects.create(comment=comment, video=video_file)

            if content or image_files or video_files:
                created_at = comment.created_at
                now = timezone.now()
                time_difference = timesince(created_at, now)
                return JsonResponse({'status': 'success'})

        # Create LikeNotification for comments
        

        notification_html = render_to_string('society/notification_item.html', {'notification': notification}, request=request)
        return JsonResponse({'message': 'Your comment has been added successfully.', 'status': 'success', 'notification_html': notification_html, 'is_owner': is_post_owner})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
@login_required
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
        if comment.user == request.user or request.user.is_staff:
            comment.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'}) 
def close_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.comments_closed = True
    post.save()
    return JsonResponse({'success': True})
def open_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.comments_closed = False
    post.save()
    return JsonResponse({'success': True})  
@login_required
def delete_reply(request, reply_id):
    try:
        reply = Reply.objects.get(pk=reply_id)
        if reply.user == request.user or request.user.is_staff:
            reply.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return JsonResponse({'success': False, 'error': 'Không có quyền xóa bình luận'})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bình luận không tồn tại'})  
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        new_content = request.POST.get('new_content')
        comment.content = new_content
        comment.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
def edit_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)

    if request.method == 'POST':
        new_content = request.POST.get('new_content')

        # Perform the update logic here
        reply.content = new_content
        reply.save()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})

def add_reply(request, comment_id):
    if request.method == 'POST': 
        parent_comment = Comment.objects.get(pk=comment_id)
        reply_text = request.POST.get('reply_content')
        if reply_text:
            Reply.objects.create(user=request.user, text=reply_text, parent=parent_comment)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})
def detail_image(request, image_id):
    image = PostImage.objects.get(id=image_id)
    post = image.post
    post_images = PostImage.objects.filter(post=post)
    return render(request, 'groups/detail-image.html', {'image': image, 'post_images': post_images})
def detail_image_comment(request, image_id):
    image = CommentImage.objects.get(id=image_id)
    comment = image.comment
    comment_images = CommentImage.objects.filter(comment=comment)
    return render(request, 'groups/detail-image-comment.html', {'image': image, 'post_images': comment_images})
def detail_image_profile(request, image_id):
    image = PostImage.objects.get(id=image_id)
    post = image.post
    profile_images = PostImage.objects.filter(post=post)
    return render(request, 'groups/detail_image-profile.html', {'image': image, 'profile_images': profile_images})
def get_users_liked_post(post_id):
    post = Post.objects.get(pk=post_id)
    likes = Like.objects.filter(post=post)
    users_liked_post = [like.user for like in likes]
    return users_liked_post
@login_required
def join_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if group.access == 'public':
        join_public_group(request, group)
    elif group.access == 'private':
        send_join_request(request, group)
    
    return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug": group.slug}))
def join_public_group(request, group):
    # Kiểm tra xem người dùng đã là thành viên của nhóm chưa
    if Membership.objects.filter(user=request.user, group=group).exists():
        messages.warning(request, f"You are already a member of {group.name}.")
    else:
        # Thêm người dùng vào nhóm
        membership = Membership.objects.create(user=request.user, group=group, status='approved')
        membership.save()
        messages.success(request, f"You are now a member of {group.name}.")
        return HttpResponseRedirect(reverse("social_network:group_detail", kwargs={"slug": group.slug}))
    
def send_join_request(request, group):
    # Kiểm tra xem người dùng đã gửi yêu cầu tham gia nhóm chưa
    if Membership.objects.filter(user=request.user, group=group, status='pending').exists():
        messages.warning(request, "You have already sent a join request for this group.")
    else:
        # Gửi yêu cầu tham gia nhóm
        membership= Membership.objects.create(user=request.user, group=group, status='Pending')
        membership.save()
        messages.success(request, "Your join request has been sent to the group's admin for approval.")
def pending_users_in_group(request,slug):
    group = Group.objects.get(slug=slug)
    pending_members = Membership.objects.filter(group=group, status='Pending')
    return render(request, 'groups/group-pending.html', {'group': group, 'pending_members': pending_members})

def approve_join_group(request):
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        membership = Membership.objects.get(id=membership_id)
        membership.status = 'approved'
        membership.save()
        pending_url = reverse("social_network:pending", kwargs={"slug": membership.group.slug})
        return HttpResponseRedirect(pending_url)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def reject_join_group(request):
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        membership = Membership.objects.get(id=membership_id)
        membership.delete()
        pending_url = reverse("social_network:pending", kwargs={"slug": membership.group.slug})
        return HttpResponseRedirect(pending_url)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
@login_required
def leave_group(request, slug):
    group = get_object_or_404(Group, slug=slug)

    try:
        # Xóa bản ghi Membership của người dùng cho nhóm này
        membership = Membership.objects.get(user=request.user, group=group)
        membership.delete()
        messages.success(request, f"You have left {group.name}.")
    except Membership.DoesNotExist:
        messages.warning(request, f"You are not a member of {group.name}.")

    # Chuyển hướng người dùng đến trang chi tiết của nhóm sau khi rời khỏi nhóm
    return HttpResponseRedirect(reverse("social_network:group"))
#society
def index(request):
    all_users = User.objects.all()
    user = request.user
    notifications = LikeNotification.objects.filter(user_owner=user).order_by('-created_at')[:5]
    notification_count = notifications.count()
    friend_requests_received = Friendship.objects.filter(friend=request.user, is_friend=False, is_following=False, is_blocking=False)
    friend_requests_sent = Friendship.objects.filter(user=request.user, is_friend=False, is_following=False, is_blocking=False)
    return render(request, 'society/index.html', {'all_users':all_users,'notifications': notifications, 'notification_count': notification_count,'friend_requests_received':friend_requests_received,'friend_requests_sent':friend_requests_sent})


#user
def Register(request):
    if request.method == "POST":
        password = request.POST['password']
        email = request.POST['email']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        gender = request.POST['gender']
        birthdate = request.POST['birthdate']
        avatar = request.FILES.get('avatar')  
        # Tạo người dùng 
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = firstname
        user.last_name = lastname
        user.save()
        # Kiểm tra nếu avatar không được tải lên, gán avatar mặc định
        if not avatar:
            avatar = 'profile_pics/avatar.jpg'
        user_profile = Profile(user=user, gender=gender, birthdate=birthdate, avatar=avatar)
        user_profile.save()
        messages.success(request, "Chỉnh sửa thành công!")
        return render(request, 'authentication/sign-in.html')

    return render(request, "authentication/sign-up.html")
def Login(request):
    if request.method=="POST":
        username = request.POST['email']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Successfully Logged In")
            return redirect("/")
        else:
            messages.error(request, "Invalid Credentials")
            return redirect("/login")
    return render(request, "authentication/sign-in.html")
def Logout(request):
    logout(request)
    messages.success(request, "Successfully logged out")
    return redirect('/login')