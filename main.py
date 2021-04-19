import os

import requests
from pprint import pprint as pp
from lxml import html
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import datetime

load_dotenv()


class PrometeoAPI:
    def __init__(self, user, pwd):
        self.base_url = 'https://prometeoapi.com'
        self.session = requests.Session()
        self.__user = user
        self.__pwd = pwd
        self._login()

    def _generate_csrf_token(self, url):
        '''
        This function gets the csrf token from the login page needed to
        do request in order log into the website

        '''
        response = self.session.get(url)

        content = response.content
        tree = html.fromstring(content)

        csrf_element = tree.xpath("//input[@name='csrfmiddlewaretoken']")[0]
        csrf = csrf_element.get('value')

        return csrf

    def _login(self):
        '''
        This function takes the username and password, logs in and sets api_key, user name, and
        ammount of requests of the month, data available from the dashboard recieved after the log in
        '''

        url = f'{self.base_url}/dashboard/login/'

        csrf = self._generate_csrf_token(url)

        payload = {
            'csrfmiddlewaretoken': csrf,
            'username': self.__user,
            'password': self.__pwd
        }

        response = self.session.request('POST', url, data=payload)

        tree = html.fromstring(response.content)

        page_title_element = tree.xpath("//title")[0]
        page_title = str(page_title_element.text_content()).strip()

        if 'Login - Prometeo' in page_title:
            error = tree.xpath("//div[contains(@class,'alert')]")[0]
            error_msj = self._strip_text(error)
            raise Exception(f'Failed to log into the site, response text: {error_msj}')

        username_element = tree.xpath("//nav//*[contains(@class,'login-info__data')]/p[contains(@class,'text-white')]")[
            0]
        self.username = self._strip_text(username_element)

        api_key_element = tree.xpath("//p[contains(@class,'api-key-field')]")[0]
        self.api_key = self._strip_text(api_key_element)

        # requests_mes_element = tree.xpath("//p[contains(.,'Requests este mes:')]/b")[0]
        # self.requests_mes = str(requests_mes_element.text_content()).strip()

    def get_requests_current_month(self):

        current_date = datetime.datetime.now()

        request_url = f'{self.base_url}/dashboard/filter_requests/?format=json&month={current_date.month}&user_id=&year={current_date.year}'
        response = self.session.get(request_url)

        if response.status_code == 200:
            json_table = response.json()
            return json_table.get('usage_table')

    def refresh_api_key(self):
        csrf = self._generate_csrf_token(f'{self.base_url}/dashboard/')
        headers = {'X-CSRFToken': csrf}

        request_url = f'{self.base_url}/dashboard/reset-key/'
        response = self.session.post(request_url, headers=headers)
        self.api_key = response.json().get('api_key')

        return self.api_key

    def _strip_text(self, element):
        return str(element.text_content()).strip()


if __name__ == '__main__':
    api = PrometeoAPI(user=os.environ.get('PROMETEO_USERNAME'), pwd=os.environ.get('PROMETEO_PASSWORD'))

    print(api.api_key)
    print(api.username)
    print(api.refresh_api_key())
    pp(api.get_requests_current_month())
