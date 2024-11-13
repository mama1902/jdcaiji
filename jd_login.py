# -*- coding: utf-8 -*-
import cv2
import time
import multiprocessing

import execjs
import numpy as np
from selenium import webdriver
import urllib as request
from selenium.webdriver.common.action_chains import ActionChains
from conn_sql import ItemQuery
from logger import logger
from config import CONFIG


options = webdriver.ChromeOptions()
# options.binary_location = r""
options.add_argument('--disable-web-security')
brower = webdriver.Chrome(chrome_options=options)

def loadpage(userid, password):

    url = "https://jdstore.jd.com/v2?_frameActiveMenu=101966&subMenu1=101966"
    brower.get(url)
    time.sleep(5)
    s1 = r'//div/div[@class="login-tab login-tab-r"]/a'
    userlogin = brower.find_element_by_xpath(s1)
    userlogin.click()
    # time.sleep(5)
    username = brower.find_element_by_id("loginname")
    username.send_keys(userid)
    userpswd = brower.find_element_by_id("nloginpwd")
    userpswd.send_keys(password)
    # time.sleep(5)
    brower.find_element_by_id("loginsubmit").click()
    time.sleep(3)
    while True:
        try:
            getPic()
        except:
            print("登陆成功----")
            break


    return brower

def crawy(page, brower,cate):

    itemquery = ItemQuery(brower,cate)
    page +=1
    itemquery.start_monitor(CONFIG['LUNX_TIME'], brower,page,cate)


def getPic():
    # 用于找到登录图片的大图
    s2 = r'//div/div[@class="JDJRV-bigimg"]/img'
    # 用来找到登录图片的小滑块
    s3 = r'//div/div[@class="JDJRV-smallimg"]/img'
    bigimg = brower.find_element_by_xpath(s2).get_attribute("src")
    smallimg = brower.find_element_by_xpath(s3).get_attribute("src")
    # print(smallimg + '\n')
    # print(bigimg)
    # 背景大图命名
    backimg = "backimg.png"
    # 滑块命名
    slideimg = "slideimg.png"
    # 下载背景大图保存到本地
    request.urlretrieve(bigimg, backimg)
    # 下载滑块保存到本地
    request.urlretrieve(smallimg, slideimg)
    # 获取图片并灰度化
    block = cv2.imread(slideimg, 0)
    template = cv2.imread(backimg, 0)
    # 二值化后的图片名称
    blockName = "block.jpg"
    templateName = "template.jpg"
    # 将二值化后的图片进行保存
    cv2.imwrite(blockName, block)
    cv2.imwrite(templateName, template)
    block = cv2.imread(blockName)
    block = cv2.cvtColor(block, cv2.COLOR_RGB2GRAY)
    block = abs(255 - block)
    cv2.imwrite(blockName, block)
    block = cv2.imread(blockName)
    template = cv2.imread(templateName)
    # 获取偏移量
    result = cv2.matchTemplate(block, template, cv2.TM_CCOEFF_NORMED)  # 查找block在template中的位置，返回result是一个矩阵，是每个点的匹配结果
    x, y = np.unravel_index(result.argmax(), result.shape)
    # print("x方向的偏移", int(y * 0.4 + 18), 'x:', x, 'y:', y)
    # 获取滑块
    element = brower.find_element_by_xpath(s3)
    ActionChains(brower).click_and_hold(on_element=element).perform()
    ActionChains(brower).move_to_element_with_offset(to_element=element, xoffset=y, yoffset=0).perform()
    ActionChains(brower).release(on_element=element).perform()
    time.sleep(3)


if __name__ == '__main__':

    id = "420625ZMD666"  # 用户账号
    passwd = "JD666888"  # 用户密码
    brower = loadpage(id, passwd)
    brower.get("https://million-goods.jd.com/iStoreFuse/goodsFuse")
    time.sleep(18)
    brower.execute_script('document.getElementsByClassName("pop-select-dropdown-list")[0].getElementsByTagName("li")[1].click()')

    cates = [{'name':'冰箱','cid':9},{'name':'厨房小电','cid':8}]
    for j in cates:
        cate = j['name']
        cid = j['cid']
        if cate != '':
            brower.execute_script(
                'var findelements=function(y, text){for (i = 0; i < y.length; i++) {if (y[i].innerText == text) {y[i].click();return true;}}};findelements(document.getElementsByClassName("shortcut-select__value__wrap")[0].getElementsByTagName("li"), "' + bytes(
                    cate) + '")')

            for i in range(500):
                crawy(i, brower, cid)
                # eat_process = multiprocessing.Process(target=crawy, args=(i, brower))
                # eat_process.start()
            skumo = False
        elif skumo:  # sku 轮询模式
            itemquery = ItemQuery(brower, cid)
            itemquery.start_monitor_sku(CONFIG['LUNX_TIME'], brower, cid)