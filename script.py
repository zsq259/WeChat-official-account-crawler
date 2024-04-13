from playwright.sync_api import Playwright, sync_playwright, expect
import time
from datetime import datetime
import json, jsonlines
import os
from keywords import keywords

def fake(page):
    page.mouse.wheel(0,1200)
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

file_path = "article_links.jsonl"

def init_dic():
    data = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = json.loads(line)
                if data.get(line["pub_name"]) is None:
                    data[line["pub_name"]] = []
                data[line["pub_name"]].append(line["url"])
    return data
    
data = init_dic()

comparison_date = datetime.strptime("2023-03-01", "%Y-%m-%d")

def get_links(page, pub_name):
    time.sleep(5)
     # 定位到所有的label元素
    labels = page.locator('label.inner_link_article_item')

    # 获取元素数量
    count = labels.count()
    print(f"当前页共有{count}篇文章")
    if count == 0:
        return False

    # 遍历所有label元素
    for i in range(count):
        # 对于每个label元素，找到其下的第二个span中的a标签的href属性
        href_value = labels.nth(i).locator('span:nth-of-type(2) a').get_attribute('href')
        date_element_text = labels.nth(i).locator('.inner_link_article_date').text_content()
        test_date = datetime.strptime(date_element_text, "%Y-%m-%d")
        if test_date < comparison_date:
            return None
        if href_value not in data[pub_name]:
            data[pub_name].append(href_value)
            with jsonlines.open(file_path, mode='a') as writer:
                writer.write({"pub_name": pub_name, "url": href_value})
            if len(data[pub_name]) >= 500:
                return None

    return True

def login(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()    
    page.goto("https://mp.weixin.qq.com/")
    with page.expect_popup() as page1_info:
        page.locator(".new-creation__icon > svg").first.click(timeout=1000000)
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

def record_state(count_path, page_count):
    with open(count_path, 'w') as f:
        f.write(str(page_count - 1))


def run(playwright: Playwright, pub_name) -> None:    
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.context.add_cookies(cookies)
    page.goto("https://mp.weixin.qq.com/")

    with page.expect_popup() as page1_info:
        page.locator(".new-creation__icon > svg").first.click(timeout=1000000)
    page1 = page1_info.value
    
    page1.get_by_text("超链接").click()
    page1.get_by_text("选择其他公众号").click()
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").click()
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").fill(pub_name)
    page1.get_by_placeholder("输入文章来源的公众号名称或微信号，回车进行搜索").press("Enter")
    page1.get_by_text("订阅号", exact=True).nth(1).click()

    page_count = 0
    count_path = f"./tmp/page_count_{pub_name}.txt"
    if os.path.exists(count_path):
        with open(count_path, 'r') as f:
            page_count = int(f.read())

    if page_count > 0:
        page1.fill('input[type="number"]', str(page_count))
        page1.get_by_role("link", name="跳转").click()
    
    error_flag = False
    this_count = 0

    while (True):
        page_count += 1
        this_count += 1
        if this_count > 48:
            record_state(count_path, page_count)
            error_flag = True
            break
        print(f"公众号 {pub_name} 第{page_count}页")
        flag = get_links(page1, pub_name)
        if flag is None:
            record_state(count_path, page_count)
            error_flag = None
            break
        
        if not flag:
            record_state(count_path, page_count)
            error_flag = True
            break
        fake(page1)
        next_button = page1.get_by_role("link", name="下一页")

        if (next_button.count() == 0):
            record_state(count_path, page_count)
            error_flag = True
            break
        print(f"此公众号总共获取到{len(data[pub_name])}篇文章")
        next_button.click()
        
    page1.close()
    page.close()
    context.close()
    browser.close()
    return error_flag

def check_folder():
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

check_folder()

for keyword in keywords:
    if data.get(keyword) is None:
        data[keyword] = []
    with sync_playwright() as playwright:
        flag = run(playwright, keyword)
        if flag is None:
            continue
        if flag:
            break