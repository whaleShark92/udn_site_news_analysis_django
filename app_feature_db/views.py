from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Max, Q
from app_user_keyword_db.models import NewsData
from app_feature_db.models import Feature
import json
from collections import Counter
import ast


def home(request):
    week_options = ['1', '2', '4', '8', '16', '24']
    keynum_options = ['5', '10', '15', '20','25']
    continents = {
        '亞洲': [
            '台灣','中國', '日本', '韓國',  '新加坡', '泰國',
            '越南', '馬來西亞', '印尼', '菲律賓', '印度', '巴基斯坦'
        ],
        '歐洲': [
            '英國', '法國', '德國', '義大利', '西班牙', '荷蘭',
            '瑞士', '瑞典', '挪威', '芬蘭', '波蘭', '烏克蘭', '俄羅斯'
        ],
        '北美洲': ['美國', '加拿大', '墨西哥'],
        '南美洲': ['巴西', '阿根廷', '智利', '哥倫比亞', '秘魯'],
        '非洲': ['南非', '奈及利亞', '埃及', '肯亞', '迦納'],
        '大洋洲': ['澳洲', '紐西蘭'],
        '中東': ['土耳其', '以色列', '沙烏地阿拉伯', '伊朗', '阿拉伯聯合大公國', '卡達']
    }
    return render(request, 'app_feature_db/home.html', {
        'week_options': week_options,
        'keynum_options': keynum_options,
        'continents': continents
    })


@csrf_exempt
def calculate_feature(request):
    if request.method != 'POST':
        return JsonResponse({'error': '僅支援 POST 請求'}, status=405)

    country = request.POST.get('country')
    weeks = int(request.POST.get('weeks', 2))
    keynum = int(request.POST.get('keynum', 20))

    allowed_countries = [
        # 亞洲
        '中國', '日本', '韓國', '台灣', '新加坡', '泰國', '越南', '馬來西亞', '印尼', '菲律賓', '印度', '巴基斯坦',
        
        # 歐洲
        '英國', '法國', '德國', '義大利', '西班牙', '荷蘭', '瑞士', '瑞典', '挪威', '芬蘭', '波蘭', '烏克蘭', '俄羅斯',
        
        # 北美洲
        '美國', '加拿大', '墨西哥',
        
        # 南美洲
        '巴西', '阿根廷', '智利', '哥倫比亞', '秘魯',

        # 非洲
        '南非', '奈及利亞', '埃及', '肯亞', '迦納',

        # 大洋洲
        '澳洲', '紐西蘭',

        # 中東
        '土耳其', '以色列', '沙烏地阿拉伯', '伊朗', '阿拉伯聯合大公國', '卡達'
    ]

    if not country or country not in allowed_countries:
        return JsonResponse({'error': f'缺少或不合法的 country 參數（{country}）'}, status=400)


    # 先檢查 Feature 表中是否已有該國家的「最舊」紀錄（日期升冪）
    oldest_record = Feature.objects.filter(country_name=country).order_by('latest_report_date').first()
    if oldest_record and oldest_record.latest_report_date and oldest_record.latest_report_date <= date(2025, 1, 1):
        sentiment_distribution = json.loads(oldest_record.sentiment_distribution_json or '{}')
        top_keywords = json.loads(oldest_record.top_keywords_json or '[]')
        report_trend = json.loads(oldest_record.report_trend_json or '[]')
        return JsonResponse({
            'sentiment_distribution': sentiment_distribution,
            'top_keywords': top_keywords,
            'report_trend': report_trend,
            'message': f'最舊資料日期為 {oldest_record.latest_report_date}，直接使用快取資料。',
        })

    # 若不是最舊資料則從 NewsData 查詢
    latest_date = NewsData.objects.filter(
        Q(title__icontains=country) | Q(content__icontains=country)
    ).aggregate(last=Max('date'))['last']

    if not latest_date:
        return JsonResponse({'error': f'沒有 {country} 的資料'}, status=404)

    start_date = latest_date - timedelta(weeks=weeks)

    queryset = NewsData.objects.filter(
        Q(title__icontains=country) | Q(content__icontains=country),
        date__gte=start_date,
        date__lte=latest_date
    )

    # 情緒統計
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

    # 關鍵字統計
    all_keywords = Counter()
    for news in queryset:
        try:
            if news.top_key_freq:
                key_freq = ast.literal_eval(news.top_key_freq)
                if isinstance(key_freq, list):
                    all_keywords.update(dict(key_freq))
        except Exception as e:
            print(f"解析 top_key_freq 失敗: {e}")

    top_keywords = [[k, v] for k, v in all_keywords.most_common(keynum)]

    # 每日新聞量趨勢
    date_counts = {}
    days = (latest_date - start_date).days + 1
    for i in range(days):
        d = start_date + timedelta(days=i)
        date_counts[d] = 0
    for news in queryset:
        if news.date in date_counts:
            date_counts[news.date] += 1
    report_trend = [{'x': d.strftime('%Y-%m-%d'), 'y': c} for d, c in date_counts.items()]

    # 存入 Feature 表
    Feature.objects.update_or_create(
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
        'message': f'已計算並儲存 {country} 的最新資料（{latest_date}）',
    })
