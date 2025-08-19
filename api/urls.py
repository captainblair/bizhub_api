from django.urls import path
from .views import (
    RegisterView, ProductListCreateView, ProductDetailView, ProductSearchView,
    LowStockView, OrderListCreateView, OrderDetailView, MpesaPaymentView,
    MpesaCallbackView, NotificationView, LoyaltyPointView, DashboardSalesView,
    DashboardBestSellersView, DashboardInventoryView, DashboardCustomersView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('inventory/low-stock/', LowStockView.as_view(), name='low-stock'),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('payments/mpesa/', MpesaPaymentView.as_view(), name='mpesa-payment'),
    path('payments/mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa-callback'),
    path('notifications/', NotificationView.as_view(), name='notifications'),
    path('loyalty-points/', LoyaltyPointView.as_view(), name='loyalty-points'),
    path('dashboard/sales/', DashboardSalesView.as_view(), name='dashboard-sales'),
    path('dashboard/best-sellers/', DashboardBestSellersView.as_view(), name='dashboard-best-sellers'),
    path('dashboard/inventory/', DashboardInventoryView.as_view(), name='dashboard-inventory'),
    path('dashboard/customers/', DashboardCustomersView.as_view(), name='dashboard-customers'),
]