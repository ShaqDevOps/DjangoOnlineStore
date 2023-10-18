from store.pagination import DefaultPagination
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from .filters import ProductFilter
from .models import Cart, CartItem, Collection, Product, Review
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CollectionSerializer, ProductSerializer, ReviewSerializer, UpdateCartItemSerializer

class ProductViewSet(ModelViewSet):
    """
    ViewSet for managing products.

    Attributes:
        queryset (QuerySet): The set of Product objects.
        serializer_class (Serializer): The serializer class for Product objects.
        filter_backends (list): The list of filter backends.
        filterset_class (FilterSet): The filterset class for filtering products.
        pagination_class (Pagination): The pagination class for paginating products.
        search_fields (list): The list of fields to search for.
        ordering_fields (list): The list of fields to order products by.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']

    def get_serializer_context(self):
        return {'request': self.request}

    def delete(self, request, pk):
        """
        Delete a product.

        Args:
            request (HttpRequest): The HTTP request.
            pk (int): The primary key of the product to delete.

        Returns:
            Response: The HTTP response indicating the status of the delete operation.
        """
        product = get_object_or_404(Product, pk=pk)
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CollectionViewSet(ModelViewSet):
    """
    ViewSet for managing collections.

    Attributes:
        queryset (QuerySet): The set of Collection objects.
        serializer_class (Serializer): The serializer class for Collection objects.
    """

    queryset = Collection.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        """
        Delete a collection.

        Args:
            request (HttpRequest): The HTTP request.
            pk (int): The primary key of the collection to delete.

        Returns:
            Response: The HTTP response indicating the status of the delete operation.
        """
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewViewSet(ModelViewSet):
    """
    ViewSet for managing reviews.

    Attributes:
        serializer_class (Serializer): The serializer class for Review objects.
    """

    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}

class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    """
    ViewSet for managing carts.

    Attributes:
        queryset (QuerySet): The set of Cart objects.
        serializer_class (Serializer): The serializer class for Cart objects.
    """

    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer

class CartItemViewSet(ModelViewSet):
    """
    ViewSet for managing cart items.

    Attributes:
        http_method_names (list): The list of HTTP methods supported by the view.
    """

    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects \
                .filter(cart_id=self.kwargs['cart_pk']) \
                .select_related('product')
