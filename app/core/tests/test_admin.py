from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class AdminSiteTests(TestCase):
    """Tests for django ADMNIN"""

    def setUp(self):
        """Create user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            "admin@example.com",
            "test1233"
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="example@example.com",
            password="test1233",
            name="chujek"
        )

    def test_user_list(self):
        """test are user is listed on the page"""

        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.name)


    def test_edit_user_page(self):
        """test are user is listed on the page"""

        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)


    def test_create_user_page(self):
        """test that create user page works"""

        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)