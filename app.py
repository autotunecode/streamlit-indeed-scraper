import streamlit as st
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage
import re
from datetime import datetime

page = ChromiumPage()  # ChromiumPageのインスタンスを作成

# Streamlitアプリの設定
st.title('Indeed求人情報検索アプリ')

# サイドバーの設定
with st.sidebar:
    st.header('検索条件')
    # ユーザー入力を受け取る
    position = st.text_input('職種', 'python', help='希望する職種を入力してください。例: エンジニア、デザイナー')
    location = st.text_input('勤務地', '福岡県 福岡市', help='希望する勤務地を入力してください。例: 東京都、大阪府')
    fromage = st.selectbox('掲載日', [1, 3, 7, 14], index=3, help='求人情報の掲載日数を選択してください。')
    start = st.number_input('開始位置', min_value=0, value=0, step=10, help='検索結果の開始位置を指定してください。')

# 検索URLを生成する関数
def get_url(position, location, fromage=14, start=0):
    position = position.replace(' ', '+')
    location = location.replace(' ', '+')
    if fromage not in [1, 3, 7, 14]:
        raise ValueError('fromageは1, 3, 7, 14のいずれかでなければなりません。')
    url = f'https://jp.indeed.com/jobs?q={position}&l={location}&fromage={fromage}&start={start}'    
    return url

# BeautifulSoupオブジェクトを取得する関数
def get_soup(url):
    time.sleep(random.uniform(1, 3))  # 1から2秒間隔でランダムにリクエスト
    page.get(url)
    return BeautifulSoup(page.html, 'html.parser')
    
# 求人IDを取得する関数
def get_job_id(soup):
    return [element.a.get('data-jk') for element in soup.find_all('div', class_='job_seen_beacon')]

# 次のページが存在するかを確認する関数
def get_next_page(soup):
    return bool(soup.find('a', {'aria-label': 'Next Page'}))
    
# 求人リンクを取得する関数
def get_link(position, location, fromage=14, start=0):
    job_ids = []
    while True:
        url = get_url(position, location, fromage, start)
        soup = get_soup(url)
        items = soup.find_all('div', class_='job_seen_beacon')
        job_ids.extend(get_job_id(soup))
        if not get_next_page(soup):
            break
        start += 10
    return job_ids

# 検索ボタンが押された時の処理
if st.button('検索'):
    data = []
    for link in get_link(position, location, fromage, start):
        page.get(f'https://jp.indeed.com/viewjob?jk={link}')
        soup = BeautifulSoup(page.html, 'html.parser')
        # 求人情報を取得
        job_title = soup.find('h1').find('span').get_text() if soup.find('h1') and soup.find('h1').find('span') else None
        company_div = soup.find('div', {'data-company-name': 'true'})
        company_name = company_div.find('a').get_text() if company_div and company_div.find('a') else None
        location_div = soup.find('div', {'data-testid': 'inlineHeader-companyLocation'})
        location_name = location_div.get_text() if location_div else None
        salary_div = soup.find('div', {'id': 'salaryInfoAndJobType'})
        salary_info = None
        employment_type = None
        if salary_div:
            salary_parts = salary_div.get_text().split('-')
            if salary_parts:
                salary_info = salary_parts[0].strip()
                if len(salary_parts) > 1:
                    employment_type = salary_parts[1].strip()
        info_div = soup.find('div', class_='css-1axw7mm eu4oa1w0')
        info = info_div.get_text() if info_div else None
        rating_div = soup.find('div', {'aria-label': re.compile('5つ星のうち')})
        rank = float(rating_div.get('aria-label').split('5つ星のうち')[1]) if rating_div else None
        # 求人情報を辞書に格納
        item = {
                '企業名': company_name,
                '勤務地': location_name,
                '職種': job_title,
                '給与': salary_info,
                '雇用形態': employment_type,
                '問い合わせ': info,
                '評価': rank,
                'url': f'https://jp.indeed.com/viewjob?jk={link}'
        }
        data.append(item)
        time.sleep(random.uniform(1, 3))  # 1から3秒間隔でランダムにリクエスト
    df = pd.DataFrame(data)
    st.write(df)
    today = datetime.now().strftime('%Y%m%d')
    filename = f'{today}_{position.replace(" ", "_")}_{location.replace(" ", "_")}.csv'
    st.download_button(label='結果をCSVでダウンロード', data=df.to_csv().encode('utf-8'), file_name=filename, mime='text/csv')
page.quit()