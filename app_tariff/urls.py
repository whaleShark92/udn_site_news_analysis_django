from django.urls import path
from . import views  

app_name = "app_tariff"

urlpatterns = [
    path('', views.home, name='home'),
]
