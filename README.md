## 微信公众号文章爬虫

### 要求

在选定微信订阅号账号的情况下，批量抓取一段时间之内的所有推文的：

- 链接
- 标题
- 封面图
- 作者
- 发布账号
- 正文文本内容
- 发布时间
- 阅读量
- 点赞数
- 在看数
- 留言数
- 是否开启留言

并导出为 excel 表格

### 实现

整体思路：枚举公众号->爬取公众号下的所有文章->对每篇文章找到所需信息

#### step1 爬取公众号下的所有文章

即使不是爬虫，想要看到一个公众号下的所有文章也不那么容易。目前统一的手段是在微信应用中打开公众号，但此页面无法抓包，也无法获得爬虫需要的请求和响应。有部分公众号给出了往期文章列表供爬取，但此方法非常依赖公众号，并不统一。

网络上已知的实现有

- 微信历史消息，但可能被封号
- [搜狗微信](https://weixin.sogou.com/)，但现在似乎已经没有维护
- [微信公众平台](https://mp.weixin.qq.com/)，也可能被封号

本爬虫使用的手段是利用微信公众平台，在创作图文消息时插入超链接，可以搜到一个公众号下的所有文章。

微信公众平台需要先注册账号并修改名称通过审核。

实际测试发现，爬取几十页后就会被封一段时间（几十分钟）。因此需要多次启动爬虫，因而记录下了失败时爬取的公众号和页数，方便下次直接跳转。

具体的实现则是使用 `playwright` 模拟浏览器，参考[script.py](https://github.com/zsq259/WeChat-official-account-crawler/blob/main/script.py)。

爬取获得的网址会存储到 `article_links.jsonl`。

#### step2 爬取一篇文章中的所有信息

第一部分爬到的链接中含有

难点在于找出所需信息是在哪个包中，以及如何发送请求和提取。

通过网络搜索和实践探索获得了相关参数，分别在两个包中，具体实现可见代码：

- 标题：rich_media_title 

- 封面图：js_row_immersive_cover_img

- 作者：

  ```html
  class="rich_media_meta_list"
  class="rich_media_meta rich_media_meta_text"
  ```

- 发布账号：id="js_name"

- 正文文本：

```html
  <div class="rich_media_content js_underline_content
                         defaultNoSetting
              " id="js_content" style="visibility: visible;">
```
- 发布时间：id="publish_time"

另一个包 getappmsgext: （[参考](https://wnma3mz.github.io/hexo_blog/2017/11/18/%E8%AE%B0%E4%B8%80%E6%AC%A1%E5%BE%AE%E4%BF%A1%E5%85%AC%E4%BC%97%E5%8F%B7%E7%88%AC%E8%99%AB%E7%9A%84%E7%BB%8F%E5%8E%86%EF%BC%88%E5%BE%AE%E4%BF%A1%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E7%82%B9%E8%B5%9E%E7%9A%84%E8%8E%B7%E5%8F%96%EF%BC%89/)）

- 阅读量：read_num
- 点赞数：old_like_num
- 在看数：like_num
- 留言数：comment_count
- 开启留言：comment_enabled

想要获取这个包的响应，即这五个信息，需要中请求中加入参数 `key`，此参数不易获取，与公众号相关联，且一段时间后失效。因此目前的程序只能通过手动查看抓到的包，再将 `key` 填入代码中，即每个公众号需要手动操作一次。可能的解决办法是自动化获取抓到的包中的 `key`。

#### 缺陷

在 step1 中， 爬虫的速度很受限制，稍微爬快一点就会被封很久，无法获取数据。即使慢到了 10s 翻一页，也会在爬五六十页后被封几十分钟左右。有多个账号的话，可以通过流水线来缓解。由于实现细节，目前没有做到记录公众号是否已经爬取完成，需要手动修改 `keywords.py`，在其中注释已经完成的公众号。

在 step2 中，目前还没有实现 key 的自动获取，因此需要先手动在微信应用端中打开公众号的文章，再通过抓包软件获取 key 并复制进代码中。如果爬的速度过快，也会被检测到而导致账号无法获得文章点赞数等信息。在实现保存文件的时候，也需要保证 `output.xlsx` 没有在其他应用（如WPS）中打开，以避免写入权限出错。

### 使用方法（目前）

`script.py` 完成了 step1 的工作。安装所需的库并运行代码，在弹出的窗口中扫码登录微信公众平台，等待一次爬取完成即可。**在爬完一个公众号的所有数据后，需要手动在 `keywords.py` 中将其注释，避免重复爬取浪费时间。**

`work.py` 完成了 step2 的工作。首先安装所需的库。然后通过抓包工具抓取文章请求，获得相关参数（`headers`, `cookies`, `key`）后填入代码中。之后运行代码即可。**在运行代码时，尽量不要在其他应用中打开输出文件 `output.xlsx`，以防写入时权限出错。** 在爬完一个公众号的所有文章后，或 `key` 时限过期后，程序会结束，此时需要再次使用抓包软件获取新的 `key`。

### 参考

[https://github.com/wnma3mz/wechat_articles_spider](https://github.com/wnma3mz/wechat_articles_spider)

[https://blog.csdn.net/nzbing/article/details/131601790](https://blog.csdn.net/nzbing/article/details/131601790)

[https://www.bilibili.com/video/BV1mK4y1F7Kp/](https://www.bilibili.com/video/BV1mK4y1F7Kp/)
