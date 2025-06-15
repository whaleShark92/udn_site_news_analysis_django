from django.db import models

class Feature(models.Model):
    country_name = models.CharField(max_length=100)
    report_count = models.IntegerField(default=0)
    avg_sentiment = models.FloatField(default=0.5)  # 新增預設值
    latest_report_date = models.DateField(null=True, blank=True)  # 允許空值
    top_keywords_json = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.country_name} - {self.latest_report_date}"
