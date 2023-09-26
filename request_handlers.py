from flask import Flask, render_template, jsonify, send_from_directory
from flask import request, session, appcontext_tearing_down
import data_functions as df
from data_functions import sessions, queues_preview, users_preview
from datetime import datetime 
import atexit

app = None
exit_settings = {}

def create_app(name, secret_key='secret'):
    app = Flask(name)
    app.secret_key = secret_key

    # Main page
    @app.route('/')
    def request_main_page():
        user_data = {
            'status': session['user_status'],
            'name': session['user_name'],
            'settings': session['settings'],
        }

        return render_template('main_page.html.j2', user=user_data)

    # Get list of queues
    @app.route('/queue', methods=['GET'])
    def request_get_queues():
        # getting (if it have) settings and save in session
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 0))
        if page != 0:
            session['settings']['per_page'] = per_page

        # Sorting queues with status 'activ'
        active_queues = list(filter(lambda q: q['status'] == 'activ', queues_preview.values()))

        # Calculate start and end index
        start_index = (page - 1) * session['settings']['per_page']
        end_index = start_index + session['settings']['per_page']

        # make list queues without _id in database
        paged_queues = []
        for item in active_queues[start_index:end_index]:
            paged_queues.append(df.limit_data_queue(item['id']))

        return jsonify({'data': paged_queues, 'queue_len': len(queues_preview)})

    # Joing to queue
    @app.route('/queue/<int:queue_id>/join', methods=['GET'])
    def request_queue_join(queue_id):
        '''
        return queue_page.html.j2 or 404_page.html.j2
        return data (dict):
            'message' (string): for errors output
            'user' (dict):
                'is_host' (string): whether the user is a host.
                'name' (string): users name.
                'user_status' (string): User registration status. May be 'temporary', 'permanent', 'admin'.
                'position' (string): users position in queue.
                'is_next' (string): whether the user is next in queue.
                'is_out' (string): whether the user has finished queue.
            'queue' (dict):
                'name' (string): queues name.
                'description' (string): queues description.
                'status' (string): queues status. May be 'activ', 'private', 'closed'.
                'id' (string): queues ID.
                Next data only if user is permanent user.
                'hostName' (string): hosts name.
                Next data only if user is host.
                participant (list): dicts of queued user data. (See data_functions.py line 46)
                finishedQueue (list): dicts of queued user data, that out of queue. (See data_functions.py line 46)
                currentParticipantId (dict): dict of user data, that is next. (See data_functions.py line 46)
        '''

        queue = None
        data = {'message': ''}

        # Check if queue is exists
        if queue_id in queues_preview.keys():
            queue = df.db_queues.find_one({'_id':queues_preview[queue_id]['_id']})
            if queue['status'] == 'closed':
                data['message'] = 'Черга вже закрита.\n'
                return render_template('404_page.html.j2', data=data), 410    
        else:
            data['message'] = 'Не знайдено черги з таким id.\n'
            return render_template('404_page.html.j2', data=data), 404
        
        # Checking user data
        is_host = session['id'] == queue['id_host']
        is_perm = session['user_status'] == 'permanent'
        is_in_queue = False

        # Check if user in queue        
        for q in session['in_queues']:
            if q['id'] == queue_id:
                is_in_queue = True
                break

        # output data
        user_data = None
        if is_in_queue and not is_host:
            # client already in queue

            # here will be check if client is finished queue
            pass

        elif not is_host:
            # first join to queue
            session['in_queues'].append(queue_id)
            session['status'] = 'in_queue'

            queue['participant'].append({
                'id': session['id'],
                'name': session['user_name'],
                'user_status': session['user_status'],
                'position': len(queue['participant']),
                'is_next': len(queue['participant']) == 0,
            })

            user_data = queue['participant'][-1]
            user_data['is_out'] = False

        else:
            # user is host
            pass

        data['user']['is_host'] = is_host
        data['user']['name'] = user_data['user_name']
        data['user']['user_status'] = user_data['user_status']
        if not is_host:
            data['user']['position'] = user_data['position']
            data['user']['is_next'] = user_data['is_next']
            data['user']['is_out'] = user_data['is_out']
        
        # queue data 
        if is_host:
            data['queue'] = df.limit_data_queue(queue_id, 'host')
        elif is_perm:
            data['queue'] = df.limit_data_queue(queue_id, 'perm_user')
        else:
            data['queue'] = df.limit_data_queue(queue_id)

        data['queue']['total'] = len(data['queue']['participant'])

        return render_template('queue_page.html.j2', data=data)

    # Get users in queue
    @app.route('/queue/<int:queue_id>/participant', methods=['GET'])
    def request_get_queue_useer_list(queue_id):
        """Return users list in queue."""
        # getting (if it have) settings and save in session
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 0))
        if page != 0:
            session['settings']['per_page'] = per_page

        queue = None
        data = {
            'message': ''
        }

        # Check if queue is exists
        if queue_id in queues_preview.keys():
            queue = queues_preview[queue_id]
        else:
            data['message'] = 'Не знайдено черги з таким id.\nМожливо її вже закрили?'
            return render_template('404_page.html.j2', data=data), 404
        # Check whether the user has the right 
        if not queue['id_host'] == session['id']:
            data['message'] = 'У вас нема прав.'
            return render_template('404_page.html.j2', data=data), 403

        # Calculate start and end index
        start_index = (session['settings']['page'] - 1) * session['settings']['per_page']
        end_index = start_index + session['settings']['per_page']
        
        data['userList'] = queue['participant'][start_index:end_index]

        return jsonify({'data':data, 'usersLen': len(queue['participant']), 'next':queue['']})
        
    # Create new queue
    @app.route('/queue', methods=['POST'])
    def request_create_queue():
        """Create new queue"""
        inp_data = request.json
        out_data = {
            'message': None
        }

        # Check if client have name
        if session['user_status'] == 'temporary':
            if inp_data['user_name'] == None or inp_data['user_name'] == '':
                if session['user_name'] == None or session['user_name'] == '':
                    # 401 error
                    out_data['message'] = 'Ви спробували створити чергу, без вводу імені.\n'
                    return render_template('404_page.html.j2', data=out_data), 401
            
            session['user_name'] = inp_data['user_name']

        if inp_data['queue_name'] == "" or inp_data['queue_name'] == None:
            que_nam = f"{session['user_name']}'s queue"
        else:
            que_nam = inp_data['queue_name']

        if inp_data['queue_description'] == "" or inp_data['queue_description'] == None:
            que_des = "Черга без опису"
        else:
            que_des = inp_data['queue_description']

        queue = df.add_queue(que_nam, f"{session['id']}", que_des)

        out_data['queue'] = df.limit_data_queue(queue['id'], 'host')

        return render_template('queue_page.html.j2', data=out_data)

    @app.route('/favicon.ico')
    def request_favicon():
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    # 404 error handler
    @app.errorhandler(404)
    def request_page_not_found(e):
        print(e)
        return render_template('404_page.html.j2', data={'message': 'Сторінка не знайдена.'}), 404

    # Handler before
    @app.before_request
    def setup():
        if request.path != '/favicon.ico':
            # request not for getting favicon.ico
            session_id = session.get('id', None)

            if session_id is None or session_id not in sessions:
                # If session ID is not in sessions, or it's a new session
                df.new_temporary_session()
            else:
                # Get session data from the database
                session_data = sessions[session_id]

                if (
                    session_data['user_status'] == 'temporary' or
                    session_data['user_status'] == 'permanent'
                ) and session_data['last_activ'] == session.get('last_activ'):
                    # If session status and last_activ match the database, update last_activ
                    session['last_activ'] = datetime.now()
                else:
                    # Otherwise, it's an unknown session data, create a new temporary session
                    df.new_temporary_session()
    
    return app