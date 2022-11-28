# Client.py: Create client and file observer, and handle server events

from threading import Thread
import time
import os
from watchdog.observers import Observer
import msgpack
import socket
from state import SharedFolderState
import shutil
from observer import  MyFileSystemEventHandler

state_obj = None

PORT = 5055
ADDRESS = socket.gethostbyname ( socket.gethostname () )


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


# Create a file system observer
def create_observer (base_path, client_socket):
    global state_obj
    event_handler = MyFileSystemEventHandler( base_path, client_socket, state_obj )
    observer = Observer( )
    observer.schedule( event_handler, base_path, recursive = True )
    observer.start( )

    try :
        while True :
            time.sleep( 1 )
    except KeyboardInterrupt :
        observer.stop( )

    observer.join( )


# Monitor the directory and send it updated state to the server
def watch_directory (base_path, client_socket):
    global state_obj

    thread_observer = Thread(target=create_observer, args=(base_path, client_socket))
    thread_observer.start()


def main ( ) :
    global state_obj
    global event

    # Read base path from the command line.
    print("Please enter the full path to your local shared folder:")
    base_path = input()

    # Clean directory
    clean_directory(base_path)

    # Connect to server
    client_socket = socket.socket( )
    client_socket.connect( (ADDRESS, PORT) )
    print(f"[CLIENT] Listening to port {PORT}")


    # Listen to messages from the server
    unpacker = msgpack.Unpacker( use_list = False, raw = False )

    # Start observing
    event_handler = MyFileSystemEventHandler( base_path, client_socket, state_obj )
    observer = Observer( )
    observer.schedule( event_handler, base_path, recursive = True )

    while True :
        # Receive the data
        data = client_socket.recv( 1024 )
        if not data :
            break
        unpacker.feed( data )
        for unpacked in unpacker :
            # We just received our first state, start observing.
            observer.stop()

            # Update state
            state_obj = SharedFolderState.from_dict( unpacked )
            state_obj.write_state_to_folder( base_path )
            print( f"[CLIENT] The real folder was updated based on state version {state_obj.version}" )

            # Restart observer
            event_handler = MyFileSystemEventHandler( base_path, client_socket, state_obj )
            observer = Observer()
            observer.schedule(event_handler, base_path, recursive=True)
            observer.start()


if __name__ == "__main__" :
    main( )
