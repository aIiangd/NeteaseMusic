# -*- coding: utf-8 -*-
import os
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time
import codecs
import pymongo
import random


def init_db():
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['netease']
    return db['songs_info1']


def find_song_from_db(collection):
    url_list = []
    for song_info in collection.find():
        url_list.append(song_info['url'])
    return url_list


def collect_one_song_by_url(browser, url):
    browser.get(url)
    browser.maximize_window()
    time.sleep(random.uniform(1.5, 2.5))

    browser.switch_to.frame('contentFrame')
    collection_elem = browser.find_element_by_xpath('//*[@id="content-operation"]/a[3]/i')
    collection_elem.click()
    time.sleep(random.uniform(1.5, 2.5))
    # with codecs.open('page_source.txt', 'w', encoding='utf-8') as fp:
    #     fp.write(browser.page_source)

    my_song_folders = browser.find_elements_by_xpath('//a[@class="s-fc0"]')
    if len(my_song_folders) > 1:
        # print my_song_folders[1].text
        action_chains = ActionChains(browser)
        action_chains.move_to_element(my_song_folders[1])
        action_chains.click(my_song_folders[1])
        action_chains.perform()
        return True
    else:
        return False


def collect_songs():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    userdata_dir = r"C:\Users\admin_ld\AppData\Local\Google\Chrome\User Data1"
    options.add_argument("user-data-dir=" + os.path.abspath(userdata_dir))
    browser = webdriver.Chrome(chrome_options=options)

    url_list = find_song_from_db(init_db())
    url_set = set(url_list)
    print u'开始收藏歌曲，共' + str(len(url_set)) + u'首'
    for song_url in url_set:
        if collect_one_song_by_url(browser, song_url):
            print song_url + u'，已收集'
        else:
            print song_url + u'，未收集，需付费'


if __name__ == '__main__':
    collect_songs()
