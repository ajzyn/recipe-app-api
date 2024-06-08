"""
Test for models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email successful"""
        email = "test@example.com"
        password = "testabc123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))


    def test_new_user_email_normalized(self):
        sample_emails=[
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['test2@Example.com','test2@example.com'],
            ['TEST3@EXAMPLE.COM','TEST3@example.com'],
            ['test4@example.COM','test4@example.com'],
        ]

        for email_to_provide, expected_email in sample_emails:
            user = get_user_model().objects.create_user(email_to_provide, 'sample123')
            self.assertEqual(user.email, expected_email)


    def test_user_without_email_raises_erro(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'sample123')


    def test_create_superuser(self):
        """Test creating a superuser with an email successful"""
        email = "test@example.com"
        password = "testabc123"

        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

