from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from apps.products.models import ProductVideo
from .models import Like, Comment
from django.db.models import Q


@login_required
def product_stream(request):
    """Main video stream feed showing all uploaded videos."""
    videos = ProductVideo.objects.all().order_by("-uploaded_at")
    content_type = ContentType.objects.get_for_model(ProductVideo)

    user_likes = []
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(
            user=request.user,
            content_type=content_type
        ).values_list("object_id", flat=True)

    video_data = []
    for video in videos:
        total_likes = Like.objects.filter(
            content_type=content_type,
            object_id=video.id
        ).count()
        total_comments = Comment.objects.filter(
            content_type=content_type,
            object_id=video.id
        ).count()
        video_data.append({
            "video": video,
            "product": video.product,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "liked": video.id in user_likes,
        })

    return render(request, "streams/stream.html", {
        "video_data": video_data,
    })

@login_required
def toggle_like(request, video_id):
    """Toggle like/unlike for a video."""
    video = get_object_or_404(ProductVideo, id=video_id)
    content_type = ContentType.objects.get_for_model(ProductVideo)

    like, created = Like.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=video.id
    )
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    likes_count = Like.objects.filter(
        content_type=content_type,
        object_id=video.id
    ).count()

    return JsonResponse({"liked": liked, "likes_count": likes_count})

@login_required
def add_comment(request, video_id):
    video = get_object_or_404(ProductVideo, id=video_id)
    content_type = ContentType.objects.get_for_model(ProductVideo)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Comment.objects.create(
                user=request.user,
                content_type=content_type,
                object_id=video.id,
                text=text
            )

    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=video.id
    ).order_by("-created_at")

    comments_data = [
        {"user": c.user.username, "text": c.text, "created": c.created_at.strftime("%H:%M")}
        for c in comments
    ]
    return JsonResponse({"comments": comments_data})

def get_comments(request, video_id):
    video = get_object_or_404(ProductVideo, id=video_id)
    content_type = ContentType.objects.get_for_model(ProductVideo)

    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=video.id
    ).order_by("-created_at")

    comments_data = [
        {"user": c.user.username, "text": c.text, "created": c.created_at.strftime("%H:%M")}
        for c in comments
    ]
    return JsonResponse({"comments": comments_data})

def trending_stream(request):
    videos = ProductVideo.objects.all()
    content_type = ContentType.objects.get_for_model(ProductVideo)
    query = request.GET.get("q", "").strip()

    if query:
        videos = videos.filter(
            Q(product__title__icontains=query) |
            Q(product__description__icontains=query) |
            Q(product__seller__username__icontains=query)
        )

    user_likes = []
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(
            user=request.user,
            content_type=content_type
        ).values_list("object_id", flat=True)

    video_data = []
    for video in videos:
        video_data.append({
            "video": video,
            "product": video.product,
            "total_likes": Like.objects.filter(content_type=content_type, object_id=video.id).count(),
            "total_comments": Comment.objects.filter(content_type=content_type, object_id=video.id).count(),
            "liked": video.id in user_likes,
        })

    # Sort by likes
    video_data.sort(key=lambda x: x["total_likes"], reverse=True)

    return render(request, "streams/trending.html", {
        "video_data": video_data,
        "query": query,
    })

def video_detail(request, video_id):
    video = get_object_or_404(ProductVideo, id=video_id)
    content_type = ContentType.objects.get_for_model(ProductVideo)

    total_likes = Like.objects.filter(content_type=content_type, object_id=video.id).count()
    total_comments = Comment.objects.filter(content_type=content_type, object_id=video.id).count()

    user_likes = []
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(user=request.user, content_type=content_type).values_list("object_id", flat=True)

    return render(request, "streams/video_detail.html", {
        "video": video,
        "product": video.product,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "user_likes": user_likes,
    })
