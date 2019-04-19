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
        # while 1:
        # 注意页面乘积数, 有可能在变动
        res = self.user_ids.find({'status': 1}).limit(1)
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

        # 照片数量
        try:
            photo_num_counts = response.xpath('//span[@class="count"]/text()')[0].extract()  # Wrong 袁和平(当图片数量只有一页的时候不会显示图片数量)
            img_num = re.findall(r'(\d+)', photo_num_counts)[0]
            print('人员链接页面数量 photo_num: ', img_num)
            # 把图片数量插入数据库
            # self.user_ids.update({'user_id': meta['user_id']}, {'$set': {'photo_num': int(img_num)}})

            # 页面数量
            page_num = response.xpath('//div[@class="paginator"]/a/text()')[-1].extract()
            print(page_num)

            # 照片链接
            photo_links = response.xpath('//div[@class="article"]/ul/li//img/@src').extract()
            for photo_url in photo_links:
                print(photo_url)
                # TODO 下载图片, 把状态下载完成后把状态修改为2

            meta['page'] = int((meta['page'] / 10 + 1)) * 30  # 人物链接页面时30

            print('请求第 %s 页' % (int((meta['page'] / 10 + 1))))
            if int(meta.get('page')) > (page_num - 1) * 10:  # Wrong
                logging.warning('请求页数大于页面数量, return')
                return

            yield Request(url=meta['url'].format(meta['user_id'], meta['page']), headers=meta['header'],
                          callback=self.parse_links, meta=meta)
        except IndexError:
            print('人员可能没有图片...')

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
