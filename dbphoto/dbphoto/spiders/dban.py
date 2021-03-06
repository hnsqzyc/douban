# -*- coding: utf-8 -*-
import scrapy
import json
import re
import logging
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
        while 1:
            # 注意页面乘积数, 有可能在变动
            res = self.user_ids.find({'status': 0}).limit(100)
            if res.count():
                for info in res:
                    user_id = info.get('user_id')
                    user_name = info.get('user_name')

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
                    meta['user_name'] = user_name

                    yield Request(url=url.format(user_id, page), headers=header, callback=self.parse_links, meta=meta)

            else:
                logging.warning('用户id采集完毕, return...')
                return

    def parse_links(self, response):

        meta = response.request.meta
        # print('response', response.text)

        cons = response.xpath('//div[@class="partners item"]')

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

        # # 统计页面数量,不足一页的时候就会报错
        # page_num_counts_1 = response.xpath('//div//span[@class="count"]/text()')  # https://movie.douban.com/celebrity/1327320/partners
        # if cons and page_num_counts_1:
        #     global page_num_count
        #     page_num_counts = page_num_counts_1[0].extract()
        #     page_num_countss = re.findall(r'(\d+)', page_num_counts)[0]
        #     page_num_count = int(int(page_num_countss) / 10) + 1
        #     print('人员链接页面数量 page_num_count: ', page_num_count)
        # elif cons:
        #     page_num_count = 1
        #     logging.info('人员链接页面数量 page_num_count: 为1')
        # else:
        #     page_num_count = 0
        #     logging.warning('人员链接页面数量 page_num_count: 为空...')

        # 页面数量
        page_nums = response.xpath('//div[@class="paginator"]/a/text()')

        # 如果有图片链接并且页面链接不为空
        if cons and page_nums:
            global page_num
            page_num = int(page_nums[-1].extract())
            print('人员图片页面数量page_num: ', meta['user_name'], page_num)
        elif cons:
            page_num = 0
        else:
            page_num = -1

        if page_num > 1:
            meta['page'] = int((meta['page']/10 + 1)) * 10  # 人物链接页面时10

            print('请求第 %s 页' % (int((meta['page']/10 + 1))))
            if int(meta.get('page')) > (page_num - 1) * 10:
                logging.warning('请求页数大于页面数量, return')
                return

            yield Request(url=meta['url'].format(meta['user_id'], meta['page']), headers=meta['header'], callback=self.parse_links, meta=meta)
