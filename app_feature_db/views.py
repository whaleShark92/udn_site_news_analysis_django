from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.db.models import Avg, Count, Max, Q
from app_user_keyword_db.models import NewsData
from app_feature_db.models import Feature
import json
from collections import Counter
import ast

def home(request):
    return render(request, 'app_feature_db/home.html')

# 假設國家列表，你可自行替換
country_list = ['中國', '美國', '日本', '韓國', '俄羅斯', '台灣', '英國', '法國', '德國', '加拿大']

@csrf_exempt
def calculate_feature(request):
    if request.method != 'POST':
        return JsonResponse({'error': '僅支援 POST 請求'}, status=405)

    country = request.POST.get('country')
    if not country:
        return JsonResponse({'error': '缺少 country 參數'}, status=400)

    # 取得新聞資料
    queryset = NewsData.objects.filter(
        Q(title__icontains=country) | Q(content__icontains=country)
    )

    if not queryset.exists():
        return JsonResponse({'error': f'找不到關於 {country} 的新聞資料'}, status=404)

    # ✅ 情緒統計 - 回傳「數量」
    # ✅ 情緒統計 - 先統計數量
    sentiment_counts = {'正向': 0, '中立': 0, '負向': 0}
    for news in queryset:
        score = news.sentiment
        if score >= 0.75:
            sentiment_counts['正向'] += 1
        elif score <= 0.4:
            sentiment_counts['負向'] += 1
        else:
            sentiment_counts['中立'] += 1

    # ✅ 轉換為百分比
    total = sum(sentiment_counts.values())
    if total == 0:
        sentiment_distribution = {'正向': 0, '中立': 0, '負向': 0}
    else:
        sentiment_distribution = {
            k: round(v / total * 100, 1) for k, v in sentiment_counts.items()
        }


    # 熱門關鍵字
    all_keywords = Counter()
    for news in queryset:
        try:
            if news.top_key_freq:
                key_freq = ast.literal_eval(news.top_key_freq)
                if isinstance(key_freq, list):
                    all_keywords.update(dict(key_freq))
        except Exception as e:
            print(f"解析 top_key_freq 失敗: {e}")

    # 🔥 關鍵修正：tuple 轉 list 才能被 JsonResponse 序列化
    top_keywords = [[k, v] for k, v in all_keywords.most_common(10)]

    # ✅ 寫入 Feature 表
    report_count = queryset.count()
    avg_sentiment = queryset.aggregate(avg=Avg('sentiment'))['avg'] or 0
    latest_date = queryset.aggregate(last=Max('date'))['last'] or datetime.today().date()

    Feature.objects.update_or_create(
    country_name=country,
    defaults={
        'report_count': report_count,
        'latest_report_date': latest_date,
        'top_keywords_json': json.dumps(top_keywords, ensure_ascii=False),
        'sentiment_distribution_json': json.dumps(sentiment_distribution, ensure_ascii=False)
    }
    )

    # ✅ 回傳給前端（注意 labels 是中文）
    return JsonResponse({
        'sentiment_distribution': sentiment_distribution,
        'top_keywords': top_keywords
    })
