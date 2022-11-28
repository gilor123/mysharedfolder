# observer.py: Class MyFileSystemEventHandler reflects a file system observer and relevant function for each event

from watchdog.events import FileSystemEventHandler
from state import SharedFolderState
import msgpack
import os

CREATED_EVENT = "created"
MODIFIED_EVENT = "modified"
RENAMED_EVENT = "renamed"
DELETED_EVENT = "deleted"


class MyFileSystemEventHandler( FileSystemEventHandler ) :
    def __init__ (self, base_path, client_socket, base_state) :
        self._base_path = base_path
        self._client_socket = client_socket
        self._state_obj = base_state


    # Called when a file or directory is created
    def on_created(self, event):
        base_name = os.path.basename(event.src_path)
        if not self.should_ignore_file(base_name):
            self.handle_event(event.src_path,CREATED_EVENT,self._base_path)


    # Called when a file or directory is renamed
    def on_moved(self, event):
        base_name = os.path.basename( event.src_path )
        if not self.should_ignore_file( base_name ) :
            self.handle_event(event.src_path,RENAMED_EVENT,self._base_path)


    # Called when a file or directory is modified
    def on_modified(self, event):
        base_name = os.path.basename( event.src_path )
        if not self.should_ignore_file( base_name ) :
            self.handle_event(event.src_path,MODIFIED_EVENT,self._base_path)


    # Called when a file or directory is deleted
    def on_deleted(self, event):
        base_name = os.path.basename( event.src_path )
        if not self.should_ignore_file( base_name ) :
            self.handle_event(event.src_path,DELETED_EVENT,self._base_path)


    # Print the event description and send the current state to the server
    def handle_event (self,file_path, event_type):
        base_state = SharedFolderState.from_real_dir(self._base_path,self._state_obj)
        file_name = os.path.basename(file_path)
        print(f"[OBSERVER] {file_name} was {event_type}, sending state to server")
        self._client_socket.send( msgpack.dumps( base_state.to_dict( ) ) )

    def should_ignore_file (self, base_name):
        if base_name == ".DS_Store" or base_name.startswith( "~" ) or base_name.endswith( "tmp" ) :
            return True
        return False





