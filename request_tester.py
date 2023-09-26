import unittest
import time
from flask_testing import TestCase
from pyServer import app, setUp

from selenium import webdriver

class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        setUp()

        self.client_list = []
        for i in range(5):
            self.client_list.append(app.test_client())
        # standart client
        self.client = self.client_list[0]

        return app

    def test_server_functionality(self):
        print('TS: start testing (TS)')
        '''
        for i in range(2):
            print(f'requests #{i}:')
            for client in self.client_list:
                response = client.get('/')
                self.assert200(response)

                data = response.data.decode('utf-8')
                print(f'TS: client data: {data}.')
        '''

        response = self.client.get('/queue')
        print('response: ', response)


if __name__ == '__main__':
    unittest.main()
