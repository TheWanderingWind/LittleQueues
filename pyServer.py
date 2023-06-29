from pymongo import MongoClient
from flask import Flask

app = Flask(__name__)
client = None
db = None
queues = None
users = None

# Main site
@app.route('/')
def hello():
    return 'Hello, World!'


# Here we will get user id
@app.before_request
def setup():
    pass


if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QueuesData']

    queues = db['queues'].find()
    users = db['users'].find()

    for document in queues:
        print(document)

    print('Сервер запущено')

    app.run()
