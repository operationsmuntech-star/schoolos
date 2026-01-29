from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_api

app_name = 'fees'

# API Router
router = DefaultRouter()
router.register(r'terms', views_api.TermViewSet, basename='term')
router.register(r'fee-structures', views_api.FeeStructureViewSet, basename='fee-structure')
router.register(r'overrides', views_api.StudentFeeOverrideViewSet, basename='override')
router.register(r'invoices', views_api.InvoiceViewSet, basename='invoice')
router.register(r'payments', views_api.PaymentViewSet, basename='payment')
router.register(r'receipts', views_api.PaymentReceiptViewSet, basename='receipt')
router.register(r'arrears', views_api.ArrearsViewSet, basename='arrears')
router.register(r'mpesa-transactions', views_api.MpesaTransactionViewSet, basename='mpesa-transaction')

urlpatterns = [
    # Web views
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # M-Pesa webhook (public endpoint)
    path('api/mpesa/webhook/', views_api.mpesa_webhook_handler, name='mpesa-webhook'),
]
