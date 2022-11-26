import threading
from threading import Thread
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import msgpack
import socket
import sys
from state import SharedFolderState
import shutil

state_obj = None


# Cleans the content of the directory
def clean_directory(base_path):
    try :
        shutil.rmtree( base_path )
    except :
        pass

    try :
        os.makedirs( base_path )
    except :
        pass

# Monitor the directory and send it updated state to the server
def watch_directory (base_path, client_socket):
    global state_obj
    while True:
        state_obj = SharedFolderState.from_real_dir(base_path,state_obj)
        # state_obj.print_state()@TODO REMOVE AFTER TESTING
        print("[CLIENT] Sending state to server")
        client_socket.send( msgpack.dumps( state_obj.to_dict( ) ) )
        time.sleep(3)


def main ( ) :
    global state_obj
    global event

    # Read base path from the command line. @TODO CHANGE TO BE AN INPUT IN THE END
    print("Please enter the full path to your local shared folder:")
    base_path = input()
    # base_path = "C:/Users/User/Downloads/networking_project/Client_Folder_1"

    # Clean directory
    clean_directory(base_path)

    # Connect to server
    client_socket = socket.socket( )
    client_socket.connect( ("127.0.0.1", 5055) )
    print(f"[CLIENT] Listening to TBD PORT and ADDRESS")

    # # Start observing the base path directory.
    thread_observer = Thread(target=watch_directory, args=(base_path, client_socket))
    thread_observer.start()

    # Listen to messages from the server
    unpacker = msgpack.Unpacker( use_list = False, raw = False )
    while True :
        # Receive the data
        data = client_socket.recv( 1024 )
        if not data :
            break
        unpacker.feed( data )
        for unpacked in unpacker :
            # Update state
            state_obj = SharedFolderState.from_dict( unpacked )
            state_obj.write_state_to_folder( base_path )

            print( f"[CLIENT] The real folder was updated based on state version {state_obj.version}" )



if __name__ == "__main__" :
    main( )
