import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, DateTime
from snownlp import SnowNLP

engine = create_engine('mysql+pymysql://root:root@127.0.0.1/posts')
DBsession = sessionmaker(bind=engine)
session = DBsession()
Base = declarative_base()

class Posts(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True)
    read = Column(Integer)
    comment = Column(Integer)
    url = Column(String(255))
    writer = Column(String(255))
    time = Column(DateTime)
    factor = Column(Float)
    code = Column(String(255))

def AddToSql(posts):
    res = session.query(Posts).filter_by(url = posts['url']).count()
    if res == 0:
        session.add(Posts(read = posts['read'], comment = posts['comment'], url = posts['url'], writer = posts['writer'], time = posts['time'], factor = posts['factor'], code = '600031'))
        session.commit()
        session.close()

def Crawler(page):
    url = 'http://gubaformgr.eastmoney.com/list,600031_' + str(page) + '.html'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
    }
    r = requests.get(url, headers = headers)
    soup = BeautifulSoup(r.text, "html.parser")

    stockname = soup.find_all('span', attrs={'id': 'stockname'})
    if stockname[0].text.replace(' ', '') != '三一重工吧':
        print('Error stockname!')
        return
    else:
        divSoup = soup.find_all('div', attrs={'id': 'articlelistnew'})
        divs = divSoup[0].find_all('div')

        for div in divs:
            if div['class'][0] != 'articleh':
                continue
            posts = {
                'read': '',
                'comment': '',
                'url': '',
                'writer': '',
                'time': '',
                'content': '',
                'factor': 0
            }

            posts['read'] = div.find_all('span', 'l1 a1')[0].text
            if posts['read'] == '':
                print('Read Error: ' + posts['url'])
                continue
            else:
                if '万' in posts['read']:
                    num = float(posts['read'].replace('万', ''))
                    posts['read'] = int(num * 10000)
                else:
                    posts['read'] = int(posts['read'])

            posts['comment'] = div.find_all('span', 'l2 a2')[0].text
            if posts['comment'] == '':
                print('Comment Error: ' + posts['url'])
                continue
            else:
                if '万' in posts['comment']:
                    num = float(posts['comment'].replace('万', ''))
                    posts['comment'] = int(num * 10000)
                else:
                    posts['comment'] = int(posts['comment'])

            msg = div.find_all('span', 'l3 a3')[0].find_all('a')[0]
            if len(msg['href']) < 100:
                posts['url'] =  'http://gubaformgr.eastmoney.com' + msg['href']
            else:
                posts['url'] =  'https:' + msg['href']
            if posts['url'] == '':
                print('Url Error: ' + posts['url'])
                continue
            
            posts['writer'] = div.find_all('span', 'l4 a4')[0].text
            if posts['writer'] == '':
                print('Writer Error: ' + posts['url'])
                continue
            
            posts['time'] = div.find_all('span', 'l5 a5')[0].text
            if posts['time'] == '':
                print('Time Error: ' + posts['url'])
                continue
            else:
                dt = datetime.strptime(posts['time'], "%m-%d %H:%M")
                posts['time'] = datetime(year = 2021, month = dt.month, day = dt.day, hour = dt.hour)

            try:
                context = requests.get(posts['url'])
                contextSoup = BeautifulSoup(context.text, "html.parser")
                if len(posts['url']) < 100:
                    content = contextSoup.find_all('div', attrs={'id': 'post_content'})[0].text
                else:
                    content = contextSoup.find_all('div', 'article-body')[0].text
                posts['content'] = re.sub('\s', '', content)
                if len(posts['content']) < 1:
                    print('Content Error: ' + posts['url'])
                    continue
                else:
                    s = SnowNLP(posts['content'])
                    posts['factor'] = s.sentiments
            except:
                print('Content Error: ' + posts['url'])
                continue
            
            AddToSql(posts)

for page in range(1, 3039):
    Crawler(page)
    print('Page ' + str(page) + ' has been successfully crawled.')
