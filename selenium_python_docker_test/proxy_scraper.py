from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
import requests
import json
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

db_url = '172.17.0.3'
db_port = 27017
database_name = 'proxy'
collection_name = 'sslproxies'
command_executor = 'http://localhost:4444/wd/hub'
source_url = "https://sslproxies.org/"
write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_url,db_port,database_name,collection_name)
read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_url,db_port,database_name,collection_name)
delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_url,db_port,database_name,collection_name)
def generate_proxy_document(ip, port, country_code, country, anonymity, google, https, last_checked):
    return {'ip':ip, 'port':port, 'country_code': country_code, 'country': country, 'anonymity': anonymity, 'google': google, 'https': https, 'last_checked': last_checked}




driver = webdriver.Remote(command_executor, desired_capabilities=DesiredCapabilities.FIREFOX)

driver.get(source_url)



Ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 1]")))]
logger.debug(len(Ips))
Ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 2]")))]
logger.debug(len(Ports))
Code = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 3]")))]
logger.debug(len(Code))
Country = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 4]")))]
logger.debug(len(Country))
Anonymity = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 5]")))]
logger.debug(len(Anonymity))
Google = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 6]")))]
logger.debug(len(Google))
Https = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 7]")))]
logger.debug(len(Https))
Last_Checked = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 8]")))]
logger.debug(len(Last_Checked))
driver.quit()
proxy_docs = []
for i in range(0, len(Ips)):
    proxy_docs.append(generate_proxy_document(Ips[i], Ports[i], Code[i], Country[i], Anonymity[i], Google[i], Https[i], Last_Checked[i]))
logger.debug(proxy_docs)
"""delete_payload = {'delete_filter': {}}
# logger.debug(read_payload)
response = requests.post(url=delete_url, data=json.dumps(delete_payload),
                         headers={'content-type': 'application/json'})"""
for doc in proxy_docs:
    read_payload = {'read_filter': {'ip': doc['ip'], 'port': doc['port'], 'country': doc['country']}}
    #logger.debug(read_payload)
    response = requests.post(url=read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    logger.debug(doc_list)
    if len(doc_list) < 1:
        # logger.debug('found doc')
        payload = {'write_docs': [doc]}
        response = requests.post(url=write_url, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})
        logger.debug(response.content)
"""payload = {'write_docs': proxy_docs}
response = requests.post(url=write_url, data=json.dumps(payload),
                         headers={'content-type': 'application/json'})
logger.debug(response.content)"""