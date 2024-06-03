from django.test import SimpleTestCase
from app import calc


class ClacTests(SimpleTestCase):
    def test_add_numbers(self):
        res = calc.add(2, 3)

        self.assertEqual(res, 5)
