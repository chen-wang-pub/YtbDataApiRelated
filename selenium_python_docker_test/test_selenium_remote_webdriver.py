from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

command_executor = 'http://localhost:4444/wd/hub'

driver = webdriver.Remote(command_executor, desired_capabilities=DesiredCapabilities.FIREFOX)
url = "https://www.youtube.com/esteevteev/videos"
driver.get(url)

item_xpath = '//*[@id="video-title"]'
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, item_xpath)))
total_music = len(driver.find_elements_by_xpath(item_xpath))
print(total_music)
"""    flag = False
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
    # print(driver.page_source)

    logger.debug(total_music)
    playlist_owner = driver.find_element_by_xpath('//*[@id="text-container"]/*[@id="text"]').text
    logger.debug(playlist_owner)
    all_link = driver.find_elements_by_xpath('//div[@id="dismissible"]')
    logger.debug(len(all_link))
    ytb_doc_list = []
    for a_link in all_link:
        # print(a_link.get_attribute('innerHTML'))
        title = a_link.find_element_by_xpath('.//*[@id="video-title"]').get_attribute('title')
        href = a_link.find_element_by_xpath('.//*[@id="video-title"]').get_attribute('href')
        duration = a_link.find_element_by_xpath('.//span[@id="text"]').text
        view = a_link.find_element_by_xpath('.//*[@id="metadata-line"]/span[1]').text
        ytb_item_doc = generate_ytb_item_doc(href, title, duration, view)
        logger.debug(ytb_item_doc)
        ytb_doc_list.append(ytb_item_doc)
    driver.quit()

    ytb_channel_db_access_dict = generate_db_access_obj(ytb_playlist_db, channel_id)

    logger.debug('This ytb channel db access dict is: {}'.format(ytb_channel_db_access_dict))

    item_id_list = []
    used_for_template_rendering = []
    number_added_doc = 0
    for doc in ytb_doc_list:
        item_id_list.append(doc['item_id'])
        read_payload = {'read_filter': {'item_id': doc['item_id']}}
        used_for_template_rendering.append([doc['item_id'], doc['title']])
        if upload_if_not_exist(doc, read_payload, ytb_channel_db_access_dict['read'], ytb_channel_db_access_dict['write']):
            number_added_doc += 1
    return {'ytb_channel_db_access_dict': ytb_channel_db_access_dict, 'item_id_list': item_id_list, 'used_for_template_rendering': used_for_template_rendering}"""