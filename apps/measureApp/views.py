from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .pose_utils import process_pose_images
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import base64
from PIL import Image
from .pose_capture import process_camera
import tempfile
from django.shortcuts import render, redirect
from django.http import HttpResponse
import os
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from apps.notifications.models import Notification
from django.shortcuts import get_object_or_404


User = get_user_model()


def build_share_users(current_user):
    qs = User.objects.exclude(id=current_user.id)
    data = []
    for u in qs:
        avatar_url = static("images/default-avatar.png")
        if hasattr(u, "profile"):
            if getattr(u.profile, "avatar", None):
                avatar_url = u.profile.avatar.url
        data.append({
            "id": u.id,
            "username": u.username,
            "avatar": avatar_url,
        })
    return data


def height_input(request):
    if request.method == "POST":
        height_cm = request.POST.get("height_cm")
        request.session["user_height_cm"] = height_cm
        return redirect("measureApp:manual_capture")
    return render(request, "measureApp/height_input.html")


def manual_capture(request):
    return render(request, "measureApp/manual_capture.html")


def preview_capture(request):
    return render(request, "measureApp/preview.html")


# ===================================================================
#  FIXED: submit_capture with full error handling
# ===================================================================
@csrf_exempt
def submit_capture(request):
    """
    Receives base64 front/side images + height via POST.
    Saves images, runs measurement pipeline, returns JSON.
    """
    # ---- Only accept POST ----
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # ---- Get POST data ----
        front_data = request.POST.get("front_img", "")
        side_data = request.POST.get("side_img", "")
        user_height = request.POST.get("height", "")

        print(f"[submit_capture] Received POST data:")
        print(f"  front_img length: {len(front_data)} chars")
        print(f"  side_img length:  {len(side_data)} chars")
        print(f"  height:           {user_height}")

        # ---- Validate inputs exist ----
        if not front_data:
            return JsonResponse({"error": "Missing front image data"}, status=400)
        if not side_data:
            return JsonResponse({"error": "Missing side image data"}, status=400)
        if not user_height:
            return JsonResponse({"error": "Missing height value"}, status=400)

        # ---- Validate height is a number ----
        try:
            height_cm = float(user_height)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Height must be a valid number"}, status=400)

        if height_cm < 50 or height_cm > 250:
            return JsonResponse({"error": "Height must be between 50-250 cm"}, status=400)

        # ---- Validate base64 format ----
        if "," not in front_data:
            return JsonResponse({"error": "Invalid front image format"}, status=400)
        if "," not in side_data:
            return JsonResponse({"error": "Invalid side image format"}, status=400)

        # ---- Decode base64 images ----
        try:
            front_b64 = front_data.split(",")[1]
            side_b64 = side_data.split(",")[1]
            front_bytes = base64.b64decode(front_b64)
            side_bytes = base64.b64decode(side_b64)
        except Exception as e:
            print(f"[submit_capture] Base64 decode error: {e}")
            return JsonResponse({"error": "Invalid image data"}, status=400)

        print(f"[submit_capture] Decoded images: front={len(front_bytes)} bytes, side={len(side_bytes)} bytes")

        # ---- Validate decoded images are actual images ----
        try:
            from io import BytesIO
            front_img = Image.open(BytesIO(front_bytes))
            side_img = Image.open(BytesIO(side_bytes))
            print(f"[submit_capture] Front image size: {front_img.size}")
            print(f"[submit_capture] Side image size: {side_img.size}")
        except Exception as e:
            print(f"[submit_capture] Image validation error: {e}")
            return JsonResponse({"error": "Decoded data is not a valid image"}, status=400)

        # ---- Save images to disk ----
        try:
            # Use MEDIA_ROOT for proper Django media handling
            media_dir = getattr(settings, "MEDIA_ROOT", "media")
            upload_dir = os.path.join(media_dir, "captures")
            os.makedirs(upload_dir, exist_ok=True)

            front_filename = f"front_{uuid.uuid4().hex}.jpg"
            side_filename = f"side_{uuid.uuid4().hex}.jpg"
            front_path = os.path.join(upload_dir, front_filename)
            side_path = os.path.join(upload_dir, side_filename)

            with open(front_path, "wb") as f:
                f.write(front_bytes)
            with open(side_path, "wb") as f:
                f.write(side_bytes)

            print(f"[submit_capture] Saved front to: {front_path}")
            print(f"[submit_capture] Saved side to:  {side_path}")

        except Exception as e:
            print(f"[submit_capture] File save error: {e}")
            return JsonResponse({"error": "Failed to save images"}, status=500)

        # ---- Run measurement pipeline ----
        try:
            print(f"[submit_capture] Starting process_camera()...")
            results = process_camera(
                front_img_path=front_path,
                side_img_path=side_path,
                height_cm=height_cm,
                save_annotated=True
            )
            print(f"[submit_capture] Results: {results}")

        except ImportError as e:
            print(f"[submit_capture] Import error: {e}")
            return JsonResponse({
                "error": "Measurement module not available",
                "detail": str(e)
            }, status=500)

        except Exception as e:
            print(f"[submit_capture] Processing error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "error": "Failed to process images",
                "detail": str(e)
            }, status=500)

        # ---- Validate results ----
        if not results:
            return JsonResponse({"error": "Processing returned no results"}, status=500)

        # ---- Store in session ----
        request.session["measurement_results"] = results
        request.session["annotated_front"] = results.get("annotated_front", "")
        request.session["annotated_side"] = results.get("annotated_side", "")
        request.session["front_img"] = front_data
        request.session["side_img"] = side_data
        request.session["user_height"] = height_cm

        # ---- Return JSON for fetch() to handle redirect ----
        return JsonResponse({
            "status": "ok",
            "redirect": "/measure/processed_capture/"
        })

    except Exception as e:
        print(f"[submit_capture] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": "Server error",
            "detail": str(e)
        }, status=500)


def processed_capture(request):
    """Target view for camera captures.

    Loads session values and builds sharing constraints.
    """
    results = request.session.get("measurement_results")
    annotated_front = request.session.get("annotated_front")
    annotated_side = request.session.get("annotated_side")

    if not results:
        messages.warning(
            request, "No measurement data found. Please capture again."
        )
        return redirect("measureApp:manual_capture")

    # FIXED: Added sharing data fetch pipeline here
    users = (
        build_share_users(request.user) if request.user.is_authenticated else []
    )

    context = {
        "results": results,
        "annotated_front": annotated_front,
        "annotated_side": annotated_side,
        "users": users,  # Connected to HTML iteration loop
    }
    return render(request, "measureApp/processed_captured.html", context)


def upload_images(request):
    if request.method == "POST":
        front_image = request.FILES.get("front_image")
        side_image = request.FILES.get("side_image")
        height_cm = request.POST.get("height_cm")

        if front_image and side_image and height_cm:
            try:
                height_cm = float(height_cm)
            except ValueError:
                return render(
                    request,
                    "measureApp/upload.html",
                    {"error": "Height must be a number."},
                )

            # 1. Save the images to your storage system (Local, S3, etc.)
            front_filename = default_storage.save(
                os.path.join("uploads", front_image.name), front_image
            )
            side_filename = default_storage.save(
                os.path.join("uploads", side_image.name), side_image
            )

            # 2. Grab the storage-agnostic display web URLs
            front_url = default_storage.url(front_filename)
            side_url = default_storage.url(side_filename)

            # 3. FIXED: Instead of sending string paths, pass the raw memory streams (request.FILES objects)
            # This bypasses cloud storage limitations and processes directly from memory!
            measurements = process_pose_images(front_image, side_image, height_cm)

            users = (
                build_share_users(request.user)
                if request.user.is_authenticated
                else []
            )

            return render(
                request,
                "measureApp/result.html",
                {
                    "measurements": measurements,
                    "front_url": front_url,
                    "side_url": side_url,
                    "users": users,
                },
            )

        return render(
            request,
            "measureApp/upload.html",
            {"error": "Please upload both images and provide your height."},
        )

    return render(request, "measureApp/upload.html")

def index(request):
    return render(request, "measureApp/index.html")


def how(request):
    return render(request, 'measureApp/how.html')


def result(request):
    return render(request, 'measureApp/result.html')


@login_required
def share_measurement(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    users = data.get("users", [])
    measurements = data.get("measurements", {})

    sent = 0
    for user_id in users:
        try:
            recipient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            continue

        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            type="measurement_share",
            verb=f"{request.user.username} shared measurements with you",
            data={"measurements": measurements},
            read=False,
        )
        sent += 1

    return JsonResponse({"ok": True, "sent": sent})


@login_required
def processed_measurement(request):
    measurements = request.session.get("measurement_results")
    users = build_share_users(request.user)
    return render(request, "measureApp/processed_captured.html", {
        "measurements": measurements,
        "users": users
    })


@login_required
def view_shared_measurement(request, notification_id):
    notif = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
        type="measurement_share"
    )
    notif.read = True
    notif.save()
    measurements = (notif.data or {}).get("measurements", {})
    return render(request, "measureApp/shared_measurement_view.html", {
        "notif": notif,
        "measurements": measurements
    })