#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
@project: AutoXue
@file: __init__.py
@author: kessil
@contact: https://github.com/kessil/AutoXue/
@time: 2019-10-26(星期六) 09:03
@Copyright © 2019. All rights reserved.
'''
import re
import random
import time
import requests
import string
import subprocess
from urllib.parse import quote
from collections import defaultdict
from appium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .unit import Timer, logger, caps, rules, cfg
from .model import BankQuery

class Automation():
    # 初始化 Appium 基本参数
    def __init__(self):
        self.connect()
        self.desired_caps = {
            "platformName": caps["platformname"],
            "platformVersion": caps["platformversion"],
            "automationName": caps["automationname"],
            "unicodeKeyboard": caps["unicodekeyboard"],
            "resetKeyboard": caps["resetkeyboard"],
            "noReset": caps["noreset"],
            'newCommandTimeout': 800,
            "deviceName": caps["devicename"],
            "uuid": caps["uuid"],
            "appPackage": caps["apppackage"],
            "appActivity": caps["appactivity"]
        }
        logger.info('打开 appium 服务,正在配置...')
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.wait = WebDriverWait(self.driver, 10)
        self.size = self.driver.get_window_size()

    def connect(self):
        logger.info(f'正在连接模拟器 {caps["uuid"]}，请稍候...')
        if 0 == subprocess.check_call(f'adb connect {caps["uuid"]}', shell=True, stdout=subprocess.PIPE):
            logger.info(f'模拟器 {caps["uuid"]} 连接成功')
        else:
            logger.info(f'模拟器 {caps["uuid"]} 连接失败')

    def disconnect(self):
        logger.info(f'正在断开模拟器 {caps["uuid"]}，请稍候...')
        if 0 == subprocess.check_call(f'adb disconnect {caps["uuid"]}', shell=True, stdout=subprocess.PIPE):
            logger.info(f'模拟器 {caps["uuid"]} 断开成功')
        else:
            logger.info(f'模拟器 {caps["uuid"]} 断开失败')

    # 屏幕方法
    def swipe_up(self):
        # 向上滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.65, 0.75),
                          self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.25, 0.35), random.uniform(800, 1200))
        logger.debug('向上滑动屏幕')

    def swipe_down(self):
        # 向下滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.25, 0.35),
                          self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.65, 0.75), random.uniform(800, 1200))
        logger.debug('向下滑动屏幕')

    def swipe_right(self):
        # 向右滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.01, 0.11),
                          self.size['height'] * random.uniform(0.75, 0.89),
                          self.size['width'] * random.uniform(0.89, 0.98),
                          self.size['height'] * random.uniform(0.75, 0.89), random.uniform(800, 1200))
        logger.debug('向右滑动屏幕')
    def swipe_left(self):
        # 向右滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.89, 0.98),
                          self.size['height'] * random.uniform(0.75, 0.89),
                          self.size['width'] * random.uniform(0.01, 0.11),
                          self.size['height'] * random.uniform(0.75, 0.89), random.uniform(800, 1200))
        logger.debug('向左滑动屏幕')

    # 返回事件
    def safe_back(self, msg='default msg'):
        logger.debug(msg)
        self.driver.keyevent(4)
        time.sleep(1)

    def safe_click(self, ele:str):
        self.wait.until(EC.presence_of_element_located((By.XPATH, ele))).click()
        time.sleep(1)

    def __del__(self):
        self.driver.close_app()
        self.driver.quit()


class App(Automation):
    def __init__(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }
        self.query = BankQuery()
        self.bank = None
        self.score = defaultdict(tuple)

        super().__init__()
        self.driver.wait_activity('com.alibaba.android.rimet.biz.home.activity.HomeActivity', 20, 3)
        self.view_score()
        self._read_init()
        self._view_init()
        self._daily_init()
        self._challenge_init()


    def view_score(self):
        self.safe_click(rules['score_entry'])
        titles = ["登录", "阅读文章", "视听学习", "文章学习时长", 
                "视听学习时长", "每日答题", "每周答题", "专项答题", 
                "挑战答题", "订阅", "收藏", "分享", "发表观点"]
        score_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['score_list'])))
        for t, score in zip(titles, score_list):
            s = score.get_attribute("name")
            self.score[t] = tuple([int(x) for x in re.findall(r'\d+', s)])

        # print(self.score)
        for i in self.score:
            logger.debug(f'{i}, {self.score[i]}')
        self.safe_back('score -> home')

    def back_or_not(self, title):
        return False
        g, t = self.score[title]
        if g == t:
            logger.debug(f'{title} 积分已达成，无需重复获取积分')
            return True
        return False

    def _search(self, content, options, exclude=''):
        logger.debug(f'搜索 {content} <exclude = {exclude}>')
        logger.info(f"选项 {options}")
        content = re.sub(r'[\(（]出题单位.*', "", content)
        if options[-1].startswith("以上") and chr(len(options)+64) not in exclude:
            logger.info(f'根据经验: {chr(len(options)+64)} 很可能是正确答案')
            return chr(len(options)+64)
        # url = quote('https://www.baidu.com/s?wd=' + content, safe=string.printable)
        url = quote("https://www.sogou.com/web?query=" + content, safe=string.printable)
        response = requests.get(url, headers=self.headers).text
        counts = []
        for i, option in zip(['A', 'B', 'C', 'D', 'E', 'F'], options):
            count = response.count(option)
            counts.append((count, i))
            logger.info(f'{i}. {option}: {count} 次')
        counts = sorted(counts, key=lambda x:x[0], reverse=True)
        counts = [x for x in counts if x[1] not in exclude]
        c, i = counts[0]
        # 降序排列第一个为计数最大值
        if 0 == c:
            randchoiceint = random.randint(1, len(options)) # 0-index + 1
            randchoicechar = chr(randchoiceint+64)
            logger.info(f'搜索结果count全0，随机一个 {randchoicechar}')
            return randchoiceint-1
        logger.info(f'根据搜索结果: {i} 很可能是正确答案')
        return i

    def _verify(self, category, content, options):
        logger.debug(f'{category} {content} {options}')
        self.bank = self.query.get({
            "category": category,
            "content": content,
            "options": options
        })
        # logger.info(options)
        if self.bank and self.bank["answer"]:
            logger.info(f'已知的正确答案: {self.bank["answer"]}')
            return self.bank["answer"]
        if "多选题" == category:
            return "ABCDEFG"[:len(options)]
        elif "填空题" == category:
            return None # ''.join(random.sample(string.ascii_letters + string.digits, 8))
        else:
            if self.bank and self.bank["excludes"]:
                logger.info(f'已知的排除项有: {self.bank["excludes"]}')
                return self._search(content, options, self.bank["excludes"])
            return self._search(content, options)

    def _update_bank(self, item):
        if not self.bank or not self.bank["answer"]:
            self.query.put(item)

# 挑战答题模块
# class Challenge(App):
    def _challenge_init(self):
        # super().__init__()
        try:
            self.challenge_count = cfg.getint('prefers', 'challenge_count')
        except:
            g, t = self.score["挑战答题"]
            if t == g:
                self.challenge_count = 0
            else:
                self.challenge_count = random.randint(
                        cfg.getint('prefers', 'challenge_count_min'), 
                        cfg.getint('prefers', 'challenge_count_max'))

        self.delay_bot = cfg.getint('prefers', 'challenge_delay_min')
        self.delay_top = cfg.getint('prefers', 'challenge_delay_max')

    def _challenge_cycle(self, num):
        self.safe_click(rules['challenge_entry'])
        while num:
            content = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, rules['challenge_content']))).get_attribute("name")
            option_elements = self.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, rules['challenge_options'])))
            options = [x.get_attribute("name") for x in option_elements]
            length_of_options = len(options)
            logger.info(f'<{num}> {content}')
            answer = self._verify(category='单选题', content=content, options=options)
            delay_time = random.randint(self.delay_bot, self.delay_top)
            logger.info(f'随机延时 {delay_time} 秒提交答案: {answer}')
            time.sleep(delay_time)
            option_elements[ord(answer)-65].click()
            try:
                time.sleep(2)
                wrong = self.driver.find_element_by_xpath(rules['challenge_revival'])
                logger.debug(f'很遗憾回答错误')
                self._update_bank({
                        "category": "单选题",
                        "content": content,
                        "options": options,
                        "answer": "",
                        "excludes": answer,
                        "notes": ""
                    })
                break
            except:
                logger.debug(f'回答正确')
                num -= 1            
                self._update_bank({
                    "category": "单选题",
                    "content": content,
                    "options": options,
                    "answer": answer,
                    "excludes": "",
                    "notes": ""
                })
        else:
            logger.info(f'已完成指定题量, 本题故意答错后自动退出，否则延时30秒等待死亡')
            content = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, rules['challenge_content']))).get_attribute("name")
            option_elements = self.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, rules['challenge_options'])))
            options = [x.get_attribute("name") for x in option_elements]
            length_of_options = len(options)
            logger.info(f'<{num}> {content}')
            answer = self._verify(category='单选题', content=content, options=options)
            final_choose = ((ord(answer)-65)+random.randint(1,length_of_options))%length_of_options
            delay_time = random.randint(self.delay_bot, self.delay_top)
            logger.info(f'随机延时 {delay_time} 秒提交答案: {chr(final_choose+65)}')
            time.sleep(delay_time)
            option_elements[final_choose].click()
            time.sleep(2)
            try:
                wrong = self.driver.find_element_by_xpath(rules['challenge_revival'])
                logger.debug(f'恭喜回答错误')
            except:
                logger.debug('抱歉回答正确')
                time.sleep(30)
        self.safe_back('challenge -> quiz')
        return num


    def _challenge(self):
        logger.info(f'挑战答题 目标 {self.challenge_count} 题, Go!')
        while True:
            result = self._challenge_cycle(self.challenge_count)
            if 0 >= result:
                logger.info(f'已成功挑战 {self.challenge_count} 题，正在返回')
                break
            else:
                delay_time = random.randint(5,10)
                logger.info(f'本次挑战 {self.challenge_count - result} 题，{delay_time} 秒后再来一组')
                time.sleep(delay_time)
                continue

        

    def challenge(self):
        if 0 == self.challenge_count:
            logger.info(f'挑战答题积分已达成，无需重复挑战')
            return
        self.safe_click(rules['mine_entry'])
        self.safe_click(rules['quiz_entry'])
        self._challenge()
        self.safe_back('quiz -> mine')
        self.safe_back('mine -> home')

# 每日答题模块
# class Daily(App):
    def _daily_init(self):
        # super().__init__()
        self.g, self.t = 0, 6
        self.count_of_group = 5
        try:
            self.daily_count = cfg.getint('prefers', 'daily_count')
        except:
            self.g, self.t = self.score["每日答题"]
            self.daily_count = self.t - self.g

        self.delay_bot = cfg.getint('prefers', 'daily_delay_min')
        self.delay_top = cfg.getint('prefers', 'daily_delay_max')

        self.delay_group_bot = cfg.getint('prefers', 'daily_group_delay_min')
        self.delay_group_top = cfg.getint('prefers', 'daily_group_delay_max')

    def _submit(self):
        self.safe_click(rules["daily_submit"])
        # time.sleep(random.randint(1,3))

    def _blank(self):
        contents = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_blank_content"])))
        content = " ".join([x.get_attribute("name") for x in contents])
        blank_edits = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_blank_edits"])))
        length_of_edits = len(blank_edits)
        logger.info(f'填空题 {content}')
        answer = self._verify("填空题", content, "") # 
        if not answer:
            words = [''.join(random.sample(string.ascii_letters + string.digits, 8))] * length_of_edits
        else:
            words = answer.split(" ")
        logger.debug(f'提交答案 {words}')
        for k,v in zip(blank_edits, words):
            # time.sleep(1)
            k.send_keys(v)

        self._submit()
        try:            
            wrong_or_not = self.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {answer}")
            notes = self.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            logger.debug(f"解析 {notes}")
            self._submit()
            if 1 == length_of_edits:
                self._update_bank({
                    "category": "填空题",
                    "content": content,
                    "options": [""],
                    "answer": answer,
                    "excludes": "",
                    "notes": notes
                })
            else:
                logger.error("多位置的填空题待完善...")
        except:
            logger.debug("填空题回答正确")

        
    def _radio(self):
        content = self.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_content"]))).get_attribute("name")
        option_elements = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_options"])))
        options = [x.get_attribute("name") for x in option_elements]
        length_of_options = len(options)
        logger.info(f"单选题 {content}")
        logger.info(f"选项 {options}")
        answer = self._verify("单选题", content, options)
        choose_index = ord(answer) - 65
        logger.info(f"提交答案 {answer}")
        option_elements[choose_index].click()
        # 提交答案
        self._submit()
        try:            
            wrong_or_not = self.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            right_answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {right_answer}")
            # notes = self.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            # logger.debug(f"解析 {notes}")
            self._submit()
            self._update_bank({
                "category": "单选题",
                "content": content,
                "options": options,
                "answer": right_answer,
                "excludes": "",
                "notes": ""
            })
        except:
            self._update_bank({
                "category": "单选题",
                "content": content,
                "options": options,
                "answer": answer,
                "excludes": "",
                "notes": ""
            })

    def _check(self):
        content = self.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_content"]))).get_attribute("name")
        option_elements = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_options"])))
        options = [x.get_attribute("name") for x in option_elements]
        length_of_options = len(options)
        logger.info(f"多选题 {content}\n{options}")
        answer = self._verify("多选题", content, options)
        logger.debug(f'提交答案 {answer}')
        for k, option in zip(list("ABCDEFG"), option_elements):
            if k in answer:
                option.click()
                time.sleep(1)
            else:
                continue
        # 提交答案
        self._submit()
        try:
            wrong_or_not = self.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            right_answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {right_answer}")
            # notes = self.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            # logger.debug(f"解析 {notes}")
            self._submit()
            self._update_bank({
                "category": "多选题",
                "content": content,
                "options": options,
                "answer": right_answer,
                "excludes": "",
                "notes": ""
            })
        except:
            self._update_bank({
                "category": "多选题",
                "content": content,
                "options": options,
                "answer": answer,
                "excludes": "",
                "notes": ""
            })

    def _dispath(self):
        for i in range(self.count_of_group):
            category = self.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_category"]))).get_attribute("name")
            if "填空题" == category:
                self._blank()
            elif "单选题" == category:
                self._radio()
            elif "多选题" == category:
                self._check()
            else:
                logger.error(f"未知的题目类型: {category}")
            delay = random.randint(self.delay_bot, self.delay_top)
            logger.debug(f'延时 {delay} 秒...')
            time.sleep(delay)

    def _daily(self, num):
        self.safe_click(rules["daily_entry"])
        while num:
            num -= 1
            logger.info(f'每日答题 第 {num}# 组')
            self._dispath()
            score = self.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_score"]))).get_attribute("name")
            try:
                score = int(score)
            except:
                raise TypeError('integer required')
            self.g += score
            if self.g == self.t:
                logger.info(f"今日答题已完成，返回")
                break
            else:
                delay = random.randint(self.delay_group_bot, self.delay_group_top)
                logger.info(f'每日答题未完成 <{self.g} / {self.t}> {delay} 秒后再来一组')
                time.sleep(delay)
                self.safe_click(rules['daily_again'])
                continue
        else:
            logger.debug(f'今日循环结束 <{self.g} / {self.t}>')
        self.safe_back('daily -> quiz')



    def daily(self):
        if 0 == self.daily_count:
            logger.info(f'每日答题积分已达成，无需重复答题')
            return
        self.safe_click(rules['mine_entry'])
        self.safe_click(rules['quiz_entry'])
        self._daily(self.daily_count)
        self.safe_back('quiz -> mine')
        self.safe_back('mine -> home')

# 新闻阅读模块
# class Read(App):
    def _read_init(self):
        # super().__init__()
        self.read_time = 720
        self.volumn_title = cfg.get("prefers", "article_volumn_title")
        self.star_share_comments_count = cfg.getint("prefers", "star_share_comments_count")
        self.titles = list()
        try:
            self.read_count = cfg.getint("prefers", "article_count")
            self.read_delay = 30
        except:
            g, t = self.score["阅读文章"]
            if t == g:
                self.read_count = 0
                self.read_delay = random.randint(45, 60)
            else:
                self.read_count = random.randint(
                        cfg.getint('prefers', 'article_count_min'), 
                        cfg.getint('prefers', 'article_count_max'))
                self.read_delay = self.read_time // self.read_count + 1

    def _star_once(self):
        if self.back_or_not("收藏"):
            return
        logger.debug(f'这篇文章真是妙笔生花呀！收藏啦！')
        self.safe_click(rules['article_stars'])
        # self.safe_click(rules['article_stars']) # 取消收藏

    def _comments_once(self, title="好好学习，天天强国"):
        if self.back_or_not("发表观点"):
            return
        logger.debug(f'哇塞，这么精彩的文章必须留个言再走！')
        self.safe_click(rules['article_comments'])
        edit_area = self.wait.until(EC.presence_of_element_located((By.XPATH, rules['article_comments_edit'])))
        edit_area.send_keys(title)
        self.safe_click(rules['article_comments_publish'])
        time.sleep(2)
        self.safe_click(rules['article_comments_list'])
        self.safe_click(rules['article_comments_delete'])
        self.safe_click(rules['article_comments_delete_confirm'])

    def _share_once(self):
        if self.back_or_not("分享"):
            return
        logger.debug(f'好东西必须和好基友分享，走起，转起！')
        self.safe_click(rules['article_share'])
        self.safe_click(rules['article_share_xuexi'])
        time.sleep(3)
        self.safe_back('share -> article')

    def _star_share_comments(self, title):
        logger.debug(f'哟哟，切克闹，收藏转发来一套')
        if random.random() < 0.33:
            self._comments_once(title)
            if random.random() < 0.5:
                self._star_once()
                self._share_once()
            else:
                self._share_once()
                self._star_once()
        else:
            if random.random() < 0.5:
                self._star_once()
                self._share_once()
            else:
                self._share_once()
                self._star_once()
            self._comments_once(title)

    def _read(self, num, ssc_count):
        logger.info(f'预计阅读新闻 {num} 则')
        while num > 0: # or ssc_count:
            try:
                articles = self.driver.find_elements_by_xpath(rules['article_list'])
            except:
                logger.debug(f'真是遗憾，一屏都没有可点击的新闻')
                articles = []
            for article in articles:
                title = article.get_attribute("name")
                if title in self.titles:
                    continue
                article.click()
                num -= 1
                logger.info(f'<{num}> 当前篇目 {title}')
                article_delay = random.randint(self.read_delay, self.read_delay+min(10, self.read_count))
                logger.info(f'阅读时间估计 {article_delay} 秒...')
                while article_delay > 0:
                    if article_delay < 20:
                        delay = article_delay
                    else:
                        delay = random.randint(min(10, article_delay), min(20, article_delay))
                    logger.debug(f'延时 {delay} 秒...')
                    time.sleep(delay)
                    article_delay -= delay
                    self.swipe_up()
                else:
                    logger.debug(f'完成阅读 {title}')

                if ssc_count > 0:
                    try:
                        comment_area = self.driver.find_element_by_xpath(rules['article_comments'])
                        self._star_share_comments(title)
                        ssc_count -= 1
                    except:
                        logger.debug('这是一篇关闭评论的文章，收藏分享留言过程出现错误')               

                self.titles.append(title)
                self.safe_back('article -> list')
                if 0 >= num:
                    break
            else:
                self.swipe_up()
    
    def read(self):
        if 0 == self.read_count:
            logger.info(f'新闻阅读已达成，无需重复阅读')
            return
        logger.debug(f'正在进行新闻学习...')
        vol_not_found = True
        while vol_not_found:
            volumns = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['article_volumn'])))
            first_vol = volumns[1]
            for vol in volumns:
                title = vol.get_attribute("name")
                logger.debug(title)
                if self.volumn_title == title:
                    vol.click()
                    vol_not_found = False
                    break
            else:
                logger.debug(f'未找到 {self.volumn_title}，左滑一屏')
                self.driver.scroll(vol, first_vol, duration=500)
        
        self._read(self.read_count, self.star_share_comments_count)

# 视听学习模块        
# class View(App): 
    def _view_init(self):
        # super().__init__()
        self.has_bgm = cfg.get("prefers", "radio_switch")
        if "disable" == self.has_bgm:
            self.view_time = 1080
        else:
            self.view_time = 360
        self.radio_chanel = cfg.get("prefers", "radio_chanel")
        try:
            self.video_count = cfg.getint("prefers", "video_count")
            self.view_delay = 15
        except:
            g, t = self.score["视听学习"]
            if t == g:
                self.video_count = 0
                self.view_delay = random.randint(15, 30)
            else:
                self.video_count = random.randint(
                        cfg.getint('prefers', 'video_count_min'), 
                        cfg.getint('prefers', 'video_count_max'))
                self.view_delay = self.view_time // self.video_count + 1

    def music(self):
        if "disable" == self.has_bgm:
            logger.debug(f'广播开关 关闭')
        elif "enable" == self.has_bgm:
            logger.debug(f'广播开关 开启')
            self._music()
        else:
            logger.debug(f'广播开关 默认')
            g, t = self.score["视听学习时长"]
            if g ==  t:
                logger.debug(f'视听学习时长积分已达成，无需重复收听')
                return
            else:
                self._music()
    
    def _music(self):
        logger.debug(f'正在打开《{self.radio_chanel}》...')
        self.safe_click('//*[@resource-id="cn.xuexi.android:id/home_bottom_tab_button_mine"]')
        self.safe_click('//*[@text="听新闻广播"]')
        self.safe_click(f'//*[@text="{self.radio_chanel}"]')
        self.safe_click(rules['home_entry'])

    def _watch(self, video_count=None):
        if not video_count:
            logger.info('视听学习已完成，无须重复学习')
            return
        logger.info("开始学习百灵视频...")
        self.safe_click(rules['bailing_enter'])
        self.safe_click(rules['bailing_enter']) # 再点一次刷新短视频列表
        self.safe_click(rules['video_first'])
        logger.info(f'预计观看视频 {video_count} 则')
        while video_count:
            video_count -= 1
            video_delay = random.randint(self.view_delay, self.view_delay + min(10, self.video_count))
            logger.info(f'正在观看视频 <{video_count}#> {video_delay} 秒进入下一则...')
            time.sleep(video_delay)
            self.swipe_up()
        else:
            logger.info(f'视听学习完毕，正在返回...')
            self.safe_back('video -> bailing')
            logger.debug(f'正在返回首页...')
            self.safe_click(rules['home_entry'])

<<<<<<< HEAD
        
=======
    def watch(self):
        self._watch(self.video_count)
>>>>>>> dev
