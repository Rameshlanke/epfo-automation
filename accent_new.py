# import the Flask class from the flask module
# sudo docker run -it -p 8050:8050 scrapinghub/splash --max-timeout 3600 --disable-private-mode
# sudo docker run -it -p 8050:8050 441973415384.dkr.ecr.ap-south-1.amazonaws.com/splash --max-timeout 3600 --disable-private-mode
# gunicorn -k gevent -w 5 -b 0.0.0.0:4000 login_epf:app
# gunicorn -k gevent -w 5 -b 0.0.0.0:4000 -e DOCKER_HOST='172.17.0.1' -e REDIS_HOST='172.17.0.1' -e REDIS_TRACKER_DATA_EXPIRE='3600' -e REDIS_TRANSACTIONID_KEY_EXPIRE_SECS='3600' -e AWS='False' -e REDIS_PASSWORD='myredisauthisrambo' app_epf:app

import time
import logging
# from pebble import concurrent
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from flask import Flask, render_template, request, session
from PIL import Image
import base64
from base64 import b64decode
import pandas as pd
import requests
import response
import json
import signal
import os
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from flask import Flask, render_template, redirect, request, jsonify, make_response
from flask_cors import CORS
# from redissession import RedisSessionInterface
import requests
import json
import redis
import string
import uuid
import random
import time
import os
import ast
import re
from os import abort
from functools import wraps
# from utils import utils
from flask import Blueprint, send_file
# from utils import utils


logger = utils.getLogger()
# selenium imports


options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')


app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO, filename="EPFO-Troubleshoot.log",
                    format='%(asctime)s  %(levelname)s  %(message)s', datefmt="%Y-%m-%d-%H-%M-%S")
logger = utils.getLogger()
# app.config.from_pyfile('config.cfg')
app.session_interface = RedisSessionInterface()
app.secret_key = b'\xe2\x92*\x1b\x96F\xf2\xafh^\xfd\xcf\xde\xb4f\xbd\x0b\xdf\xa1@#\xd4\xb1\x9c'

# browser={}
# browser=webdriver.Chrome(executable_path=r"/home/ubuntu/chromedriver", chrome_options=options)

global proxy

proxy = {

    # 'DOCKER_HOST':    os.environ['DOCKER_HOST'], #  '172.17.0.1',
    'REDIS_HOST':     os.environ['REDIS_HOST'],  # '172.17.0.1',
    # 'USE_PROXY' :     os.environ['USE_PROXY'],
    # 'PROXY_IP' :      os.environ['PROXY_IP'],
    # 'PROXY_USER':     os.environ['PROXY_USER'],
    # 'PROXY_PASS':     os.environ['PROXY_PASS'],
    'REDIS_TRACKER_DATA_EXPIRE':   os.environ['REDIS_TRACKER_DATA_EXPIRE'],
    'REDIS_TRANSACTIONID_KEY_EXPIRE_SECS': os.environ['REDIS_TRANSACTIONID_KEY_EXPIRE_SECS'],
    'AWS': os.environ['AWS'],
    'REDIS_PASSWORD': os.environ['REDIS_PASSWORD']

}


REDIS_TRANSACTIONID_KEY_EXPIRE_SECS = proxy['REDIS_TRANSACTIONID_KEY_EXPIRE_SECS']
REDIS_TRACKER_DATA_EXPIRE = proxy['REDIS_TRACKER_DATA_EXPIRE']

DIGIVERIFIER_URL = 'https://www.digiverifier.com'

if proxy['AWS'] == "True":
    r = redis.StrictRedis(host=proxy['REDIS_HOST'],
                          port=6379,
                          db=0,
                          password=proxy['REDIS_PASSWORD'],
                          ssl_cert_reqs=u'none',
                          # ssl_ca_certs=None,
                          ssl=True
                          )
    # #
else:
    r = redis.StrictRedis(host=proxy['REDIS_HOST'], port=6379)


EPFO_URL = "https://unifiedportal-mem.epfindia.gov.in/memberinterface/"


@app.route('/epfo', methods=['GET'])
def epfo():
    return 'Not logged in to epfo'


# import codecs
# import time


chrome_options = Options()
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--enable-logging")

chrome_options.headless = True
driver = webdriver.Chrome(options=chrome_options)

# driver = webdriver.Chrome()
prod = "https://api-oauth2.digiverifier.com"
test = "http://ec2-13-233-217-249.ap-south-1.compute.amazonaws.com:7000"
check = test


@app.route('/get-captcha', methods=['GET'])
def index():
    driver.get("https://unifiedportal-mem.epfindia.gov.in/memberinterface")

    assert "Member Home" in driver.title
    wait = WebDriverWait(driver, 20)  # Maximum wait time in seconds

    btn_KNOW_YOUR_UAN = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//html/body/div[2]/div/div[3]/div[3]/div[3]/div/div[2]/ul/li[4]/a')))
    btn_KNOW_YOUR_UAN.click()

    captcha = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
    data = captcha.screenshot_as_base64

    return render_template('index_v1.html', image=data, txnid='1234')


@app.route('/submit-otp', methods=['POST'])
def submit_otp():

    mobile_numer = request.form['username']  # mobile
    # password= request.form['password']
    captcha1 = request.form['captcha']
    print(mobile_numer, captcha1)

    driver.find_element(
        By.XPATH, '//*[@id="mobileNo"]').send_keys(mobile_numer)
    driver.find_element(By.XPATH, '//*[@id="captcha"]').send_keys(captcha1)
    driver.find_element(By.XPATH, '//*[@id="get-otp-btn"]').click()

    driver.save_screenshot('chrom223.png')
    try:
        wait = WebDriverWait(driver, 10)
        btn_ok_postotp = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="successBtn"]')))
        btn_ok_postotp.click()
        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        data = captcha.screenshot_as_base64
        return render_template('index_v2.html', image=data, txnid='1234')
    except:
        error_label = driver.find_element(By.ID, "errorMsg")
        print(error_label.text)
        btn_error = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="errorBtn"]')))
        btn_error.click()

        driver.find_element(
            By.XPATH, '//*[@id="mobileNo"]').clear()

        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        data = captcha.screenshot_as_base64
        return render_template('index_v1.html', image=data, txnid='1234')


@app.route('/enter-otp', methods=['POST'])
def enter_otp():
    wait = WebDriverWait(driver, 10)

    otp = request.form['otp']
    captcha1 = request.form['captcha']
    driver.find_element(By.XPATH, '//*[@id="otp-no-val"]').send_keys(otp)
    driver.find_element(By.XPATH, '//*[@id="captcha"]').send_keys(captcha1)
    driver.save_screenshot('chrom223.png')

    btn_validate_otp = driver.find_element(By.XPATH, '//*[@id="get-otp-btn"]')
    btn_validate_otp.click()

    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//html/body/div[2]/div[2]/div/div/div[2]/label')))
        error_label = driver.find_element(By.ID, "errorMsg")
        print(error_label.text)
        btn_error = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="errorBtn"]')))
        btn_error.click()
        driver.find_element(By.XPATH, '//*[@id="otp-no-val"]').clear()
        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        data = captcha.screenshot_as_base64
        return render_template('index_v2.html', error=error_message, image=data, txnid='1234')
    except:
        pass

    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="successBtn"]')))
        btn_ok_postotp = driver.find_element(By.XPATH, '//*[@id="successBtn"]')
        btn_ok_postotp.click()

        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        data = captcha.screenshot_as_base64

        return render_template('index_v3.html', image=data, txnid='1234')
    except:
        error_label = driver.find_element(By.ID, "errorMsg")
        print(error_label.text)
        error_message = "Invalid OTP"
        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        driver.find_element(By.XPATH, '//*[@id="otp-no-val"]').clear()
        data = captcha.screenshot_as_base64
        return render_template('index_v2.html', error=error_message, image=data, txnid='1234')


@app.route('/get-uan', methods=['POST'])
def get_uan():
    wait = WebDriverWait(driver, 20)
    name = request.form['name']
    date_of_birth = request.form['dob']
    pan_number = request.form['pan_number']
    captcha1 = request.form['captcha']
    btn_pan = driver.find_element(
        By.XPATH, '//*[@id="mem-det-div"]/div[3]/div[1]/div[2]/button[2]')
    btn_pan.click()
    driver.find_element(By.XPATH, '//*[@id="name"]').send_keys(name)
    driver.find_element(By.XPATH, '//*[@id="pan"]').send_keys(pan_number)
    driver.find_element(By.XPATH, '//*[@id="captcha"]').send_keys(captcha1)

    datepicker_element = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//*[@id='dob']")))
    datepicker_element.click()

    date_of_birth = request.form['dob']

    day, month, year = date_of_birth.split('/')
    month = int(month)
    month_value = month - 1
    year_value = int(year)
    day_value = int(day)
    # time.sleep(3)
    # /epfo/login
    wait = WebDriverWait(driver, 20)
    month_dropdown = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[@id='ui-datepicker-div']/div/div/select[1]")))
    month_dropdown.find_element(
        By.XPATH, f"option[@value='{month_value}']").click()
    print("Year Done")
    month_dropdown = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[@id='ui-datepicker-div']/div/div/select[2]")))
    month_dropdown.find_element(
        By.XPATH, f"option[@value='{year_value}']").click()
    print("Month Done")

    datepicker_tbody = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody')))
    number_element = datepicker_tbody.find_element(
        By.XPATH, f".//a[contains(text(), '{day_value}')]")
    number_element.click()
    print("Day Done")

    btn_show_uan = driver.find_element(By.XPATH, '//*[@id="get-otp-btn"]')
    btn_show_uan.click()

    try:
        error_label = driver.find_element(By.ID, "errorMsg")
        print(error_label.text)
        btn_error = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="errorBtn"]')))
        btn_error.click()
        driver.find_element(By.XPATH, '//*[@id="name"]').clear()
        driver.find_element(By.XPATH, '//*[@id="pan"]').clear()
        captcha = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')))
        data = captcha.screenshot_as_base64
        return render_template('index_v3.html', image=data, txnid='1234')

    except:
        wait = WebDriverWait(driver, 10)
        UAN_number = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '/html/body/div[2]/div[4]/div/div/div[2]/table/tbody/tr/td')))
        # print(UAN_number.text)
        print("Your UAN Number is: ", UAN_number.text)
        uan_num = UAN_number.text
        driver.quit()
        return function_get_data(uan_num)


# prod = 'https://example.com'  # Replace with the correct URL


@app.route('/get-data')
def function_get_data(uan_num):
    global prod
    uan_num = str(uan_num)

    prod = "https://api-oauth2.digiverifier.com"
    test = "http://ec2-13-233-217-249.ap-south-1.compute.amazonaws.com:7000"
    # check = test

    response = requests.post(prod+"/epfo/generate-post/", headers={'Content-Type': 'application/json'},
                             json={'client_id': 'af5cc093-26d6-424d-8825-582e26ae1a10', 'client_secret': '31VegAwOG2iLr1wBeR72mTEvn'})
    token = pd.read_json(response.text)
    # Get transaction id
    response = requests.get(prod+"/epfo/transaction-get/",
                            headers={'accept': 'application/json', 'bearer': token['message'][0]})
    tid = response.json()

    # trigger report
    response = requests.post(prod+"/epfo/submit-post/?txnid="+str(tid['message']),
                             headers={'accept': 'application/json',
                                      'Bearer': token['message'][0], 'txnid': tid['message']},
                             json={'employee-uan': uan_num})
    uan_data = response.json()
    print(response.json())

    return uan_data


@app.route('/epfo/cancel/<txnid>', methods=['GET', 'POST'])
def hi(txnid):
    # redirectUrl = r.get('epfo-redirectUrl')
    # redirectUrl = redirectUrl.decode('utf-8')

    redirectUrl = r.lrange(txnid, 0, 1)
    redirectUrl = [x.decode('utf-8') for x in redirectUrl]

    redirectUrl = redirectUrl[0]

    r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS,  json.dumps({"message": "cancelled",
                                                                     "code": "cancelled",
                                                                     "success": False}))
    x = r.get(txnid+'session')
    session = x.decode('utf-8')
    session = json.loads(session)
    session_id = session['session_id']
    executor_url = session['executor_url']
    pid = session['pid']
    browser = create_driver_session(session_id, executor_url)
    browser.close()
    kill_chrome(pid, txnid)
    return redirect(redirectUrl + '?status=cancelled&status_code=516&txnid=' + txnid)


# from multiprocessing import Process, Queue,Manager
# manager = Manager()
# browser = manager.dict()
# q = Queue()
# Global = manager.Namespace()


def uinewprocess(txnid):
    res = loginget(txnid)
    results = res.result()

    print(results)
    results = json.loads(results)
    # print("TYPE",type(results))
    data = results['captcha']
    return render_template('index_v1.html', image=data, txnid=txnid)


@app.route('/epfo/login-get/<txnid>', methods=['GET'])
def newprocessnouiLogin(txnid):
    txnid = request.args.get('txnid')
    print("NO UI", txnid)
    rule = request.url_rule  # Get route name
    ROUTENAME = rule.rule
    print("Route", ROUTENAME)
    if ('get' in ROUTENAME):
        r.setex(txnid+'apitype', REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, 'NOUI')
        res = loginget(txnid)
        results = res.result()
        results = json.loads(results)
        # print(type(results))
        if (results['success']):
            print(results['captcha'])
            data = {
                "message": {
                    "epfo-param_c": [
                        {
                            "domain": "string",
                            "secure": "true",
                            "value": "string",
                            "httpOnly": "true",
                            "name": "string",
                            "path": "string"
                        }
                    ],
                    "epfo-param_ch": "string",
                    "epfo-im": results['captcha'],
                    "epfo-param_h": "string",
                    "epfo-param_e": "string",
                    "epfo-param_l": "string"
                },
                "success": "true",
                "code": "success"
            }
        else:
            data = results
            print(results)

        return data


@app.route('/epfo/login/<txnid>', methods=['GET'])
def newprocess(txnid):
    rule = request.url_rule  # Get route name
    ROUTENAME = rule.rule

    print("Route", ROUTENAME)
    ROUTENAME = ""
    if ('get' in ROUTENAME):
        r.setex(txnid+'apitype', REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, 'NOUI')
        res = loginget(txnid)
        results = res.result()
        return results
    else:
        print("UI METHOD")
        r.setex(txnid+'apitype', REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, 'UI')
        res = loginget(txnid)
        results = res.result()
        print("145", type(results))
        print(results)
        results = json.loads(results)
        if (results['success']):
            data = results['captcha']
            return render_template('index_v1.html', image=data, txnid=txnid)
        else:
            return results


@concurrent.process
def loginget(txnid):
    #  print("I in login GET  method",txnid)

    # logging.info("EPFO Page load request for txnid "+txnid)
    # if proxy['AWS'] == "True":
    #     r=redis.StrictRedis(host=proxy['REDIS_HOST'],
    #     port=6379,
    #     db=0,
    #     password=proxy['REDIS_PASSWORD'],
    #     ssl_cert_reqs=u'none',
    #     #ssl_ca_certs=None,
    #     ssl=True
    #     )
    # else:
    #     r=redis.StrictRedis(host=proxy['REDIS_HOST'], port=6379)
    #     print("local redis")
    # token_id=r.get(txnid+'client').decode('utf-8')
    # token_id=json.loads(token_id)
    # #logger = utils.getLogger()
    # #logger.info("success")
    # y=r.get(txnid+'apitype')
    # APITYPE=y.decode('utf-8')
    # if request.method == 'GET':
    #   if(APITYPE=='UI'):
    #     try:
    #       redirectUrl = r.lrange(txnid, 0, 1)
    #       if not redirectUrl:
    #           return json.dumps({"message": "invalid transactionid",
    #               "code": "internal_error",
    #               "success":False})

    #     except redis.ResponseError:
    #       return json.dumps({"message": "invalid transactionid",
    #           "code": "internal_error",
    #           "success":False})
    #     redirectUrl = [x.decode('utf-8') for x in redirectUrl]
    #     redirectUrl = redirectUrl[0]
    #     print("RedirectUrl GET",redirectUrl)
    #   else:
    #     print("APITYPE",APITYPE)

    # print("RedirectUrl",redirectUrl)
    # print("session_1 ALL KEYS",browser.keys())
    # browser = webdriver.Chrome(executable_path=r"/home/ubuntu/chromedriver", chrome_options=options)

    EPFO_URL = 'https://unifiedportal-mem.epfindia.gov.in/memberinterface/'

    if proxy['AWS'] == "True":
        r = redis.StrictRedis(host=proxy['REDIS_HOST'],
                              port=6379,
                              db=0,
                              password=proxy['REDIS_PASSWORD'],
                              ssl_cert_reqs=u'none',
                              # ssl_ca_certs=None,
                              ssl=True
                              )
    else:
        r = redis.StrictRedis(host=proxy['REDIS_HOST'], port=6379)
        print("local redis")
    selenium_url = "http://ec2-13-233-217-249.ap-south-1.compute.amazonaws.com:4445/wd/hub"
    browser = webdriver.Remote(selenium_url, options=options)

    print("Loginget", browser)
    # pid=browser.service.process.pid
    session = {'executor_url': browser.command_executor._url,
               'session_id': browser.session_id,
               # 'pid':pid
               }
    r.setex(txnid+'session', REDIS_TRANSACTIONID_KEY_EXPIRE_SECS,
            json.dumps(session))
    print("***********************")
    # print('PID',pid)

    # try:
    print('in try')
    browser.get(EPFO_URL)
    browser.find_element(
        By.XPATH, '/html/body/div[2]/div/div[3]/div[3]/div[3]/div/div[2]/ul/li[4]/a').click()
    # browser.find_element(By.XPATH,'//*[@id="mobileNo"]').send_keys("9600581434")
    captcha = browser.find_element(
        By.XPATH, '//*[@id="captchaDiv"]/div[1]/img')
    data = captcha.screenshot_as_base64
    print(DeprecationWarning)

    # except AssertionError as error1:
    #     logger.error("Epfo site is Busy for txnid",extra={'txnid': txnid,'code':'failure','client_id':token_id['client_id'],"client_name":token_id['client_name'],'client_ip': request.remote_addr})
    #     browser.close()
    #     kill_chrome(pid,txnid)
    #     logging.error("Epfo site is Busy for txnid "+txnid)
    #     return json.dumps({'message':"Epfo site is Busy,pls make the request again",
    #                       'code':'fail',
    #                       'success':False})

    return json.dumps({'captcha': data,
                      'code': 'success',
                       'success': True})

####################################################################################


@app.route('/epfo/submit-post/', methods=['POST'])
def newprocess_post_noui():
    txnid = request.args.get('txnid')
    res = loginpost(txnid)
    print("RES", res)
    results = res.result()
    print("results:", results)
    x = r.get(txnid+'session')
    session = x.decode('utf-8')
    session = json.loads(session)
    pid = session['pid']
    print('session', pid)
    kill_chrome(pid, txnid)
    return results


@app.route('/epfo/login/<txnid>', methods=['POST'])
def newprocess_post_ui(txnid):
    if request.method == "POST":
        print("Iam in POST")
        res = loginpost(txnid)
        results = res.result()
        x = r.get(txnid+'session')
        session = x.decode('utf-8')
        session = json.loads(session)
        pid = session['pid']
        print('session', pid)
        kill_chrome(pid, txnid)
    return results


@concurrent.process
def loginpost(txnid):
    print("I am in loginpost")
    # token_id=r.get(txnid+'client').decode('utf-8')
    # token_id=json.loads(token_id)
    x = r.get(txnid+'session')
    session = x.decode('utf-8')
    session = json.loads(session)
    print('session', session)
    session_id = session['session_id']
    executor_url = session['executor_url']
    # pid=session['pid']
    browser = create_driver_session(session_id, executor_url)
    # y=r.get(txnid+'apitype')
    APITYPE = "UI"
    # APITYPE=y.decode('utf-8')
    print("API", APITYPE)

    mobile_numer = request.form['username']  # mobile
    # password= request.form['password']
    captcha1 = request.form['captcha']
    print("in Except***********")

    print(mobile_numer, captcha1)
    try:
        browser.find_element(
            By.XPATH, '//*[@id="mobileNo"]').send_keys(mobile_numer)
        browser.find_element(
            By.XPATH, '//*[@id="captcha"]').send_keys(captcha1)
        browser.find_element(By.XPATH, '//*[@id="get-otp-btn"]').click()
        # wait1 = WebDriverWait(browser, 20)
        # wait1.until(ec.visibility_of_element_located((By.XPATH,'//*[@id="successBtn"]/i')))

        # browser.find_element(By.XPATH,'//*[@id="successBtn"]/i').click()
        # captcha2=browser.find_element(By.XPATH,'//*[@id="captchaDiv"]/div[1]/img')
        # data2=captcha2.screenshot_as_base64
        # return render_template('index_v1.html',image=data2,txnid = txnid)

    except Exception as e:
        print("in Except***********")
        logging.error(e, exc_info=True)
        browser.save_screenshot('chrom223.png')

    return json.dumps({})

    # breakpoint()

    # breakpoint()
    #   try:
    #     print('Iam in try*********')
    #     redirectUrl = r.lrange(txnid, 0, 1)
    #     if not redirectUrl:
    #         return json.dumps({"message": "invalid transactionid",
    #             "code": "internal_error",
    #             "success":False})
    #   except redis.ResponseError:
    #     return json.dumps({"message": "invalid transactionid",
    #         "code": "internal_error",
    #         "success":False})
    #   redirectUrl = [x.decode('utf-8') for x in redirectUrl]
    #   redirectUrl = redirectUrl[0]
    #   print("RedirectUrl POST",redirectUrl)
    # logging.info("Received username,password,captcha for txnid "+txnid)
    # try:
    #   print('Iam in try!!!!')
    #   browser.find_element_by_xpath('//*[@id="userName"]').send_keys(username)
    #   browser.find_element_by_xpath('//*[@id="password"]').send_keys(password)
    #   browser.find_element_by_xpath('//*[@id="captcha"]').send_keys(captcha)
    #   browser.find_element_by_xpath('//*[@id="AuthenticationForm"]/div[5]/div[2]/button').submit()
    #   logger.info("Posted login-data to EPFO",extra={'txnid': txnid,'code':'success','client_id':token_id['client_id'],"client_name":token_id['client_name'],'client_ip': request.remote_addr})

    #   logging.info("Submitted username,password,captcha for txnid "+txnid)
    #   wait = WebDriverWait(browser, 10)
    #   wait1 = WebDriverWait(browser, 20)
    #   try:
    #       wait1.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="btnCloseModal"]')))
    #       browser.find_element_by_xpath('//*[@id="btnCloseModal"]').click()
    #       logging.info("Closed the dialogue box for txnid "+txnid)
    #       print("closed the dialogue box")
    #   except:
    #       error=browser.find_element_by_xpath('/html/body/div[2]/div/div[3]/div[1]/div[2]/div/div[2]/div/div[1]').text
    #       error=error.split('\n')[0]
    #       print("Error",error)
    #       logger.error(str(error),extra={'txnid': txnid,'code':'failure','client_id':token_id['client_id'],"client_name":token_id['client_name'],'client_ip': request.remote_addr})
    #       browser.close()
    #       kill_chrome(pid,txnid)
    #       logging.error(str(error)+"for txnid "+txnid)
    #       errormsg=error.lower()

    #       print("APITYPE******************",APITYPE)
    #       if(APITYPE=='UI'):
    #         return errorhandling(errormsg,txnid,redirectUrl)
    #       else:
    #         r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, json.dumps({"message": errormsg,
    #                       "code": 'fail',
    #                       "success":False}) )
    #         return json.dumps({'message':errormsg,
    #                           'code':'fail',
    #                           'success':False})
    #   time.sleep(2)
    #   print('**********************************************')
    #   print('Logged in as ', username)
    #   print('**********************************************')
    #   print("button closed")
    #   browser.find_element_by_xpath('//*[@id="menu"]/li[2]/a').click()
    #   print("view_button")
    #   logging.info("Clicked the View button for txnid "+txnid)
    #   browser.find_element_by_xpath('//*[@id="menu"]/li[2]/ul/li[2]/a').click()
    #   logging.info("Clicked the Service history button for txnid "+txnid)
    #   wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="viewMember"]/div[1]/div[1]/h3')))
    #   page_source=browser.page_source
    #   epfo_data=scrapThePage(page_source)
    #   logging.info("Scrapped the UAN details for txnid "+txnid)
    #   logger.info("fetched report details",extra={'txnid': txnid,'code':'success','client_id':token_id['client_id'],"client_name":token_id['client_name'],'client_ip': request.remote_addr})
    #   browser.close()                 ###close browser after scraping
    #   kill_chrome(pid,txnid)
    #   #del browser[txnid]
    #   #del browser[txnid+"_createtime"]
    #   print("Quitting the browser",txnid)
    #   print("EPFO_DATA",epfo_data)

    #   r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, json.dumps({"message": epfo_data,
    #       "code": "success",
    #       "success":True}) )
    #   print("Redirecting success url 200")
    #   #kill=killStaleBrowsers()
    #   #print("Stale browsers are killed",kill)
    #   if(APITYPE=='UI'):
    #     return redirect(redirectUrl + '?status=success&status_code=200&txnid=' + txnid)
    #   else:
    #     return json.dumps(
    #                         {"message": epfo_data,
    #                         "code": "success",
    #                         "success":True}
    #                       )

    # except Exception as e:
    #   print("Error****",e)
    #   epfo_data="Epfo site is not accessible, Pls try after sometime"
    #   logger.error(epfo_data,extra={'txnid': txnid,'code':'failure','client_id':token_id['client_id'],"client_name":token_id['client_name'],'client_ip': request.remote_addr})

    #   logging.error("Error of txnid "+str(e)+txnid)
    #   logging.error("Epfo site is not accessible, Pls try after sometime "+txnid)
    #   browser.close()
    #   kill_chrome(pid,txnid)
    #   #try:
    #     #browser[txnid].close()
    #     #del browser[txnid]
    #     #del browser[txnid+"_createtime"]
    #     #print("Quitting txnid",txnid)
    #   #except:
    #   #  print("Error on deleting tid")
    #   #kill=killStaleBrowsers()
    # return json.dumps({})


def scrapThePage(page_source):
    epfo_data = list()
    soup_level1 = BeautifulSoup(page_source, 'lxml')
    table = soup_level1.find_all('table')[0]
    dt = soup_level1.find_all('span')
    df = dt[6].text.split('\n')
    uan = df[1].replace(' ', '').replace('UAN:', '')
    name = df[2].replace('/', '')
    rows = table.find_all('tr')

    for tr in rows:
        td = tr.find_all('td')
        if (td):
            row = {'name': name,
                   'uan': uan,
                   'company': td[2].text,
                   'doj': td[4].text,
                   'doe': td[5].text}
            if (row['doe'] == 'NOT AVAILABLE'):
                row['doe'] = 'NOT_AVAILABLE'
            epfo_data.append(row)
    return epfo_data


def errorhandling(errormsg, txnid, redirectUrl):
    if ('captcha' in errormsg):
        r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, json.dumps({"message": "invalid captcha",
                                                                        "code": "invalid_captcha",
                                                                        "success": False}))
        url = redirectUrl + '?status=invalid_captcha&status_code=402&txnid=' + txnid
        print("Redirecting captcha fail", url)

    elif 'username or password' in errormsg:
        r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, json.dumps({"message": "invalid username or password",
                                                                        "code": "invalid_usr_pwd",
                                                                        "success": False}))
        url = redirectUrl + '?status=invalid_usr_pwd&status_code=401&txnid=' + txnid
        print("Redirecting username /passw fail", url)

    else:
        r.setex(txnid, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, json.dumps({"message": "service unavailable",
                                                                        "code": "internal_error",
                                                                        "success": False}))
        # return str(temp['status'])
        url = redirectUrl + '?status=internal_error&status_code=504&txnid=' + txnid
        print("Redirecting unknown fail", url)
    print("Redirecting to ", url)
    return redirect(url)


def browser_list():
    kys = browser.keys()
    b = len(kys)
    print("Browser keys", kys)
    print("Browsers length", b)
    return str(kys)


@app.route('/browser', methods=['GET', 'POST'])
def killStaleBrowsers():
    """
    close browser that is is more than 20mns old
    and remove entry in global driver dict
    """
    print("No of browsers before killing", len(browser.keys()))
    for k, v in browser.items():

        print("TEST", k, v)
        if (type(v) == int):
            curr_time = int(time.time())
            run_time = curr_time-v
            if (run_time > 300):
                # finding the txnid from key "DIGI1729663953728631095450218_createdtime"
                tid = k.split("_createtime")[0]
                try:
                    # browser[tid].close() ### closing the browser
                    # browser[tid].quit()
                    # kill_chrome(browser[tid].service.process.pid)
                    print('Stale SEssion:', browser[tid], browser[k])
                    del browser[tid]  # deletimg the browser object key
                    del browser[k]  # deleting the timestamp key
                except Exception as e:
                    print("Error occured while killing browser", e)
    print('No of browsers after killing', len(browser.keys()), browser)
    return "True"


def kill_chrome(thepid, txnid):
    try:
        os.kill(thepid, signal.SIGKILL)
        # del browser[txnid]  ### deletimg the browser object key
        # k=txnid+"_createtime"
        # del browser[k]    ### deleting the timestamp key
        print("killed Pid: ", thepid)
        return 1
    except Exception as e:
        print("failed to kill Pid: ", str(e))
        return 0


"""
print ("Loaded thing, now I' kill it!")
try:
    driver.close()
    driver.quit()
    driver.dispose()
except:
    pass
"""


def create_driver_session(session_id, executor_url):
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params)

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(
        command_executor=executor_url, desired_capabilities={})
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute

    return new_driver


@app.route('/epfo/generate-post/', methods=['POST'])
def generateAccesstoken():

    # Expiry time for redis to store the access token : A week in seconds
    REDIS_ACCESS_TOKEN_KEY_EXPIRE_SECS = 10 * 24 * 60 * 60
    event = request.get_json()
    client_id = event['client_id']
    # client        = r.get('client_name')
    client_secret = event['client_secret']

    if client_id is not None and client_secret is not None:

        stored_client_names = [
            x.decode('utf-8') for x in r.lrange('stored_client_names_epfo', 0, -1)]

        for c in stored_client_names:
            # temp = {'client_id': ..., 'client_secret': ...}
            temp = (r.get(c)).decode('utf-8')
            temp = json.loads(temp)  # convert to dict

            if temp['client_id'] == client_id:

                # obtain client_name from client_id
                client = json.loads(r.get(c).decode('utf-8'))

                if client['client_id'] == client_id:
                    if client['client_secret'] == client_secret:
                        access_token = str(uuid.uuid4())
                        param = {
                            'access_token': access_token,
                            'client_id':    client_id,
                            'client_name': c,
                            'expires_in':   900,
                            'created_time': int(time.time()),
                        }
                        r.set(access_token, json.dumps(param))
                        r.expire(access_token,
                                 REDIS_ACCESS_TOKEN_KEY_EXPIRE_SECS)
                        logger.info("access_token generated", extra={
                                    'txnid': access_token, 'code': 'success', 'client_id': client_id, "client_name": c, 'client_ip': request.remote_addr})
                        return {
                            'message': param,
                            'code': 'success',
                            'success': True
                        }

                    else:
                        logger.error("client secret is not correct", extra={
                                     'txnid': "None", 'code': 'failure', 'client_id': client_id, "client_name": c, 'client_ip': request.remote_addr})
                        return {
                            "message": "client secret is not correct",
                            "code": "internal_error",
                            "success": False}
        else:
            return {
                "message": "client id is not registered",
                "code": "internal_error",
                "success": False}
    else:
        return {
            "message": "client id and client secret is not provided",
            "code": "internal_error",
            "success": False}


@app.route('/epfo/transaction-get/', methods=['GET'])
def generateTransactionId():
    # logger = utils.getLogger()
    event = request.get_json()
    # context_serializable = {k:v for k, v in context.__dict__.items() if type(v) in [int, float, bool, str, list, dict]}
    # uan         = event['body']['uan']
    try:
        redirectUrl = event['redirectUrl']
    except:
        redirectUrl = DIGIVERIFIER_URL

    try:
        auth = request.headers['bearer']
    except KeyError:
        return {"message": "Authorization header is expected",
                "code": "authorization_header_missing",
                "success": False}

    token = auth
    if r.exists(token):
        cid_details = r.get(token)
        token_id = json.loads(cid_details)
        t = int(time.time()) - int(token_id['created_time'])
        if int(token_id['expires_in']) >= t:
            # print("Logger here")
            data = gen_token(redirectUrl)  # generate transactionid
            txnid = data['message']
            r.setex(txnid+'client',
                    REDIS_TRANSACTIONID_KEY_EXPIRE_SECS, cid_details)
            # print(r.get(txnid+'client'))
            logger.info("txnid generated", extra={
                        'txnid': txnid, 'code': 'success', 'client_id': token_id['client_id'], "client_name": token_id['client_name'], 'client_ip': request.remote_addr})
            return data
            # return f(*args, **kwargs)
        else:
            logger.error("txnid generation failed,token gets expired", extra={
                         'txnid': "None", 'code': 'failure', 'client_id': token_id['client_id'], "client_name": token_id['client_name'], 'client_ip': request.remote_addr})
            return {"message": "token gets expired ",
                    "code":    "expired_token",
                    "success":  False}
    else:
        return {"message": "token is invalid for the client",
                "code":    "invalid_token",
                "success":  False}

    return {
        'uan': uan,
        'redirectUrl': redirectUrl,
        'header': auth
    }


# Generates transaction id and stores in pan key (list data structure)
def gen_token(redirectUrl):

    txnidPOST = str(uuid.uuid1().int)

    r.lpush(txnidPOST, redirectUrl)  # store transaction id as second element
    r.expire(txnidPOST, REDIS_TRANSACTIONID_KEY_EXPIRE_SECS)  # key expires in
    r.ltrim(txnidPOST, 0, 0)  # Take only first two elements

    return {
        'message': txnidPOST,
        "redirectUrl": redirectUrl,
        'code': 'success',
        'success': 'True'
    }


@app.route('/epfo/report-get/', methods=['GET'])
def fetch_report():
    # context_serializable = {k:v for k, v in context.__dict__.items() if type(v) in [int, float, bool, str, list, dict]}
    # uan         = event['body']['uan']
    # redirectUrl = event['body']['redirectUrl']

    txnid = request.args.get('txnid')
    # format = request.args.get('format')

    try:
        auth = request.headers['Bearer']
        print("Berer", auth)
    except KeyError:
        return {"message": "Authorization header is expected",
                "code": "authorization_header_missing",
                "success": False}

    # r.set('pan', pan)
    """
    parts = auth.split()
    if parts[0].lower() != "bearer":
        return {"message": "Authorization header must start with Bearer",
                        "code": "invalid_header",
                        "success": False}
    elif len(parts) == 1:
        return {"message": "Token not found",
                        "code": "invalid_header",
                        "success": False}
    elif len(parts) > 2:
        return {"message": "Authorization header must be Bearer Token",
                        "code": "invalid_header",
                        "success": False}
    """
    token = auth
    if r.exists(token):
        token_id = json.loads(r.get(token))
        t = int(time.time()) - int(token_id['created_time'])
        if int(token_id['expires_in']) >= t:
            return get_report(txnid, token_id)  # generate transactionid
            # return f(*args, **kwargs)
        else:
            return {"message": "token gets expired ",
                    "code":    "expired_token",
                    "success":  False}
    else:
        return {"message": "token is invalid for the client",
                "code":    "invalid_token",
                "success":  False}


def get_report(txnid, token_id):
    try:
        temp = r.get(txnid)
    except redis.exceptions.ResponseError:
        logger.error("report processing", extra={
                     'txnid': txnid, 'code': 'failure', 'client_id': token_id['client_id'], "client_name": token_id['client_name'], 'client_ip': request.remote_addr})
        # condition when transactionid key is not yet changed to hold report output
        # i.e., it is still a list that holds uan and redirectUrl
        return {"message": "report processing",
                "code":    "report_processing",
                "success":  False}

    if temp is not None:
        temp = temp.decode('utf-8')
        try:
            data = json.loads(temp)
            logger.info("report delivered successfully", extra={
                        'txnid': txnid, 'code': 'success', 'client_id': token_id['client_id'], "client_name": token_id['client_name'], 'client_ip': request.remote_addr})

        except:
            logger.error("Report not generated", extra={
                         'txnid': txnid, 'code': 'failure', 'client_id': token_id['client_id'], "client_name": token_id['client_name'], 'client_ip': request.remote_addr})

            data = {"message": "Report not generated",
                    "code": "internal error",
                    "success": False}
        return data

    else:

        return {"message": "transactionid expires",
                "code": "internal_error",
                "success": False}


@app.route('/epfo/generate_invoice', methods=['GET', 'POST'])
def generate_invoice():
    from datetime import datetime
    client = request.args.get('client', None)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    print(start_date, end_date)
    utils.generateInvoiceCSV(client, start_date, end_date)
    try:
        return send_file(os.path.join(utils.path, client+'.xlsx'), as_attachment=True)
    except Exception as e:
        print('ERROR!!', e)
        abort(404)

    return True
