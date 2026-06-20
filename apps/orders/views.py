from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages

import uuid
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta



from .models import Order
from .forms import OrderCreateForm, SellerUpdateForm, BuyerFeedbackForm
from apps.products.models import Product
from apps.notifications.models import Notification  # reuse your notifications app

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.user not in [order.buyer, order.seller]:
        return HttpResponseForbidden("Not allowed")

    # ======================================================
    # SELLER VIEW
    # ======================================================
    if request.user == order.seller:
        form = SellerUpdateForm(instance=order)

        if request.method == "POST" and "seller_update" in request.POST:
            form = SellerUpdateForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
        

                # 🔥 THIS IS THE FIX
                order.status = "completed_by_seller"
                order.save()

                Notification.objects.create(
                    sender=request.user,
                    recipient=order.buyer,
                    type="info",
                    verb="Seller has reviewed your order",
                    data={"order_id": order.id},
                )

                messages.success(
                    request,
                    "Delivery details saved and sent to buyer."
                )
                return redirect(order.get_absolute_url())

        return render(
            request,
            "orders/seller_detail.html",
            {"order": order, "form": form},
        )

    # ======================================================
    # BUYER VIEW
    feedback_form = BuyerFeedbackForm()

    if request.method == "POST":

        # --------------------------------------------------
        # SEND ORDER TO SELLER
        # --------------------------------------------------
        if "send_order" in request.POST:

            if order.status != "pending" or order.is_sent_to_seller:
                messages.error(request, "Order can no longer be sent.")
                return redirect(order.get_absolute_url())

            order.is_sent_to_seller = True
            order.save(update_fields=["is_sent_to_seller"])

            Notification.objects.create(
                sender=request.user,
                recipient=order.seller,
                type="info",
                verb="Buyer sent an order for review",
                data={"order_id": order.id},
            )

            messages.success(request, "Order sent to seller.")
            return redirect(order.get_absolute_url())

        # --------------------------------------------------
        # ACCEPT ORDER (AFTER SELLER COMPLETES)
        # --------------------------------------------------
        if (
            "satisfactory" in request.POST
            and order.status == "completed_by_seller"
        ):
            order.status = "satisfactory"
            order.save(update_fields=["status"])

            messages.success(request, "Order accepted. Proceed to payment.")
            return redirect("orders:checkout", pk=order.pk)

        # --------------------------------------------------
        # FEEDBACK / CANCEL ORDER
        # --------------------------------------------------
        if "feedback_action" in request.POST:
            feedback_form = BuyerFeedbackForm(request.POST)

            if feedback_form.is_valid():
                action = feedback_form.cleaned_data["action"]
                feedback = feedback_form.cleaned_data["feedback"]

                if action == "cancel":
                    order.status = "cancelled"
                    order.is_sent_to_seller = False  # 🔥 IMPORTANT FIX
                else:
                    order.status = "not_satisfactory"

                order.buyer_notes = feedback
                order.save(update_fields=["status", "buyer_notes", "is_sent_to_seller"])

                Notification.objects.create(
                    sender=request.user,
                    recipient=order.seller,
                    type="info",
                    verb="Buyer responded to order",
                    data={
                        "order_id": order.id,
                        "action": action,
                        "feedback": feedback,
                    },
                )

                messages.success(request, "Your response has been sent.")
                return redirect(order.get_absolute_url())

    return render(
        request,
        "orders/buyer_detail.html",
        {"order": order, "feedback_form": feedback_form},
    )


@login_required
def orders_list(request):
    user = request.user

    buyer_orders = Order.objects.filter(buyer=user)
    seller_orders = Order.objects.filter(seller=user)

    # Buyer only
    if buyer_orders.exists() and not seller_orders.exists():
        return redirect("orders:buyer_list")

    # Seller only
    if seller_orders.exists() and not buyer_orders.exists():
        return redirect("orders:seller_list")

    # Both buyer & seller → dashboard
    return render(request, "orders/orders_dashboard.html", {
        "buyer_orders": buyer_orders.order_by("-created_at"),
        "seller_orders": seller_orders.order_by("-created_at"),
    })

@login_required
def create_order(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    
    if product.seller == request.user:
        messages.error(request, "You cannot order your own product.")
        return redirect(product.get_absolute_url())

    # ✅ get proposed price from URL
    proposed_price = request.GET.get("proposed_price")
    try:
        proposed_price = float(proposed_price)
    except (TypeError, ValueError):
        proposed_price = None

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = Order.objects.create(
                buyer=request.user,
                seller=product.seller,
                product=product,

                product_title=product.title,
                product_image=(
                    product.images.first().image.url
                    if product.images.exists()
                    else ""
                ),
                description=product.description,

                quantity=form.cleaned_data["quantity"],

                # ✅ FINAL PRICE LOGIC
                price_at_order=proposed_price if proposed_price else product.price,
                suggested_price=proposed_price,

                buyer_state=form.cleaned_data["buyer_state"],
                buyer_lga=form.cleaned_data["buyer_lga"],
                buyer_address=form.cleaned_data["buyer_address"],
                buyer_notes=form.cleaned_data.get("buyer_notes", ""),

                status="pending",
            )

            messages.success(request, "Order sent to seller successfully.")
            return redirect(order.get_absolute_url())

    else:
        form = OrderCreateForm()

    return render(request, "orders/create_order.html", {
        "product": product,
        "form": form,
        "proposed_price": proposed_price,  # ✅ REQUIRED
    })



@login_required
def buyer_orders_list(request):
    qs = Order.objects.filter(buyer=request.user).order_by("-created_at")
    return render(request, "orders/buyer_list.html", {"orders": qs})

@login_required
def seller_orders_list(request):
    qs = Order.objects.filter(seller=request.user).order_by("-created_at")
    return render(request, "orders/seller_list.html", {"orders": qs})



@login_required
def checkout(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user)

    if order.is_paid:
        messages.info(request, "This order has already been paid.")
        return redirect(order.get_absolute_url())

    # ---- PRICE CALCULATION ----
    transport = float(order.transport_cost or 0)
    product_cost = float(order.price_at_order) * order.quantity
    platform_fee = round(product_cost * 0.03, 2)  # 3%
    total = product_cost + transport + platform_fee

    # ---- GENERATE PAYMENT REF ----
    if not order.payment_reference:
        order.payment_reference = f"ORD-{uuid.uuid4().hex[:10]}"
        order.save()

    context = {
        "order": order,
        "product_cost": product_cost,
        "transport": transport,
        "platform_fee": platform_fee,
        "total": total,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY,
        "reference": order.payment_reference,
        "amount_kobo": int(total * 100),  # Paystack uses kobo
        "email": request.user.email,
    }

    return render(request, "orders/checkout.html", context)
@login_required
def tracking(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # both buyer & seller may view tracking
    if request.user not in [order.buyer, order.seller]:
        return HttpResponseForbidden()
    return render(request, "orders/tracking.html", {"order": order})


@login_required
def delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    # Only buyer or seller can cancel
    if request.user not in [order.buyer, order.seller]:
        return HttpResponseForbidden("Not allowed")

    # Do NOT allow deletion after payment
    if order.is_paid:
        messages.error(request, "Paid orders cannot be deleted.")
        return redirect(order.get_absolute_url())

    if request.method == "POST":
        buyer = order.buyer
        seller = order.seller
        product_title = order.product_title

        order.delete()

        # Notify buyer
        Notification.objects.create(
            sender=request.user,
            recipient=buyer,
            type="info",
            verb=f"Order for '{product_title}' was cancelled",
        )

        # Notify seller
        Notification.objects.create(
            sender=request.user,
            recipient=seller,
            type="info",
            verb=f"Order for '{product_title}' was cancelled",
        )

        messages.success(request, "Order cancelled successfully.")
        return redirect("orders:list")


@login_required
def verify_payment(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user)

    if not order.payment_reference:
        messages.error(request, "No payment reference found.")
        return redirect(order.get_absolute_url())

    url = f"https://api.paystack.co/transaction/verify/{order.payment_reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    response = requests.get(url, headers=headers)
    result = response.json()

    if result["status"] and result["data"]["status"] == "success":
        order.is_paid = True
        order.status = "paid"
        order.paid_at = timezone.now() 
        order.save()

        messages.success(request, "Payment successful!")
        if request.user == order.buyer:
            return redirect("orders:buyer_tracking", pk=order.pk)
        else:
            return redirect("orders:seller_tracking", pk=order.pk)


    messages.error(request, "Payment verification failed.")
    return redirect("orders:checkout", pk=order.pk)




@login_required
def buyer_tracking(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user)

    # Buyer must have paid
    if not order.is_paid:
        messages.error(request, "Payment not completed yet.")
        return redirect(order.get_absolute_url())

    if request.method == "POST":

        # ---------------- APPROVE EXTENSION ----------------
        if "approve_extension" in request.POST:

            if order.status != "in_transit":
                messages.error(request, "Order is not in transit.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            if order.extension_status != "pending":
                messages.error(request, "No pending extension request.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            if not order.delivery_deadline or not order.extension_requested_days:
                messages.error(request, "Invalid extension request.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            # ✅ Apply extension
            order.delivery_deadline = order.delivery_deadline + timedelta(
                days=order.extension_requested_days
            )
            order.extra_days_requested += order.extension_requested_days
            order.extension_requested_days = 0
            order.extension_status = "approved"
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.seller,
                type="success",
                verb="Buyer approved delivery extension",
                data={
                    "order_id": order.id,
                    "new_deadline": order.delivery_deadline.isoformat(),
                },
            )

            messages.success(request, "Delivery extension approved.")
            return redirect("orders:buyer_tracking", pk=order.pk)
    # ---------------- REJECT EXTENSION ----------------
        if "reject_extension" in request.POST:

            if order.status != "in_transit":
                messages.error(request, "Order is not in transit.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            if order.extension_status != "pending":
                messages.error(request, "No pending extension request.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            # ✅ Reject safely
            order.extension_status = "rejected"
            order.extension_requested_days = 0
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.seller,
                type="error",
                verb="Buyer rejected delivery extension",
                data={"order_id": order.id},
            )

            messages.info(request, "Delivery extension rejected.")
            return redirect("orders:buyer_tracking", pk=order.pk)

        # ---------------- CONFIRM DELIVERY ----------------
        if "confirm_delivery" in request.POST:
            if order.status != "in_transit":
                messages.error(request, "Order is not currently in transit.")
                return redirect("orders:buyer_tracking", pk=order.pk)

            order.status = "delivered"
            order.delivered_at = timezone.now()
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.seller,
                type="success",
                verb="Buyer confirmed delivery",
                data={"order_id": order.id},
            )

            messages.success(request, "Delivery confirmed successfully.")
            return redirect("orders:buyer_tracking", pk=order.pk)

        # ---------------- ORDER NOT RECEIVED ----------------
        if "order_not_received" in request.POST:

            if order.status != "in_transit":
                messages.error(
                    request,
                    "This action is only allowed while the order is in transit."
                )
                return redirect("orders:buyer_tracking", pk=order.pk)

            Notification.objects.create(
                sender=request.user,
                recipient=order.seller,
                type="warning",
                verb="Buyer reports order not received",
                data={
                    "order_id": order.id,
                    "buyer": request.user.username,
                },
            )

            messages.success(
                request,
                "Seller has been notified. Please allow them time to respond."
            )

            return redirect("orders:buyer_tracking", pk=order.pk)

    return render(request, "orders/tracking_buyer.html", {
        "order": order
    })


@login_required
def seller_tracking(request, pk):
    order = get_object_or_404(Order, pk=pk, seller=request.user)

    if not order.is_paid:
        messages.error(request, "Buyer has not paid yet.")
        return redirect(order.get_absolute_url())

    if request.method == "POST":

        # --------------------------------------------------
        # MARK AS IN TRANSIT
        # --------------------------------------------------
        if "mark_in_transit" in request.POST:
            if order.status != "paid":
                messages.error(request, "Order cannot be dispatched now.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.status = "in_transit"
            order.dispatched_at = timezone.now()
            order.delivery_note = request.POST.get("delivery_note")
            order.delivery_contact = request.POST.get("delivery_contact")
            order.delivery_deadline = (
                order.dispatched_at + timedelta(days=order.days_to_deliver)
            )
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="info",
                verb="Order is now in transit",
                data={"order_id": order.id},
            )

            messages.success(request, "Order marked as in transit.")
            return redirect("orders:seller_tracking", pk=order.pk)

        # --------------------------------------------------
        # REQUEST DELIVERY EXTENSION
        # --------------------------------------------------
        if "request_extension" in request.POST and order.status == "in_transit":
            extra_days = int(request.POST.get("extra_days", 0))
            if extra_days <= 0:
                messages.error(request, "Invalid number of days.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.delivery_deadline += timedelta(days=extra_days)
            order.extra_days_requested += extra_days
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="info",
                verb="Seller requested delivery extension",
                data={"order_id": order.id, "extra_days": extra_days},
            )

            messages.success(request, "Deadline extended.")
            return redirect("orders:seller_tracking", pk=order.pk)
        # orders/views.py (seller_tracking)

        if "request_extension" in request.POST and order.status == "in_transit":

            try:
                extra_days = int(request.POST.get("extra_days", 0))
            except ValueError:
                extra_days = 0

            if extra_days <= 0:
                messages.error(request, "Invalid number of days.")
                return redirect("orders:seller_tracking", pk=order.pk)

            if order.extension_status == "pending":
                messages.error(request, "Extension already pending approval.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.extension_requested_days = extra_days
            order.extension_requested_at = timezone.now()
            order.extension_status = "pending"
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="warning",
                verb="Seller requested delivery time extension",
                data={
                    "order_id": order.id,
                    "extra_days": extra_days,
                },
            )

            messages.success(request, "Extension request sent to buyer.")
            return redirect("orders:seller_tracking", pk=order.pk)

        # --------------------------------------------------
        # SUBMIT BANK DETAILS
        # --------------------------------------------------
        # --------------------------------------------------

        if "submit_bank_details" in request.POST:

            if order.status != "delivered":
                messages.error(
                    request,
                    "Bank details can only be submitted after delivery is confirmed."
                )
                return redirect("orders:seller_tracking", pk=order.pk)

            if order.seller_bank_name:
                messages.error(
                    request,
                    "Bank details already submitted. Await admin payout."
                )
                return redirect("orders:seller_tracking", pk=order.pk)

            bank_name = request.POST.get("bank_name")
            account_name = request.POST.get("account_name")
            account_number = request.POST.get("account_number")

            if not bank_name or not account_name or not account_number:
                messages.error(request, "All bank details are required.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.seller_bank_name = bank_name
            order.seller_account_name = account_name
            order.seller_account_number = account_number
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="info",
                verb="Seller submitted bank details for payout",
                data={"order_id": order.id},
            )

            messages.success(
                request,
                "Bank details submitted successfully. "
                "Admin will process payout within 24 hours."
            )
            if order.seller_bank_name:
                messages.info(request, "Bank details already submitted.")


            return redirect("orders:seller_tracking", pk=order.pk)
        
        # --------------------------------------------------
# SELLER CONFIRMS PAYOUT RECEIVED
# --------------------------------------------------
        if "confirm_payout" in request.POST:
            if not order.payment_verified_by_admin:
                messages.error(request, "Payment not yet verified by admin.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.seller_confirmed_payout = True
            order.status = "completed"
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="success",
                verb="Seller confirmed payout received",
                data={"order_id": order.id},
            )

            messages.success(request, "Payout confirmed successfully.")
            return redirect("orders:seller_tracking", pk=order.pk)


        # --------------------------------------------------
        # SELLER CONFIRMS PAYOUT RECEIVED
        # --------------------------------------------------
        if "confirm_payout" in request.POST:
            if not order.payment_verified_by_admin:
                messages.error(request, "Payment not yet verified by admin.")
                return redirect("orders:seller_tracking", pk=order.pk)

            order.seller_confirmed_payout = True
            order.status = "completed"
            order.save()

            Notification.objects.create(
                sender=request.user,
                recipient=order.buyer,
                type="success",
                verb="Seller confirmed payout received",
                data={"order_id": order.id},
            )

            messages.success(request, "Payout confirmed successfully.")
            return redirect("orders:seller_tracking", pk=order.pk)

    return render(request, "orders/tracking_seller.html", {"order": order})


