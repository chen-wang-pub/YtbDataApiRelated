from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

command_executor = 'http://localhost:4445/wd/hub'

driver = webdriver.Remote(command_executor, desired_capabilities=DesiredCapabilities.FIREFOX)

driver.get("https://sslproxies.org/")
ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 1]")))]
ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
    EC.visibility_of_all_elements_located((By.XPATH,
                                           "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 2]")))]
driver.quit()
proxies = []
for i in range(0, len(ips)):
    proxies.append(ips[i] + ':' + ports[i])
print(proxies)