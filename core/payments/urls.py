from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('', views.index, name='index'),
    path('parent-portal/', views.parent_portal, name='parent_portal'),
    # M-Pesa payment endpoints
    path('api/initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]
