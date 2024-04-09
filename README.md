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

具体的实现则是使用 `playwright` 模拟浏览器，参考。

#### step2 爬取一篇文章中的所有信息

难点在于找出所需信息是在哪个包中，以及如何发送请求和提取。

通过网络搜索和实践探索获得了相关参数，分别在两个包中，具体实现可见代码：

- 链接

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

