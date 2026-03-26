from django.test import TestCase
from django.urls import reverse

from .models import Booking, Menu


class BookingModelTest(TestCase):
    def test_create_booking(self):
        item = Booking.objects.create(first_name="TestUser", reservation_date="2026-03-10", reservation_slot=15)
        self.assertEqual(str(item), "TestUser")

    def test_duplicate_slot_not_allowed(self):
        Booking.objects.create(first_name="A", reservation_date="2026-03-10", reservation_slot=15)
        response = self.client.post(
            reverse('bookings'),
            data='{"first_name":"B","reservation_date":"2026-03-10","reservation_slot":15}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 409)


class MenuViewTest(TestCase):
    def test_menu_sorted_a_to_z(self):
        Menu.objects.create(name="Zebra Dish", price=10, menu_item_description="z")
        Menu.objects.create(name="Apple Dish", price=20, menu_item_description="a")

        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)
        menu_items = list(response.context['menu'])
        self.assertEqual([m.name for m in menu_items], ["Apple Dish", "Zebra Dish"])