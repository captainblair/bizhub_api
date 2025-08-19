from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Product, Order, OrderItem, Payment, Notification, LoyaltyPoint
from django.urls import reverse
from rest_framework import status
from decimal import Decimal

User = get_user_model()

class BizHubAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', email='admin@bizhub.com', password='admin123', role='admin'
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@bizhub.com', password='staff123', role='staff'
        )
        self.customer = User.objects.create_user(
            username='customer', email='customer@bizhub.com', password='cust123', role='customer',
            phone_number='+254123456789'
        )
        self.product = Product.objects.create(
            name='Laptop', description='High-performance laptop', price=999.99,
            stock_level=10, category='Electronics', image_url='https://example.com/laptop.jpg'
        )

    def test_register_user(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@bizhub.com',
            'password': 'newpass123',
            'role': 'customer',
            'phone_number': '+254987654321'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)

    def test_login(self):
        data = {'username': 'customer', 'password': 'cust123'}
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])

    def test_create_product_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'Phone',
            'description': 'Smartphone with 5G',
            'price': 499.99,
            'stock_level': 20,
            'category': 'Electronics',
            'image_url': 'https://example.com/phone.jpg'
        }
        response = self.client.post(reverse('product-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_product_search(self):
        response = self.client.get(reverse('product-search'), {'q': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Laptop')

    def test_product_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('product-list-create'), {'category': 'Electronics', 'stock_available': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_order_customer(self):
        self.client.force_authenticate(user=self.customer)
        data = {
            'user_id': self.customer.id,
            'total_amount': 999.99,
            'payment_method': 'M-Pesa',
            'status': 'pending',
            'items': [{'product_id': self.product.id, 'quantity': 1, 'price': 999.99}]
        }
        response = self.client.post(reverse('order-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Product.objects.get(id=self.product.id).stock_level, 9)
        self.assertEqual(LoyaltyPoint.objects.filter(user=self.customer).count(), 1)

    def test_low_stock_alert(self):
        self.client.force_authenticate(user=self.staff)
        product = Product.objects.create(
            name='Tablet', description='Portable tablet', price=299.99,
            stock_level=3, category='Electronics', image_url='https://example.com/tablet.jpg'
        )
        response = self.client.get(reverse('low-stock'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Tablet')

    def test_dashboard_sales_admin(self):
        self.client.force_authenticate(user=self.admin)
        order = Order.objects.create(
            user=self.customer, total_amount=999.99, payment_method='M-Pesa', status='confirmed'
        )
        response = self.client.get(reverse('dashboard-sales'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['total_sales'], 999.99)