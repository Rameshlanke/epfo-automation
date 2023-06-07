import json
import response
import requests
import pandas as pd
from base64 import b64decode
# import codecs
import base64
# import time
from PIL import Image
from flask import Flask, render_template, request, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import traceback
app = Flask(__name__)

chrome_options = Options()
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
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
    try:

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
    
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the full traceback
        print("An exception occurred:", e)


@app.route('/submit-otp', methods=['POST'])
def submit_otp():
    try:
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
        
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the full traceback
        print("An exception occurred:", e)


@app.route('/enter-otp', methods=['POST'])
def enter_otp():
    try:
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
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the full traceback
        print("An exception occurred:", e)


@app.route('/get-uan', methods=['POST'])
def get_uan():
    try:
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

        datepicker_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='dob']")))
        datepicker_element.click()

        date_of_birth = request.form['dob'] #(dd/MM/yyyy) 01/01/1970    

        day, month, year = date_of_birth.split('/')
        month = int(month)
        month_value = month - 1
        year_value = int(year)
        day_value = int(day)
        # time.sleep(3)
        # /epfo/login
        wait = WebDriverWait(driver, 20)
        # time.sleep(10)
        month_dropdown = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='ui-datepicker-div']/div/div/select[1]")))
        month_dropdown.find_element(
            By.XPATH, f"option[@value='{month_value}']").click()
        print("Month Done")
        month_dropdown = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='ui-datepicker-div']/div/div/select[2]")))
        month_dropdown.find_element(
            By.XPATH, f"option[@value='{year_value}']").click()
        print("Year Done")

        datepicker_tbody = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody')))
        number_element = datepicker_tbody.find_element(
            By.XPATH, f".//a[contains(text(), '{day_value}')]")
        number_element.click()
        print("Day Done")

        btn_show_uan = driver.find_element(By.XPATH, '//*[@id="get-otp-btn"]')
        btn_show_uan.click()

           
        try:
            wait = WebDriverWait(driver, 10)
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
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the full traceback
        print("An exception occurred:", e)


# prod = 'https://example.com'  # Replace with the correct URL


@app.route('/get-data')
def function_get_data(uan_num):
    global prod
    uan_num = str(uan_num)

    prod = "https://api-oauth2.digiverifier.com"
    test = "http://ec2-13-233-217-249.ap-south-1.compute.amazonaws.com:7000"
    # check = test
    try:

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
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the full traceback
        print("An exception occurred:", e)


if __name__ == '__main__':
    app.run(debug=True)

