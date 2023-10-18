from decimal import Decimal
from store.models import Cart, CartItem, Product, Collection, Review
from rest_framework import serializers

class CollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Collection model.

    Fields:
        id (int): The unique identifier for the collection.
        title (str): The title of the collection.
        products_count (int): The number of products in the collection.
    """
    products_count = serializers.IntegerField(read_only=True)

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.

    Fields:
        id (int): The unique identifier for the product.
        title (str): The title of the product.
        description (str): The description of the product.
        slug (str): The slug for the product.
        inventory (int): The available inventory of the product.
        unit_price (Decimal): The unit price of the product.
        price_with_tax (Decimal): The unit price of the product with tax applied.
        collection (Collection): The collection to which the product belongs.
    """
    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')

    def calculate_tax(self, product: Product):
        """
        Calculate the product price with tax.

        Args:
            product (Product): The product instance.

        Returns:
            Decimal: The product price with tax.
        """
        return product.unit_price * Decimal(1.1)

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.

    Fields:
        id (int): The unique identifier for the review.
        date (datetime): The date when the review was created.
        name (str): The name of the reviewer.
        description (str): The description of the review.
    """
    def create(self, validated_data):
        """
        Create a new review.

        Args:
            validated_data (dict): The validated review data.

        Returns:
            Review: The created review instance.
        """
        product_id = self.context['product_id']
        return Review.objects.create(product_id=product_id, **validated_data)

class SimpleProductSerializer(serializers.ModelSerializer):
    """
    Serializer for a simplified Product model.

    Fields:
        id (int): The unique identifier for the product.
        title (str): The title of the product.
        unit_price (Decimal): The unit price of the product.
    """
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the CartItem model.

    Fields:
        id (int): The unique identifier for the cart item.
        product (SimpleProductSerializer): The product added to the cart.
        quantity (int): The quantity of the product in the cart.
        total_price (Decimal): The total price of the cart item.
    """
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        """
        Calculate the total price of the cart item.

        Args:
            cart_item (CartItem): The cart item instance.

        Returns:
            Decimal: The total price of the cart item.
        """
        return cart_item.quantity * cart_item.product.unit_price

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for the Cart model.

    Fields:
        id (UUID): The unique identifier for the cart.
        items (CartItemSerializer): The items in the cart.
        total_price (Decimal): The total price of all items in the cart.
    """
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        """
        Calculate the total price of all items in the cart.

        Args:
            cart (Cart): The cart instance.

        Returns:
            Decimal: The total price of all items in the cart.
        """
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])

class AddCartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for adding items to the cart.

    Fields:
        product_id (int): The ID of the product to add to the cart.
        quantity (int): The quantity of the product to add to the cart.
    """
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        """
        Validate the product ID.

        Args:
            value (int): The product ID to validate.

        Returns:
            int: The validated product ID.

        Raises:
            serializers.ValidationError: If no product with the given ID is found.
        """
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product with the given ID was found.')
        return value

    def save(self, **kwargs):
        """
        Save the cart item.

        Args:
            kwargs (dict): Additional context data.

        Returns:
            CartItem: The saved cart item instance.
        """
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try: 
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        
        return self.instance

class UpdateCartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for updating cart item quantities.

    Fields:
        quantity (int): The updated quantity of the cart item.
    """
    class Meta:
        model = CartItem
        fields = ['quantity']
