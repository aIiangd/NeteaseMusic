# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from lxml import etree
import time


def get_html(page):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'}
    url = 'http://www.xicidaili.com/nn/%d' % page
    return requests.get(url, headers=headers).content

'''
def parse_html(html):
    iplist = []
    soup = BeautifulSoup(html, 'lxml')
    trlist = soup.find_all('tr')
    for tr in trlist[1:]:
        tdlist = tr.find_all('td')
        ip = tdlist[1].text.strip()
        port = tdlist[2].text.strip()
        iplist.append(ip + ":" + port)
    return iplist
'''


def parse_html(content):
    iplist = []
    html = etree.HTML(content)
    ip_elems = html.xpath('//*[@id="ip_list"]//tr/td[position()<4 and position()>1]')
    for index in range(0, len(ip_elems), 2):
        iplist.append(ip_elems[index].text + ":" + ip_elems[index+1].text)
    return iplist


def test_proxy(proxylist):
    print 'start to test proxies:%d' % + len(proxylist)
    for proxy in proxylist:
        proxies = {'https': 'https://' + proxy}
        try:
            requests.get('https://www.baidu.com', proxies=proxies, timeout=2)
        except:
            print proxy + ',false'
        else:
            print proxies
            return proxies['https']
    return None


def get_proxy():
    proxy = None
    start = time.time()
    for page_index in range(1, 5):
        proxylist = parse_html(get_html(page_index))
        proxy = test_proxy(proxylist)
        if proxy is not None:
            break
    end = time.time()
    print "Running time:{}s".format(end-start)
    return proxy


if __name__ == '__main__':
    get_proxy()
