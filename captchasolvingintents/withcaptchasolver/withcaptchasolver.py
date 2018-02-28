## BASED ON: http://scraping.pro/recaptcha-solve-selenium-python/ - ADDED captcha-solver:
## https://github.com/lorien/captcha_solver

from captcha_solver import CaptchaSolver
from time import sleep, time
from random import uniform, randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import urllib

def wait_between(a,b):
	rand=uniform(a, b) 
	sleep(rand)

def dimention(driver): 
	d = int(driver.find_element_by_xpath('//div[@id="rc-imageselect-target"]/table').get_attribute("class")[-1]);
	return d if d else 3  # dimention is 3 by default
	


url='http://ubuntu-jeffermendoza.c9users.io/catcha/1.html'
driver = webdriver.Chrome()
driver.get(url)

buttons = driver.find_element(By.XPATH,"//*[@class='solid fat info button']")
buttons.click()
mainWin = driver.current_window_handle

driver.switch_to_frame(driver.find_elements_by_tag_name("iframe")[0])

# ************* recaptcha Checkbox *************
check_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID ,"recaptcha-anchor"))
        )

# *************  click CheckBox  ***************
wait_between(0.5, 0.7)  
# making click on captcha CheckBox 
check_box.click() 
 
#***************** back to main window **************************************
driver.switch_to_window(mainWin)  

wait_between(2.0, 2.5) 

# ************ switch to the second iframe by tag name ******************
driver.switch_to_frame(driver.find_elements_by_tag_name("iframe")[1])

WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID ,"rc-imageselect-target"))
        )

dim = dimention(driver)

img = driver.find_element_by_css_selector('div.rc-image-tile-wrapper > img')
src = img.get_attribute('src') 

urllib.urlretrieve(src, "captcha.jpeg")

# ********** for captcha solving **************************
solver = CaptchaSolver('antigate', api_key='--')
raw_data = open('captcha.jpeg', 'rb').read()
print(solver.solve_captcha(raw_data))
