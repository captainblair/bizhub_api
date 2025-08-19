from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import User, Product, Order, OrderItem, Payment, Notification, LoyaltyPoint
from .serializers import UserSerializer, ProductSerializer, OrderSerializer, PaymentSerializer, NotificationSerializer, LoyaltyPointSerializer
from .permissions import IsAdminOrStaff, IsAdmin, IsOrderOwnerOrStaff
from django.db import transaction
from django.conf import settings
import requests
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime, timedelta
import base64
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category')
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        stock_available = self.request.query_params.get('stock_available')

        if category:
            queryset = queryset.filter(category=category)
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        if stock_available == 'true':
            queryset = queryset.filter(stock_level__gt=0)

        return queryset

class ProductSearchView(APIView):
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        query = request.query_params.get('q', '')
        queryset = Product.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrStaff]

class LowStockView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        low_stock_products = Product.objects.filter(stock_level__lte=5)
        serializer = ProductSerializer(low_stock_products, many=True)
        return Response(serializer.data)

class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(user=self.request.user)
            items = order.items.all()
            total_amount = 0
            for item in items:
                product = item.product
                if product.stock_level < item.quantity:
                    raise serializers.ValidationError(f"Insufficient stock for {product.name}")
                product.stock_level -= item.quantity
                product.save()
                total_amount += item.price * item.quantity
                if product.stock_level <= 5:
                    admin_user = User.objects.filter(role='admin').first()
                    if admin_user:
                        Notification.objects.create(
                            user=admin_user,
                            message=f"Low stock alert: {product.name} has {product.stock_level} units left.",
                            type='email'
                        )
            order.total_amount = total_amount
            order.save()
            if order.payment_method == 'M-Pesa':
                Payment.objects.create(
                    order=order,
                    amount=total_amount,
                    payment_method='M-Pesa',
                    status='pending'
                )
            LoyaltyPoint.objects.create(user=self.request.user, points=int(total_amount // 10))
            async_to_sync(channel_layer.group_send)(
                'orders',
                {
                    'type': 'order_update',
                    'message': f"New order {order.id} created"
                }
            )

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwnerOrStaff]

class MpesaPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        amount = request.data.get('amount')
        phone_number = request.data.get('phone_number', request.user.phone_number)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_method != 'M-Pesa':
            return Response({"error": "Order does not use M-Pesa payment"}, status=status.HTTP_400_BAD_REQUEST)

        access_token = self.get_mpesa_access_token()
        if not access_token:
            return Response({"error": "Failed to get M-Pesa access token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = f"{settings.SAFARICOM_API}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}"}
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(amount),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"Order {order.id}",
            "TransactionDesc": "Payment for order"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'amount': amount,
                    'payment_method': 'M-Pesa',
                    'transaction_id': response.json().get('CheckoutRequestID'),
                    'status': 'pending'
                }
            )
            return Response(response.json(), status=status.HTTP_200_OK)
        return Response({"error": "Payment initiation failed", "details": response.json()}, status=status.HTTP_400_BAD_REQUEST)

    def get_mpesa_access_token(self):
        url = f"{settings.SAFARICOM_API}/oauth/v1/generate?grant_type=client_credentials"
        auth = (settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            return response.json().get('access_token')
        return None

class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = data.get('CheckoutRequestID')
        result_code = data.get('ResultCode')
        result_desc = data.get('ResultDesc')

        try:
            payment = Payment.objects.get(transaction_id=checkout_request_id)
            if result_code == 0:
                payment.status = 'completed'
                payment.order.status = 'confirmed'
                payment.order.save()
                Notification.objects.create(
                    user=payment.order.user,
                    message=f"Your payment of {payment.amount} for Order {payment.order.id} was successful.",
                    type='SMS'
                )
                async_to_sync(channel_layer.group_send)(
                    'orders',
                    {
                        'type': 'order_update',
                        'message': f"Order {payment.order.id} confirmed"
                    }
                )
            else:
                payment.status = 'failed'
            payment.save()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

class NotificationView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            notification = serializer.save()
            if notification.type == 'SMS':
                self.send_sms(notification.user, notification.message)
            elif notification.type == 'email':
                self.send_email(notification.user, notification.message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_sms(self, user, message):
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        try:
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=user.phone_number
            )
        except Exception as e:
            print(f"SMS sending failed: {e}")

    def send_email(self, user, message):
        mail = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=user.email,
            subject='BizHub Notification',
            plain_text_content=message
        )
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(mail)
        except Exception as e:
            print(f"Email sending failed: {e}")

class LoyaltyPointView(generics.ListCreateAPIView):
    queryset = LoyaltyPoint.objects.all()
    serializer_class = LoyaltyPointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LoyaltyPoint.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DashboardSalesView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = datetime.now().date()
        sales = Order.objects.filter(created_at__date=today).aggregate(
            total_sales=models.Sum('total_amount')
        )
        return Response({"total_sales": sales['total_sales'] or 0})

class DashboardBestSellersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        best_sellers = OrderItem.objects.values('product__name').annotate(
            total_quantity=models.Sum('quantity')
        ).order_by('-total_quantity')[:5]
        return Response(best_sellers)

class DashboardInventoryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        inventory = Product.objects.all().values('name', 'stock_level')
        return Response(inventory)

class DashboardCustomersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        customer_activity = User.objects.filter(role='customer').annotate(
            order_count=models.Count('orders')
        ).values('username', 'order_count')
        return Response(customer_activity)