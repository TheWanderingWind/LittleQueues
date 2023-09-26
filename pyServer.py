######### Main includes #########
import data_functions as df
import request_handlers as rh
import random

if __name__ == '__main__':
    key = "BuildTest_" + str(random.random())
    print("secret key: ", key)

    try:
        # Setup mongoDB client and load all data from database
        df.setUp('mongodb://localhost:27017/', key)

        # Create server-app
        app = rh.create_app('main', secret_key=key)

        # When the server closes, will clear all sessions 
        rh.exit_settings['clean_sessions'] = True
        
        # Setup session checker
        df.start_session_cheker()
        # Setup server-app
        app.run()
    except KeyboardInterrupt:
        print("test", df.sessions.keys())
        for ses in df.sessions:
            print(df.sessions[ses])
    finally:
        df.close(clean_all_sessions=True)