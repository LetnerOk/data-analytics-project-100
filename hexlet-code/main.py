#!/usr/bin/env python
# coding: utf-8

# In[39]:


import pandas as pd
import requests
import json
from dotenv import load_dotenv, find_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path


# In[40]:


load_dotenv()  # загружаются переменные из файла

DATE_BEGIN = os.getenv('DATE_BEGIN')
DATE_END = os.getenv('DATE_END')
API_URL = os.getenv('API_URL')
print(DATE_BEGIN)


# In[9]:


# Отправляем запрос по API для получения визитов по URL
def request_api(date_1, date_2):
    data_visit_api = requests.get(f'{API_URL}/visits?begin={date_1}&end={date_2}') 
    visit_json = data_visit_api.json() #Преобразуем данные в объект JSON
    visit_api = pd.DataFrame(visit_json) #преобразуем JSON в DataFrame
   
    #Отправляем запрос по API для получения регистраций по URL
    data_regist_api = requests.get(f'{API_URL}/registrations?begin={date_1}&end={date_2}') 
    regist_json = data_regist_api.json() #Преобразуем данные в объект JSON
    regist_api = pd.DataFrame(regist_json) #преобразуем JSON в DataFrame
    #df_regist_api.head()
    return visit_api, regist_api


# In[10]:


# Чистка данных визитов
def visits_cleared(df):
    # Убираем дублирующиеся строки
    visit_api_clear = df.drop_duplicates()
    # проверим, есть ли в таблице визиты ботов
    visit_api_clear['user_agent'] =  visit_api_clear['user_agent'].fillna('')
    #Исключим ботов данных применением метода drop() и проверим оставшееся количество строк в датафрейме визитов
    visit_without_bot = df.drop(df[df['user_agent'].str.contains('bot')].index)
    return visit_without_bot


# In[11]:


# Отбор уникальные визиты по модели last
def unique_visits(df):
    visit_dt = df.copy()
    #df_visit_unique_dt.sort_values(by='datetime', ascending=True)
    #Преобразуем данные в столбце 'datetime' в объект типа datetime64[ns]
    visit_dt['date_group'] = pd.to_datetime(visit_dt['datetime'], format='%a, %d %b %Y %H:%M:%S GMT')
    #Сортируем по полю 'date_group' в обратном порядке после преобразования в формат datetime64[ns], чтобы сортировка прошла кооректно
    visit_sorted = visit_dt.sort_values(by='date_group', ascending=False)
    # применим функцию drop_duplicates для удаления повторяющихся значений по полю visit_id.
    #По умолчанию функция drop_duplicates() сохранит первый дубликат, поэтому останутся только последние визиты для каждого уникального посетителя.
    visit_unique = visit_sorted.drop_duplicates(subset=['visit_id'])
    return visit_unique


# In[12]:


# Преобразование даты, агрегация и подсчет уникальных визитов
def count_unigue_visits(df):
    #С помощью функции dt.strftime() преобразуем datetime в формат даты YYYY-MM-DD
    df['date_group'] = df['date_group'].dt.strftime('%Y-%m-%d')
    #df_visit_unique_dt.groupby(['datetime', 'platform'], as_index=False).agg({'visit_id': ['count']}) 
    agreegated_visit = df.groupby(['date_group', 'platform']) \
    .size().reset_index(name='visits')
    return agreegated_visit


# In[13]:


# Чистка данных регистраций
def cleared_registrations(df):
    # Убираем дублирующиеся строки
    regist_api_dt = df.drop_duplicates()
    #Заполняем пусные ячейки в столбце platform
    regist_api_dt['platform'] =  regist_api_dt['platform'].fillna('web')
    return regist_api_dt


# In[14]:


# Подсчет регистраций
def count_registrations(df):
    #Преобразуем данные в столбце 'datetime' в объект типа datetime64[ns]
    df['date_group'] = pd.to_datetime(df['datetime'])#, format='%a, %d %b %Y %H:%M:%S GMT')
    #df_regist_api_dt.dtypes
    df.sort_values(by='date_group', ascending=True)
    #С помощью функции to_datetime() преобразуем datetime в формат даты и времени
    df['date_group'] = df['date_group'].dt.strftime('%Y-%m-%d')
    agreegated_regist = df.groupby(['date_group', 'platform']) \
    .size().reset_index(name='registrations')
    return agreegated_regist


# In[15]:


# Соединие таблиц визитов и регистраций
def merged_visit_registration_convarsion(df1, df2):
    merged_conv = pd.merge(df1, df2, on=['date_group', 'platform'])
    # Считаем конверсию визитов в регистрации в процентах и добавляем поле conversion в итоговую таблицу
    merged_conv['conversion'] = (merged_conv['registrations'] / merged_conv['visits']) * 100
    merged_conv_sort = merged_conv.sort_values(by='date_group', ascending=True)
    #Сохраняем таблицу с конверсиями в формате json
    merged_conv_sort.to_json('conversion.json')
    # Сгрупируем данные только по дате, исключив группировку по 'platfotm'
    merged_without_platform = merged_conv.copy()
    merged_conv_without_platform = merged_without_platform.groupby(['date_group']).sum(['visits', 'registrations']).reset_index()
    merged_conv_without_platform['conversion'] = (merged_conv_without_platform['registrations'] / merged_conv_without_platform['visits']) * 100
    return merged_conv, merged_conv_without_platform


# In[16]:


def get_data_path(file_name):
    current_dir = Path(__file__).absolute().parent
    return current_dir / 'Data' / file_name    


# In[17]:


# Очистка данных по рекламным кампаниям
def clean_ads_csv(df):
    df_ads = df.drop_duplicates()
    df_ads['date'] = pd.to_datetime(df['date'])
    df_ads['date'] = df_ads['date'].dt.strftime('%Y-%m-%d')
    df_ads['utm_campaign'] = df_ads['utm_campaign'].fillna('none')
    df_ads['cost'] = df_ads['cost'].fillna('0')
    #df_ads['ads_campaign'] = df_ads['utm_source'] + '_'  +  df_ads['utm_medium'] + '_' + df_ads['utm_campaign']
    return df_ads


# In[20]:


# Группировка затрат на рекламу по дате и рекламной кампании
def df_ads_aggregation(df):
    df_agg =  df.groupby(['date', 'utm_campaign']).sum(['cost']).reset_index()
    return df_agg


# In[24]:


# Соединим таблицу конверсий, сагрерированных только по дате, с таблицей затрат на рекламу.
# Используем левое соединение, чтобы оставить все даты в нужном интервале, даже если затраты на рекламу были нулевыми.
# Так как соединение левое, то в итоговую таблицу не попадут даты, выходящие за пределы интервала в таблице конверсий/
def merge_df_conv_ads(df_conv, df_ads):
    df_conv_end = df_conv.copy()
    df_merged = pd.merge(df_conv_end,  df_ads,
    left_on='date_group',
    right_on='date',
    how='left')
    df_merged.drop('date', axis= 1 , inplace= True)
    df_merged_sort = df_merged.sort_values(by='date_group', ascending=True)
    df_merged_sort = df_merged[['date_group', 'visits', 'registrations', 'conversion', 'cost', 'utm_campaign']]

    df_merged_sort.to_json(f'./ads.json')
    
    return df_merged_sort


# In[25]:


# Данные по неделям
def weekly_data(df):
    conv_w = df.copy()
    conv_w['date_week'] = pd.to_datetime(conv_w ['date_group'])
    conv_w['date_week'] = conv_w['date_week'].dt.to_period('W').dt.start_time.dt.date
    df_conv_week_platform = conv_w.groupby(['date_week', 'platform']).sum(['visits', 'registrations']).reset_index()
    df_conv_week = conv_w.groupby(['date_week']).sum(['visits', 'registrations']).reset_index()
    df_conv_week_platform['conversion'] = (df_conv_week_platform['registrations'] / df_conv_week_platform['visits']) * 100
    #df_conv_week = df_conv_w[['date_week', 'platform', 'visits', 'registrations']]
    df_conv_week['conversion'] = (df_conv_week['registrations'] / df_conv_week['visits']) * 100
    #df_conv_week.head(200)
    return df_conv_week, df_conv_week_platform


# In[26]:


# Визуализация визитов по неделям
def visualizated_visits(df_w, df_w_p):
    #Create bar chart for weekly visits by date_group without platform 
    plt.figure(figsize=(14, 7))
    #visits_platform = df_w.pivot_table(index='date_week', columns='visits', fill_value=0)
    df_w.plot(kind='bar', y='visits', x='date_week', stacked=False, figsize=(14, 7))
    plt.xticks(rotation=45)
    plt.title('Weekly Visits', fontsize=16) # заголовок
    plt.xlabel("Date_group", fontsize=14) # ось абсцисс
    plt.ylabel("Visits", fontsize=14) # ось ординат
    plt.savefig(f'./charts/Weekly_Visits.png')
    

    #Create bar chart for weekly visits by date_group and platform
    plt.figure(figsize=(14, 7))
    visits_platform = df_w_p.pivot_table(index='date_week', columns='platform', values='visits', fill_value=0)
    visits_platform.plot(kind='bar', stacked=True, figsize=(14, 7))
    plt.xticks(rotation=45)
    plt.title('Weekly visits by platform', fontsize=16) # заголовок
    plt.xlabel("Date_group", fontsize=14) # ось абсцисс
    plt.ylabel("Visits", fontsize=14) # ось ординат
    plt.savefig(f'./charts/Weekly_Visits_by_platform.png')


# In[27]:


#Визуализация регистраций по неделям
def visualizated_registrations(df_w, df_w_p):
    #Create bar chart for weekly visits by date_group without platform 
    plt.figure(figsize=(14, 7))
    #visits_platform = df_w.pivot_table(index='date_week', columns='visits', fill_value=0)
    df_w.plot(kind='bar', y='registrations', x='date_week', stacked=False, figsize=(14, 7))
    plt.xticks(rotation=45)
    plt.title('Weekly registrations', fontsize=16) # заголовок
    plt.xlabel("Date", fontsize=14) # ось абсцисс
    plt.ylabel("Registrations", fontsize=14) # ось ординат
    plt.savefig(f'./charts/Weekly_registrations.png')
    

    #Create bar chart for weekly visits by date_group and platform
    plt.figure(figsize=(14, 7))
    visits_platform = df_w_p.pivot_table(index='date_week', columns='platform', values='registrations', fill_value=0)
    visits_platform.plot(kind='bar', stacked=True, figsize=(14, 7))
    plt.xticks(rotation=45)
    plt.title('Weekly registrations by platform', fontsize=16) # заголовок
    plt.xlabel("Date", fontsize=14) # ось абсцисс
    plt.ylabel("Registrations", fontsize=14) # ось ординат
    plt.savefig(f'./charts/Weekly_registrations_by_platform.png')


# In[28]:


#Визуализация регистраций по типу и piecharts
def visualizated_registrations_by_type(df):
    # Подготавливаем таблицу с регистрациями в зависимости от типа регистрации
    regist_type = df.copy()
    regist_type['date_week'] = pd.to_datetime(regist_type['date_group'])
    regist_type['date_week'] = regist_type['date_week'].dt.to_period('W').dt.start_time.dt.date
    df_regist_type = regist_type.groupby(['date_week', 'registration_type']) \
    .size().reset_index(name='registrations')

     #Create bar chart for weekly registrations by registration type
    plt.figure(figsize=(14, 7))
    plt_regist_type = df_regist_type.pivot_table(index='date_week', columns='registration_type', values='registrations', fill_value=0)
    plt_regist_type.plot(kind='bar', stacked=True, figsize=(14, 7))
    plt.xticks(rotation=45)
    plt.title('Weekly registrations by registration type', fontsize=16) # заголовок
    plt.xlabel("Date", fontsize=14) # ось абсцисс
    plt.ylabel("Registrations", fontsize=14) # ось ординат
    plt.savefig(f'./charts/Weekly_registrations_by_type.png')

    #Create pie chart for total registrations by registration type and platform
    regist_type_pie = df.groupby(['registration_type']).size().reset_index(name='registrations')  
    regist_platform_pie = df.groupby(['platform']).size().reset_index(name='registrations') 
    fig, ax = plt.subplots(1, 2, figsize=(14, 7))
    ax[0].pie(regist_type_pie['registrations'], labels=regist_type_pie['registration_type'], autopct='%1.1f%%')
    ax[1].pie(regist_platform_pie['registrations'], labels=regist_platform_pie['platform'], autopct='%1.1f%%')
    ax[0].set_title('Registrations by type')
    ax[1].set_title('Registrations by platform')
    #plt.tight_layout()
    plt.savefig(f'./charts/registrations_pies.png')


# In[29]:


# Визуализация конверсий по платформам
def visualizated_conversion_by_platform(df):
    plt_conv_by_platform = df.pivot_table(index='date_week', columns='platform', values='conversion', fill_value=0)
    plt_conv_by_platform.reset_index(inplace=True)
    fig, ax = plt.subplots(3, 1, figsize=(14, 14))
    ax[0].plot(plt_conv_by_platform['date_week'], plt_conv_by_platform['android'], marker='o', c='b', label='android')
    x0 = plt_conv_by_platform['date_week']
    y0 = plt_conv_by_platform['android']
    for x0,y0 in zip(x0,y0):
        label = "{:.0f}%".format(y0)
        ax[0].annotate(label, (x0,y0), textcoords="offset points",  xytext=(0,10), ha='center')
    ax[0].legend()
    ax[0].set_title('Conversion by android plarform')
    ax[0].set_xlabel('Date')
    ax[0].set_ylabel('Conversion')
    ax[0].set_xticks(plt_conv_by_platform['date_week'])
    ax[0].set_xticklabels(plt_conv_by_platform['date_week'], rotation=45)
    ax[0].set_ylim([67, 100])
    ax[0].grid()
    
    ax[1].plot(plt_conv_by_platform['date_week'], plt_conv_by_platform['ios'], marker='o', c='b', label='ios')
    x1 = plt_conv_by_platform['date_week']
    y1 = plt_conv_by_platform['ios']
    for x1,y1 in zip(x1,y1):
        label = "{:.0f}%".format(y1)
        ax[1].annotate(label, (x1,y1), textcoords="offset points",  xytext=(0,10), ha='center')
    ax[1].legend()
    ax[1].set_title('Conversion by ios plarform')
    ax[1].set_xlabel('Date')
    ax[1].set_ylabel('Conversion')
    ax[1].set_xticks(plt_conv_by_platform['date_week'])
    ax[1].set_xticklabels(plt_conv_by_platform['date_week'], rotation=45)
    ax[1].set_ylim([65, 120])
    ax[1].grid()
    
    ax[2].plot(plt_conv_by_platform['date_week'], plt_conv_by_platform['web'], marker='o', c='b', label='web')
    x2 = plt_conv_by_platform['date_week']
    y2 = plt_conv_by_platform['web']
    for x2,y2 in zip(x2,y2):
        label = "{:.0f}%".format(y2)
        ax[2].annotate(label, (x2,y2), textcoords="offset points",  xytext=(0,10), ha='center')
    ax[2].legend()
    ax[2].set_title('Conversion by web plarform')
    ax[2].set_xlabel('Date')
    ax[2].set_ylabel('Conversion')
    ax[2].set_xticks(plt_conv_by_platform['date_week'])
    ax[2].set_xticklabels(plt_conv_by_platform['date_week'], rotation=45)
    ax[2].set_ylim([2.5, 9])
    ax[2].grid()
    
    plt.tight_layout()
    plt.savefig(f'./charts/conversion_by_platform.png')


# In[30]:


# Визуализация полной конверсии по неделям и месяцам
def visualizated_full_conversion(df):
    conv_m = df.copy()
    conv_m['date_month'] = pd.to_datetime(conv_m['date_week'])
    conv_m['date_month'] = conv_m['date_month'].dt.to_period('M').dt.start_time.dt.date
    df_conv_m = conv_m.groupby(['date_month']).sum(['visits', 'registrations']).reset_index()
    df_conv_m['conversion'] = (df_conv_m['registrations'] / df_conv_m['visits']) * 100

    #Create plot chart for weekly overall convertion
    plt.figure(figsize=(14, 5))
    plt.plot(df['date_week'], df['conversion'], marker='o', c='b', label='overall convertion')
    x0 = df['date_week']
    y0 = df['conversion']
    for x0,y0 in zip(x0,y0):
        label = "{:.0f}%".format(y0)
        plt.annotate(label, (x0,y0), textcoords="offset points",  xytext=(0,10), ha='center')
    plt.legend()
    plt.title('Overall convertion')
    plt.xlabel('Date')
    plt.ylabel('Conversion')
    plt.xticks(df['date_week'], rotation=45)
    plt.ylim([11, 25])
    plt.grid()
    plt.tight_layout()
    plt.savefig(f'./charts/weekly_overall_conversion.png')


    #Create plot chart for monthly overall convertion
    plt.figure(figsize=(14, 5))
    plt.plot(df_conv_m['date_month'], df_conv_m['conversion'], marker='o', c='b', label='overall convertion per months')
    x0 = df_conv_m['date_month']
    y0 = df_conv_m['conversion']
    for x0,y0 in zip(x0,y0):
        label = "{:.0f}%".format(y0)
        plt.annotate(label, (x0,y0), textcoords="offset points",  xytext=(0,10), ha='center')
    plt.legend()
    plt.title('Overall convertion per months')
    plt.xlabel('Date')
    plt.ylabel('Conversion')
    plt.xticks(df_conv_m['date_month'], rotation=45)
    plt.ylim([15, 22])
    plt.grid()
    plt.tight_layout()
    plt.savefig(f'./charts/monthly_overall_conversion.png')


# In[31]:


# Визуализация затрат на рекламу по дням и неделям
def visualizated_cost(df):
    #Create plot chart for weekly overall convertion
    plt.figure(figsize=(14, 5))
    plt.plot(df['date_group'], df['cost'], marker='o', c='b', label='cost')
    plt.legend()
    plt.title('Daily cost')
    plt.xlabel('Date')
    plt.ylabel('Cost')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    plt.savefig(f'./charts/daily_cost.png')

    conv_cost_week = df.copy()
    conv_cost_week['date_week'] = pd.to_datetime(conv_cost_week['date_group'])
    conv_cost_week['date_week'] = conv_cost_week['date_week'].dt.to_period('W').dt.start_time.dt.date
    df_conv_cost_week = conv_cost_week.groupby(['date_week', 'utm_campaign']).sum(['visits', 'registrations', 'cost']).reset_index()
    df_conv_cost_week['conversion'] = (df_conv_cost_week['registrations'] / df_conv_cost_week['visits']) * 100
    df_conv_cost_week.head()
    
    plt.figure(figsize=(14, 5))
    plt.plot(df_conv_cost_week['date_week'], df_conv_cost_week['cost'], marker='o', c='b', label='cost')
    x0 = df_conv_cost_week['date_week']
    y0 = df_conv_cost_week['cost']
    for x0,y0 in zip(x0,y0):
        label = "{:.0f}уе".format(y0)
        plt.annotate(label, (x0,y0), textcoords="offset points",  xytext=(0,10), ha='center')
    plt.legend()
    
    plt.title('Weekly cost')
    plt.xlabel('Date')
    plt.ylabel('Cost')
    plt.xticks(df_conv_cost_week['date_week'], rotation=45)
    plt.ylim([100, 1750])
    plt.grid()
    plt.tight_layout()
    plt.savefig(f'./charts/weekly_cost.png')


# In[32]:


# Визуализация визитов с цветовым выделением рекламных кампаний
def visualizated_visits_with_active_marketing(df):
    conv_ads_campaign1 = df[df["utm_campaign"] == "cybersecurity_special"]
    conv_ads_campaign2 = df[df["utm_campaign"] == "game_dev_crash_course"]
    conv_ads_campaign3 = df[df["utm_campaign"] == "tech_career_fair"]
    conv_ads_campaign4 = df[df["utm_campaign"] == "virtual_reality_workshop"]
    conv_ads_campaign5 = df[df["utm_campaign"] == "web_dev_workshop_series"]
        
    fig, ax = plt.subplots(2, 1, figsize=(14, 10))
    plt.suptitle("Visits during marketing active days", fontsize=16)
    
    ax[0].plot(df['date_group'], df['visits'], marker='o', c='b', label='Visits') 
    ax[0].axvspan(conv_ads_campaign4['date_group'].min(), conv_ads_campaign4['date_group'].max(), facecolor='yellow', alpha=0.5, label='virtual_reality_workshop')
    ax[0].axvspan(conv_ads_campaign2['date_group'].min(), conv_ads_campaign2['date_group'].max(), facecolor='lightgreen', alpha=0.5, label='game_dev_crash_course')
    ax[0].axvspan(conv_ads_campaign5['date_group'].min(), conv_ads_campaign5['date_group'].max(), facecolor='cyan', alpha=0.5, label='web_dev_workshop_series')
    ax[0].axvspan(conv_ads_campaign3['date_group'].min(), conv_ads_campaign3['date_group'].max(), facecolor='pink', alpha=0.5, label='tech_career_fair')
    ax[0].axvspan(conv_ads_campaign1['date_group'].min(), conv_ads_campaign1['date_group'].max(), facecolor='lightblue', alpha=0.5, label='cybersecurity_special')

    
    ax[0].set_xticks(df['date_group'], )
    ax[0].set_xticklabels(df['date_group'], rotation=45)    
    ax[0].legend(loc='upper right')
    ax[0].set_title('Daily visits for the entire period', fontsize=14)
    ax[0].set_xlabel('Date', fontsize=14)
    ax[0].set_ylabel('Visits', fontsize=14)
    ax[0].grid()

    ax[1].plot(df['date_group'], df['visits'], marker='o', c='b', label='Visits')
    ax[1].axvspan(conv_ads_campaign4['date_group'].min(), conv_ads_campaign4['date_group'].max(), facecolor='yellow', alpha=0.5, label='virtual_reality_workshop')
    ax[1].axvspan(conv_ads_campaign2['date_group'].min(), conv_ads_campaign2['date_group'].max(), facecolor='lightgreen', alpha=0.5, label='game_dev_crash_course')
    ax[1].axvspan(conv_ads_campaign5['date_group'].min(), conv_ads_campaign5['date_group'].max(), facecolor='cyan', alpha=0.5, label='web_dev_workshop_series')
    ax[1].axvspan(conv_ads_campaign3['date_group'].min(), conv_ads_campaign3['date_group'].max(), facecolor='pink', alpha=0.5, label='tech_career_fair')
    ax[1].axvspan(conv_ads_campaign1['date_group'].min(), conv_ads_campaign1['date_group'].max(), facecolor='lightblue', alpha=0.5, label='cybersecurity_special')

    ax[1].set_xticks(df['date_group'])
    ax[1].set_xticklabels(df['date_group'], rotation=45)
    ax[1].legend(loc='upper right')
    ax[1].set_title('Daily visits till 2023-05-08', fontsize=14)
    ax[1].set_xlabel('Date', fontsize=14)
    ax[1].set_ylabel('Visits', fontsize=14)
    ax[1].set_xlim(df['date_group'].min(), '2023-05-08')
    ax[1].grid()
 
    plt.tight_layout()
    plt.savefig(f'./charts/visits_with_active_marketing.png')


# Визуализация регистраций с цветовым выделением рекламных кампаний
def visualizated_registrations_with_active_marketing(df):
    conv_ads_campaign1 = df[df["utm_campaign"] == "cybersecurity_special"]
    conv_ads_campaign2 = df[df["utm_campaign"] == "game_dev_crash_course"]
    conv_ads_campaign3 = df[df["utm_campaign"] == "tech_career_fair"]
    conv_ads_campaign4 = df[df["utm_campaign"] == "virtual_reality_workshop"]
    conv_ads_campaign5 = df[df["utm_campaign"] == "web_dev_workshop_series"]
        
    fig, ax = plt.subplots(2, 1, figsize=(14, 10))
    plt.suptitle("Registrations during marketing active days", fontsize=16)
    
    ax[0].plot(df['date_group'], df['registrations'], marker='o', c='b', label='Visits') 
    ax[0].axvspan(conv_ads_campaign4['date_group'].min(), conv_ads_campaign4['date_group'].max(), facecolor='yellow', alpha=0.5, label='virtual_reality_workshop')
    ax[0].axvspan(conv_ads_campaign2['date_group'].min(), conv_ads_campaign2['date_group'].max(), facecolor='lightgreen', alpha=0.5, label='game_dev_crash_course')
    ax[0].axvspan(conv_ads_campaign5['date_group'].min(), conv_ads_campaign5['date_group'].max(), facecolor='cyan', alpha=0.5, label='web_dev_workshop_series')
    ax[0].axvspan(conv_ads_campaign3['date_group'].min(), conv_ads_campaign3['date_group'].max(), facecolor='pink', alpha=0.5, label='tech_career_fair')
    ax[0].axvspan(conv_ads_campaign1['date_group'].min(), conv_ads_campaign1['date_group'].max(), facecolor='lightblue', alpha=0.5, label='cybersecurity_special')
    
    ax[0].set_xticks(df['date_group'], )
    ax[0].set_xticklabels(df['date_group'], rotation=45)    
    ax[0].legend(loc='upper right')
    ax[0].set_title('Daily registrations for the entire period', fontsize=14)
    ax[0].set_xlabel('Date', fontsize=14)
    ax[0].set_ylabel('Registrations', fontsize=14)
    ax[0].grid()

    ax[1].plot(df['date_group'], df['registrations'], marker='o', c='b', label='Visits')
    ax[1].axvspan(conv_ads_campaign4['date_group'].min(), conv_ads_campaign4['date_group'].max(), facecolor='yellow', alpha=0.5, label='virtual_reality_workshop')
    ax[1].axvspan(conv_ads_campaign2['date_group'].min(), conv_ads_campaign2['date_group'].max(), facecolor='lightgreen', alpha=0.5, label='game_dev_crash_course')
    ax[1].axvspan(conv_ads_campaign5['date_group'].min(), conv_ads_campaign5['date_group'].max(), facecolor='cyan', alpha=0.5, label='web_dev_workshop_series')
    ax[1].axvspan(conv_ads_campaign3['date_group'].min(), conv_ads_campaign3['date_group'].max(), facecolor='pink', alpha=0.5, label='tech_career_fair')
    ax[1].axvspan(conv_ads_campaign1['date_group'].min(), conv_ads_campaign1['date_group'].max(), facecolor='lightblue', alpha=0.5, label='cybersecurity_special')

    ax[1].set_xticks(df['date_group'])
    ax[1].set_xticklabels(df['date_group'], rotation=45)
    ax[1].legend()
    ax[1].set_title('Daily registrations till 2023-05-08', fontsize=14)
    ax[1].set_xlabel('Date', fontsize=14)
    ax[1].set_ylabel('Registrations', fontsize=14)
    ax[1].set_xlim(df['date_group'].min(), '2023-05-08')
    ax[1].grid()
 
    plt.tight_layout()
    plt.savefig(f'./charts/registrations_with_active_marketing.png')



# In[34]:


def run_all():
    df_visit_api, df_regist_api = request_api(DATE_BEGIN, DATE_END)
    df_visit_without_bot = visits_cleared(df_visit_api)
    df_visit_unique = unique_visits(df_visit_without_bot)
    df_agreegated_visit = count_unigue_visits(df_visit_unique)
    df_regist_api_dt = cleared_registrations(df_regist_api)
    df_agreegated_regist = count_registrations(df_regist_api_dt)
    df_merged_conv, df_merged_conv_without_platform = merged_visit_registration_convarsion(df_agreegated_visit, df_agreegated_regist)
    ads = pd.read_csv(get_data_path('ads.csv'))
    cleaned_ads = clean_ads_csv(ads)
    df_ads_agg = df_ads_aggregation(cleaned_ads)
    df_merged_conv_ads = merge_df_conv_ads(df_merged_conv_without_platform, df_ads_agg)
    df_conv_week, df_conv_week_platform = weekly_data(df_merged_conv)
    visualizated_visits(df_conv_week, df_conv_week_platform)
    visualizated_registrations(df_conv_week, df_conv_week_platform)
    visualizated_registrations_by_type(df_regist_api_dt)
    visualizated_conversion_by_platform(df_conv_week_platform)
    visualizated_full_conversion(df_conv_week) 
    visualizated_cost(df_merged_conv_ads)
    visualizated_visits_with_active_marketing(df_merged_conv_ads)
    visualizated_registrations_with_active_marketing(df_merged_conv_ads)


# In[35]:


if __name__ == "__main__":
    run_all()


# In[ ]:




