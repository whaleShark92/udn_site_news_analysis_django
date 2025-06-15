from django.urls import path
from . import views

app_name="app_feature_db"

urlpatterns = [
    # top (popular) persons
    path('', views.home, name='home'),
    # ajax path
    # path('api_get_feature/', views.api_get_feature, name='api_get_feature'),
    
    # # calculate top person
    path('calculate_feature/', views.calculate_feature, name='calculate_feature'),
]

