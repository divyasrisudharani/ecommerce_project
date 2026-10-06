from django.contrib import admin

# Register your models here.
from django.db import connection
import csv
from django.http import HttpResponse
from .models import Cart, CartItem, Order, OrderItem,FastAPIOrder
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.template.response import TemplateResponse
from django.urls import path
from django.shortcuts import render
from products.models import Product
from django.db.models.functions import TruncMonth
from products.models import Product
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cart',
        'product',
        'quantity',
    )
    search_fields = (
        'product__name',
        'cart__user__username',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'total',
        'payment_status',
        'order_status',
        'created_at',
    )

    list_filter = (
        'payment_status',
        'order_status',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__email',
    )

    ordering = (
        '-created_at',
    )

    # def get_urls(self):
    #     urls = super().get_urls()

    #     custom_urls = [
    #         path(
    #             'analytics/',
    #             self.admin_site.admin_view(self.analytics_view),
    #             name='order-analytics',
    #         ),
    #     ]

    #     return custom_urls + urls
  

    # keep your existing list_display, list_filter, etc. above

    def analytics_view(self, request):

        total_sales = (
        Order.objects
        .filter(payment_status="paid")
        .aggregate(total=Sum("total"))["total"]
        or 0
        )

        total_orders = Order.objects.count()

        pending_orders = (
        Order.objects
        .filter(order_status="pending")
        .count()
         )

        top_products = (
        OrderItem.objects
        .values("product__name")
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by("-total_quantity")[:5]
        )

        low_stock_products = (
        Product.objects
        .filter(stock__lte=5)
        .order_by("stock")
        )

        monthly_revenue = (
        Order.objects
        .filter(payment_status="paid")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            revenue=Sum("total")
        )
        .order_by("month")
        )

        context = {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "top_products": top_products,
        "low_stock_products": low_stock_products,
        "monthly_revenue": monthly_revenue,
        }

        return render(
        request,
        "admin/orders/analytics.html",
        context
        )

        
    def report_csv(self, request):
        orders = Order.objects.all().order_by('-created_at')

        response = HttpResponse(
        content_type='text/csv'
        )

        response['Content-Disposition'] = (
        'attachment; filename="orders_report.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
        'Order ID',
        'User',
        'Total',
        'Payment Status',
        'Order Status',
        'Created At',
        ])

        for order in orders:
            writer.writerow([
            order.id,
            order.user.username,
            order.total,
            order.payment_status,
            order.order_status,
            order.created_at,
        ])

        return response
    def report_pdf(self, request):
        orders = Order.objects.all().order_by('-created_at')

        response = HttpResponse(
        content_type='application/pdf'
        )

        response['Content-Disposition'] = (
        'attachment; filename="orders_report.pdf"'
        )

        pdf = canvas.Canvas(response, pagesize=A4)

        width, height = A4

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 50, "E-Commerce Order Report")

        pdf.setFont("Helvetica", 10)

        y = height - 90

        for order in orders:
            text = (
            f"Order ID: {order.id} | "
            f"User: {order.user.username} | "
            f"Total: {order.total} | "
            f"Payment: {order.payment_status} | "
            f"Status: {order.order_status}"
        )

        pdf.drawString(50, y, text)

        y -= 20

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50

        pdf.save()

        return response
    
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
        path(
            'analytics/',
            self.admin_site.admin_view(self.analytics_view),
            name='order-analytics',
        ),
        path(
            'report/csv/',
            self.admin_site.admin_view(self.report_csv),
            name='order-report-csv',
        ),
        path(
            'report/pdf/',
            self.admin_site.admin_view(self.report_pdf),
            name='order-report-pdf',
        ),
        ]

        return custom_urls + urls

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'quantity',
        'price',
    )

    search_fields = (
        'product__name',
    )
@admin.register(FastAPIOrder)
class FastAPIOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_id',
        'total_amount',
        'status',
    )

    list_filter = ('status',)

    search_fields = (
        'id',
        'user_id',
    )

    ordering = ('-id',)