"""
Admin configuration for the payments app.
"""

import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Payment, Subscription


@admin.action(description="Export selected payments to CSV")
def export_payments_csv(modeladmin, request, queryset):
    """Export selected payments as a CSV file."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payments_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Razorpay Order ID", "Razorpay Payment ID", "Booking ID",
        "Amount", "Currency", "Status", "Paid At", "Created At",
    ])

    for payment in queryset.select_related("booking"):
        writer.writerow([
            payment.razorpay_order_id,
            payment.razorpay_payment_id,
            str(payment.booking_id),
            payment.amount,
            payment.currency,
            payment.status,
            payment.paid_at.strftime("%Y-%m-%d %H:%M") if payment.paid_at else "",
            payment.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "razorpay_order_id",
        "booking",
        "amount",
        "currency",
        "status",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "currency"]
    search_fields = ["razorpay_order_id", "razorpay_payment_id", "booking__id"]
    readonly_fields = [
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "amount",
        "currency",
        "paid_at",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"
    actions = [export_payments_csv]
    list_per_page = 25
    show_full_result_count = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "start_date", "end_date", "is_active"]
    list_filter = ["plan", "is_active"]
    search_fields = ["user__email", "user__first_name", "razorpay_subscription_id"]
    date_hierarchy = "start_date"
    list_per_page = 25
