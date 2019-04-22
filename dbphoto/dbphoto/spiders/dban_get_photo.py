# -*- coding: utf-8 -*-
import scrapy
import scrapy
import json
import re
import os
import csv
import codecs
import copy
import hashlib
import time
import logging
from urllib import parse
from random import choice
from scrapy import signals
from scrapy.item import Item, Field
from scrapy.http import Request, FormRequest
from scrapy.utils.project import get_project_settings
from dbphoto.connection import RedisConnection, MongodbConnection

settings = get_project_settings()


class UniversalRow(Item):
    # This is a row wrapper. The key is row and the value is a dict
    # The dict wraps key-values of all fields and their values
    row = Field()
    table = Field()
    image_urls = Field()


class DbanSpider(scrapy.Spider):
    name = 'dban_get_photo'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(DbanSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)

        return spider

    def __init__(self, params, *args, **kwargs):
        super(DbanSpider, self).__init__(self.name, *args, **kwargs)
        # dispatcher.connect(self.spider_closed, signals.spider_closed)
        paramsjson = json.loads(params)
        self.remote_resource = paramsjson.get('remote_resource', True)
        self.enable_proxy = paramsjson.get('enable_proxy', True)

    def spider_opened(self, spider):
        logging.info("爬取开始了...")

        self.redis_conn = RedisConnection(settings['REDIS']).get_conn()
        self.mongo_conn = MongodbConnection(settings['MONGODB']).get_conn()
        self.db = self.mongo_conn.douban
        self.user_ids = self.db.user_ids

    def spider_closed(self, spider):
        logging.info('爬取结束了...')

    def start_requests(self):
        while 1:
            # 注意页面乘积数, 有可能在变动
            res = self.user_ids.find({'status': 0}).limit(1)
            if res.count():
                for info in res:
                    user_id = info.get('user_id')

                    # 请求的时候把状态修改为1, 说明已经请求过了
                    con = self.user_ids.update({'user_id': user_id}, {'$set': {'status': 2}})

                    page = 0
                    url = 'https://movie.douban.com/celebrity/{}/photos/?type=C&start={}&sortby=like&size=a&subtype=a'

                    header = {
                        "Host": "movie.douban.com",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Referer": "https://movie.douban.com/celebrity/%s/photos/" % (user_id),
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "zh-CN,zh;q=0.9"
                    }

                    meta = {}

                    meta['page'] = 0
                    meta['url'] = url
                    meta['header'] = header
                    meta['user_id'] = user_id

                    yield Request(url=url.format(user_id, page), headers=header, callback=self.parse_links, meta=meta)

            else:
                logging.warning('用户id采集完毕, return...')
                return

    def parse_links(self, response):

        meta = response.request.meta
        # print('response', response.text)

        # 照片链接
        photo_links = response.xpath('//div[@class="article"]/ul/li//img/@src').extract()

        # 如果照片链接存在
        if photo_links:
            for img_url in photo_links:
                print(img_url)

                # TODO 下载图片, 把状态下载完成后把状态修改为2
                img_id = re.search(r'p(\d+).webp', img_url).group(1)
                head = re.search(r'https://(.*?)/', img_url).group(1)
                header = {
                    "Host": head,
                    "Connection": "keep-alive",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://movie.douban.com/celebrity/{}/photo/{}/".format(meta['user_id'], img_id),
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9"
                }

                if not os.path.exists(settings['DATA_DIR'] + str(meta['user_id'])):
                    os.mkdir(settings['DATA_DIR'] + str(meta['user_id']))
                save_location = os.path.join(settings['DATA_DIR'], str(meta['user_id']))

                file_name = os.path.join(save_location, str(img_id) + '.jpg')

                meta['file_name'] = file_name
                logging.info(meta['file_name'])
                logging.info('正在下载:' + file_name)
                yield Request(url=img_url, headers=header, callback=self.download_image, meta=meta, priority=10)

            logging.info('下载图片完成后修改Uid状态为2...')
            # result = self.user_ids.update({'realUid': meta['user_id']}, {'$set': {'status': 2}})

        # 照片数量
        if meta['page'] == 0: # 如果页面数量不是0, 就不再请求照片数量
            photo_num_counts = response.xpath('//span[@class="count"]/text()')  # Wrong 袁和平(当图片数量只有一页的时候不会显示图片数量)

            # 如果有图片链接并且图片数量不为空
            if photo_links and photo_num_counts:
                photo_num_co = photo_num_counts[0].extract()
                img_num = re.findall(r'(\d+)', photo_num_co)[0]
                print('人员照片数量 photo_num: ', img_num)
            elif photo_links:
                img_num = len(photo_links)
                print('人员照片数量 photo_num: ', img_num)
            else:
                img_num = 0

            # 把图片数量插入数据库
            self.user_ids.update({'user_id': meta['user_id']}, {'$set': {'photo_num': int(img_num)}})

        # 页面数量
        page_nums = response.xpath('//div[@class="paginator"]/a/text()')

        # 如果有图片链接并且页面链接不为空
        if photo_links and page_nums:
            global page_num
            page_num = page_nums[-1].extract()
            print('人员图片页面数量page_num: ', page_num)
        elif photo_links:
            page_num = 0
        else:
            page_num = -1

        if int(page_num) > 1:
            meta['page'] = int((meta['page'] / 30 + 1)) * 30  # 人物链接页面是30

            print('请求第 %s 页' % (int((meta['page'] / 30 + 1))))
            if int(meta.get('page')) > 0 or int(meta.get('page')) > (int(page_num) - 1) * 30:  # 大于页面数量或者大于1000张
                logging.warning('请求页数大于页面数量, return')
                return

            yield Request(url=meta['url'].format(meta['user_id'], meta['page']), headers=meta['header'],
                          callback=self.parse_links, meta=meta)

    def download_image(self, response):
        meta = response.request.meta
        res = response.body
        try:
            with open(meta['file_name'], 'wb') as f:
                f.write(res)
                f.close()
            logging.info('已经下载...')
        except FileNotFoundError:
            logging.warning('捕捉到文件名有误...')
