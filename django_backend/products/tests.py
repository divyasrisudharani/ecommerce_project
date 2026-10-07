from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from .models import Product, Category


class ProductModelTest(TestCase):

    def test_product_creation(self):
        category = Category.objects.create(
            name="Test Category",
            description="Test category"
        )

        product = Product.objects.create(
            category=category,
            name="Test Laptop",
            description="Test product",
            price=50000,
            stock=10
        )

        self.assertEqual(product.name, "Test Laptop")
        self.assertEqual(product.price, 50000)
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.category, category)