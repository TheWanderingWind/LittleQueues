from pymongo import MongoClient
from datetime import datetime, timedelta
import threading, time
from flask import session
from uuid import uuid4

client = MongoClient('mongodb://localhost:27017/')
db = client['Data']

###### Vars #################################
###
sessions = {}
'''
Links to session objects 

`sessions` using UUID (uuid.UUID) as keys.

parameters in session:
    id (uuid.UUID): UUID of this session. Temporary users have id like "temporaty_ID"
    user_status (string): User registration status. May be 'temporary', 'permanent', 'admin'.
    status (string): User status (activity). May be 'downtime', 'in_queue'.
    last_activ (datetime.datetime): The time when the user was last active.
    user_name (string): User's name.
    in_queues (list): ID of the queues in which the user is located.
    settings (dict): user's settings.
'''
###
session_loker = threading.Lock()
''' Loker for use `sessions` in different threads  '''
###
db_sessions = db["Sessions"]
'''
Sessions in database.

It has the same parameters as `sessions`, but additionally has:
    secret_key (string): the key for which the session was created
'''
SECRET_KEY = "your_secret_key"
"""Secret key that using which is used in this startup"""
###
db_queues = db['Queues']
''' 
Queues data in database

parametres:
    id (int): Queue's ID.
    id_host (uuid.UUID): User's UUID who host this queue.
    name (string): Queue's name.
    description (string): Queue's description.
    participant (list): dicts of queued user data. (More details below)
    finishedQueue (list): dicts of queued user data, that out of queue. (More details below)
    currentParticipantId (dict): dict of user data, that is next. (More details below)
    status (string): Queue's status. Can be 'unready', 'activ', 'privat', 'closed'.

participant (and finishedQueue, and currentParticipantId) dict:
    id (uuis.UUID): User's UUID.
    name (string): User's name.
    user_status (status): User registration status. May be 'temporary', 'permanent', 'admin'.
    position (int): User's position in queue.
    is_next (bool): If user is next in queue.
'''
###
queues_preview = {}
''' 
Perview queue data (and links to database)

`queues_preview` using queue ID (int) as keys.

parametres:
    _id (ObjectID): Queue's ID in database.
    id (int): Queue's ID.
    id_host (uuid.UUID): User's UUID who host this queue.
    name (string): Queue's name.
    description (string): Queue's description.
    status (string): Queue's status. Can be 'unready', 'activ', 'privat', 'closed'.
'''
###
db_users = db['Users']
''' 
Users data in database.

parametres:
    user_name (string): user's name.
    login (string): user's login.
    password (string): user's password.
    settings (dict): user's settings.
    host_queues (list): list of queue IDs in which client is host.
    in_queues (list): list of queue IDs in which client is participant.
    activ_sessions (list): list of activ user's sessions.
}
'''
###
users_preview = {}
''' 
Preview queue data (and links to the database) for different users.

`users_preview` using users IDs (ObjectID) as keys.

Parameters:
    user_name (str): User's name.
    settings (dict): User's settings.
    host_queues (list): List of queue IDs in which the client is the host.
    in_queues (list): List of queue IDs in which the client is a participant.
'''
###
###### End vars #############################



###### Session functions ####################
### Functions for work with data in sessions
###
def add_session_db(ses):
    """Save session in database"""
    ses["secret_key"] = SECRET_KEY
    db_sessions.insert_one(ses)
###
def edit_session_db(session_id, new_data):
    """Edit session in database"""
    ses = db_sessions.find_one({"id": session_id, "secret_key": SECRET_KEY })
    if ses:
        db_sessions.update_one({"_id": session_id, "secret_key": SECRET_KEY }, 
                               {"$set": {"data": new_data}})
        return True
    else:
        return False
###
def delete_session_db(session_id):
    """delete session in database"""
    ses = db_sessions.find_one({"_id": session_id, "secret_key": SECRET_KEY})
    if ses:
        db_sessions.delete_one({"_id": session_id, "secret_key": SECRET_KEY})
###
def get_all_sessions_db(secret_key):
    """Load all sessions from database by secret key"""
    ses_dict = {}
    sess = db_sessions.find({"secret_key": secret_key})
    for ses in sess:
        # Видалення секретного ключа перед додаванням сесії в словник
        ses.pop("secret_key", None)
        ses_dict[str(ses["id"])] = ses
    return ses_dict
###
def new_temporary_session():
    ''' create new temporary session '''

    print(F'DEBUG: new temporary session.')
    if 'id' not in session:
        new_id = None
        while new_id is None:
            new_id = uuid4()
            if new_id in sessions.keys():
                new_id = None
 
    session_loker.acquire()

    session['id'] = "temporary_" + str(new_id)  
    session['user_status'] = 'temporary'
    session['status'] = 'downtime'
    session['last_activ'] = datetime.now()
    session['user_name'] = None
    session['in_queues'] = [],
    session['settings'] = {
        'per_page': 10
    }

    ses_data = {
        'id': session['id'],
        'user_status': session['user_status'],
        'status': session['status'],
        'last_activ': session['last_activ'],
        'user_name': session['user_name'],
        'in_queues': session['in_queues'],
        'settings': session['settings'],
    }

    # add new session-obj to general list 
    sessions["temporary_" + str(new_id)] = ses_data
    add_session_db(ses_data)

    session_loker.release()
###
###
def new_permanent_session():
    ''' create new permanent session (session for permanent user)
     not done yet '''
    
    pass
###
###
def clean_session(id):
    ''' clear data in session '''
    print(f"cleaning {id} session.\nBefore cleaning: {sessions[id]}")
    
    if id not in sessions:
        print(f"No session with id {id} for clean")
        return

    session_loker.acquire()
    session_item = sessions[id]
    delete_session_db(id)

    session_item['status'] = None
    session_item['id'] = None
    session_item['last_activ'] = None
    session_item['user_name'] = None
    session_item['in_queues'] = None
    session_item['settings'] = None
    session_item['user_status'] = None

    if session_item['user_status'] == 'temporary':
        # delete data that only for temporary user
        pass
    elif session_item['user_status'] == 'permanent':
        # delete data that only for peermanent user
        #session_item['database_id'] = None
        #session_item['host_queues'] = None
        pass

    print(f"Cleaned session: {id}")

    sessions[id] = None
    session_loker.release()
###
###
exit_session_cheker = None
'''Boolean for closing thread'''
###
ready_session_cheker = True
'''Boolean whether this thread can be started.'''
###
def session_cheker():
    ''' Function for tread for cheking idle time sessions '''

    while True:
        # Delay to check
        for i in range(10):
            time.sleep(5) # little but many delays for fast close tread
            if exit_session_cheker == True:
                return
        # total delay: 10*5 = 50 sec

        session_loker.acquire()
        time_now = datetime.now()
        for id in sessions.keys():
            
            delta = time_now - sessions[id]['last_activ']

            if sessions[id]['status'] == 'downtime':
                if sessions[id]['user_status'] == 'temporary' and delta > timedelta(hours=2):
                    clean_session(id)
                elif sessions[id]['user_status'] == 'permanent' and delta > timedelta(days=2):
                    clean_session(id)

        session_loker.release()
session_cheker_tread = threading.Thread(target=session_cheker)
###
###
def start_session_cheker():
    '''Starting session cheker'''
    global ready_session_cheker, exit_session_cheker

    if ready_session_cheker == True:
        exit_session_cheker = False
        ready_session_cheker = False
        session_cheker_tread.start()
        return True
    else:
        return False
###
###
def close_session_cheker():
    '''Closing session checker'''
    global ready_session_cheker, exit_session_cheker

    if ready_session_cheker == True:
        return True
    exit_session_cheker = True
    session_cheker_tread.join()
    ready_session_cheker = True
    exit_session_cheker = False
    return True
###
###### End session functions ################



###### Queue functions ######################
### Finctions for work with queue data
###
def add_queue(name, id_host, description="Черга без опису", status='unready'):
    ''' Create new queue to database '''
    collection_queues = list(db_queues.find())
    new_queue = {
        'id': len(collection_queues),
        'id_host': id_host,
        'name': name,
        'description': description,
        'participant': [],
        'finishedQueue': [],
        'currentParticipantId': None,
        'status': status
    }
    result = db_queues.insert_one(new_queue)
    queues_preview[new_queue['id']] = {
        '_id': result.inserted_id,
        'id': new_queue['id'],
        'id_host': id_host,
        'name': name,
        'description': description,
        'status': status
        }
    return queues_preview[new_queue['id']]
###
###
def get_queue(id):
    ''' Get queue data '''
    if id not in queues_preview:
        print('Not found')
        return None
    else:
        return db_queues.find_one({'_id': queues_preview[id]['_id']})
###
###
def update_queue(id: int, data: dict):
    """
    Update queues data in database.
    Can be update only:
        'name', 'description', 'participant', 'finishedQueue', 'currentParticipantId', 'status'.
    
    return:
        0: successfully updated the data
        -1: queue not find
        -2: there is no data to update
        -3: data not update in database
    """

    queue = get_queue(id)
    if queue == None:
        return -1
    
    upd_data = {}
    if 'name' in data:
        upd_data['name'] = data['name']
    if 'description' in data:
        upd_data['description'] = data['description']
    if 'participant' in data:
        upd_data['participant'] = data['participant']
    if 'finishedQueue' in data:
        upd_data['finishedQueue'] = data['finishedQueue']
    if 'currentParticipantId' in data:
        upd_data['currentParticipantId'] = data['currentParticipantId']
    if 'status' in data:
        upd_data['status'] = data['status']

    if len(upd_data) == 0:
        return -2

    result = db_queues.update_one({"_id":queue["_id"]}, {'$set': upd_data})
    
    if result.modified_count == 0:
        return -3
    
    queues_preview[id]['name'] = data['name']
    queues_preview[id]['description'] = data['description']
    queues_preview[id]['status'] = data['status']

    return 0    
###
###
def limit_data_queue(id, status='temp_user'):
    ''' Limit queue data for diferent users status '''
    queue = get_queue(id)
    if not queue:
        return None

    # Standart data for everyone
    limited_queue = {
        'name': queue['name'],
        'description': queue['description'],
        'status': queue['status'],
        'id': queue['id']
    }
    # additional data for permanent
    if status == 'perm_user':
        limited_queue['hostName'] = users_preview[queue['id_host']]['user_name']
    # data for host
    elif status == 'host':
        limited_queue['hostName'] = users_preview[queue['id_host']]['user_name']
        limited_queue['participant'] = queue['participant']
        limited_queue['finishedQueue'] = queue['finishedQueue']
        limited_queue['currentParticipantId'] = queue['currentParticipantId']
    # fully data for admins
    elif status == 'admin':
        pass
    
    print(limited_queue)
    return limited_queue
###
###### End queue functions ##################



###### User functions #######################
### Functions for work with permanent users
### not used yet
###
def add_user(name, login, password, settings={}):
    ''' Create new user to database '''

    new_user = {
        'user_name': name,
        'login': login,
        'password': password,
        'settings': settings,
        'host_queues': [],
        'in_queues': [],
        'activ_sessions': [session['session']]
    }
    result = db_users.insert_one(new_user)
    
    users_preview[result.inserted_id] = {
        'user_name': name,
        'settings': settings,
        'host_queues': [],
        'in_queues': [],
    }

    return users_preview[result.inserted_id]
###
###
def get_user(id):
    ''' Get user data '''

    if id not in users_preview:
        print('Not found')
        return None
    else:
        return db_queues.find_one({'_id': id})
###
###### End user functions ###################

# Load all data from database
def setUp(link='mongodb://localhost:27017/', secret_key=None):
    client = MongoClient(link)

    if secret_key:
        SECRET_KEY = secret_key
        sessions = get_all_sessions_db(secret_key)
    
    queue_array = list(db_queues.find())
    for item in queue_array:
        queues_preview[item['id']] = {
            '_id': item['_id'],
            'id': item['id'],
            'hostId': item['hostId'],
            'name': item['name'],
            'description': item['description'],
            'status': item['status'],
        }

def close(clean_all_sessions=False, clean_all_this_sessions=False, clean_all_queues_basedata=False, clean_all_users_basedata=False):
    """
    Delete data in database and close DB client
    
    clean_all_sessions          : Delete all sessions (any secret key).
    clean_all_this_sessions     : Delete all sessions from this setup (only this secret key).
    clean_all_queues_basedata   : Delete all queue data
    clean_all_users_basedata    : Delete all user data
    """
    print("Close checker")
    close_session_cheker()

    if clean_all_sessions:
        print(f"Cleaning session.")

        res = db_sessions.delete_many({})
        print("DEBUG: deleted sessions: ", res.deleted_count)
    elif clean_all_this_sessions:
        print(f"Cleaning session. All this sessions: {sessions.keys()}")

        res = db_sessions.delete_many({"secret_key": SECRET_KEY})
        print("DEBUG: deleted sessions: ", res.deleted_count)

    if clean_all_queues_basedata:
        print("Cleaning queues in database")

        res = db_queues.delete_many({})
        print("DEBUG: deleted queues: ", res.deleted_count)

    if clean_all_users_basedata:
        print("Cleaning users in database")

        res = db_users.delete_many({})
        print("DEBUG: deleted users: ", res.deleted_count)