from pymongo import MongoClient
from flask import Flask
import uuid

app = Flask(__name__)
client = None
db = None
queues = None
users = None

# Add new user
def add_user(name, cookies=[]):
    new_user = {
        'name': name,
        'cookies': cookies,
    }
    result = users.insert_one(new_user)
    new_user['id'] = result.inserted_id
    return new_user


# Add new queue
def add_queue(name, hostId, description):
    collection_queues = queues.find()
    new_queue = {
        'id': len(collection_queues),
        'name': name,
        'hostId': hostId,
        'description': description,
        'queue': [],
        'finishedQueue': [],
        'currentParticipantId': None,
        'status': 'active'
    }
    queues.insert_one(new_queue)


# Get user data by id
def get_user_by_id(id):
    collection_user = users.find()
    user_data = None
    for item in collection_user:
        if item['id'] == id:
            user_data = item
            break
    return user_data


# Get queue data by id
def get_queue_by_id(id):
    collection_queues = queues.find()
    queue_data = None
    for item in collection_queues:
        if item['id'] == id:
            queue_data = item
            break
    return queue_data


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

    queues = db['queues']
    users = db['users']

    for document in queues:
        print(document)

    print('Сервер запущено')

    app.run()
