from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recpie(user, **params):
    """Create a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
        'description': 'Sample description',
        'link': 'https://sample.com/sample-recipe'
    }

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)

def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecpieApiTests(TestCase):
    """Test the public available recpie API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecpieApiTests(TestCase):
    """Test the private available recpie API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass')
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Create a sample recipe"""
        create_recpie(user=self.user)
        create_recpie(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = create_user(email='user1@example.com', password='testpass')

        create_recpie(user=other_user)
        create_recpie(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_get_recipe_detail(self):
        recipe = create_recpie(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Chocolate Cheesecake',
            'time_minutes': 2,
            'price': Decimal('30.00')
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = 'http://example123.com'
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chocolate Cheesecake',
            link=original_link,
            time_minutes=2
        )

        payload = {
            'title': 'New recipe name',
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(self.user, recipe.user)

    def test_full_update(self):
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chocolate Cheesecake',
            link='http://example123.com',
            time_minutes=2,
            description= 'Old description'
        )
        url = detail_url(recipe.id)
        payload = {
            'title': 'New recipe name',
            'time_minutes': 3,
            'price': Decimal('30.00'),
            'link': 'http://example.com',
            'description': 'New description'
        }

        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(self.user, recipe.user)

    def test_update_user_returns_error(self):
        original_link = 'http://example123.com'
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chocolate Cheesecake',
            link=original_link,
            time_minutes=2
        )

        other_user = create_user(email='test2@exmapkl.eomc', password='testpass')

        payload = {
            'user': other_user.id,
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_deleting_recipe_succesfull(self):
        recipe = create_recpie(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        new_user = create_user(email='test3@gmail.com', password='testpass')
        recipe = create_recpie(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recpie_with_new_tags(self):
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'vegan'}, {'name':'dessert'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(user=self.user, name=tag['name']).exists()
            self.assertTrue(exists)

    def test_create_recpie_with_existing_tags(self):
        tag_vegan = Tag.objects.create(user=self.user, name='vegan')
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'vegan'}, {'name':'dessert'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_vegan, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(user=self.user, name=tag['name']).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recpie(user=self.user)
        payload = {
            'tags': [{'name': 'vegan'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='vegan')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_vegan = Tag.objects.create(user=self.user, name='vegan')
        recipe = create_recpie(user=self.user)
        recipe.tags.add(tag_vegan)

        tag_breakfast = Tag.objects.create(user=self.user, name='breakfast')
        payload={
            'tags': [{'name': tag_breakfast.name}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_breakfast, recipe.tags.all())
        self.assertNotIn(tag_vegan, recipe.tags.all())

    def test_clear_tags(self):
        tag_vegan = Tag.objects.create(user=self.user, name='vegan')
        recipe = create_recpie(user=self.user)
        recipe.tags.add(tag_vegan)

        payload = {
            'tags': []
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)



