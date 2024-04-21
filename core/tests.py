from django.test import TestCase
from django.test import TestCase, Client
from django.urls import reverse
from .models import Item, Order, OrderItem, UserProfile, Address, Payment, Coupon, Refund
from .forms import CheckoutForm, CouponForm, RefundForm
from unittest.mock import patch
from decimal import Decimal
import stripe

class TestViews(TestCase):

    def pay(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            user=self.user,
            ordered=False,
            billing_address=None,
            shipping_address=None,
            coupon=None,
            being_delivered=False,
            received=False,
            refund_requested=False,
            refund_granted=False
        )
        self.order.items.add(
            OrderItem(
                item=Item.objects.create(title='Test Item', price=Decimal('10.00')),
                quantity=2,
                order=self.order
            )
        )
        self.order.save()

    def setUp(self):
        self.client = Client()
        self.user = UserProfile.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            user=self.user,
            ordered=False,
            billing_address=None,
            shipping_address=None,
            coupon=None,
            being_delivered=False,
            received=False,
            refund_requested=False,
            refund_granted=False
        )
        self.order.items.add(
            OrderItem(
                item=Item.objects.create(title='Test Item', price=Decimal('10.00')),
                quantity=2,
                order=self.order
            )
        )
        self.order.save()


    def login(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_login(self.user)

    @patch('stripe.Charge.create')
    def test_payment_view(self, mock_charge_create):
        # Test that the view returns a 200 status code
        response = self.client.get(reverse('core:payment', kwargs={'payment_option': 'stripe'}))
        self.assertEqual(response.status_code, 200)

        # Test that the view renders the correct template
        self.assertTemplateUsed(response, 'payment.html')

        # Test that the view passes the correct context to the template
        self.assertContains(response, 'STRIPE_PUBLIC_KEY', status_code=200)

        # Test that the view creates a payment when a valid form is submitted
        mock_charge_create.return_value = {'id': 'ch_1234567890'}
        response = self.client.post(reverse('core:payment', kwargs={'payment_option': 'stripe'}), {
            'stripeToken': 'tok_visa',
            'save': False,
            'use_default': False
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:order-summary'))
        self.assertTrue(Payment.objects.exists())

        # Test that the view does not create a payment when an invalid form is submitted
        response = self.client.post(reverse('core:payment', kwargs={'payment_option': 'stripe'}), {
            'stripeToken': '',
            'save': False,
            'use_default': False
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.exists())