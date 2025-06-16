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
from django.utils import timezone
from datetime import timedelta


def home(request):
    week_options = ['1', '2', '3', '4', '6', '8', '12']
    keynum_options = ['5', '10', '15', '20']
    return render(request, 'app_feature_db/home.html', {
        'week_options': week_options,
        'keynum_options': keynum_options
    })


# 假設國家列表，你可自行替換
# country_list = ['中國', '美國', '日本', '韓國', '俄羅斯', '台灣', '英國', '法國', '德國', '加拿大']
# 允許的國家NER類別
allowedNE = ['GPE']

from datetime import date

@csrf_exempt
def calculate_feature(request):
    if request.method != 'POST':
        return JsonResponse({'error': '僅支援 POST 請求'}, status=405)

    country = request.POST.get('country')
    weeks = int(request.POST.get('weeks', 2))
    keynum = int(request.POST.get('keynum', 20))

    if not country:
        return JsonResponse({'error': '缺少 country 參數'}, status=400)

    # 嘗試從 Feature 拿資料
    latest_record = Feature.objects.filter(country_name=country).order_by('-latest_report_date').first()

    # 判斷 Feature 是否有資料，且資料是否夠新或最舊是2025-01-01或更早
    if latest_record:
        # 如果最舊日期是2025-01-01或更早，直接用快取資料，不查 NewsData
        if latest_record.latest_report_date and latest_record.latest_report_date <= date(2025, 1, 1):
            sentiment_distribution = json.loads(latest_record.sentiment_distribution_json or '{}')
            top_keywords = json.loads(latest_record.top_keywords_json or '[]')
            report_trend = json.loads(latest_record.report_trend_json or '[]')
            return JsonResponse({
                'sentiment_distribution': sentiment_distribution,
                'top_keywords': top_keywords,
                'report_trend': report_trend,
                'message': f'資料日期為 {latest_record.latest_report_date}，不重新查詢 NewsData。',
            })

        # 或者資料夠新，也直接用快取資料
        if latest_record.latest_report_date >= timezone.now().date() - timedelta(weeks=weeks):
            sentiment_distribution = json.loads(latest_record.sentiment_distribution_json or '{}')
            top_keywords = json.loads(latest_record.top_keywords_json or '[]')
            report_trend = json.loads(latest_record.report_trend_json or '[]')
            return JsonResponse({
                'sentiment_distribution': sentiment_distribution,
                'top_keywords': top_keywords,
                'report_trend': report_trend,
                'message': f'使用快取資料，日期為 {latest_record.latest_report_date}',
            })

    # 如果上述條件都不符合，繼續查 NewsData，做計算...
    # (此處省略原本查詢 NewsData 與計算邏輯)
    ...


    # 如果 Feature 沒有資料或資料過舊，去 NewsData 查詢，做計算
    latest_date = NewsData.objects.filter(
        Q(title__icontains=country) | Q(content__icontains=country)
    ).aggregate(last=Max('date'))['last']

    if not latest_date:
        return JsonResponse({'error': f'找不到關於 {country} 的新聞資料'}, status=404)

    start_date = latest_date - timedelta(weeks=weeks)

    queryset = NewsData.objects.filter(
        Q(title__icontains=country) | Q(content__icontains=country),
        date__gte=start_date,
        date__lte=latest_date
    )

    sentiment_counts = {'正向': 0, '中立': 0, '負向': 0}
    for news in queryset:
        score = news.sentiment
        if score >= 0.75:
            sentiment_counts['正向'] += 1
        elif score <= 0.4:
            sentiment_counts['負向'] += 1
        else:
            sentiment_counts['中立'] += 1

    total = sum(sentiment_counts.values())
    if total == 0:
        sentiment_distribution = {'正向': 0, '中立': 0, '負向': 0}
    else:
        sentiment_distribution = {k: round(v / total * 100, 1) for k, v in sentiment_counts.items()}

    all_keywords = Counter()
    import ast
    for news in queryset:
        try:
            if news.top_key_freq:
                key_freq = ast.literal_eval(news.top_key_freq)
                if isinstance(key_freq, list):
                    all_keywords.update(dict(key_freq))
        except Exception as e:
            print(f"解析 top_key_freq 失敗: {e}")

    top_keywords = [[k, v] for k, v in all_keywords.most_common(keynum)]

    date_counts = {}
    days = (latest_date - start_date).days + 1
    for i in range(days):
        d = start_date + timedelta(days=i)
        date_counts[d] = 0
    for news in queryset:
        if news.date in date_counts:
            date_counts[news.date] += 1
    report_trend = [{'x': d.strftime('%Y-%m-%d'), 'y': c} for d, c in date_counts.items()]

    # 把計算結果存回 Feature，若已有則更新，沒有就建立
    feature_obj, created = Feature.objects.update_or_create(
        country_name=country,
        defaults={
            'latest_report_date': latest_date,
            'sentiment_distribution_json': json.dumps(sentiment_distribution, ensure_ascii=False),
            'top_keywords_json': json.dumps(top_keywords, ensure_ascii=False),
            'report_trend_json': json.dumps(report_trend, ensure_ascii=False),
        }
    )

    return JsonResponse({
        'sentiment_distribution': sentiment_distribution,
        'top_keywords': top_keywords,
        'report_trend': report_trend,
        'message': f'已計算最新資料並更新 Feature 表。',
    })
