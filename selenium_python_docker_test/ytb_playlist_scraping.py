from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
import requests
import time
import json
from selenium_python_docker_test.utils.check_existence_before_upload import upload_if_not_exist
from selenium_python_docker_test.utils.proxy_extractor import ProxyExtractor

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


#TODO: Add proxies


def generate_ytb_item_doc(video_url, video_title, video_duration, video_view):
    video_id = video_url.replace('https://www.youtube.com/watch?v=', '')
    #  naming it as item_id is to keep consistency with the data got from youtube data api
    return {'item_id': video_id, 'title': video_title, 'duration': video_duration, 'view': video_view}

def crawl_ytb_user_videos(source_url='https://www.youtube.com/channel/UCDK54OyzWnOczY7LzEd9V2Q/videos', db_url='172.17.0.5', db_port=27017):
    db_name = 'ytb_playlist_from_selenium'
    col_name = ''  # extracted from scraping

    command_executor = 'http://localhost:4445/wd/hub'

    driver = webdriver.Remote(command_executor, desired_capabilities=DesiredCapabilities.FIREFOX)

    driver.get(source_url)

    item_xpath = '//*[@id="video-title"]'
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, item_xpath)))
    total_music = len(driver.find_elements_by_xpath(item_xpath))
    flag = False
    while not flag:
        driver.execute_script(
            "window.scrollBy(0,document.body.scrollHeight || document.documentElement.scrollHeight)")

        max_wait = 30
        while max_wait > 0:
            time.sleep(0.5)
            temp_total = len(driver.find_elements_by_xpath(item_xpath))
            if temp_total != total_music:
                total_music = temp_total
                break
            # height = driver.execute_script("return document.body.scrollHeight")
            # print('current scroll height is {}'.format(height))

            max_wait -= 1
        if max_wait == 0:
            flag = True
    #print(driver.page_source)

    logger.debug(total_music)
    playlist_owner = driver.find_element_by_xpath('//*[@id="text-container"]/*[@id="text"]').text
    if not col_name:
        col_name = playlist_owner
    logger.debug(playlist_owner)
    all_link = driver.find_elements_by_xpath('//div[@id="dismissible"]')
    logger.debug(len(all_link))
    ytb_doc_list = []
    for a_link in all_link:
        #print(a_link.get_attribute('innerHTML'))
        title = a_link.find_element_by_xpath('.//*[@id="video-title"]').get_attribute('title')
        href = a_link.find_element_by_xpath('.//*[@id="video-title"]').get_attribute('href')
        duration = a_link.find_element_by_xpath('.//span[@id="text"]').text
        view = a_link.find_element_by_xpath('.//*[@id="metadata-line"]/span[1]').text
        ytb_item_doc = generate_ytb_item_doc(href, title, duration, view)
        logger.debug(ytb_item_doc)
        ytb_doc_list.append(ytb_item_doc)
    driver.quit()

    write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_url, db_port, db_name,
                                                                                 col_name)
    read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_url, db_port, db_name,
                                                                                 col_name)
    delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_url, db_port, db_name,
                                                                                 col_name)
    logger.debug('write url is: {}'.format(write_url))
    logger.debug('read url is: {}'.format(read_url))
    logger.debug('delete url is: {}'.format(delete_url))

    number_added_doc = 0
    for doc in ytb_doc_list:
        read_payload = {'read_filter': {'item_id': doc['item_id']}}
        if upload_if_not_exist(doc, read_payload, read_url, write_url):
            number_added_doc += 1
    return number_added_doc

if __name__ == '__main__':
    logger.debug(crawl_ytb_user_videos())