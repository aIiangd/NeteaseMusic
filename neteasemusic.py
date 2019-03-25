# -*- coding: utf-8 -*-

import requests
from requests.exceptions import ConnectTimeout, ProxyError
from lxml import etree
import time
from getproxy import get_proxy
from Crypto.Cipher import AES
import base64
import json
import pymongo
from multiprocessing import Process

target_url = 'https://music.163.com/discover/playlist/'
headers = {
    'Referer': 'https://music.163.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/73.0.3683.75 Safari/537.36'
}
param_list = [{'order': 'hot', 'cat': '华语', 'limit': '35', 'offset': ''},
              {'order': 'hot', 'cat': '流行', 'limit': '35', 'offset': ''},
              {'order': 'hot', 'cat': '民谣', 'limit': '35', 'offset': ''},
              {'order': 'hot', 'cat': '榜单', 'limit': '35', 'offset': ''}]

collections = ['songs_info1', 'songs_info2', 'songs_info3', 'songs_info4']
proxies = {'https': 'https://171.41.80.191:9998'}


def init_db(col_name):
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['netease']
    return db[col_name]


def update_proxy(proxies):
    proxies['https'] = get_proxy()


def my_get_request(url, params=None, **kwargs):
    retry_cnt = 0
    while retry_cnt < 5:
        try:
            #print proxies
            response = requests.get(url, params, **kwargs)
            return response
        except ConnectTimeout:
            update_proxy(proxies)
        except ProxyError:
            #print 'update proxy and request again..'
            update_proxy(proxies)
        finally:
            retry_cnt += 1


def my_post_request(url, data=None, json=None, **kwargs):
    retry_cnt = 0
    while retry_cnt < 5:
        try:
            response = requests.post(url, data, json, **kwargs)
            return response
        except ConnectTimeout:
            update_proxy(proxies)
        except ProxyError:
            #print 'update proxy and request again..'
            update_proxy(proxies)
        finally:
            retry_cnt += 1


def AES_encrypt(key, text):
    iv = '0102030405060708'
    pad = 16 - len(text) % 16
    text += pad * chr(pad)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    encrypt_text = encryptor.encrypt(text)
    encrypt_text = base64.b64encode(encrypt_text)
    return encrypt_text


def get_params(pagenumber, count):
    pagenumber = (pagenumber-1)*20
    first_param = "{ rid: \"R_SO_4_418603077\", offset: "+str(pagenumber)+", total: \"false\", " \
                                                                          "limit: "+str(count)+", csrf_token: \"\" }"
    forth_param = "0CoJUm6Qyw8W8jud"
    first_key = forth_param
    second_key = 'nienienienienien'
    h_encText = AES_encrypt(first_key, first_param)
    h_encText = AES_encrypt(second_key, h_encText)
    return h_encText


def get_encseckey():
    encseckey = "6469da86a183fc2fc9df65ac98f67138c8d3048d0626714fe646ecb564d4f8cd386a9c9618bb8a4f2929e50ba32e8991" \
                "266aba783975e39cc7cf8a61cc3ba76c81c64a3414f38d604ca1bf9f4647c29cd92d5b362eff15cf7bb1e3a52df798a5" \
                "2aafac2f09420a68af9686e2c1a294ccf426b5aac64899486011fc7eca8e79b8"
    return encseckey


def get_number_of_song_comments(id_str):
    url = "http://music.163.com/weapi/v1/resource/comments/R_SO_4_" + str(id_str) + "?csrf_token="
    data = {'params': get_params(1, 1), 'encSecKey': get_encseckey()}
    response = my_post_request(url, headers=headers, data=data, proxies=proxies, timeout=2)
    comments_json = json.loads(response.content)
    if 'total' in comments_json:
        return int(comments_json['total'])
    else:
        return 0


def get_song_hrefs(url):
    response = my_get_request(url, headers=headers, proxies=proxies, timeout=2)
    #print response.text
    html = etree.HTML(response.content)
    song_href_list = html.xpath('//*[@id="song-list-pre-cache"]/ul//li/a/@href')
    song_name_list = html.xpath('//*[@id="song-list-pre-cache"]/ul//li/a/text()')
    for (href, name) in zip(song_href_list, song_name_list):
        #print href, name
        yield 'https://music.163.com' + href


def get_song_folder_hrefs(url, params):
    response = my_get_request(url, params=params, headers=headers, proxies=proxies, timeout=2)
    #print response.status_code
    html = etree.HTML(response.content)
    song_folder_href_list = html.xpath('//*[@id="m-pl-container"]//li/p[1]/a/@href')
    play_cnt_list = html.xpath('//*[@id="m-pl-container"]//li/div/div/span[2]/text()')
    for (href, cnt) in zip(song_folder_href_list, play_cnt_list):
        cnt_str = cnt.replace(u'万', '0000').strip()
        if cnt_str.isdigit():
            cnt_int = int(cnt_str)
        else:
            cnt_int = 0
        if cnt_int > 5000000:   #只取播放量大于500万的歌单
            #print href, cnt, cnt_int
            yield 'https://music.163.com' + href


def find_target_song(url, params, col_name):
    collection = init_db(col_name)
    for page in range(0, 38):
        print "[%s]获取第%d页所有播放量大于500万歌单中..." % (params['cat'], page+1)
        params['offset'] = str(page * 35)
        for folder_url in get_song_folder_hrefs(url, params):
            print folder_url
            for song_url in get_song_hrefs(folder_url):
                #time.sleep(0.5)
                if 100000 < get_number_of_song_comments(song_url.split('=')[1]):
                    print "发现一首评论数大于10万的歌：" + song_url
                    collection.insert_one({'url': song_url})


if __name__ == '__main__':
    for index in range(0, 4):
        process = Process(target=find_target_song, args=(target_url, param_list[index], collections[index]))
        process.start()


