import base64
import json
import time
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import TryOnUsage

FASHN_API_KEY = getattr(settings, "FASHN_API_KEY", "your-fashn-ai-api-key")


def file_to_base64_uri(uploaded_file):
    """Converts an uploaded file buffer in memory into a base64 Data URI."""
    encoded_bytes = base64.b64encode(uploaded_file.read()).decode("utf-8")
    content_type = uploaded_file.content_type or "image/jpeg"
    return f"data:{content_type};base64,{encoded_bytes}"


@login_required
def tryon_view(request):
    # Fetch or create the user's try-on usage record
    usage, _ = TryOnUsage.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Check usage limit
        if not usage.can_use_tryon():
            return JsonResponse(
                {"error": "You have reached your limit of 2 free try-ons."},
                status=403,
            )

        # Retrieve file objects from request.FILES
        model_file = request.FILES.get("model_image")
        garment_file = request.FILES.get("garment_image")

        if not model_file or not garment_file:
            return JsonResponse(
                {"error": "Both model photo and garment photo are required."},
                status=400,
            )

        try:
            # Convert uploaded images to base64 URIs
            model_b64 = file_to_base64_uri(model_file)
            garment_b64 = file_to_base64_uri(garment_file)

            headers = {
                "Authorization": f"Bearer {FASHN_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model_name": "tryon-max",
                "inputs": {
                    "model_image": model_b64,
                    "garment_image": garment_b64,
                    "category": "tops",  # Options: 'tops', 'bottoms', 'one-pieces'
                },
            }

            # 1. Initiate job with Fashn AI
            response = requests.post(
                "https://api.fashn.ai/v1/run", json=payload, headers=headers
            )
            res_data = response.json()

            if response.status_code not in [200, 201]:
                error_detail = res_data.get("error")
                error_msg = (
                    error_detail.get("message")
                    if isinstance(error_detail, dict)
                    else (error_detail or "Fashn AI request failed.")
                )
                return JsonResponse({"error": error_msg}, status=400)

            pred_id = res_data.get("id")
            output_images = res_data.get("output")

            # 2. Poll until job completes if output isn't immediately available
            if not output_images and pred_id:
                status_url = f"https://api.fashn.ai/v1/status/{pred_id}"
                max_retries = 30  # Wait up to 30 seconds
                for _ in range(max_retries):
                    time.sleep(1)
                    poll_res = requests.get(status_url, headers=headers).json()
                    status = poll_res.get("status")

                    if status == "completed":
                        output_images = poll_res.get("output")
                        break
                    elif status == "failed":
                        error_msg = poll_res.get("error", {}).get(
                            "message", "Generation failed."
                        )
                        return JsonResponse({"error": error_msg}, status=400)

            # 3. Increment count upon successful output generation
            if output_images:
                usage.tryon_count += 1
                usage.save()

                return JsonResponse(
                    {
                        "success": True,
                        "remaining": usage.remaining_tryons(),
                        "prediction_id": pred_id,
                        "output": output_images,
                    }
                )
            else:
                return JsonResponse(
                    {"error": "Generation timed out. Please try again."},
                    status=504,
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # GET Request: Pass remaining try-ons count to context
    return render(
        request, "tryon/tryon.html", {"remaining_tryons": usage.remaining_tryons()}
    )