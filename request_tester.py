import unittest
import time
from flask_testing import TestCase
from pyServer import app

class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True

        self.client_list = []
        for i in range(5):
            self.client_list.append(app.test_client())

        return app

    def test_server_functionality(self):
        print('TS: start testing (TS)')
        for i in range(2):
            print(f'requests #{i}:')
            for client in self.client_list:
                response = client.get('/')
                self.assert200(response)

                data = response.data.decode('utf-8')
                print(f'TS: client data: {data}.')

if __name__ == '__main__':
    unittest.main()
