from django.urls import path
from app_feature_db import views

app_name = 'app_feature_db'

urlpatterns = [
    path('', views.home, name='home'),
    path('calculate_feature/', views.calculate_feature, name='calculate_feature'),
]
