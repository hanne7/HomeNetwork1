import urllib.request
import datetime
import json
import os
import threading
import time
import ctypes
from random import *
from bs4 import BeautifulSoup
from gtts import gTTS

g_Dehumid = False
g_Humid = False
g_Radiator = False
g_Gas_Valve = False
g_Balcony_Windows = False
g_Door = False
g_AI_Mode = False

humidMax = 60
humidMin = 40
dustMax1 = 40
dustMax2 = 30


repo_base_name="BigData_Repo"
dir_delimeter='/'
depth_level2_dir="weather_info"
file_limit=3

access_key = "4ruU7ayu0r%2BGctDhbc6L3IruWayh2oiaMDsR%2Fo8iuhpo2qZTPwKyhrKj1EvfIMqssGehRSCfQlQw4uO%2BR6bSXg%3D%3D"

def terminate_thread(thread):
    '''Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    '''
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError('nonexistent thread id')
    elif res > 1:
        # '''if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect'''
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError('PythreadState_SetAsyncExc failde')

def make_base_dir():
    os.mkdir('.'+dir_delimeter+repo_base_name)

def make_d2_dir(dir_num):
    os.mkdir('.'+dir_delimeter+repo_base_name+'\\'+depth_level2_dir+dir_num)

def directory_num():
    dir_num=len(os.listdir('.'+dir_delimeter+repo_base_name))
    if len(os.listdir('.'+dir_delimeter+repo_base_name+dir_delimeter+depth_level2_dir+str(dir_num))) == file_limit:
        dir_num+=1
        make_d2_dir(str(dir_num))
    return str(dir_num)

def get_request_url(url):
    req = urllib.request.Request(url)

    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            print('[%s] Url Request Success'%datetime.datetime.now())
            return response.read().decode('utf-8')
    except Exception as e:
        print(e)
        print('[%s] Error for URL : %s'%(datetime.datetime.now(), url))
        return  None

def getFinedust(sidoName):
    end_point = "http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    parameters = "?sidoName=" + sidoName
    parameters += "&pageNo=1&numOfRows=15&ver=1.3"
    parameters += "&_returnType=json&serviceKey=" + access_key
    url = end_point + parameters

    retData = get_request_url(url)

    if(retData == None):
        return  None
    else:
        return json.loads(retData)

def getForecast(base_date, base_time, nx, ny):
    end_point = "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastTimeData"

    parameters = "?_type=json&serviceKey=" + access_key
    parameters += "&base_date=" + base_date
    parameters += "&base_time=" + base_time
    parameters += "&nx=" + nx
    parameters += "&ny=" + ny
    parameters += '&numOfRows=100'

    url = end_point + parameters

    retData = get_request_url(url)

    if(retData == None):
        return  None
    else:
        return  json.loads(retData)

def print_main_menu():
    print('\n1. 장비상태 확인')
    print('2. 장비제어')
    print('3. 스마트 모드')
    print('4. 프로그램 종료')

def print_device_status(device_name,device_status):
    print('%s 상태: '%device_name, end='')
    if device_status == True: print('작동')
    else: print('정지')

def check_device_status():
    print_device_status('난방기', g_Radiator)
    print_device_status('가스벨브', g_Gas_Valve)
    print_device_status('발코니(베란다) 창문', g_Balcony_Windows)
    print_device_status('출입문 상태', g_Door)
    print_device_status('가습기 상태', g_Humid)
    print_device_status('제습기 상태', g_Dehumid)

def print_device_menu():
    print('\n상태 변경할 기기를 선택하세요.')
    print('1. 난방기')
    print('2. 가스벨브')
    print('3. 발코니(베란다) 창')
    print('4. 출입문')
    print('5. 가습기')
    print('6. 제습기')

def control_device():
    global g_Radiator, g_Gas_Valve, g_Balcony_Windows, g_Door, g_Dehumid, g_Humid

    check_device_status()
    print_device_menu()
    menu_num = int(input('번호를 입력하세요: '))

    if menu_num == 1: g_Radiator = not g_Radiator
    if menu_num == 2: g_Gas_Valve = not g_Gas_Valve
    if menu_num == 3: g_Balcony_Windows = not g_Balcony_Windows
    if menu_num == 4: g_Door = not g_Door
    if menu_num == 5: g_Humid = not g_Humid
    if menu_num == 6: g_Dehumid = not g_Dehumid
    check_device_status()

def get_realtime_weather_info():
    jsonResult = []
    now = datetime.datetime.now()

    # 초단기예보
    base_date = now.strftime('%Y%m%d')
    if int(now.strftime('%M')) >= 30 and int(now.strftime('%M')) <= 59:
        base_time = now.strftime('%H%M')
    else:
        hour = int(now.strftime('%H')) - 1
        min = int(now.strftime('%M')) - 30 + 60
        base_time = str(hour) + str(min)
    nx = '89'
    ny = '91'

    jsonData = getForecast(base_date, base_time, nx, ny)
    if (jsonData['response']['header']['resultMsg'] == 'OK'):
        for i in jsonData['response']['body']['items']['item']:
            jsonResult.append(i)

    # 미세먼지
    sidoName = '%EB%8C%80%EA%B5%AC'  # 대구
    jsonData2 = getFinedust(sidoName)
    for i in jsonData2['list']:
        if i['stationName'] == '신암동':
            jsonResult.append(i)

    with open('.%s%s%s%s%s%s동구_신암동_초단기예보조회_%s.json' \
                  % (dir_delimeter, repo_base_name, dir_delimeter, depth_level2_dir, \
                     directory_num(), dir_delimeter, now.strftime('%Y%m%d%H%M')), \
                  'w', encoding='utf8') as outfile:
        retJson = json.dumps(jsonResult, indent=4, sort_keys=True, ensure_ascii=False)
        outfile.write(retJson)
    print('동구_신암동_초단기예보조회_%s_%s.json SAVED\n' % (base_date, now.strftime('%H%M')))
    return jsonResult

def auto_control(result):
    global g_Dehumid, g_Humid, humidMin, humidMax, g_Balcony_Windows, dustMax1, dustMax2
    humid = 0
    rain = 0
    dust1 = 0
    dust2 = 0
    for i in result:
        try:
            if i['category'] == 'RN1':
                if i['fcstValue'] > 0 and g_Balcony_Windows == True:
                    g_Balcony_Windows = False
                    print('발코니 창문을 닫습니다.')
                elif i['fcstValue'] == 0 and g_Balcony_Windows == False and dust1 < dustMax1 and dust2 < dustMax2:
                    g_Balcony_Windows = True
                    print('발코니 창문을 엽니다.')
                rain = int(i['fcstValue'])
            if i['category'] == 'REH':
                humid = int(i['fcstValue'])
                break
        except:
            continue
    for i in result:
        try:
            if i['mangName'] == '도시대기':
                dust1 = int(i['pm10Value'])
                dust2 = int(i['pm25Value'])
        except:
            continue
    print('강우량 :', rain)
    print('습도 :', humid)
    print('미세먼지(pm10)농도 : ', dust1)
    print('초미세먼지(pm2.5)농도 : ', dust2)
    if humid > humidMax and g_Dehumid == False:
        g_Dehumid = True
        print('제습기가 가동됩니다.')
    if humid < humidMin and g_Humid == False:
        g_Humid = True
        print('가습기가 가동됩니다.')
    if (dust1 > dustMax1 or dust2 > dustMax2) and g_Balcony_Windows == True:
        g_Balcony_Windows = False
        print('미세먼지로 인해 발코니 창문을 닫습니다.')

def simulator():
    print('1. 습한날')
    print('2. 건조한날')
    print('3. 비오는날')
    print('4. 화창한날')
    menu_num = int(input('시뮬레이션하고자 하는 날씨를 선택하세요: '))

    simul_data = []
    if not os.path.exists('./simulator'):
        os.mkdir('./simulator')

    if menu_num == 1:
        simul_data.append(
            {'category':'REH',
             'fcstValue':randint(61, 100)})
        auto_control(simul_data)
        with open('./simulator/simul_data01.json', 'w',encoding='utf-8') as outfile:
            retJson = json.dumps(simul_data, indent=4, sort_keys=True, ensure_ascii=False)
            outfile.write(retJson)
        print('simul_data01.json SAVED')
    elif menu_num == 2:
        simul_data.append(
            {'category': 'REH',
             'fcstValue': randint(1, 40)})
        auto_control(simul_data)
        with open('./simulator/simul_data02.json', 'w', encoding='utf-8') as outfile:
            retJson = json.dumps(simul_data, indent=4, sort_keys=True, ensure_ascii=False)
            outfile.write(retJson)
        print('simul_data02.json SAVED')
    elif menu_num == 3:
        simul_data.append(
            {'category': 'RN1',
             'fcstValue': randint(1, 200)})
        auto_control(simul_data)
        with open('./simulator/simul_data03.json', 'w', encoding='utf-8') as outfile:
            retJson = json.dumps(simul_data, indent=4, sort_keys=True, ensure_ascii=False)
            outfile.write(retJson)
        print('simul_data03.json SAVED')
    elif menu_num == 4:
        simul_data.append({'category':'RN1','fcstValue':0})
        simul_data.append({'mangName': '도시대기','pm10Value': randint(1,40),'pm25Value': randint(1,30)})
        auto_control(simul_data)
        with open('./simulator/simul_data04.json', 'w', encoding='utf-8') as outfile:
            retJson = json.dumps(simul_data, indent=4, sort_keys=True, ensure_ascii=False)
            outfile.write(retJson)
        print('simul_date04.json SAVED')

def news_speaker(news):
    # tts = gTTS(text=news, lang='ko')
    # tts.save('ranking_news.wav')
    print('ranking_news SAVED')

def print_news(news):
    num = 1
    for i in news:
        print(str(num) + '. ' + i)
        num+=1

def ranking_news():
    news_link = 'https://news.naver.com'

    html = urllib.request.urlopen('https://news.naver.com/main/ranking/popularDay.nhn')
    soup = BeautifulSoup(html, 'html.parser')

    tags = soup.findAll('ul', attrs={'class': 'section_list_ranking'})

    news_url = []
    num = 0
    for news in tags:
        with open('ranking_news%s.csv' % str(num + 1), 'w', encoding='utf-8') as outfile:
            outfile.write(str(tags[num]))
            num += 1

    num = 0
    for news in tags:
        with open('ranking_news%s.csv' % str(num + 1), 'r', encoding='utf-8') as readfile:
            a = readfile.readlines()
            del a[11]
            del a[0]
            for line in a:
                i = line.split('href="')
                j = i[1].split('" title')
                k = j[1].split('>')
                m = k[1].split('<')
                news_url.append(m[0] + '\n' + news_link + j[0].replace('&amp;', '&') + '\n')
        num += 1

    politic_news = news_url[:10]
    economic_news = news_url[10:20]
    social_news = news_url[20:30]
    living_news = news_url[30:40]
    world_news = news_url[40:50]
    IT_news = news_url[50:]

    print('1. 정치\n2. 경제\n3. 사회\n4. 생활/문화\n5. 세계\n6. IT/과학\n')
    menu_num = int(input('메뉴를 선택하세요: '))
    if menu_num == 1:
        print_news(politic_news)
        news_speaker(politic_news)
    elif menu_num == 2:
        print_news(economic_news)
        news_speaker(economic_news)
    elif menu_num == 3:
        print_news(social_news)
        news_speaker(social_news)
    elif menu_num == 4:
        print_news(living_news)
        news_speaker(living_news)
    elif menu_num == 5:
        print_news(world_news)
        news_speaker(world_news)
    elif menu_num == 6:
        print_news(IT_news)
        news_speaker(IT_news)

def smart_play():
    while True:
        print('1. 실시간 랭킹 뉴스 헤드라인')
        print('2. 실시간 도로교통정보')
        print('3. 실시간 뮤직차트')
        print('4. 실시간 영화 랭킹')
        print('5. 초기메뉴')

        menu_num = int(input('메뉴를 선택하세요: '))
        if menu_num == 1:
            ranking_news()
        elif menu_num == 2:
            pass
        elif menu_num == 3:
            pass
        elif menu_num == 4:
            pass
        elif menu_num == 5:
            print('초기메뉴로 돌아갑니다.')
            break

def smart_mode():
    global g_AI_Mode, g_Dehumid, g_Humid, g_Balcony_Windows, humidMax, humidMin
    print('1. 인공지능 모드 조회')
    print('2. 인공지능 모드 상태 변경')
    print('3. 실시간 기상정보 Update')
    print('4. 시뮬레이터 모드')
    print('5. 스마트 모드')
    menu_num = int(input('메뉴를 선택하세요: '))
    t = threading.Thread(target=update_scheduler)

    if menu_num == 1:
        print('현재 인공지능 모드: ', end='')
        if g_AI_Mode == True: print('작동')
        else: print('중지')
    if menu_num == 2:
        g_AI_Mode = not g_AI_Mode
        print('현재 인공지능 모드: ', end='')
        if g_AI_Mode == True:
            print('작동')
            t.daemon = True
            t.start()
        else:
            print('중지')
            terminate_thread(t)
    elif menu_num == 3:
        if not os.path.exists('.' + dir_delimeter + repo_base_name):
            make_base_dir()
        if not os.path.exists('.' + dir_delimeter + repo_base_name + dir_delimeter + depth_level2_dir + '1'):
            make_d2_dir('1')
        result = get_realtime_weather_info()
        if g_AI_Mode == True:
            auto_control(result)
    elif menu_num == 4:
        simulator()
    elif menu_num == 5:
        smart_play()
def update_scheduler():
    while True:
        if g_AI_Mode == False:
            continue
        else:
            result = get_realtime_weather_info()
            auto_control(result)
            time.sleep(6)

print('<스마트 홈네트워크 시뮬레이션 프로그램 ver1.0>')
while True:
    print_main_menu()
    menu_num = int(input('메뉴를 선택하세요: '))

    if(menu_num == 1):
        check_device_status()
    elif(menu_num == 2):
        control_device()
    elif(menu_num == 3):
        smart_mode()
    elif(menu_num == 4):
        break