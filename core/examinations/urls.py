from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('', views.index, name='index'),
]
