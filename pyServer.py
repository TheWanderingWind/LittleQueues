### Main includes ###
from pymongo import MongoClient
from flask import Flask, render_template, jsonify
from flask import request, session
from datetime import datetime, timedelta
import threading, time
from uuid import uuid4

### Main variable ###
app = Flask(__name__)
app.secret_key = 'secretBuild1'
client = MongoClient('mongodb://localhost:27017/')
db = client['QueuesData']

# links to session objects 
sessions = {}
session_loker = threading.Lock()

queues = db['queues']
# perview queue data (and links to database)
queues_preview = {}

users = db['users']
# perview queue data (and links to database)
users_preview = {}

def new_temporary_session():
    ''' create new temporary session '''
    print(F'DEBUG: session data: {session}')
    if 'id' not in session:
        new_id = None
        while new_id is None:
            new_id = uuid4()
            if new_id in sessions.keys():
                new_id = None
 
    session_loker.acquire()

    # add new session-obj to general list 
    if 'id' in session:
        sessions[new_id] = session

    session['id'] = new_id
    session['user_status'] = 'temporary'
    session['status'] = 'downtime'
    session['last_activ'] = datetime.now()
    session['user_name'] = None
    session['in_queues'] = [],
    session['settings'] = {
        'page': 1,
        'per_page': 10
    }

    session_loker.release()

def new_permanent_session():
    ''' create new permanent session (session for permanent user)
     not done yet '''
    pass

def clean_session(id):
    ''' clear data in session '''
    session_loker.acquire()
    session_item = sessions[id]

    session_item['status'] = "close"
    session_item['last_activ'] = None
    session_item['user_name'] = None
    session_item['in_queues'] = None
    session_item['settings'] = None

    if session_item['user_status'] == 'temporary':
        # delete data that only for temporary user
        pass
    elif session_item['user_status'] == 'permanent':
        # delete data that only for peermanent user
        #session_item['database_id'] = None
        #session_item['host_queues'] = None
        pass
    
    session_item['user_status'] = None
    session_loker.release()

exit_session_cheker = False
def session_cheker():
    ''' Function for tread for cheking idle time sessions   '''
    print('Start session_cheker')

    while True:
        # Delay to check
        for i in range(10):
            time.sleep(5) # little but many delays for fast close tread
            if exit_session_cheker == True:
                return
        # total delay: 10*5 = 50 sec

        session_loker.acquire()
        time_now = datetime.now()
        for id in sessions:
            if sessions[id]['status'] == 'closed':
                continue
            
            delta = time_now - session[id]['last_activ']

            if session[id]['status'] == 'downtime':
                if session[id]['user_status'] == 'temporary' and delta > timedelta(hours=2):
                    clean_session(id)
                elif session[id]['user_status'] == 'permanent' and delta > timedelta(days=2):
                    clean_session(id)

        session_loker.release()
session_cheker_tread = threading.Thread(target=session_cheker)

def add_queue(name, hostId, description, status='active'):
    ''' Create new queue to database '''
    collection_queues = list(queues.find())
    new_queue = {
        'id': len(collection_queues),
        'name': name,
        'hostId': hostId,
        'description': description,
        'queue': [],
        'finishedQueue': [],
        'currentParticipantId': None,
        'status': status
    }
    result = queues.insert_one(new_queue)
    queues_preview[new_queue['id']] = {
        '_id': result.inserted_id,
        'id': new_queue['id'],
        'name': name,
        'description': description,
        'status': status
        }
    return queues_preview[new_queue['id']]

def get_queue(id):
    ''' Get queue data '''
    if id not in queues_preview:
        print('Not found')
        return None
    else:
        return queues.find_one({'_id': queues_preview[id]})

def add_user(name, login, password, settings={}):
    ''' Create new user to database '''
    new_user = {
        'user_name': name,
        'login': login,
        'password': password,
        'settings': settings,
        'host_queues': [],
        'activ_sessions': [session['session']]
    }
    result = users.insert_one(new_user)
    
    users_preview[result.inserted_id] = {
        'user_name': name,
        'settings': settings,
        'host_queues': [],
    }

    return users_preview[result.inserted_id]

def get_user(id):
    ''' Get user data '''
    if id not in users_preview:
        print('Not found')
        return None
    else:
        return queues.find_one({'_id': id})

# Main page
@app.route('/')
def main_page():
    ### ALL PRINTS FOR DEBUG ###
    #print('main request')

    out_data = {
        'id': session['id'],
        'user_status': session['user_status'],
        'user_name': session['user_name'],
        'in_queues': session['in_queues'],
        'settings': session['settings'],
    }

    return render_template('main_page.html.j2', data=out_data)

@app.route('/queue', methods=['GET'])
def get_queues():

    # getting (if it have) settings and save in session
    page = int(request.args.get('page', 0))
    if page != 0:
        session['settings']['page'] = page
    per_page = int(request.args.get('per_page', 0))
    if page != 0:
        session['settings']['per_page'] = per_page

    # Sorting queues with status 'activ'
    active_queues = list(filter(lambda q: q['status'] == 'activ', queues_preview.values()))

    # Calculate start and end index
    start_index = (session['settings']['page'] - 1) * session['settings']['per_page']
    end_index = start_index + session['settings']['per_page']

    # make list queues without _id in database
    paged_queues = []
    for item in active_queues[start_index:end_index]:
        paged_queues.append({
            'name': item['name'],
            'description': item['description'],
            'status': item['status'],
            'id': item['id']
        })

    return jsonify({'data': paged_queues, 'queue_len': len(queues_preview)})

# Handler before 
@app.before_request
def setup():
    ### ALL PRINTS FOR DEBUG ###
    #print('BG: before request (BG)')

    if request.path != '/favicon.ico':
        # request not for get favicon.ico

        if not ('status' in session):
            # if session is new
            #print('BG: it\'s new session')
            new_temporary_session()

        elif session['status'] == 'closed':
            # if session was closed
            #print('BG: it\'s closed session')
            new_temporary_session()

        elif 'user_status' in session.keys() and session['user_status'] == 'temporary':
            # if it's temporary user
            #print('BG: it\'s temporary session')
            session['last_activ'] = datetime.now()
        
        elif 'user_status' in session.keys() and session['user_status'] == 'permanent':
            # if it's permanent user
            #print('BG: it\'s permanent session')
            session['last_activ'] = datetime.now()
        
        else:
            print('BG: unknow session data')
            new_temporary_session()


def setUp():
    # read queues in database
    queue_array = list(queues.find())
    for item in queue_array:
        queues_preview[item['id']] = {
            '_id': item['_id'],
            'id': item['id'],
            'name': item['name'],
            'description': item['description'],
            'status': item['status']
        }

if __name__ == '__main__':
    try:
        ### DEBUG PRINTS ###
        setUp()

        #for i in range(20):
        #    add_queue(f'Test Queue #{i+20}', 0, 'None', 'activ')

        session_cheker_tread.start()
        print('start app')
        app.run()
    finally:
        ### DEBUG PRINTS ###
        print('closed app')
        exit_session_cheker = True
        print('closing session_cheker_tread...')
        session_cheker_tread.join()
        client.close()