# -*- coding = utf-8 -*-
# @Time: 2022/4/8 11:12
# @Author: CHN-QY
# @File: spider.py
# @Software: PyCharm

from bs4 import BeautifulSoup  # 网页解析，获取数据
import re  # 正则表达式，进行文字匹配
import urllib.request
import urllib.parse  # 指定URL,获取网页数据
import xlwt  # 进行Excel操作
import sqlite3  # 进行SQLite数据库操作


def main():
    base_url = "https://movie.douban.com/top250?start="
    # 爬取网页
    dataList = getdata(base_url)
    save_path = ".\\豆瓣电影Top250.xls"
    dbPath = "movie.db"

    # 保存数据
    savedata(dataList, save_path)
    # save_data_db(dataList, dbPath)


# 创建正则表达式对象，表示规则
# 影片详情链接的规则 小括号里就是要提前的内容
findLink = re.compile(r'<a href="(.*?)">')
# 图片的链接
findImgSrc = re.compile(r'<img.*src="(.*?)"', re.S)  # re.S 让换行符包含在字符（.）中
# 影片片面
findTitle = re.compile(r'<span class="title">(.*?)</span>')
# 影片评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*?)</span>')
# 找到评价人数
findJudge = re.compile(r'<span>(\d*?)人评价</span>')
# 找到概况
findInq = re.compile(r'<span class="inq">(.*?)</span>')
# 找到影片的相关内容
findBd = re.compile(r'<p class="">(.*?)</p>', re.S)


# 1.爬取网页
def getdata(baseUrl):
    data_list = []
    for i in range(0, 10):  # 调用获取页面信息的函数，10次
        url = baseUrl + str(i * 25)
        html = askurl(url)  # 保存获取到的网页源码
        # 逐一解析数据
        soup = BeautifulSoup(html, "html.parser")
        # print(soup)
        for item in soup.find_all("div", class_="item"):
            # print(item)  # 测试查看电影item全部信息
            data = []
            item = str(item)
            # print(item)
            # 影片详情的链接
            link = re.findall(findLink, item)[0]  # re库用来通过正则表达式查找指定的字符串
            data.append(link)  # 添加链接

            imgSrc = re.findall(findImgSrc, item)[0]
            data.append(imgSrc)  # 添加图片

            titles = re.findall(findTitle, item)
            if len(titles) == 2:
                ctitle = titles[0]  # 添加中文名
                data.append(ctitle)
                otitle = titles[1].replace(" ", "")  # 去掉NBSP符合
                otitle = re.sub("/", "", otitle)  # 去掉多于的/
                data.append(otitle)  # 添加外文名
            else:
                data.append(titles[0])
                data.append(" ")  # 为外文名留空

            rating = re.findall(findRating, item)[0]  # 添加评分
            data.append(rating)

            judgeNum = re.findall(findJudge, item)[0]  # 添加评价人数
            data.append(judgeNum)

            inq = re.findall(findInq, item)  # 概述有可能为空
            if len(inq) != 0:
                inq = inq[0].replace("。", "")  # 去掉句号
                data.append(inq)
            else:
                data.append(" ")  # 留空

            bd = re.findall(findBd, item)[0]  # 添加影片相关内容
            bd = re.sub('<br(\s+)?/>(\s+)?', " ", bd)  # 去掉Br
            bd = re.sub('/', " ", bd)  #
            bd = re.sub(" ", "", bd)
            bd = bd.strip()  # strip去掉前后的空格
            data.append(bd)

            data_list.append(data)  # 将处理好的一部电影信息放入data_list中
    # print(data_list)
    return data_list


# 3.保存数据
def savedata(dataList, savePath):
    print("save...")
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)
    sheet = book.add_sheet("豆瓣电影Top250", cell_overwrite_ok=True)
    col = ("电影详情链接", "图片链接", "影片中文名", "影片外文名", "评分", "评价数", "概况", "相关信息")
    for i in range(0, len(col)):
        sheet.write(0, i, col[i])  # 列名
    for i in range(0, 250):
        print("第%d条" % (i + 1))
        data = dataList[i]
        for j in range(0, len(col)):
            sheet.write(i + 1, j, data[j])  # 数据写入

    book.save(savePath)  # 保存


# 存储数据到db中
def save_data_db(dataList, dbPath):
    init_db(dbPath)
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()

    for data in dataList:
        for index in range(len(data)):
            if index == 4 or index == 5:
                continue
            # 将每个列表的信息加上双引号
            data[index] = '"' + data[index] + '"'
        sql = '''
            insert into movie250 (
            info_link, pic_link, cname, ename, score, rated, introduction,info)
            values (%s) ''' % ",".join(data)
        # print(sql)
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()


def init_db(dbPath):
    # 创建数据表
    sql = '''
        create table movie250
        (
        id integer primary key autoincrement,
        info_link text,
        pic_link text,
        cname varchar,
        ename varchar,
        score numeric,
        rated numeric,
        introduction text,
        info text
        )
    '''
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()
    cur.execute(sql)

    conn.commit()
    conn.close()


def askurl(url):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/100.0.4896.75 Safari/537.36 "
    }

    req = urllib.request.Request(url, headers=header)
    html = ""
    try:
        res = urllib.request.urlopen(req)
        html = res.read().decode("utf-8")
        # print(html)
    except Exception as err:
        print(err)

    return html


if __name__ == "__main__":  # 程序执行的入口
    main()
    # init_db("movietest.db")
    print("爬取完毕")
    pass
