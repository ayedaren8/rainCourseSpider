# -*- coding: utf-8 -*-
import json
import os
import re
import time
import requests
from PIL import Image
from requests.cookies import RequestsCookieJar
from selenium import webdriver


_URL={"index":"https://changjiang.yuketang.cn/web",
      "courseList":"https://changjiang.yuketang.cn/v2/api/web/courses/list?identity=2",
      "lession":"https://changjiang.yuketang.cn/v/lesson/get_lesson_replay_timeline/?lesson_id="
      }
_COURSES=[]
_LESSIONS=[]


def getDriver():
    browser_path = r"./chromedriver.exe"
    try:                                    
        driver = webdriver.Chrome(executable_path=browser_path)
        return driver
    except Exception:
        raise IOError("加载web驱动出错了")

def openLogin():
    # 打开二维码扫描获得cooikes存在本地
    driver=getDriver()
    driver.get(_URL["index"])
    logma=driver.find_element_by_class_name("logma").screenshot_as_png
    with open("./"+"qrcode.png","wb") as f:
        f.write(logma)
    im=Image.open("qrcode.png")
    im.show()
    while(True):
        time.sleep(2)
        title=driver.title
        if(title!="雨课堂网页版-登录"):
            print(title)
            break
    cookies=driver.get_cookies()
    with open("./"+"cookies.json","w") as f:
        f.write(json.dumps(cookies))
    return cookies

def localCookies():
    # 读取本地cookies
    driver=getDriver()
    driver.get(_URL["index"])
    with open("./"+"cookies.json","r") as f:
        cookies=json.loads(f.read())
        for cookie in cookies:
            if type(cookie)==dict:
                print(cookie["domain"])
                driver.add_cookie({
                    'domain': cookie['domain'],
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'path': cookie['path'],
                    'httpOnly':cookie['httpOnly'],
                    'secure': cookie['secure']
                })
    return driver 

def getCourse(driver):
    # 保存科目列表
    driver.get(_URL["courseList"])
    couserData=driver.find_element_by_tag_name("pre").text
    with open("./course.json","w",encoding="utf-8") as f:
        dic=json.loads(couserData)
        for item in dic["data"]['list']:
            course={}
            course['teacherName']=item['teacher']['name']
            course['courseName']=item['course']['name']
            course['courseID']=item['course']['id']
            course['classroom_id']=item['classroom_id']
            _COURSES.append(course)
        f.write(json.dumps(_COURSES,ensure_ascii=False))
    return driver


def getLession(driver,id):
    # 需要传一个课程号来获取每一课时的课
    lessionListURL="https://changjiang.yuketang.cn/v2/api/web/logs/learn/{classroom_id}?actype=3&prev_id=-1&offset=100&sort=-1".format(classroom_id=id)
    driver.get(lessionListURL)
    lessionData=driver.find_element_by_tag_name("pre").text
    with open("./lession.json","w",encoding="utf-8") as f:
        dic=json.loads(lessionData)
        for item in dic["data"]["activities"]:
            lesson={}
            lesson["title"]=item["title"]
            lesson["courseware_id"]=item["courseware_id"]
            _LESSIONS.append(lesson)
        f.write(json.dumps(_LESSIONS,ensure_ascii=False))
    return driver
    
    
def getAllwares(driver):
    for lession in _LESSIONS:
        getM3u8(driver,lession["courseware_id"])


def getM3u8(driver,wareID):
    path=os.getcwd()+"/down/"
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)
    driver.get(_URL["lession"]+str(wareID))
    playPage=driver.find_element_by_tag_name("pre").text
    playPage=json.loads(playPage)
    replay_url=playPage["data"]["live_timeline"][0]["replay_url"]
    baseURL=replay_url.split("playlist")[0]
    m3u8=requests.get(replay_url).text
    with open(path+"{}.m3u8".format(wareID),"w") as f:
        f.write(m3u8)
    pat =re.compile(r"^[^#]+")
    with open(path+"{}.m3u8".format(wareID),"r") as f:
        lines=f.readlines()
        print(type(lines))
        for index,line in enumerate(lines):
                if pat.match(line) is not None:
                       lines[index]=baseURL+line
    with open(path+"{}.m3u8".format(wareID),"w") as f:
        f.writelines(lines)

    
def chooseLessionDown(driver):
    for course in _COURSES: 
        print("课程ID  {}\n{} {}".format(course['classroom_id'],course['courseName'],course['teacherName']))
        print("___________________________________")
    ID=input("输入你想抓取的课程ID")
    getLession(driver,ID)
    getAllwares(driver)
    
    
def init():
    driver=localCookies()
    getCourse(driver)
    return driver



def run():
    driver=init()
    chooseLessionDown(driver)
    
if __name__ == "__main__":
    run()