import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import json
import ssl
import time
ssl._create_default_https_context = ssl._create_unverified_context

cookies = {} # fill in the cookies you get

headers = {} # fill in the headers you get

data = {
    "is_only_read": "1",
    "is_temp_url": "0",              
    "appmsg_type": "9", # 新参数，不加入无法获取like_num
    "reward_uin_count": "0",
}

# work2() 额外需要的：
# 都可以在 work1() 的包中获取
uin = "" # fill in the uin you get
article_key = "" # fill in the article_key you get

links = []
titles = []
cover_images = []
arthors = []
publishers = []
texts = []
publish_times = []
read_nums = []
old_like_nums = []
like_nums = []
conment_nums = []
conment_enableds = []

def get_params(url):
    url = url.split("&")
    __biz = url[0].split("__biz=")[1]
    article_mid = url[1].split("=")[1]
    article_idx = url[2].split("=")[1]
    article_sn = url[3].split("=")[1]
    return __biz, article_mid, article_idx, article_sn

def work1(origin_url, need_more_info=False):    
    __biz, article_mid, article_idx, article_sn = get_params(origin_url)
    url = "https://mp.weixin.qq.com/s?"
    article_url = url + "__biz={}&mid={}&idx={}&sn={}".format(__biz, article_mid, article_idx, article_sn)    
    url2 = url + "__biz={}&key={}&uin={}&mid={}&idx={}&sn={}".format(__biz, article_key, uin, article_mid, article_idx, article_sn)    
    content = requests.get(url2, headers=headers, data=data)    
    links.append(article_url)

    soup = BeautifulSoup(content.text, 'lxml')

    # 提取标题、封面图、作者、发布账号和发布时间    
    title = soup.find('meta', property="og:title")['content'] if soup.find('meta', property="og:title") else ""    
    cover_image = soup.find('meta', property="og:image")['content'] if soup.find('meta', property="og:image") else ""
    author = soup.find(class_="rich_media_meta rich_media_meta_text").text.strip() if soup.find(class_="rich_media_meta rich_media_meta_text") else ""    

    publisher_test = soup.find(id="js_name")
    publisher = ""
    if publisher_test is None:
        print(origin_url)
        publisher = ""
    else:
        publisher = soup.find(id="js_name").text.strip()
    
    # 查找具有特定类名的<div>标签
    text_content = soup.find('div', id='js_content')
    text = None

    # 如果找到该标签，则提取其文本内容；否则，输出提示信息
    if text_content:        
        text = text_content.get_text(separator=' ', strip=True)                
    else:        
        print(origin_url)
        # raise Exception("找不到文章正文")
        text = ""
    texts.append(text)

    # 使用正则表达式从JavaScript中提取变量值
    js_content = str(soup.find_all('script'))
    publish_time = re.search(r'var createTime = [\'"](.*?)[\'"]', js_content).group(1) if re.search(r'var createTime = [\'"](.*?)[\'"]', js_content) else ""
    comment_id = re.search(r'var comment_id = [\'"](.*?)[\'"]', js_content).group(1) if re.search(r'var comment_id = [\'"](.*?)[\'"]', js_content) else ""

    titles.append(title)
    cover_images.append(cover_image)
    arthors.append(author)
    publishers.append(publisher)
    publish_times.append(publish_time)

    if need_more_info:
        work2(__biz, article_mid, article_idx, article_sn, article_key, uin, comment_id)
    else:
        read_nums.append(-1)
        old_like_nums.append(-1)
        like_nums.append(-1)
        conment_nums.append(-1)
        conment_enableds.append(-1)

def work2(__biz, article_mid, article_idx, article_sn, article_key, uin, article_comment_id):
    params = {
        "__biz": __biz,
        "mid": article_mid,
        "sn": article_sn,
        "idx": article_idx,
        "key": article_key,
        "uin": uin,
        "comment_id": article_comment_id,
    }        
    url = "https://mp.weixin.qq.com/mp/getappmsgext?"    
    contents = requests.post(url, params=params, data=data, cookies=cookies, headers=headers).json()
    # print(contents)        
            
    if 'appmsgstat' not in contents:
        read_nums.append(-1)
        old_like_nums.append(-1)
        like_nums.append(-1)
        conment_nums.append(-1)
        conment_enableds.append(-1)
        output()
        raise Exception("获取文章信息失败")

    read_num = contents['appmsgstat']['read_num'] if 'appmsgstat' in contents else -1
    old_like_num = contents['appmsgstat']['old_like_num'] if 'appmsgstat' in contents else -1
    like_num = contents['appmsgstat']['like_num'] if 'appmsgstat' in contents else -1
    conment_num = contents['comment_count']  if 'comment_num' in contents else 0
    conment_enabled = contents['comment_enabled'] if 'comment_enabled' in contents else 0

    read_nums.append(read_num)
    old_like_nums.append(old_like_num)
    like_nums.append(like_num)
    conment_nums.append(conment_num)
    conment_enableds.append(conment_enabled)
    
file_path = "./output.xlsx"

def output(file_path=file_path):
    df = pd.DataFrame({
        "链接": links,
        "标题": titles,
        "封面图": cover_images,
        "作者": arthors,
        "发布账号": publishers,
        "发布时间": publish_times,
        "阅读量": read_nums,
        "点赞数": old_like_nums,
        "在看数": like_nums,
        "留言数": conment_nums,
        "留言是否开启": conment_enableds,
        "正文": texts
    })
    
    if not os.path.exists(file_path):
        df.to_excel(file_path, index=False)
        return
    old_df = pd.read_excel(file_path)
    new_df = pd.concat([old_df, df], ignore_index=True).drop_duplicates()
    new_df.to_excel(file_path, index=False)

links_path = "./article_links.jsonl"

def init(file_path=file_path):
    file_path = "./output.xlsx"
    links = []
    if os.path.exists(file_path):
        data = pd.read_excel(file_path)
        links = data["链接"].tolist()        

    return links

ready_links = init()

now_biz = ""

with open(links_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = json.loads(line)
        url = line["url"].split("&chksm=")[0]
        url = "https" + url.split("http")[1]        
                
        if url not in ready_links:
            # print(url)
            __biz = url.split("&")[0].split("__biz=")[1]
            if __biz != now_biz:
                if now_biz != "":
                    break
                now_biz = __biz
            time.sleep(2)
            ready_links.append(url)
            work1(url, True)            
output()
df = pd.read_excel(file_path).drop_duplicates()
df.to_excel(file_path, index=False)