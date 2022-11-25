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


state = None


class MyFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, base_path, client_socket):
        self._base_path = base_path
        self._client_socket = client_socket


    def create_file (self,event):
        try :
            global state
            if state is None :
                return

            if event.is_directory :
                file_content = None
            else :
                with open( event.src_path, "rb" ) as f :
                    file_content = f.read( )

            state.update_file(
                path = self._strip_base_path( event.src_path ),
                is_directory = event.is_directory,
                file_content = file_content
            )

            self._client_socket.send( msgpack.dumps( state.to_dict( ) ) )
        except PermissionError:
            time.sleep(2)
            self.create_file(event)
        except FileNotFoundError:
            state.update_file(
                path = self._strip_base_path( event.src_path ),
                is_directory = event.is_directory,
                file_content = file_content
            )

    def on_created(self, event):
        """Called when a file or directory is created."""
        # self.create_file(event)
        state.update_file(
            path = self._strip_base_path( event.src_path ),
            is_directory = event.is_directory,
            file_content = bytes()
        )

    def on_moved(self, event):
        """Called when a file or a directory is moved or renamed."""
        global state
        if state is None:
            return

        state.rename_file(
            src_path=self._strip_base_path(event.src_path),
            dest_path=self._strip_base_path(event.dest_path),
        )

        self._client_socket.send(msgpack.dumps(state.to_dict()))

    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        global state
        if state is None:
            return

        state.delete_file(
            path=self._strip_base_path(event.src_path),
            is_directory=event.is_directory
        )

        self._client_socket.send(msgpack.dumps(state.to_dict()))

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        # global state
        # if state is None:
        #     return
        #
        # if event.is_directory:
        #     return
        #
        # try:
        #     with open(event.src_path, "rb") as f:
        #         file_content = f.read()
        # except FileNotFoundError:
        #     file_content = None
        #
        # state.update_file(
        #     path=self._strip_base_path(event.src_path),
        #     is_directory=event.is_directory,
        #     file_content=file_content
        # )
        #
        # self._client_socket.send(msgpack.dumps(state.to_dict()))
        pass
    
    def _strip_base_path(self, path):
        return os.path.relpath(path, self._base_path)


def watch_directory(base_path, client_socket):
    event_handler = MyFileSystemEventHandler(base_path, client_socket)

    observer = Observer()
    observer.schedule(event_handler, base_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


def main():
    global state

    # Read base path from the command line.
    base_path = sys.argv[1]

    # Clean directory
    try:
        shutil.rmtree(base_path)
    except:
        pass
   
    try:
        os.makedirs(base_path)
    except:
        pass

    # Connect to server
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 5055))

    # # Start observing the base path directory.
    # thread = Thread(target=watch_directory, args=(base_path, client_socket))
    # thread.start()
    
    # Listen to messages from the server
    unpacker = msgpack.Unpacker(use_list=False, raw=False)

    # Start observing
    event_handler = MyFileSystemEventHandler(base_path, client_socket)

    observer = Observer()
    observer.schedule(event_handler, base_path, recursive=True)

    while True:
        data = client_socket.recv(1024)
        if not data:
            break

        unpacker.feed(data)

        for unpacked in unpacker:
            # We just received our first state, start observing.

            observer.stop()

            # Update state
            state = SharedFolderState.from_dict(unpacked)
            state.write(base_path)

            print("Just received new state with version", state.version) 

            # Restart observer
            observer = Observer()
            observer.schedule(event_handler, base_path, recursive=True)
            observer.start()


if __name__ == "__main__":
    main()

