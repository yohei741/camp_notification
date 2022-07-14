import json
import sys
import urllib.parse
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary
import os
from os.path import join, dirname
# from dotenv import load_dotenv
from bs4 import BeautifulSoup

# プルダウンの選択
from selenium.webdriver.support.select import Select

# 正規表現での抽出用
import re

#曜日を判定
import datetime as dt

# ChromeDriver(WebDriver)を自動更新する
from webdriver_manager.chrome import ChromeDriverManager

# 日本語の曜日を取得する
# https://qiita.com/_masa_u/items/e104d42bd6f200d3b959
# import locale
# locale.setlocale(locale.LC_ALL, 'ja_JP.utf8') # LC_TIME → LC_ALL



# 予約画面を Selenium で立ち上げ
options = Options()
options.add_argument('--headless') # コメントアウトすると、ブラウザ表示され操作を確認できる
# browser = webdriver.Chrome(options=options)
browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)



# 土曜以外のサーチ対象日リスト （行けそうな日があれば、こちらに追加してください！！！！）
selected_days = [
    "2022年7月17日"
    , "2022年8月10日"
    , "2022年8月11日"
    , "2022年8月12日"
    , "2022年9月18日"
    , "2022年9月19日"
    , "2022年9月23日"
]

# NG日リスト
ng_days = [
        "2022年7月9日"
        , "2022年7月16日"
        , "2022年7月17日"
        , "2022年7月23日"
        , "2022年7月30日"
        , "2022年8月10日"
        , "2022年8月11日"
        , "2022年8月12日"
        , "2022年8月13日"
        , "2022年8月20日"
        , "2022年9月18日"
        , "2022年9月19日"
]

# Beautiful Soup でHTMLの中からHTML要素を取得：　https://gammasoft.jp/blog/difference-find-and-select-in-beautiful-soup-of-python/

# ここから：　ふもとっぱらキャンプ場 --------

browser.get("https://fumotoppara.secure.force.com/")

# プルダウンから月の取得
dropdown = browser.find_element_by_id('f_nengetsu')
select = Select(dropdown)
all_options = select.options # 全ての選択肢を取得(list)

# プルダウン月を格納するリスト
select_list = []
for option in all_options:
    select_list.append(option.text)

# 土曜はデフォでサーチ対象する
find_weekofday = "土"

# 予約OKな日程を入れるリスト
ok_days = []


# 各月をループで見ていく
for i, selected_month in enumerate(select_list):
    
    # 次ページへ遷移
    if i != 0:
        # プルダウンで選択
        dropdown = browser.find_element_by_id('f_nengetsu')
        select = Select(dropdown)
        select.select_by_visible_text(select_list[i]) 

        # 検索ボタンを押す
        elem_next_page = browser.find_element_by_id("j_id0:fSearch:searchBtn")
        elem_next_page.click()


    # ブラウザ表示されている HTML から BeautifulSoup オブジェクトを作りパースする
    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # 日にち＆曜日が含まれるHTMLを取得
    l_1 = soup.select("[class='td_itemvalue tbl_top_td1']")

    # 日にちごとにリストとしてまとめ直し
    l_days = []
    l=[]
    cnt=0
    for j in range(len(l_1)):
        cnt+=1
        if cnt>2:
            l_days.append(l)
            cnt=1
            l=[]
            l.append(l_1[j])
        elif j == (len(l_1))-1:
            l.append(l_1[j])
            l_days.append(l)
        else:
            l.append(l_1[j])


    # 予約状況が含まれるHTMLを取得
    l_2 = soup.select(".td_itemvalue.tbl_top_td3")
    
    # 日にちごとにリストとしてまとめ直し
    # 20220109_バグ修正
    l_preserve = []
    l_tmp=[]
    cnt=0
    for i, k in enumerate(l_2, 1):
        if i%4 != 0:
            l_tmp.append(k)
        else:
            l_preserve.append(l_tmp)
            l_tmp = []


    # 曜日だけのリストを作成
    l_weekofdays = [re.search(r"(.)(?=</span>)", str(i[1])).group() for i in l_days]


    # l_days と l_preserve の要素数が同じかテスト
    # Heroku上でバグる、いったんコメントアウト
    # assert len(l_days) == len(l_preserve) == len(l_weekofdays)


    # すべての空きのある日にちをサーチ
    for x in range(len(l_preserve)):
        if ("○" in str(l_preserve[x][0]) or "△" in str(l_preserve[x][0])) and \
                (l_weekofdays[x] == find_weekofday or f"{selected_month}{x+1}日" in selected_days) and \
                (f"{selected_month}{x+1}日" not in ng_days):
            message = f"{selected_month}{x+1}日({str(l_weekofdays[x])}曜)"
            ok_days.append(message)


# ここまで：　ふもとっぱらキャンプ場 --------


# ここから：　浩庵キャンプ場 --------

browser.get("https://kouan-motosuko.com/reserve/Reserve/input/")

# ブラウザに表示されている HTML から BeautifulSoup オブジェクトを作りパースする
soup = BeautifulSoup(browser.page_source, 'html.parser')

# 年月の取得
p = soup.find("h3").text
year_word = re.search(r'\d*年', p).group()
month_word = re.search(r'\d*月', p).group()
year_word = int(year_word.replace('年', ''))
month_word = int(month_word.replace('月', ''))

# 次月、次々月の文字列を取得
months_l = [str(month_word).zfill(2), str(month_word+1).zfill(2), str(month_word+2).zfill(2)]

# 予約OKな日程を入れるリスト
ok_list_koan = []

for selected_month in months_l:

    browser.get(f"https://kouan-motosuko.com/reserve/Reserve/input/?type=camp&ym=2022{selected_month}")
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    l = soup.select("[class='form-group']")

    # 年月の取得
    p = soup.find("h3").text
    year_word = re.search(r'\d*年', p).group()
    month_word = re.search(r'\d*月', p).group()
    year_word = int(year_word.replace('年', ''))
    month_word = int(month_word.replace('月', ''))

    for day, text in enumerate(l, 1):
        if (dt.date(year_word, month_word, day).strftime('%A') == "Saturday" or f"{year_word}年{month_word}月{day}日" in selected_days) \
                and f"{year_word}年{month_word}月{day}日" not in ng_days \
                and 0 <= (dt.date(year_word, month_word, day) - dt.date.today()).days < 60:
            if "満" not in str(text): 
                ok_list_koan.append(f"{month_word}月{day}日({dt.date(year_word, month_word, day).strftime('%a')})")

# ここまで：　浩庵キャンプ場 --------


LINE_TOKEN=os.environ.get("LINE_TOKEN")
LINE_NOTIFY_URL="https://notify-api.line.me/api/notify"

# LINE通知を行う関数
# こちらのコードを参照：　https://qiita.com/kutsurogi194/items/6b9c8d37b2b83fc2ce87
def send_line_push(message):
    method = "POST"
    headers = {"Authorization": "Bearer %s" % LINE_TOKEN}
    payload = {"message": message}
    try:
        payload = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            url=LINE_NOTIFY_URL, data=payload, method=method, headers=headers)
        urllib.request.urlopen(req)
    except Exception as e:
        print ("Exception Error: ", e)
        sys.exit(1)


# 通知表示の修正
ok_list_fumoto = "\n".join(ok_days)
# ok_list_koan_parse = "\n".join(ok_list_koan) # 浩庵キャンプ場いったん停止（2022/5/15）
ok_days_parse = "\n\n空きが出ましたよ！\n\n\n▼ふもとっぱらキャンプ場\n" + ok_list_fumoto 
                                    # + "\n\n▼浩庵キャンプ場\n" + ok_list_koan_parse + "\n"


# 空きがあればLINE通知する
if len(ok_days) != 0: # +len(ok_list_koan)
    send_line_push(ok_days_parse)

