from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentCategoryViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'categories', PaymentCategoryViewSet, basename='payment-category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
