# apps/feedback/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Feedback

def feedback_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        feedback_type = request.POST.get('feedback_type', 'general')
        rating_raw = request.POST.get('rating', '5')
        message = request.POST.get('message', '').strip()

        # Validation
        if not message:
            return JsonResponse({'status': 'error', 'message': 'Please provide your feedback.'}, status=400)

        # Safely convert rating to integer
        try:
            rating = int(rating_raw)
            rating = max(1, min(5, rating))  # Clamp between 1 and 5
        except (ValueError, TypeError):
            rating = 5

        # Save record directly to Supabase via Django ORM
        Feedback.objects.create(
            name=name or None,
            email=email or None,
            phone_number=phone_number or None,
            feedback_type=feedback_type,
            rating=rating,
            message=message
        )

        return JsonResponse({'status': 'success', 'message': 'Thank you! Your feedback has been submitted.'})

    # Render template (adjust path if inside feedback/feedback.html)
    return render(request, 'feedback.html')