from playwright.sync_api import Playwright, sync_playwright, expect
import time
from datetime import datetime
import json
import os
from keywords import keywords

def fake(page):    
    page.mouse.wheel(0,200)
    time.sleep(1)
    page.mouse.wheel(0,200)
    time.sleep(1)
    page.mouse.wheel(0,200)
    time.sleep(1)
    page.mouse.wheel(0,200)
    time.sleep(1)
    page.mouse.wheel(0,200)
    time.sleep(1)
    page.mouse.wheel(0,200)

def init_dic():
    filename = "article_links.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)    
            return data
    return dict()

data = init_dic()

comparison_date = datetime.strptime("2023-03-01", "%Y-%m-%d")
def check_time(url):
    if "http" in url:
        return url
    else:
        return "https://mp.weixin.qq.com" + url

def get_links(page, pub_name):
    time.sleep(5)
     # 定位到所有的label元素
    labels = page.locator('label.inner_link_article_item')

    # 获取元素数量
    count = labels.count()
    print(f"当前页共有{count}篇文章")

    # 遍历所有label元素
    for i in range(count):
        # 对于每个label元素，找到其下的第二个span中的a标签的href属性
        href_value = labels.nth(i).locator('span:nth-of-type(2) a').get_attribute('href')
        date_element_text = labels.nth(i).locator('.inner_link_article_date').text_content()
        test_date = datetime.strptime(date_element_text, "%Y-%m-%d")
        if test_date < comparison_date:
            return False
        if href_value not in data[pub_name]:
            data[pub_name].append(href_value)

    return True

def login(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()    
    page.goto("https://mp.weixin.qq.com/")
    with page.expect_popup() as page1_info:
        page.locator(".new-creation__icon > svg").first.click()
    page1 = page1_info.value
    cookies = page.context.cookies()
    page1.close()
    page.close()
    context.close()
    browser.close()
    return cookies

def get_cookies():
    with sync_playwright() as playwright:
        cookies = login(playwright)
    return cookies

cookies = get_cookies()

def run(playwright: Playwright, pub_name) -> None:    
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.context.add_cookies(cookies)
    page.goto("https://mp.weixin.qq.com/")

    with page.expect_popup() as page1_info:
        page.locator(".new-creation__icon > svg").first.click()
    page1 = page1_info.value
    
    page1.get_by_text("超链接").click()
    page1.get_by_text("选择其他公众号").click()
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").click()
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").fill(pub_name)
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").press("Enter")
    page1.get_by_text("订阅号", exact=True).nth(1).click()

    count = 0
    while (True):
        count += 1
        print(f"公众号 {pub_name} 第{count}页")
        flag = get_links(page1, pub_name)
        if not flag:
            break
        fake(page1)
        next_button = page1.get_by_role("link", name="下一页")
        if (next_button.count() == 0):
            break
        next_button.click()        
        
    page1.close()
    page.close()
    context.close()
    browser.close()

for keyword in keywords:
    if data.get(keyword) is None:
        data[keyword] = []
    with sync_playwright() as playwright:
        run(playwright, keyword)
    with open("article_links.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)