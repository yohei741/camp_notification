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



# 予約画面を Selenium で立ち上げ
options = Options()
options.add_argument('--headless') # コメントアウトすると、ブラウザ表示され操作を確認できる
browser = webdriver.Chrome(options=options)
browser.get("https://fumotoppara.secure.force.com/")


# プルダウンから月の取得
dropdown = browser.find_element_by_id('f_nengetsu')
select = Select(dropdown)
all_options = select.options # 全ての選択肢を取得(list)

# プルダウン月を格納するリスト
select_list = []
for option in all_options:
    select_list.append(option.text)


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


    # 土曜はデフォでサーチ対象する
    find_weekofday = "土"

    # 土曜以外のサーチ対象日リスト （行けそうな日があれば、こちらに追加してください！！！！）
    selected_days = [
        "2022年2月11日"
        , "2022年3月20日"
        , "2022年4月29日"
        , "2022年5月1日"
        , "2022年5月2日"
        , "2022年5月3日"
        , "2022年5月4日"
        , "2022年5月5日"
        , "2022年7月17日"
    ]

    # NG日リスト
    ng_days = [
            "2022年1月15日"
            , "2022年1月22日"
            , "2022年2月5日"
            , "2022年2月11日"
            , "2022年2月12日"
            , "2022年2月19日"
            , "2022年2月26日"
            , "2022年3月20日"
    ]


    # すべての空きのある日にちをサーチ
    for x in range(len(l_preserve)):
        if ("○" in str(l_preserve[x][0]) or "△" in str(l_preserve[x][0])) and \
                (l_weekofdays[x] == find_weekofday or f"{selected_month}{x+1}日" in selected_days) and \
                (f"{selected_month}{x+1}日" not in ng_days):
            message = f"{selected_month}{x+1}日({str(l_weekofdays[x])}曜)"
            ok_days.append(message)


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
ok_days_parse = "\n".join(ok_days)
ok_days_parse = "\n\n空きが出ましたよ！\n\n" + ok_days_parse + "\n\n▼いますぐ予約！\nhttps://fumotoppara.secure.force.com/"


# 空きがあればLINE通知する
if len(ok_days) != 0:
    send_line_push(ok_days_parse)
