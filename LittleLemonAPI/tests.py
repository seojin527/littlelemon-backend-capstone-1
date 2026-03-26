from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase

from .models import Category, MenuItem


class LittleLemonAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(slug='main', title='Main')
        MenuItem.objects.create(title='Greek Salad', price='10.00', featured=True, category=self.category)
        MenuItem.objects.create(title='Lemon Dessert', price='8.00', featured=False, category=self.category)

        self.manager_group, _ = Group.objects.get_or_create(name='Manager')
        self.crew_group, _ = Group.objects.get_or_create(name='Delivery crew')

        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass12345')
        self.manager = User.objects.create_user('manager', password='pass12345')
        self.manager.groups.add(self.manager_group)
        self.user = User.objects.create_user('customer', password='pass12345')

    def test_menu_items_public_list(self):
        response = self.client.get('/api/menu-items')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_menu_items_requires_admin_for_create(self):
        payload = {'title': 'Pasta', 'price': '14.00', 'featured': True, 'category_id': self.category.id}
        response = self.client.post('/api/menu-items', payload, format='json')
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/menu-items', payload, format='json')
        self.assertEqual(response.status_code, 201)

    def test_delivery_crew_assignment_requires_manager(self):
        User.objects.create_user('crewuser', password='pass12345')

        self.client.force_authenticate(self.user)
        response = self.client.post('/api/groups/delivery-crew/users', {'username': 'crewuser'}, format='json')
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/groups/delivery-crew/users', {'username': 'crewuser'}, format='json')
        self.assertEqual(response.status_code, 201)