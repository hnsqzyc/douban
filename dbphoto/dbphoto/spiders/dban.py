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
    name = 'dban'

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
        res = self.user_ids.find({'status': 0}).limit(100)
        if res.count():
            for info in res:
                user_id = info.get('user_id')

                # 请求的时候把状态修改为1, 说明已经请求过了
                con = self.user_ids.update({'user_id': user_id}, {'$set': {'status': 1}})

                page = 0
                url = 'https://movie.douban.com/celebrity/{}/partners?start={}'
                meta = {}
                header = {
                    "Host": "movie.douban.com",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Referer": "https://movie.douban.com/celebrity/%s/" % (user_id),
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9"
                }

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

        cons = response.xpath('//div[@class="partners item"]')

        page_num_counts = response.xpath('//div//span[@class="count"]/text()')[0].extract()
        page_num_countss = re.findall(r'(\d+)', page_num_counts)[0]
        page_num_count = int(int(page_num_countss) / 10) + 1
        print('人员链接页面数量 page_num_count: ', page_num_count)

        for con in cons:

            item_tuple = {}
            item_tuple['user_id'] = con.xpath('./@id')[0].extract()
            item_tuple['user_name'] = con.xpath('.//h2/a/text()')[0].extract()
            item_tuple['status'] = 0
            item_tuple['photo_num'] = 0
            item_tuple['img_url_li'] = []
            print(item_tuple['user_id'], item_tuple['user_name'])

            # self.redis_conn.sadd('douban', item_tuple['user_id'])
            if self.user_ids.find_one({'user_id': item_tuple['user_id']}):
                print('数据库已经存在...')
                logging.info('数据库已经存在...')
            else:
                print('数据库不存在, 插入...')
                logging.info('数据库不存在, 插入...')
                item_tuples = item_tuple.copy()
                result = self.user_ids.insert_one(item_tuples)

        meta['page'] = int((meta['page']/10 + 1)) * 10  # 人物链接页面时10

        print('请求第 %s 页' % (int((meta['page']/10 + 1))))
        if int(meta.get('page')) > (page_num_count - 1) * 10:
            logging.warning('请求页数大于页面数量, return')
            return

        yield Request(url=meta['url'].format(meta['user_id'], meta['page']), headers=meta['header'], callback=self.parse_links, meta=meta)
