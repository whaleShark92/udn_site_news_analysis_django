from django.contrib import admin
from .models import Feature

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'report_count', 'avg_sentiment', 'latest_report_date', 'top_keywords_json']
