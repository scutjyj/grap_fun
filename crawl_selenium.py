#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
import os
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

SELENIUM_CHROMEDRIVER_PATH = 'D:\\chromedriver.exe'
TARGET_URL = 'https://www.lagou.com/'
AREA = u'广州站'
POSITION_KEYWORD = u'腾讯'
HTML_DIR = os.path.join(os.getcwd(), POSITION_KEYWORD)
if not os.path.exists(HTML_DIR):
    os.mkdir(HTML_DIR)
PAGE_FILE_NAME = '{page_number}.html'


def save_html_files(client, page_number):
    with open(os.path.join(HTML_DIR, PAGE_FILE_NAME.format(page_number=page_number)), 'wb') as fp:
        fp.write(client.page_source.encode('utf-8'))


def crawl_with_selenium():
    client = webdriver.Chrome(SELENIUM_CHROMEDRIVER_PATH)
    client.get(TARGET_URL)
    client.find_element_by_link_text(AREA).click()
    client.find_element_by_id('search_input').send_keys(POSITION_KEYWORD)
    client.find_element_by_id('search_button').click()
    page_number = 10
    #print type(client.page_source)
    save_html_files(client, page_number)

    while True:
        page_number += 1
        try:
            time.sleep(3)
            client.find_element_by_class_name('pager_next_disabled').click()
        except:
            try:
                #client.find_element_by_class_name('pager_next ').click()
                client.find_element_by_css_selector('div.s_position_list div.item_con_pager div.pager_container span.pager_next').click()
            except Exception as e:
                print e
                print 'get page {page_number} failed...'.format(page_number=page_number)
                break
            else:
                save_html_files(client, page_number)
        else:
            break
    time.sleep(5)
    client.close()


class ChromeConsoleLogging(object):
    def __init__(self):
        self.driver = None

    def setUp(self):
        desired = DesiredCapabilities.CHROME
        desired['loggingPrefs'] = {'browser': 'ALL'}
        self.driver = webdriver.Chrome(SELENIUM_CHROMEDRIVER_PATH, desired_capabilities=desired)

    def analyzeLog(self):
        for entry in self.driver.get_log('browser'):
            print entry

    def testMethod(self):
        self.setUp()
        self.driver.get('https://www.lagou.com/jobs/list_python?px=default&city=%E5%B9%BF%E5%B7%9E#filterBox')
        self.analyzeLog()


if __name__ == '__main__':
    crawl_with_selenium()
    #ccl = ChromeConsoleLogging()
    #ccl.testMethod()
