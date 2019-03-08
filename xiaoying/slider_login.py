# encoding:utf8
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, ElementNotVisibleException
import time
from PIL import Image
import numpy as np


def get_track(distance):
    """
    根据偏移量获取移动轨迹
    :param distance: 偏移量
    :return: 移动轨迹
    """
    # 移动轨迹
    track = []
    # 当前位移
    current = 0
    # 减速阈值
    mid = distance * 2 / 5
    # 计算间隔
    t = 0.5
    # 初速度
    v = 0

    while current < distance:
        if current < mid:
            # 加速度为正2
            a = 2
        else:
            # 加速度为负3
            a = -3
        # 初速度v0
        v0 = v
        # 当前速度v = v0 + at
        v = v0 + a * t
        # 移动距离x = v0t + 1/2 * a * t^2
        move = v0 * t + 1 / 2 * a * t * t
        # 当前位移
        current += move
        # 加入轨迹
        track.append(round(move))
    return track

class Slider(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()
        self.config_init()
        self.driver.set_window_size(self.window_weight, self.window_height)

    def config_init(self):
        self.origin_captcha_path = './captcha/origin.png'
        self.incomplete_captcha_path = './captcha/incomplete.png'
        self.window_weight = 1280
        self.window_height = 800
        self.WAIT_SECONDS = 3
        self.crop_size = (500, 245, 757, 426)
        self.threshold = 150
        self.left_gap_weight = 15.5
        self.diff_of_y_pixels = 2
        self.max_attempt_times = 4

    def before_slider_appear(self):
        self.driver.get('https://www.xiaoying.com/user/login')
        username_input_ele = self.driver.find_element_by_css_selector('input.i-text.jUsername')
        username_input_ele.send_keys(self.username)
        password_input_ele = self.driver.find_element_by_css_selector('input.i-text.jPassword')
        password_input_ele.send_keys(self.password)
        self.click_login()

    def save_slider_captcha(self):
        get_origin_image_js = 'document.getElementsByClassName("geetest_canvas_fullbg")[0].style.display="block"'
        self.driver.execute_script(get_origin_image_js)
        self.driver.save_screenshot(self.origin_captcha_path)
        get_incomplete_image_js = 'document.getElementsByClassName("geetest_canvas_fullbg")[0].style.display="none";document.getElementsByClassName("geetest_canvas_slice")[0].style.display="none"'
        self.driver.execute_script(get_incomplete_image_js)
        self.driver.save_screenshot(self.incomplete_captcha_path)

    def get_distance(self):
        im1 = Image.open(self.origin_captcha_path)
        im1 = im1.resize((self.window_weight, self.window_height))
        im1 = im1.crop(self.crop_size)
        im2 = Image.open(self.incomplete_captcha_path)
        im2 = im2.resize((self.window_weight, self.window_height))
        im2 = im2.crop(self.crop_size)
        im1 = im1.convert('L')
        im2 = im2.convert('L')
        table = []
        for i in range(256):
            if i < self.threshold:
                table.append(0)
            else:
                table.append(1)
        im1 = im1.point(table, '1')
        im2 = im2.point(table, '1')
        arr1 = np.array(im1)
        arr2 = np.array(im2)
        y_pixel_1 = np.sum(arr1, axis=0)
        y_pixel_2 = np.sum(arr2, axis=0)
        diff_abs = np.abs(y_pixel_1 - y_pixel_2)
        self.distance = np.where(diff_abs >= self.diff_of_y_pixels)[0][0] - self.left_gap_weight


    def drag_slider(self):
        slider = self.driver.find_element_by_css_selector("div.geetest_slider_button")
        track = get_track(self.distance)
        webdriver.ActionChains(self.driver).click_and_hold(slider).perform()
        for x in track:
            webdriver.ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        webdriver.ActionChains(self.driver).release().perform()
        # self.driver.implicitly_wait(30)
        time.sleep(self.WAIT_SECONDS)


    def click_login(self):
        login_submit_ele = self.driver.find_element_by_css_selector('a.btn.btn-2.jSubmit')
        login_submit_ele.click()
        time.sleep(self.WAIT_SECONDS)

    def judge_password_wrong(self):
        self.driver.find_element_by_css_selector("div.err-tip.jErrorContainer")

    def judge_slider_success(self):
        try:
            self.driver.find_element_by_css_selector('a.geetest_refresh_1').click()
            return False
        except ElementNotVisibleException:
            return True
        except NoSuchElementException:
            return True


    def check_login_res(self):
        try:
            self.driver.find_element_by_css_selector('div#header li a[href="https://www.xiaoying.com/user/logout"]')
            return 0
        except NoSuchElementException:
            pass
        if u'不正确' in self.driver.find_element_by_css_selector('div.err-tip.jErrorContainer').text:
            return 1
        if u'登陆账户是手机号':
            return 1

    def if_slider_appear(self):
        try:
            self.driver.find_element_by_css_selector('a.geetest_refresh_1').click()
            time.sleep(2)
            return True
        except NoSuchElementException:
            return False

    def run(self):
        res = 99
        for _ in range(self.max_attempt_times):
            self.before_slider_appear()
            if self.if_slider_appear():
                print 'slider appeared~'
                self.save_slider_captcha()
                self.get_distance()
                if self.distance >= self.crop_size[2]-self.crop_size[0]:
                    print 'distance is too longer'
                    continue
                self.drag_slider()
                print 'action slide have completeed'
                if not self.judge_slider_success():
                    print 'failure of sliding validation'
                    continue
                print 'successful of sliding validation'
            res = self.check_login_res()
            if res == 0 or res == 1:
                print 'login result code:%s' % res
                break
            print 'login result is unknown, continue~'
        return res

if __name__ == '__main__':
    res = 0
    s = Slider('', '')
    print s.run()
