from django.contrib import admin
from .models import User, Product, Order, OrderItem, Payment, Notification, LoyaltyPoint

admin.site.register(User)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Notification)
admin.site.register(LoyaltyPoint)