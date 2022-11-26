import msgpack
import glob
import os
import shutil


class SharedFolderState :
    def __init__ (self) :
        self.state = {}
        self.version = None

    def update_file_in_state (self, path, is_directory, file_content) :
        self.state[path] = {
            "is_directory" : is_directory,
            "file_content" : file_content
        }

    # Deleting a file element or a sub-folder and its files from the state
    def delete_file_from_state (self, path, is_directory) :
        paths_to_remove = []

        # If this is a directory, append all files inside it to the remove list.
        if is_directory :
            for key in self.state.keys( ) :
                if key.startswith( path + "/" ) :
                    paths_to_remove.append( key )

        # Append  the file itself to the remove list.
        paths_to_remove.append( path )

        # Actually delete all keys to remove
        for key in paths_to_remove :
            if key in self.state :
                del self.state[key]

    # def rename_file (self, src_path, dest_path) :
    #     self.state[dest_path] = self.state[src_path]
    #     del self.state[src_path]


    # Write the file's content from the state to the real file and handle errors
    def update_real_file (self, full_path, path, is_dir ):
        if is_dir:
            self.create_directory(full_path,path)
        else:
            try :
                with open( full_path, "wb" ) as f :
                    new_content = self.state[path]["file_content"]
                    f.write( new_content )
            # If file is open, it's content isn't overrided. When it will be closed the updated
            except PermissionError :
                print( f"ERROR PermissionError. Skipped {path} file, when write state to folder " ) #@TODO REMOVE LINE AFTER TESTING
            except FileNotFoundError :
                print( f"ERROR FileNotFoundError. Skipped {path} file, when write state to folder " ) #@TODO REMOVE LINE AFTER TESTING


    # Align the real folder based on the state
    def write_state_to_folder (self, base_path) :
        # List the files that are currently in the directory
        directory_files = self.list_directory_files(base_path)
        # print(f"Test files in real dir: {directory_files}") #@TODO REMOVE LINE AFTER TESTING

        # Go over all files in the directory
        for path in directory_files :
            base_name = os.path.basename(path)
            if base_name == ".DS_Store" or base_name.startswith( "~" ) :
                continue
            full_path = os.path.join( base_path, path )
            is_dir = os.path.isdir(full_path)

            # If the file exists in state & real folder align real file to the content from state. Ignore directories.
            if path in self.state.keys( ) :
                if not is_dir :
                    self.update_real_file(full_path, path, False)

            # If the file doesn't exist in the state, it needs to be deleted.
            else :
                self.remove_real_file(full_path,path,is_dir)

        # Go over all files in the state that did not exist in the directory,
        for path in self.state.keys( ) :
            full_path = os.path.join( base_path, path )
            is_dir = self.state[path]["is_directory"]
            if path not in directory_files :
                self.update_real_file(full_path, path, is_dir)


    def to_dict (self) :
        return {
            "state" : self.state,
            "version" : self.version
        }


    @staticmethod
    #@TODO CHECK IF SHOULD BE A STATIC METHOD
    def create_directory (full_path, path):
        try :
            os.makedirs( full_path )
        except :
            print( f"[CONTROLLED ERROR]. When creating {path} directory" )  # @TODO REMOVE LINE AFTER TESTING


    @staticmethod
    #@TODO CHECK IF SHOULD BE A STATIC METHOD
    def remove_real_file (full_path, path, is_dir):
        if is_dir:
            try :
                shutil.rmtree( full_path )
            except :
                print( f"[CONTROLLED ERROR] . Skipped {path} folder, when removing the folder " )
        else:
            try:
                os.remove( full_path )
            except PermissionError :
                print( f"[CONTROLLED ERROR] PermissionError. Skipped {path} file, when removing the file " )
            except FileNotFoundError :
                print( f"[CONTROLLED ERROR] FileNotFoundError. Skipped {path} file, when removing the file " )


    @staticmethod
    #@TODO CHECK IF SHOULD BE A STATIC METHOD
    def list_directory_files (base_path):
        directory_files = [
            os.path.relpath( filename, base_path )
            for filename in glob.iglob( base_path + '/**/*', recursive = True )
        ]
        return directory_files


    @staticmethod
    def from_dict (d) :
        state_obj = SharedFolderState( )
        state_obj.state = d["state"]
        state_obj.version = d["version"]

        return state_obj

    def remove_redundant_files_from_state (self, directory_files):
        # Create the list of the files to remove, to avoid changing dict while iterating it
        paths_to_remove = []
        for key in self.state.keys( ) :
            if key not in directory_files :
                paths_to_remove.append( key )
        # Iterate the list to actually remove the files for the state
        for path in paths_to_remove :
            if path in self.state :
                is_dir = self.state[path].get( "is_directory" )
                self.delete_file_from_state( path, is_dir )

    @staticmethod
    def from_real_dir (base_path, base_state_obj) :
        # What files do I actually have in the filesystem?
        directory_files = [
            os.path.relpath( filename, base_path )
            for filename in glob.iglob( base_path + '/**/*', recursive = True )
        ]

        state_obj= SharedFolderState( )

        # Remove files elements from the state if they aren't in the real folder
        if base_state_obj != None:
            state_obj = base_state_obj
            state_obj.remove_redundant_files_from_state(directory_files)

        for path in directory_files :
            # ignore OS temporary files in folder
            base_name = os.path.basename(path)
            if base_name == ".DS_Store" or path.startswith("~"):
                continue
            full_path = os.path.join( base_path, path )
            # Add a directory to state
            if os.path.isdir( full_path ) :
                state_obj.update_file_in_state( path, True, None )

            # Add a file to state, if the file is opened it's skipped and will be updated next time
            else :
                try:
                    with open( full_path, "rb" ) as f :
                        file_content = f.read( )
                    state_obj.update_file_in_state( path, False, file_content )
                except PermissionError:
                    print(f"[CONTROLLED ERROR] PermissionError. Skipped {path} file, when tried to read it from folder to state ")
                except FileNotFoundError:
                    print(f"[CONTROLLED ERROR] FileNotFoundError. Skipped {path} file, when tried to read it from folder to state ")

        return state_obj


    # Print the state
    def print_state (self):
        print(f"State version: {self.version}")
        for path in self.state.keys():
            is_dir = self.state[path].get("is_directory")
            print (f"Name: {path}, Is dir? {is_dir}")




