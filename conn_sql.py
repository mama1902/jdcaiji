# -*- coding: utf-8 -*-
import calendar

import mysql.connector
from requests.cookies import RequestsCookieJar

from send_email import SendEmail
import time
import execjs
import requests
import urllib as request
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,NoSuchElementException,JavascriptException
from selenium.webdriver.common.keys import Keys
import json
from config import CONFIG
import os
import sys   #引用sys模块进来，并不是进行sys的第一次加载
reload(sys)  #重新加载sys
sys.setdefaultencoding('utf8')  ##调用setdefaultencoding函数
from logger import logger

class ItemQuery(object):
    conn = mysql.connector.connect(user='root', password='123456', database='m_price')  # static variable
    start_flag = 0  # 记录是否为首轮
    jsobj = execjs.compile(open('rsa.js').read())
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'}

    def __init__(self, brower,cate):
        requests.packages.urllib3.disable_warnings()
        self._session = requests.session()
        self._session.verify = False
        self.brower = brower
        self.cate = cate
        self._session.headers = {
            'Content-Type': 'text/plain; charset=UTF-8',
            'Origin':'https://million-goods.jd.com',
            'Referer':'https://million-goods.jd.com/iStoreFuse/goodsFuse',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        }

        cookies = self.brower.get_cookies()
        jar = RequestsCookieJar()
        for cookie in cookies:
            jar.set(cookie['name'], cookie['value'])
        self._session.cookies = jar

    def cookie_handle(self,cookies):
        """
        cookies 转化为字典函数
        :param cookies: selenium获取的cookies
        """
        dic = {}
        for i in cookies:
            dic[i["name"]] = i["value"]
        return dic
    def read_itemid(self):
        cursor = self.conn.cursor()
        cursor.execute('select item_id from j_cms_addonproduct where cro=1')
        items_inner = cursor.fetchall()
        localtime = time.asctime(time.localtime(time.time()))
        print 'Local Time:', localtime
        print 'All item:', items_inner
        print '----------------------'
        cursor.close()
        return items_inner

    def read_itemid_temp(self):
        cursor = self.conn.cursor()
        cursor.execute('select item_id, user_id, mall_name from monitor where item_price is null and status = 1')
        items_inner = cursor.fetchall()
        localtime = time.asctime(time.localtime(time.time()))
        print 'Local Time:', localtime
        print 'All item:', items_inner
        print '----------------------'
        cursor.close()
        return items_inner

    def write_to_file(self, content):
        # encoding ='utf-8',ensure_ascii =False,使写入文件的代码显示为中文
        with open('result.txt', 'a', encoding='utf-8') as f:
            f.write(json.dumps(content, ensure_ascii=False) + '\n')
            f.close()
    def write_item_info(self, sku, goodsname, price, jdprice,money,img):

        if (CONFIG['DOWNIMG']):
            try:
                dir_name = CONFIG['IMGPATH']
                xyheader = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30 '
                }
                if not os.path.isdir(dir_name):
                    os.makedirs(dir_name)
                file_name = dir_name+sku+'_i.jpg'
                if not os.path.exists(file_name):
                    res = requests.get(img, headers=xyheader)
                    if res.status_code == 404:
                        print("图片{img}下载出错------->")
                    with open(file_name, "wb") as f:
                        f.write(res.content)
                        print("存储路径：" + file_name)

                    #request.urlretrieve(img, file_name)
                img = sku+'_i.jpg'
            except Exception as e:
                print(img+"下载U图片异常", e)
                logger.info(img+"下载U图片异常%s", e)


        cursor = self.conn.cursor()
        try:
            sql = 'select id,item_id,item_price from j_cms_addonproduct where item_id =\'%s\' ' % (sku)
            print 'SQL query: ', sql
            cursor.execute(sql)
            row = cursor.fetchone()
        except mysql.connector.errors.InternalError:
            print '连接异常.'
            return
        datecur = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ts = calendar.timegm(time.gmtime())
        price = price.replace(',', '')
        price = price.replace('--', '')
        jdprice = jdprice.replace(',', '')
        jdprice = jdprice.replace('--', '')
        money = money.replace(',', '')
        money = money.replace('--', '')
        if row:

            sql = 'update j_cms_addonproduct set item_price =  \'%s\',jdprice =  \'%s\',money =  \'%s\' where id = %s ' % (price,jdprice,money,row[0])
            print 'SQL update:', sql.encode('utf-8')  # ascii错误解决，不加的话控制台中文乱码, 记得添加回去
            cursor.execute(sql)
            sql = 'update j_cms_archives set channel_id =  \'%s\',title =  \'%s\',image =  \'%s\',updatetime =  \'%s\' where id = %s ' % (
            self.cate, goodsname, img, ts, row[0])
            cursor.execute(sql)
            if row[2] != price :
                sql = "INSERT INTO j_cms_addonpricehistory (item_id,item_price,add_date,mall_name) VALUES (%s, %s, %s,'jd')"
                val = (sku, price, datecur)
                cursor.execute(sql, val)
            self.conn.commit()
        else :
            sql = "INSERT INTO j_cms_addonproduct (item_id,item_price,jdprice,money,mall_name) VALUES (%s, %s, %s, %s, %s)"
            val = (sku,price,jdprice,money,'jd')
            cursor.execute(sql, val)
            lastrowid = cursor.lastrowid
            sql = "INSERT INTO j_cms_archives (id,user_id,channel_id,model_id,title,image,createtime,updatetime,status) VALUES (%s,1,%s,2,%s, %s, %s, %s, 'normal')"
            val = (lastrowid,self.cate,goodsname, img, ts, ts)
            cursor.execute(sql, val)
            sql = "INSERT INTO j_cms_addonpricehistory (item_id,item_price,add_date,mall_name) VALUES (%s, %s, %s,'jd')"
            val = (sku, price, datecur)
            cursor.execute(sql, val)

            self.conn.commit()
        cursor.close()
    def update_item_info(self, sku, price, jdprice,money):
        cursor = self.conn.cursor()
        sql = 'update j_cms_addonproduct set item_price =  \'%s\',jdprice =  \'%s\',money =  \'%s\'  where item_id = \'%s\' ' % (
        price, jdprice, money, sku)
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()
    def start_monitor(self, break_time, brower,page,cate):
        start = time.time()
        query = ItemQuery(brower,cate)
        """
        url = "https://goods-million.jd.com/sys/shop/getSkus?loginType=102&version=1.0&source=pc&requestId=1649953117625&t=1649953117625&safeTimestamp=1649953117625&safeSignature=2a9b24a8eccda18d57d20ff24834560a&safeSignType=0"
        try:
                data = {
                    "loginType": 102,
                    "version": "1.0",
                    "source": "pc",
                    "requestId": 1649953117625,
                    "t": 1649953117625,
                    "pageIndex": 121,
                    "pageSize": 50,
                    "keyword": "",
                    "category": [],
                    "priceType": 2,
                    "brandId": "",
                    "purchaseType": 0,
                    "prodSource": "",
                    "tags": [],
                    "isNew": "false",
                    "isExclusive": "false",
                    "isHot": "false",
                    "isDiscountCoupon": "false",
                    "tagList": [],
                    "sortField": 2,
                    "sortType": 2,
                    "cates": []
                }
                response = self._session.post(url, json=data)
                exit(response.text)
                data = response.json()

                #if data.get("error"):
        except Exception as e:
            print(e)
            pass
        exit('')
        """
        ic = 1
        if  page > 1:
            s1 = r'//div[@class="pop-page-options-elevator"]/input'
            nextpage = brower.find_element_by_xpath(s1)
            #nextpage.send_keys(page)
            brower.execute_script('document.getElementsByClassName("pop-page-options-elevator")[0].getElementsByTagName("input")[0].value='+bytes(page))
            nextpage.send_keys(Keys.ENTER)
            time.sleep(18)
            ic += 1

        # brower.refresh()
        # brower.switch_to.frame('main-content')

        i = 0
        while i < 22:
            try:
                sku = brower.execute_script('return encodeURIComponent(document.getElementsByClassName("goods-card")['+bytes(i)+'].__vue__.$vnode.data.key)')
                goodsname = brower.execute_script('return encodeURIComponent(document.getElementsByClassName("goods-card")['+bytes(i)+'].getElementsByClassName("title")[0].innerText)')
                price = brower.execute_script('return encodeURIComponent(document.getElementsByClassName("goods-card")['+bytes(i)+'].getElementsByClassName("price-inner")[0].innerText)')
                jdprice = brower.execute_script('return encodeURIComponent(document.getElementsByClassName("goods-card")['+bytes(i)+'].getElementsByClassName("jd-price-money")[0].innerText)')
                money = brower.execute_script('return encodeURIComponent(document.getElementsByClassName("goods-card")['+bytes(i)+'].getElementsByClassName("profit-money")[0].innerText)')
                img = brower.execute_script(
                    'return encodeURIComponent(document.getElementsByClassName("goods-card")[' + bytes(
                        i) + '].getElementsByTagName("img")[0].src)')

                query.write_item_info(self.jsobj.call('decodeURI', sku), self.jsobj.call('decodeURI', goodsname), self.jsobj.call('decodeURI', price), self.jsobj.call('decodeURI', jdprice), self.jsobj.call('decodeURI', money), self.jsobj.call('decodeURI', img))
                # query.compare_send_email(user_id, item_id, item_price, item_name)
                i += 1
                continue
            except NoSuchElementException:
                localtime = time.asctime(time.localtime(time.time()))
                print '元素没有找到.', localtime
                i += 1
                continue
            except JavascriptException:
                logger.info('sku vue节点读取失败')
                i += 1
                break
            except TimeoutException:
                proxy = query.use_proxy()
                localtime = time.asctime(time.localtime(time.time()))
                print '页面请求超时了.', localtime
                i += 1
                continue
            except IndexError as e:
                print e
                print 'Change method to catch name'
                i += 1
                continue

        end = time.time()
        self.start_flag = 1
        print '一页抓取 Total time (sec)', end - start, ' for (sec):', break_time
        logger.info('%s页抓取 Total time (%s)', page ,end - start)

    def start_monitor_sku(self, break_time, brower,cate):
        while (1):
            start = time.time()
            query = ItemQuery(brower,cate)
            items = query.read_itemid()
            for item in items:
                item_id = str(item[0])
                while (1):
                    try:
                        sku = brower.execute_script(
                            'return encodeURIComponent(document.getElementsByClassName("goods-card")[0].__vue__.$vnode.data.key)')
                        price = brower.execute_script(
                            'return encodeURIComponent(document.getElementsByClassName("goods-card")[0].getElementsByClassName("price-inner")[0].innerText)')
                        jdprice = brower.execute_script(
                            'return encodeURIComponent(document.getElementsByClassName("goods-card")[0].getElementsByClassName("jd-price-money")[0].innerText)')
                        money = brower.execute_script(
                            'return encodeURIComponent(document.getElementsByClassName("goods-card")[0].getElementsByClassName("profit-money")[0].innerText)')

                        query.update_item_info(self.jsobj.call('decodeURI', sku),
                                              self.jsobj.call('decodeURI', price),
                                              self.jsobj.call('decodeURI', jdprice),
                                              self.jsobj.call('decodeURI', money))
                        continue
                    except JavascriptException:
                        logger.info('sku vue节点读取失败')
                        break
                    except IndexError as e:
                        print e
                        continue
            # self.conn.close()  # 由于conn为静态变量，此处不能关闭
            end = time.time()
            self.start_flag = 1
            print 'Total time (sec)', end - start, 'Take a break for (sec):', break_time
            time.sleep(break_time)