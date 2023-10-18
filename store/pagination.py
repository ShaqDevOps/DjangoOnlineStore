from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    """
    Default pagination class for paginating API querysets.

    Attributes:
        page_size (int): The number of items to include on each page.
    """
    page_size = 10
