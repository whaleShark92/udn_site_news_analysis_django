"""
總目錄
URL configuration for website_configs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('topword/', include('app_top_keyword.urls')),
    # app top persons
    path('topperson/', include('app_top_person.urls')),
    # user keyword analysis
    path('userkeyword/', include('app_user_keyword.urls')),
    # trump
    path('trump/', include('app_trump.urls')),
    # full text search and associated keyword display
    path('userkeyword_assoc/', include('app_user_keyword_association.urls')),
    # tariff
    path('tariff/', include('app_tariff.urls')),
    # user keyword sentiment 
    path('userkeyword_senti/', include('app_user_keyword_sentiment.urls')),
    # app_presidents
    path('presidents/', include('app_presidents.urls')),
    # full text search and associated keyword display using db
    path('userkeyword_db/', include('app_user_keyword_db.urls')),
    # full text search and associated keyword display using db
    path('topperson_db/', include('app_top_person_db.urls')),    
    # admin 後台資料庫管理
    path('admin/', admin.site.urls),

]
