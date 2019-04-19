import requests
import json
from urllib import parse
import re
import time
from lxml import etree
from pymongo import MongoClient


url = 'mongodb://47.105.103.8:27017/'
mongo_conn = MongoClient(url)
db = mongo_conn.douban
user_ids = db.user_ids

# user_ids.insert_one({'user_name': '杨紫琼 Michelle Yeoh', 'user_id': 1022664, 'status': 0, 'img_url_li':[]})
user_ids.insert_one({'user_name': '孙晔 Ye Sun', 'user_id': 1349113, 'status': 0, 'img_url_li':[]})

# proxy = '119.132.108.12:4223'
# real_proxy = {
#     'http': proxy,
#     'https': proxy
# }
#
# url = 'http://www.baidu.com/'
# # url = 'http://ip.cn/'
# print(requests.get(url, proxies=real_proxy).content.decode())
#
# # # 视频列表获取视频id
# url_start = 'https://movie.douban.com/j/search_subjects?'
#
# for page in range(0, 500):
#     url_end = {
#         'type': 'tv',
#         'tag': '韩剧',
#         'sort': 'rank',
#         # 'sort': 'recommend',
#         # 'playable': 'on',
#         'page_limit': 20,
#         'page_start': page * 20
#     }
#
#     url_ends = parse.urlencode(url_end)
#
#     url = url_start + url_ends
#
#     headers = {
#         "Host": "movie.douban.com",
#         "Connection": "keep-alive",
#         "Accept": "*/*",
#         "X-Requested-With": "XMLHttpRequest",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
#         "Referer": "https://movie.douban.com/tv/",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "zh-CN,zh;q=0.9",
#         "Cookie":'bid=eDe_1FZyc8s; ll="108090"; _vwo_uuid_v2=D40F48E2FD349B422C70A5A1CB69C398F|1791bd35b31f2cb20f863ba1866a9ac9; douban-fav-remind=1; ct=y; __utmc=30149280; __utmc=223695111; gr_user_id=50218341-d9e7-4199-b599-62c9cf745f53; gr_session_id_22c937bbd8ebd703f2d8e9445f7dfd03=ba1bc951-15f0-4d66-9da7-5abbef091081; gr_cs1_ba1bc951-15f0-4d66-9da7-5abbef091081=user_id%3A0; gr_session_id_22c937bbd8ebd703f2d8e9445f7dfd03_ba1bc951-15f0-4d66-9da7-5abbef091081=true; ap_v=0,6.0; viewed="30275106_30426201"; __utma=30149280.657213308.1554800162.1555567993.1555568166.16; __utmz=30149280.1555568166.16.6.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmb=30149280.2.9.1555568166; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1555568167%2C%22https%3A%2F%2Fwww.douban.com%2F%22%5D; _pk_ses.100001.4cf6=*; __utma=223695111.1240478973.1554800162.1555477996.1555568167.15; __utmb=223695111.0.10.1555568167; __utmz=223695111.1555568167.15.5.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; dbcl2="195017492:1Qb2Ll+IvqY"; ck=usDc; _pk_id.100001.4cf6=1c4ef195607a72b8.1554800162.15.1555569621.1555478283.; push_noty_num=0; push_doumail_num=0'
#     }
#     time.sleep(5)
#     res1 = json.loads(requests.get(url, headers=headers, proxies=real_proxy).text)
#     print('爬取到第 %s 页...' % (page))
#     for res in res1['subjects']:
#         item_tuple = {}
#         item_tuple['title'] = res.get('title')
#         item_tuple['rate'] = res.get('rate')
#         item_tuple['id'] = res.get('id')
#         print(item_tuple)
#
#         if douban_video_ids.find_one({'id': item_tuple['id']}):
#             print('数据库已经存在...')
#         else:
#             print('数据库不存在, 插入...')
#             item_tuples = item_tuple.copy()
#             result = douban_video_ids.insert_one(item_tuples)

# # 通过视频id获取演职员信息id
# url = 'https://movie.douban.com/subject/27068596/celebrities'
# headers = {
#     "Host": "movie.douban.com",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#     "Referer": "https://movie.douban.com/subject/27068596/",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "zh-CN,zh;q=0.9",
# }
# res = requests.get(url, headers=headers, proxies=real_proxy).text
# # print(res)
# # print(type(res))
#
# con = etree.HTML(res)
# cons = con.xpath('//li[@class="celebrity"]/a')
# for con1 in cons:
#     name = con1.xpath('./@title')[0]
#     link = con1.xpath('./@href')[0]
#     id = link[-8:].replace('/', '')
#     id1 = re.search(r'(\d+)', link).group(1)
#     print(name, link, id1)

# # 通过id获取个人图片链接
# url = 'https://movie.douban.com/celebrity/1018604/photos/?type=C&start=0&sortby=like&size=a&subtype=a'
# headers = {
#     "Host": "movie.douban.com",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#     "Referer": "https://movie.douban.com/celebrity/1018604/photos/",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "zh-CN,zh;q=0.9"
# }
# res = requests.get(url, headers=headers, proxies=real_proxy).text
# # print(res)
#
# con = etree.HTML(res)
# cons = con.xpath('//ul[@class="poster-col3 clearfix"]/li//img/@src')
# print(cons)
# print(len(cons))