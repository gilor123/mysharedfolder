import msgpack
import glob
import os
import shutil


class SharedFolderState:
    def __init__(self):
        self.state = {}
        self.version = None

    def update_file(self, path, is_directory, file_content):
        if path == ".DS_Store" or path.startswith("~"):
            return

        self.state[path] = {
            "is_directory": is_directory,
            "file_content": file_content
        }

    def delete_file(self, path, is_directory):
        keys_to_remove = []

        # If this is a directory, delete all files inside it.
        if is_directory:
            for key in self.state.keys():
                if key.startswith(path + "/"):
                    keys_to_remove.append(key)

        # Delete the file itself.
        keys_to_remove.append(path)

        # Actually delete all keys to remove
        for key in keys_to_remove:
            if key in self.state:
                del self.state[key]
        
    def rename_file(self, src_path, dest_path):
        if src_path == ".DS_Store" or src_path.startswith("~"):
            return
        if src_path in self.state:
            self.state[dest_path] = self.state[src_path]
            del self.state[src_path]
    
    def write(self, base_path):
        # What files do I actually have in the directory right now??
        directory_files = [
            os.path.relpath(filename, base_path)
            for filename in glob.iglob(base_path + '/**/*', recursive=True)
        ]

        # Go over all files in the directory
        for path in directory_files:
            if path in self.state.keys():
                # EDGE CASE: If we had a directory called "x" and then a file called "x", this will break.
                if self.state[path]["is_directory"]:
                    continue

                try:
                    with open(os.path.join(base_path, path), "rb") as f:
                        file_content = f.read()
                except FileNotFoundError:
                    print(base_path)
                    print("temp text")

                # If the file exists in the state as well, and its content is different, then 
                # override it FROM state.
                if self.state[path] != file_content:
                    with open(os.path.join(base_path, path), "wb") as f:
                        f.write(self.state[path]["file_content"])
            else:
                # If the file doesn't exist in the state, it needs to be deleted.
                try:
                    shutil.rmtree(os.path.join(base_path, path))
                except NotADirectoryError:
                    os.remove(os.path.join(base_path, path))
                except FileNotFoundError:
                    pass

        # Go over all files in the state that did not exist in the directory,
        for path in self.state.keys():
            if path in directory_files:
                continue

            if self.state[path]["is_directory"]:
                try:
                    os.makedirs(os.path.join(base_path, path))
                except:
                    pass
            else:
                if (self.state[path]["file_content"] is not None):
                    with open(os.path.join(base_path, path), "wb") as f:
                        f.write(self.state[path]["file_content"])

    def to_dict(self):
        return {
            "state": self.state,
            "version": self.version
        }

    @staticmethod
    def from_dict(d):
        state = SharedFolderState()
        state.state = d["state"]
        state.version = d["version"]

        return state

    @staticmethod
    def from_real_dir(base_path):
        # What files do I actually have in the filesystem?
        directory_files = [
            os.path.relpath(filename, base_path)
            for filename in glob.iglob(base_path + '/**/*', recursive=True)
        ]

        # Create state
        state = SharedFolderState()
        for path in directory_files:
            # Add directory to state
            if os.path.isdir(os.path.join(base_path, path)):
                state.update_file(path, True, None)

            # Add file to state
            else:
                with open(os.path.join(base_path, path), "rb") as f:
                    file_content = f.read()
                
                state.update_file(path, False, file_content)
        
        return state
