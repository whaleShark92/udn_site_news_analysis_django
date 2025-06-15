from django.contrib import admin
from .models import Feature

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'report_trend_json', 'latest_report_date', 'top_keywords_json' , 'sentiment_distribution_json'
]
