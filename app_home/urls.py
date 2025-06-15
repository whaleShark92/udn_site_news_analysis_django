from django.urls import path
from app_home import views

# Declare a namespace for this APP
app_name = 'app_home'

urlpatterns = [
    # For home
    path('', views.home, name='home'),
]
