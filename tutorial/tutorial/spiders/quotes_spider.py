#!/usr/bin/env python
# coding: utf-8
import scrapy
import json
import os
import urllib
import time
import datetime
from selenium import webdriver
import mysql.connector

SELENIUM_CHROMEDRIVER_PATH = 'D:\\chromedriver.exe'

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'lagou',
    'use_unicode': True
}

TABLE_NAME = 'lagou_position'

FIANANCE_STAGE = {
    u'\u672a\u878d\u8d44': '0',
    u'\u5929\u4f7f\u8f6e': '1',
    u'A\u8f6e': '2',
    u'B\u8f6e': '3',
    u'C\u8f6e': '4',
    u'D\u8f6e\u53ca\u4ee5\u4e0a': '5',
    u'\u4e0a\u5e02\u516c\u53f8': '6',
    u'\u4e0d\u9700\u8981\u878d\u8d44': '7'
}

EDUCATION = {
    u'\u4e0d\u9650': '0',
    u'\u5927\u4e13': '1',
    u'\u672c\u79d1': '2',
    u'\u7855\u58eb': '3',
    u'\u535a\u58eb': '4'
}


EXPERIENCE = {
    u'\u7ecf\u9a8c\u4e0d\u9650': '0',
    u'\u7ecf\u9a8c\u5e94\u5c4a\u6bd5\u4e1a\u751f': '1',
    u'\u7ecf\u9a8c1\u5e74\u4ee5\u4e0b': '2',
    u'\u7ecf\u9a8c1-3\u5e74': '3',
    u'\u7ecf\u9a8c3-5\u5e74': '4',
    u'\u7ecf\u9a8c5-10\u5e74': '5',
    u'\u7ecf\u9a8c10\u5e74\u4ee5\u4e0a': '6'

}


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    """
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
    ]
    """

    # the start_urls above is the shortcut of start_requests.
    def start_requests(self):
        url = 'http://quotes.toscrape.com/'
        tag = getattr(self, 'tag', None)
        if tag is not None:
            url = url + 'tag/' + tag
        yield scrapy.Request(url, self.parse)
        #for url in urls:
        #    yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        """
        page = response.url.split('/')[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
        """
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').extract_first(),
                'author': quote.css('small.author::text').extract_first(),
                #'tags': quote.css('div.tags a.tag::text').extract(),
            }
        """
        next_page = response.css('li.next a::attr(href)').extract_first()
        if next_page is not None:
            #next_page = response.urljoin(next_page)
            #yield scrapy.Request(url=next_page, callback=self.parse)
            
            # using shortcut:response.follow
            yield response.follow(next_page, callback=self.parse)
        """

        """
        for href in response.css('li.next a::attr(href)'):
            yield response.follow(href, callback=self.parse)
        """

        # simpler way.
        for a in response.css('li.next a'):
            yield response.follow(a, callback=self.parse)


class AuthorSpider(scrapy.Spider):
    name = 'author'

    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        for href in response.css('.author + a::attr(href)'):
            yield response.follow(href, self.parse_author)

        for href in response.css('li.next a::attr(href)'):
            yield response.follow(href, self.parse)

    def parse_author(self, response):
        def extract_with_css(query):
            return response.css(query).extract_first().strip()

        yield {
            'name': extract_with_css('h3.author-title::text'),
            'birthdate': extract_with_css('.author-born-date::text'),
            'bio': extract_with_css('.author-description::text'),
        }


class ToScrapeSpiderXPath(scrapy.Spider):
    name = 'toscrape-xpath'

    start_urls = [
        'http://quotes.toscrape.com/',
    ]

    def parse(self, response):
        for quote in response.xpath('//div[@class="quote"]'):
            yield {
                'text': quote.xpath('./span[@class="text"]/text()').extract_first(),
                'author': quote.xpath('.//small[@class="author"]/text()').extract_first(),
                'tags': quote.xpath('.//div[@class="tags"]/a[@class="tag"]/text()').extract(),
            }
        next_page_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))


class LagouSpider(scrapy.Spider):
    name = 'lagou_old'

    start_urls = [
        #'https://www.lagou.com/jobs/list_python?px=default&city=%E5%B9%BF%E5%B7%9E#filterBox',
        'https://www.lagou.com'
    ]

    cookie_dict = {}

    city = '%E5%B9%BF%E5%B7%9E'

    json_api = 'https://www.lagou.com/jobs/positionAjax.json?px=default&city={city}&needAddtionalResult=false'.format(
        city=city
    )

    approve_url = 'https://www.lagou.com/c/approve.json?companyIds={company_ids}'

    result_dir = os.path.join(os.getcwd(), 'result')

    formdata = {
        'first': 'true',
        'pn': '1',
        'kd': 'python',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_index, meta={'cookiejar': True})

    def parse_index(self, response):
        """
        from scrapy.http.cookies import CookieJar
        cookie_jar = CookieJar()
        cookie_jar.extract_cookies(response, response.request)
        print "cookie_jar._cookies", cookie_jar._cookies
        for k, v in cookie_jar._cookies.items():
            for i, j in v.items():
                for m, n in j.items():
                    self.cookie_dict[m] = n.value
        print "cookie_dict:", self.cookie_dict
        """

        yield scrapy.FormRequest(url=self.json_api, callback=self.parse_json, formdata=self.formdata)

    def parse_json(self, response):
        json_body = json.loads(response.body)
        #print json_body
        if not json_body['success']:
            print 'the website reject your request.'
            print json_body
            return

        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        json_path = os.path.join(self.result_dir, 'lagou_gz_no_cookie.json')
        with open(json_path, 'wb') as fp:
            fp.write(response.body)
        # extract the needed data.
        rst = json_body['content']['positionResult']['result']
        result_path = os.path.join(self.result_dir, 'result.txt')
        cp_list = []
        with open(result_path, 'a+b') as fp:
            for r in rst:
                l = []
                l.append(r.get('companyShortName', 'null'))
                l.append(r.get('salary', 'null'))
                l.append(r.get('companySize', 'null'))
                l.append(r.get('financeStage', 'null'))
                #l.append(r.get('district', 'null'))
                l.append(r['district'] if r['district'] else 'null')
                l.append(r.get('workYear', 'null'))
                l.append(str(r.get('positionId', 0)))
                cp_list.append(str(r.get('companyId', 0)))
                if l:
                    print l
                    line = '\t'.join(l)+'\n'
                fp.write(line.encode('utf-8'))

        # handle next page.
        page_num = json_body['content']['pageNo']
        page_size = json_body['content']['pageSize']
        total_count = json_body['content']['positionResult']['totalCount']
        print page_num, page_size, total_count
        if page_num <= total_count / page_size:
            self.formdata['first'] = 'false'
            self.formdata['pn'] = str(int(page_num)+1)
            print self.formdata
            #time.sleep(10)

            yield scrapy.FormRequest(url=self.json_api, callback=self.parse_json, formdata=self.formdata,
                                     headers={
                    'Referer': 'https://www.lagou.com/jobs/list_python?px=default&city=%E5%B9%BF%E5%B7%9E',
                    'x-requested-with': 'XMLHttpRequest',
                })
            """
            # request the approve.json
            company_ids = urllib.quote(','.join(cp_list))
            print cp_list
            print self.approve_url.format(company_ids=company_ids)
            yield scrapy.Request(url=self.approve_url.format(company_ids=company_ids), callback=self.parse_next,
                                 headers={'Referer': 'https://www.lagou.com/jobs/list_python?px=default&city=%E5%B9%BF%E5%B7%9E',
                                          'x-requested-with': 'XMLHttpRequest'})
            """

    def parse_next(self, response):
        print response.request.headers
        print json.loads(response.body)
        yield scrapy.FormRequest(url=self.json_api, callback=self.parse_json, formdata=self.formdata)


class LagouSeleniumSpider(scrapy.Spider):
    name = 'lagou'

    def __init__(self):
        self.AREA = u'广州站'
        self.POSITION_KEYWORD = u'网易游戏'
        self.browser = webdriver.Chrome(SELENIUM_CHROMEDRIVER_PATH)
        self.browser.set_page_load_timeout(30)
        self.lines = []
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.file_name = os.path.join(os.getcwd(), u'{kw}_{ts}.txt'.format(kw=self.POSITION_KEYWORD,
                                                                           ts=self.timestamp)).encode('utf-8')
        self.pos_desc = {}
        self.pos_id_list = []

    start_urls = [
        'https://lagou.com/'
    ]

    def closed(self, spider):
        """
        rec_sum = len(self.lines)
        i = 0
        while i < rec_sum:
            self.lines[i].append(self.pos_desc[self.lines[i][0]]['location'])
            self.lines[i].append(self.pos_desc[self.lines[i][0]]['description'])
            i += 1
        """

        # now comes the last page.we can write the self.lines into file.
        with open(self.file_name, 'wb') as fp:
            for line in self.lines:
                _line = '\t'.join(line) + '\n'
                fp.write(_line.encode('utf-8'))
        # load the file into mysql.
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
        except Exception as e:
            print 'can not connect to mysql: %s' % e
        else:
            cursor = conn.cursor()
            # clear the data of the table at first.
            _sql = """DELETE FROM {tb} WHERE keyword='{keyword}';"""
            cursor.execute(_sql.format(tb=TABLE_NAME, keyword=self.POSITION_KEYWORD.encode('utf-8')))
            conn.commit()
            # load new data into table.
            _sql = """LOAD DATA INFILE "{file_name}" REPLACE INTO TABLE `{tb}` CHARACTER SET utf8 FIELDS TERMINATED BY '\t'
                       LINES TERMINATED BY '\n' (positionId, companyShortName, salaryRange, district, financeStage, experience,
                       education, createTime, companyId, hrId, keyword, city, salaryLow, salaryHigh,
                       createTimestamp, positionName);"""
            print _sql.format(file_name=self.file_name.replace('\\', '\\\\'), tb=TABLE_NAME)
            cursor.execute(_sql.format(file_name=self.file_name.replace('\\', '\\\\'), tb=TABLE_NAME))
            conn.commit()

            # set the position description and location.
            _sql = """UPDATE `{tb}` SET location='{location}', description='{description}' WHERE positionId = {pos_id};"""
            rec_sum = len(self.lines)
            i = 0
            while i < rec_sum:
                location = self.pos_desc[self.lines[i][0]]['location']
                description = self.pos_desc[self.lines[i][0]]['description']
                sql = _sql.format(tb=TABLE_NAME, location=location.encode('utf-8'),
                                  description=description.encode('utf-8'),
                                  pos_id=self.lines[i][0])
                print sql
                cursor.execute(sql)
                i += 1
            conn.commit()
            cursor.close()
            conn.close()
        print 'spider closed.'
        self.browser.close()

    def parse(self, response):
        """
        extract the data that we want, handle the next page and save the data into file or database.
        besides the way shown below ,we can extract part of the data using:
        "response.css('li.con_list_item::attr(data-positionname)').extract()"
        :param response:
        :return:
        """
        # extract the data that we want.
        positionName = response.css('div.p_top h3::text').extract()
        salary = response.css('span.money::text').extract()
        company = response.css('div.company_name a::text').extract()
        _financeStage = response.css('div.industry::text').extract()
        financeStage = [FIANANCE_STAGE[i.strip().split('/')[1].strip()] for i in _financeStage]
        _experienceEducation = response.css('div.p_bot div.li_b_l::text').extract()
        experience = []
        education = []
        for e in _experienceEducation:
            if e.strip():
                ee = e.strip().split('/')
                experience.append(EXPERIENCE[ee[0].strip()])
                education.append(EDUCATION[ee[1].strip()])
        district = response.css('span.add em::text').extract()
        _companyId = response.css('div.company_name a::attr(href)').extract()
        companyId = [i.split('/')[-1].split('.')[0] for i in _companyId]
        # the url of the company is like: https://www.lagou.com/gongsi/{companyId}.html
        print _companyId[0]
        _positionId = response.css('div.p_top a::attr(href)').extract()
        positionId = [i.split('/')[-1].split('.')[0] for i in _positionId]
        _createTime = response.css('span.format-time::text').extract()
        createTime = [i.strip(u'\u53d1\u5e03') for i in _createTime]
        hrId = response.css('input.target_hr::attr(value)').extract()
        position_total_count = response.css('div.tab-wrapper a.active span::text').extract_first()
        print 'the total count of this position is: ', position_total_count
        current_page_num = response.css('div.s_position_list div.item_con_pager span.pager_is_current::text').extract_first().strip()
        _page_not_current = response.css('div.item_con_pager span.pager_not_current::text').extract()
        page_not_current = [i.strip() for i in _page_not_current]

        # transform the time string to timestamp.
        create_timestamp = []
        for t in createTime:
            if t.find(':') != -1:
                # if time string format is: 08:10.
                now_date = time.strftime('%Y-%m-%d %H:%M:%S').split()
                t_str = '{now_date} {time}:00'.format(now_date=now_date[0], time=t)
                create_timestamp.append(int(time.mktime(time.strptime(t_str, '%Y-%m-%d %H:%M:%S'))))
            elif t.find('-') != -1:
                # if time string format is: 2018-07-14.
                t_str = '{now_date} 00:00:00'.format(now_date=t)
                create_timestamp.append(int(time.mktime(time.strptime(t_str, '%Y-%m-%d %H:%M:%S'))))
            else:
                day_delta = int(t.rstrip(u'\u5929\u524d'))
                now_time = datetime.datetime.now() - datetime.timedelta(days=day_delta)
                create_timestamp.append(int(time.mktime(time.struct_time(now_time.timetuple()))))

        # save the extracted data into file or database.
        #time.sleep(10)
        page_size = len(company)
        i = 0
        while i < page_size:
            #print company[i], salary[i], district[i], financeStage[i], experienceEducation[i]
            """
            _line = ','.join([positionId[i], company[i], salary[i], district[i], financeStage[i], experience[i],
                              education[i], createTime[i], companyId[i], hrId[i], self.POSITION_KEYWORD, 'guangzhou',
                             salary[i].split('-')[0].strip()[:-1], salary[i].split('-')[1].strip()[:-1],
                              str(create_timestamp[i]), positionName[i],
                              self.pos_desc[positionId[i]]['location'],
                              self.pos_desc[positionId[i]]['description']]) + '\n'
            """
            _line = [positionId[i], company[i], salary[i], district[i], financeStage[i], experience[i],
                     education[i], createTime[i], companyId[i], hrId[i], self.POSITION_KEYWORD, 'guangzhou',
                     salary[i].split('-')[0].strip()[:-1], salary[i].split('-')[1].strip()[:-1],
                     str(create_timestamp[i]), positionName[i]]
            #print _line
            #self.lines.append(_line.encode('utf-8'))
            self.lines.append(_line)
            self.pos_id_list.append(positionId[i])
            i += 1
        print current_page_num
        # handle next page.
        if int(current_page_num) < int(page_not_current[-1]):
            # it is not the last page,just yield the request.
            yield scrapy.Request(url='{url}{pn}'.format(url=self.start_urls[0], pn=str(int(current_page_num)+1)),
                                 callback=self.parse)
        else:
            # get the position description.
            for p in self.pos_id_list:
                url = 'https://www.lagou.com/jobs/{p_id}.html'.format(p_id=p)
                yield scrapy.Request(url=url, callback=self.parse_description)

    def parse_description(self, response):
        pos_dict = {}
        positon_id = response.request.url.split('/')[-1].split('.')[0]
        try:
            pos_desc_list = response.css('dd.job_bt p::text').extract()
            #pos_dict['description'] = '\r\n'.join(pos_desc_list)
            # handle the space problem about '\xa0' when the default encoding of terminal is gbk.
            pos_dict['description'] = ''.join('\r\n'.join(pos_desc_list).split(u'\xa0'))
        except Exception as e:
            print 'get description failed: ', e
            pos_dict['description'] = ''
        try:
            pos_list = response.css('div.work_addr a::text').extract()[:-1]
            pos_list.append(response.css('div.work_addr::text').extract()[-2].strip().split()[-1])
            pos_dict['location'] = '-'.join(pos_list)
        except Exception as e:
            print 'get location failed: ', e
            pos_dict['location'] = ''
        self.pos_desc[positon_id] = pos_dict
