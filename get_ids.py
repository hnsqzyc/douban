import requests
import re
from lxml import etree

proxy = '202.96.133.156:4223'
real_proxy = {
    'http': proxy,
    'https': proxy
}

# url = 'https://movie.douban.com/celebrity/1274438/'
#
# header = {
#     "Host": "movie.douban.com",
#     "Connection": "keep-alive",
#     "Cache-Control": "max-age=0",
#     "Upgrade-Insecure-Requests": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#     "Referer": "https://movie.douban.com/celebrity/1275593/",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "zh-CN,zh;q=0.9"
# }

# res = requests.get(url=url, headers=header, proxies=real_proxy).text
# print(res)
#
# con = etree.HTML(res)
# cons = str(con.xpath('//div[@id="content"]/h1/text()')[0])
# print(cons)
# print(type(cons))

# 获取全部作品链接 *****************************************
# url = 'https://movie.douban.com/celebrity/1274438/movies?sortby=time&format=pic'
# header = {
#     "Host": "movie.douban.com",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#     "Referer": "https://movie.douban.com/celebrity/1274438/",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "zh-CN,zh;q=0.9"
# }
#
# res1 = requests.get(url=url, headers=header, proxies=real_proxy).text
# # print(res1)
# con1 = etree.HTML(res1)
# cons1 = con1.xpath('//div[@class="grid_view"]/ul/li')
#
# for con in cons1:
#     works_name = con.xpath('./dl/dd//a/text()')
#     works_link = con.xpath('dl/dd//a/@href')
#     wroks_id = ''

# 获取全部搭档人员链接 *****************************************
url = 'https://movie.douban.com/celebrity/1022664/partners?start=30'
header = {
    "Host": "movie.douban.com",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://movie.douban.com/celebrity/1022664/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
res3 = requests.get(url=url, headers=header).text
# print(res3)
con3 = etree.HTML(res3)
cons3 = con3.xpath('//div[@class="partners item"]')
for con in cons3:
    partner_id = con.xpath('./@id')[0]
    partner_name = con.xpath('.//h2/a/text()')[0]
    page_num_counts = con.xpath('//div//span[@class="count"]/text()')[0]
    page_num_countss = re.findall(r'(\d+)', page_num_counts)[0]
    page_num_count = int(int(page_num_countss) / 10) + 1

    print(partner_id, partner_name, page_num_count)