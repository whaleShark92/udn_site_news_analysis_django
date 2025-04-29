from django.urls import path
from app_presidents import views

app_name='app_presidents'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_presidents_data/', views.api_get_presidents_data),
]
