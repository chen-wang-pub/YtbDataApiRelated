import requests
import json
import logging

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

class ProxyExtractor:
    """
    The idea of this class is to pick proxies based on country code that are in the same group with the current
    country code.
    """
    country_code_group = [['CA', 'US', ],
                          ['NL', 'DE'],]

    def __init__(self, country_code, db_url='172.17.0.5', db_port=27017, db_name='proxy', col_name='sslproxies'):
        self.read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_url, db_port, db_name,
                                                                                        col_name)
        self.country_code = country_code
        self._proxies = []


    def get_all_proxies(self):
        read_payload = {'read_filter': {},
                        'read_projection': {'ip': 1, 'port': 1, 'https': 1, 'country_code': 1}}

        response = requests.post(url=self.read_url, data=json.dumps(read_payload),
                                 headers={'content-type': 'application/json'})
        logger.debug(response)
        doc_list = response.json()['response']
        self._proxies.extend(doc_list)


    def get_proxies(self):
        code_group = []
        for group in self.country_code_group:
            if self.country_code in group:
                code_group = group.copy()

        if not code_group:
            logger.error('Country code {} does not belong to any pre-set country code'.format(self.country_code))
            return False

        read_payload = {'read_filter': {'country_code': {"$in": code_group}},
                        'read_projection': {'ip': 1, 'port': 1, 'https': 1, 'country_code': 1}}

        response = requests.post(url=self.read_url, data=json.dumps(read_payload),
                                 headers={'content-type': 'application/json'})
        logger.debug(response)
        doc_list = response.json()['response']
        self._proxies.extend(doc_list)

    @property
    def proxies(self):
        return self._proxies

    @proxies.setter
    def max_key(self, new_proxies):
        logger.warning('You are not supposed to set the proxies directly')
        self._proxies = new_proxies

    def parse_proxies_for_requests(self):
        """
        Generate a list of proxy dictionary that will be used for python requests module
        :return:
        """
        proxy_dict_list = []
        for record in self.proxies:
            if record['https'] == 'yes':
                proxy_dict = {'https': 'https://{}:{}'.format(record['ip'], record['port'])}
            else:
                proxy_dict = {'http': 'http://{}:{}'.format(record['ip'], record['port'])}
            proxy_dict_list.append(proxy_dict)
        return proxy_dict_list


if __name__ == '__main__':
    pe = ProxyExtractor('CA')
    pe.get_proxies()
    logger.debug(pe.proxies)
    logger.debug(pe.parse_proxies_for_requests())
