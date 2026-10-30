import base64
import io
import urllib.request
from PIL import Image
from fashn import Fashn

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import TryOnUsage


def file_to_base64_uri(uploaded_file, max_size=(1024, 1024), quality=80):
    """
    Resizes and compresses an uploaded image buffer before converting to Base64.
    Keeps payload sizes light and prevents upload connection drops.
    """
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        encoded_bytes = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded_bytes}"
    except Exception:
        uploaded_file.seek(0)
        encoded_bytes = base64.b64encode(uploaded_file.read()).decode("utf-8")
        content_type = getattr(uploaded_file, "content_type", "image/jpeg")
        return f"data:{content_type};base64,{encoded_bytes}"


def fetch_url_to_base64_uri(image_url):
    """Downloads a remote image URL server-side and converts it directly to a Base64 URI."""
    req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        image_bytes = response.read()
    encoded_bytes = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded_bytes}"

def tryon_view(request):
    """Renders the main Try-On HTML page with guest session tracking and user limits."""
    remaining_tryons = 0

    if request.user.is_authenticated:
        # Get or create usage for logged-in users, ensuring they get 2 tries if newly created
        usage, created = TryOnUsage.objects.get_or_create(user=request.user)
        
        # If your TryOnUsage model defaults to something else, you can ensure the limit is set to 2:
        # if created and hasattr(usage, 'remaining_tryons'): ...
        
        remaining_tryons = usage.remaining_tryons()
    else:
        # For guest users, initialize session tracking if it doesn't exist
        # Let's say we give them 1 try total.
        if 'guest_tryons_left' not in request.session:
            request.session['guest_tryons_left'] = 1
        
        remaining_tryons = request.session['guest_tryons_left']

    garment_url = request.GET.get("garment_url", "").strip()
    
    # Ensure URL has an absolute protocol scheme
    if garment_url:
        if garment_url.startswith("http://"):
            garment_url = "https://" + garment_url[7:]
        elif not garment_url.startswith("https://"):
            garment_url = "https://" + garment_url.lstrip("/")

    return render(
        request,
        "tryon/tryon.html",
        {
            "remaining_tryons": remaining_tryons,
            "garment_url": garment_url,
        },
    )

def initiate_tryon(request):
    """Starts prediction on Fashn AI using file upload or remote URL fallback."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    api_key = getattr(settings, "FASHN_API_KEY", "").strip()
    if not api_key:
        return JsonResponse(
            {"error": "Fashn AI API key is not configured on the server."}, status=500
        )

    # Check limits based on authentication status
    if request.user.is_authenticated:
        usage, _ = TryOnUsage.objects.get_or_create(user=request.user)
        if not usage.can_use_tryon():
            return JsonResponse(
                {"error": "You have reached your limit of free try-ons."}, status=403
            )
    else:
        # Guest user gets 1 try tracked via session
        guest_tries_left = request.session.get('guest_tryons_left', 1)
        if guest_tries_left <= 0:
            return JsonResponse(
                {
                    "error": "You have used your free guest try-on. Please log in to continue using this feature.", 
                    "login_required": True
                }, 
                status=403
            )

    model_file = request.FILES.get("model_image")
    garment_file = request.FILES.get("garment_image")
    garment_url = request.POST.get("garment_url", "").strip()

    if not model_file:
        return JsonResponse({"error": "Model photo is required."}, status=400)

    if not garment_file and not garment_url:
        return JsonResponse(
            {"error": "Please upload a garment image or select a product."}, status=400
        )

    try:
        model_b64 = file_to_base64_uri(model_file)

        # Prioritize uploaded file over remote URL string
        if garment_file:
            garment_b64 = file_to_base64_uri(garment_file)
        else:
            garment_b64 = fetch_url_to_base64_uri(garment_url)

        client = Fashn(api_key=api_key)

        prediction = client.predictions.run(
            model_name="tryon-max",
            inputs={
                "model_image": model_b64,
                "product_image": garment_b64,
            },
        )

        return JsonResponse({
            "status": "processing",
            "prediction_id": prediction.id,
        })

    except Exception as e:
        return JsonResponse({"error": f"Try-on execution failed: {str(e)}"}, status=500)



def check_tryon_status(request, pred_id):
    """Polled via AJAX by the frontend every 2 seconds until complete."""
    api_key = getattr(settings, "FASHN_API_KEY", "").strip()

    if not api_key:
        return JsonResponse(
            {"error": "Fashn AI API key is not configured on the server."}, status=500
        )

    try:
        client = Fashn(api_key=api_key)
        prediction = client.predictions.status(pred_id)

        if prediction.status == "completed":
            session_key = f"processed_pred_{pred_id}"
            remaining_tryons = 0
            message = None

            if request.user.is_authenticated:
                usage, _ = TryOnUsage.objects.get_or_create(user=request.user)
                if not request.session.get(session_key):
                    usage.tryon_count += 1
                    usage.save()
                    request.session[session_key] = True
                remaining_tryons = usage.remaining_tryons()
            else:
                # Deduct from guest session if not already counted for this prediction
                if not request.session.get(session_key):
                    request.session['guest_tryons_left'] = max(0, request.session.get('guest_tryons_left', 1) - 1)
                    request.session[session_key] = True
                    request.session.modified = True
                
                remaining_tryons = request.session.get('guest_tryons_left', 0)
                if remaining_tryons == 0:
                    message = "Please log in to continue using this feature."

            raw_output = prediction.output
            if isinstance(raw_output, list) and len(raw_output) > 0:
                image_url = raw_output[0]
            else:
                image_url = raw_output

            response_data = {
                "status": "completed",
                "output": image_url,
                "remaining": remaining_tryons,
            }
            if message:
                response_data["message"] = message

            return JsonResponse(response_data)

        elif prediction.status in ("failed", "cancelled"):
            error_details = getattr(prediction, "error", "Generation failed.")
            error_msg = getattr(error_details, "message", str(error_details))

            return JsonResponse(
                {"status": "failed", "error": error_msg}, status=400
            )

        return JsonResponse({"status": "processing"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)