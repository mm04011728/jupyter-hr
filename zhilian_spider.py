# coding:utf-8


TOTAL_PAGE_NUMBER = 30
KEYWORDS = ['python', '.net', '数据挖掘', '大数据',
            '数据分析', '推荐算法', '机器学习', '.net core']
ADDRESS = ['北京', ]
BASIC_URL = 'http://sou.zhaopin.com/jobs/searchresult.ashx?'


from datetime import datetime
from urllib.parse import urlencode
import requests
from multiprocessing import Pool
from bs4 import BeautifulSoup
import time
from itertools import product
import random
import re
import os



def get_between_re(start, end):
    return '(?<={0}).*(?={1})'.format(start, end)


def get_search_str(match_re):
    if match_re:
        return match_re.group(0)
    return ''


def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}
    response = requests.get(url, headers=headers)
    delay = random.randint(0, 2)
    time.sleep(delay)  # 设置等待时间，防止网站反爬虫
    return response.text


def get_content(html):
    # 记录保存日期
    date = datetime.now().date()
    date = datetime.strftime(date, '%Y-%m-%d')  # 转变成str

    soup = BeautifulSoup(html, 'lxml')
    body = soup.body
    data_main = body.find('div', {'class': 'newlist_list_content'})

    if data_main:
        tables = data_main.find_all('table')

        for i, table_info in enumerate(tables):
            if i == 0:
                continue
            tds = table_info.find('tr').find_all('td')
            zwmc = tds[0].find('a').get_text()  # 职位名称
            zw_link = tds[0].find('a').get('href')  # 职位链接
            fkl = tds[1].find('span').get_text()  # 反馈率
            gsmc = tds[2].find('a').get_text()  # 公司名称
            zwyx = tds[3].get_text()  # 职位月薪
            gzdd = tds[4].get_text()  # 工作地点
            gbsj = tds[5].find('span').get_text()  # 发布日期

            tr_brief_spans = table_info.find(
                'tr', {'class': 'newlist_tr_detail'}).find_all('span')

            gsdd = ""
            gsxz = ""
            gsgm = ""
            gzjy = ""
            xlyq = ""
            zwyx_1 = ""
            for list in tr_brief_spans:
                if len(list.get_text().split('：')) >= 2:
                    if list.get_text().split('：')[0] == "地点":
                        gsdd = list.get_text().split('：')[1]  # 公司地点
                    elif list.get_text().split('：')[0] == "公司性质":
                        gsxz = list.get_text().split('：')[1]  # 公司性质
                    elif list.get_text().split('：')[0] == "公司规模":
                        gsgm = list.get_text().split('：')[1]  # 公司规模
                    elif list.get_text().split('：')[0] == "经验":
                        gzjy = list.get_text().split('：')[1]  # 工作经验
                    elif list.get_text().split('：')[0] == "学历":
                        xlyq = list.get_text().split('：')[1]  # 学历要求
                    elif list.get_text().split('：')[0] == "职位月薪":
                        zwyx_1 = list.get_text().split('：')[1]  # 职位月薪(元/月)
                    else:
                        break

            # 用生成器获取信息
            yield {'职位名称': zwmc,  # 职位名称
                   '反馈率': fkl,  # 反馈率
                   '公司名称': gsmc,  # 公司名称
                   '职位月薪': zwyx,  # 职位月薪
                   '工作地点': gzdd,  # 工作地点
                   '公布时间': gbsj,  # 公布时间
                   '职位链接': zw_link,  # 网页链接
                   '保存时间': date,  # 记录信息保存的日期
                   '公司地点': gsdd,  # 公司地点
                   '公司性质': gsxz,  # 公司性质
                   '公司规模': gsgm,  # 公司规模
                   '工作经验': gzjy,  # 工作经验
                   '学历要求': xlyq,  # 学历要求
                   '职业薪水': zwyx_1,  # 职位月薪(元/月)
                   }


def get_detail(html):
    soup = BeautifulSoup(html, 'lxml')
    body = soup.body
    data_main = body.find('div', {'class': 'tab-inner-cont'})
    if data_main:
        text = data_main.get_text()
        to_del_re = '\r|\n|\t| |查看职位地图|·|【|】|：|:'
        text_clear = re.sub(to_del_re, '', text)
        text_clear = re.sub(',', '，', text_clear)
        first_re = '((职位介绍)|(职位描述)|(岗位职责)|(岗位描述)|(工作职责)|(职责描述)|(职位职责))'
        second_re = '((岗位要求)|(职位要求)|(任职要求)|(任职资格)|(工作要求)|(任职标准)|(技术要求)|(任职条件)|(能力要求))'
        # first_re = '((职位要求(：|:))|(职位介绍(：|:))|(职位描述(：|:))|(岗位职责(：|:))|(岗位描述(：|:))|(工作职责(：|:))|(职责描述(：|:)))'
        # second_re = '((岗位要求(：|:))|(职位要求(：|:))|(任职要求(：|:))|(任职资格(：|:))|(工作要求(：|:)))'
        third_re = '工作地址'
        responsibilities_search = re.search(
            get_between_re(first_re, second_re), text_clear)
        if '工作地址' in text_clear:
            requirements_search = re.search(
                get_between_re(second_re, third_re), text_clear)
        else:
            requirements_search = re.search(
                '(?<={0}).*'.format(second_re), text_clear)
        addr_search = re.search('(?<={0}).*'.format(third_re), text_clear)
        responsibilities = get_search_str(
            responsibilities_search)          # 岗位职责
        requirements = get_search_str(
            requirements_search)                  # 技能要求
        addr = get_search_str(addr_search)          # 公司地址
        return(responsibilities, requirements, addr)


def main(args):
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d")
    path = 'data\{0}'.format(start_date)
    if not(os.path.exists('data')):
        os.mkdir('data')
    if not(os.path.exists(path)):
        os.mkdir(path)
    f = open('{0}\{1}_{2}.csv'.format(path, args[0],args[1]), mode= 'w',encoding='utf-8')
    list_title = ['城市', '关键字', '职位名称', '反馈率', '公司名称', '职位月薪', '工作地点',
                  '公布时间', '职位链接', '岗位职责', '技能要求', '公司地址', '保存时间', '公司地点', '公司性质', '公司规模', '工作经验', '学历要求', '职业薪水']
    line_title_str = ','.join(list_title)
    print(line_title_str,file= f)
    for page_num in range(TOTAL_PAGE_NUMBER):
        paras = {'jl': args[0],
                 'kw': args[1],
                 'p': str(page_num)  # 第X页
                 }
        url = BASIC_URL + urlencode(paras)
        # print(url)
        html = download(url)
        data = get_content(html)
        for each in data:
            if 'xiaoyuan' in each['职位链接'] or '置顶' in each['公布时间']:
                continue
            line = []
            line.append(args[0])
            line.append(args[1])
            for k, v in each.items():
                line.append(v)
                if k == '职位链接':
                    # print(v)
                    html_detail = download(v)
                    data_detail = get_detail(html_detail)
                    for each in data_detail:
                        line.append(each)
            line_str = ','.join(line)
            print(line_str,file= f)
    f.close()

if __name__ == '__main__':
    start = time.time()
    # number_list = list(range(TOTAL_PAGE_NUMBER))
    args = product(ADDRESS, KEYWORDS)
    pool = Pool()
    pool.map(main, args)  # 多进程运行
    end = time.time()
    print('Finished, task runs %s seconds.' % (end - start))
