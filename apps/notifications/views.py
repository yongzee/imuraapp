from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Notification
from .forms import PriceProposalForm, SendMessageForm
from apps.products.models import Product

@login_required
def notification_list(request):
    """Display paginated list of notifications for the logged-in user."""
    qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    notifications = paginator.get_page(page)
    return render(request, "notifications/list.html", {"notifications": notifications})

@login_required
@require_POST
def send_message(request):
    """Send a message to another user (recipient notif + sender copy)."""
    form = SendMessageForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    recipient_id = request.POST.get("recipient_id")
    try:
        recipient = get_user_model().objects.get(pk=recipient_id)
    except Exception:
        return JsonResponse({"ok": False, "error": "Recipient not found"}, status=404)

    text = form.cleaned_data["text"].strip()

    # 1) Recipient notification (incoming)
    incoming = Notification.objects.create(
        sender=request.user,
        recipient=recipient,
        type="message",
        verb="sent you a message",
        read=False,
        data={
            "text": text,
            "other_user_id": request.user.id,         # always "the other person"
            "other_username": request.user.username,
            "direction": "in",
        },
    )

    # 2) Sender copy (outgoing) -> so sender can view it in their notifications too
    outgoing = Notification.objects.create(
        sender=request.user,
        recipient=request.user,
        type="message",
        verb=f"You sent a message to {recipient.username}",
        read=True,
        data={
            "text": text,
            "other_user_id": recipient.id,            # always "the other person"
            "other_username": recipient.username,
            "direction": "out",
        },
    )

    # Backward compatible response (your current JS expects ok)
    return JsonResponse({
        "ok": True,
        "id": outgoing.id,   # keep "id" so nothing breaks
        "notification": {    # extra payload for notifications page to render instantly
            "id": outgoing.id,
            "verb": outgoing.verb,
            "text": text,
            "created_at": outgoing.created_at.strftime("%Y-%m-%d %H:%M"),
            "created_natural": "just now",
            "other_user_id": recipient.id,
            "other_username": recipient.username,
        }
    })

@login_required
@require_POST
def propose_price(request):
    """Propose a price for a product."""
    form = PriceProposalForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    product_id = request.POST.get("product_id")
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Product not found"}, status=404)

    recipient = product.seller
    if recipient == request.user:
        return JsonResponse({"ok": False, "error": "Cannot propose price to yourself"}, status=400)

    notif = Notification.objects.create(
        sender=request.user,
        recipient=recipient,
        type="price_proposal",
        verb=f"proposed a price for {product.title}",
        data={
            "product_id": product.id,
            "suggested_price": str(form.cleaned_data["suggested_price"]),
            "message": form.cleaned_data.get("message", ""),
        },
        accepted=None  # initially None, means pending
    )

    return JsonResponse({"ok": True, "id": notif.id})

@login_required
@require_POST
def proposal_accept(request, pk):
    """Accept a price proposal."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user, type="price_proposal")

    if notif.accepted is None:
        notif.accepted = True
        notif.read = True
        notif.save()

        # Send a new notification to the proposer
        Notification.objects.create(
            sender=request.user,  # seller
            recipient=notif.sender,  # proposer
            type="info",
            verb=f"accepted your price proposal for {notif.data.get('product_id')}",
            data={
                "product_id": notif.data.get('product_id'),
                "suggested_price": notif.data.get('suggested_price'),
                "original_notification_id": notif.id
            }
        )

    return JsonResponse({"ok": True})

@login_required
@require_POST
def proposal_decline(request, pk):
    """Decline a price proposal."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user, type="price_proposal")

    if notif.accepted is None:
        notif.accepted = False
        notif.read = True
        notif.save()

        # Send a new notification to the proposer
        Notification.objects.create(
            sender=request.user,  # seller
            recipient=notif.sender,  # proposer
            type="info",
            verb=f"declined your price proposal for {notif.data.get('product_id')}",
            data={
                "product_id": notif.data.get('product_id'),
                "suggested_price": notif.data.get('suggested_price'),
                "original_notification_id": notif.id
            }
        )

    return JsonResponse({"ok": True})

@login_required
@require_POST
def mark_read(request, pk):
    """Mark a notification as read."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.read = True
    notif.save()
    return JsonResponse({"ok": True})

@login_required
def delete_notification(request, id):
    """Delete a notification."""
    if request.method == "POST":
        try:
            notification = Notification.objects.get(id=id, recipient=request.user)
            notification.delete()
            return JsonResponse({"ok": True})
        except Notification.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Notification not found."})
    return JsonResponse({"ok": False, "error": "Invalid request."})
