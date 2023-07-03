### Main includes ###
from pymongo import MongoClient
from flask import Flask, render_template, request
### Main variable ###
app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['QueuesData']
queues = db['queues']
users = db['users']

### Includes for sessions ###
from uuid import uuid4 
from datetime import datetime, timedelta
import threading
import time
### Variable for sessions ###
sessions = {}
lock = threading.Lock()
exit_process = False

# Get session data
def get_session(session_id):
    ### ALL PRINT HERE FOR DEBUG ###
    print(f'Trying find session with id {session_id}...')
    lock.acquire()
    if session_id in sessions:
        ret_session = sessions[session_id]
        print(f'Session found')
        lock.acquire()
        return ret_session
    else:
        print(f'Session not found')
        lock.acquire()
        return None

# Create session
def create_session():
    ### ALL PRINT HERE FOR DEBUG ###
    print('Create new session')
    session_id = None
    while session_id is None:
        session_id = str(uuid4())
        #print(f'Sessions: {sessions}')

        if session_id in sessions.keys():
            if sessions[session_id]['status'] != 'deleted':
                session_id = None
                break
        
    session = {
        'id': session_id, 
        'status': "downtime",
        'last_activ': datetime.now(),
        'name': None,
    }

    print('trying save session...')
    lock.acquire()
    sessions[session_id] = session
    lock.release()

    print(f'Success create new sesion with id {session_id}')
    return session

# For cheking and removing sessions
def cheking_sessions():
    ### ALL PRINT HERE FOR DEBUG ###
    print('cheking_sessions setup')

    while True:
        # delay
        for i in range(2):
            time.sleep(10)
            if exit_process:
                return
        # total delay: 2*10 = 20 sec (0.(3) min)
        # so little for debug

        now_time = datetime.now()
        print('Cheking sessions...', end='\t')

        lock.acquire()
        for session in sessions:
            if sessions[session]['status'] == 'downtime':
                if (now_time - sessions[session]['last_activ']) > timedelta(seconds=30):
                    closed_session = {
                        'id': session,
                        'status': 'deleted',
                    }
                    sessions[session] = closed_session
                    print(f'\nsession with id {session} was closed')
        lock.release()
        print('Cheked')


cheker_thread = threading.Thread(target=cheking_sessions)

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
def main_page():
    ### DEBUG PRINT ###
    print(f'Request to main page. User status: {request.user_status}')
    output_data = {
        'message': 'Hello, word!',
        'user_status': request.user_status,
        'user_data': request.user_data
    }
    
    return render_template('test.html.j2', data=output_data)


# Here we will get user id
@app.before_request
def setup():
    if  'session_id' in request.form:
        # if client has send session id
        session = get_session(request.session_id)
        if session:
            request.user_data = session
            request.user_status = 'permanent_user'
    elif 'user_id' in request.form:
        # if client has send user id
        user_data = queues.find_one({'id': request.user_id})
        if user_data:
            request.user_data = user_data
            request.user_status = 'permanent_user'
        else:
            # if we don't found user, we create new session
            ### DEBUG PRINT ###
            print(f'ERROR: not found user data by id {request.user_id}. Creating new session.')
            request.user_data = create_session()
            request.user_status = 'temporary_user'
    else:
        # if client has not send anything
        request.user_data = create_session()
        request.user_status = 'temporary_user'


if __name__ == '__main__':
    print('Сервер запущено')

    try:
        cheker_thread.start()
        app.run()
    finally:
        exit_process = True
        ### DEBUG PRINT ###
        print('join cheker thread...')
        cheker_thread.join()
        client.close()