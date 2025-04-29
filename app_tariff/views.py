import pandas as pd
from django.shortcuts import render
from collections import Counter
import ast
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import io
import urllib, base64
import json

def load_articles():
    file_path = 'app_tariff/dataset/clean_articles.csv'
    return pd.read_csv(file_path, sep='|')

# 篩選資料根據類別和日期範圍
def filter_data_by_category_and_date(df, category=None, start_date=None, end_date=None):
    if category:
        df = df[df['category'] == category]
    
    if start_date and end_date:
        # 將日期字符串轉換為日期對象
        df.loc[:, 'date'] = pd.to_datetime(df['date'], errors='coerce')  # 假設日期欄位名稱是 'date'
        df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    
    return df

# 雲圖
def get_top_keywords(df):
    keyword_list = []
    for item in df['top_key_freq'].dropna():
        try:
            keywords = ast.literal_eval(item) if isinstance(item, str) else []
            for keyword, freq in keywords:
                keyword_list.append(keyword)
        except Exception as e:
            continue
    keyword_counter = Counter(keyword_list)
    return [[word, count] for word, count in keyword_counter.items() if count > 1]

# 關稅類別分布
def get_category_distribution(df):
    category_counts = df['category'].value_counts()
    return [{"name": category, "count": count} for category, count in category_counts.items()]

# 畫長條圖並返回圖片
def generate_bar_chart(df):
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    date_counts = df.groupby('date').size()
    
    # 計算每天的關鍵字提及次數
    keyword_mentions = df['top_key_freq'].dropna().apply(lambda x: len(ast.literal_eval(x) if isinstance(x, str) else []))
    date_keyword_mentions = df.groupby('date')['top_key_freq'].apply(lambda x: sum([len(ast.literal_eval(k) if isinstance(k, str) else []) for k in x]))
    
    # 設定圖表
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 繪製文章數量的長條圖
    ax1.bar(date_counts.index, date_counts.values, color='lightblue', label='Number of Articles')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Articles', color='lightblue')
    
    # 設定第二個Y軸顯示關鍵字提及次數
    ax2 = ax1.twinx()
    ax2.plot(date_keyword_mentions.index, date_keyword_mentions.values, color='orange', label='Keyword Mentions', marker='o')
    ax2.set_ylabel('Number of Mentions', color='orange')

    # 設定圖表標題
    plt.title('Articles and Keyword Mentions Over Time')
    ax1.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    # 將圖表保存到緩存區並轉換為base64編碼
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return chart_data

def generate_time_series_data(df):
    # 計算每個日期的文章數量
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    date_counts = df.groupby('date').size()

    # 計算每個日期的關鍵字提及次數
    keyword_mentions = df['top_key_freq'].dropna().apply(lambda x: len(ast.literal_eval(x) if isinstance(x, str) else []))
    date_keyword_mentions = df.groupby('date')['top_key_freq'].apply(lambda x: sum([len(ast.literal_eval(k) if isinstance(k, str) else []) for k in x]))

    # 整理資料以便傳遞到模板
    time_series_data = {
        'dates': date_counts.index.strftime('%Y-%m-%d').tolist(),
        'article_counts': date_counts.values.tolist(),
        'keyword_mentions': date_keyword_mentions.values.tolist(),
    }

    return time_series_data

# 主視圖函數
def home(request):
    df = load_articles()
    category_filter = request.GET.get('category', None)
    start_date = request.GET.get('start_date', '2025-03-10')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    CATEGORIES = ['全球', '兩岸', '社會', '地方', '生活']

    # 過濾資料
    df_filtered = filter_data_by_category_and_date(df, category=category_filter, start_date=start_date, end_date=end_date)
    
    # 生成圖表和時間序列數據
    chart_data = generate_bar_chart(df_filtered)
    time_series_data = generate_time_series_data(df_filtered)
    
    top_keywords = get_top_keywords(df_filtered)
    category_distribution = get_category_distribution(df_filtered)

    return render(request, 'app_tariff/home.html', {
        'keywords': top_keywords,
        'categories': [{"name": cat} for cat in CATEGORIES],
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
        'chart_data': chart_data,
        'time_series_data': json.dumps(time_series_data),  # 傳遞時間序列資料
        'category_distribution': category_distribution
    })
