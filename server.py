import socket
import msgpack
import os

from threading import Thread
from state import SharedFolderState

base_path = "C:/Users/User/Downloads/networking_project/Server_Folder"

# Create base path if doesn't exist
try:
    os.makedirs(base_path)
except:
    pass

state_obj = SharedFolderState.from_real_dir(base_path,None)
state_obj.version = 0
# state_obj.print_state() @TODO REMOVE AFTER TESTINGS
clients = []


def handle_client(client_socket):
    global state_obj
    unpacker = msgpack.Unpacker(use_list=False, raw=False)

    while True:
        data = client_socket.recv(1024)
        if not data:
            break

        unpacker.feed(data)

        for unpacked in unpacker:
            # Client just sent a new state. Load it.
            client_state = SharedFolderState.from_dict(unpacked)

            if client_state.version == state_obj.version:
                state_obj = client_state
                state_obj.version += 1
                state_obj.write_state_to_folder(base_path)
                print("[SERVER] Received new state from client, new version", state_obj.version)

                # Update all clients with the new state.
                serialized_state = msgpack.dumps(state_obj.to_dict())
                for client in clients:
                    client.send(serialized_state)
            # If receive an old version, need to updates the client with the current version
            else:
                print("[SERVER] a client isn't up to date!")
                client_socket.send(msgpack.dumps(state_obj.to_dict()))


def main():
    # Create server
    server = socket.socket()
    server.bind(("0.0.0.0", 5055))
    server.listen()
    print(f"[SERVER] Listening to TBD PORT and ADDRESS")

    while True:
        client_socket, _ = server.accept()
        client_socket.send(msgpack.dumps(state_obj.to_dict()))

        clients.append(client_socket)

        thread = Thread(target=handle_client, args=(client_socket, ))
        thread.start()



if __name__ == "__main__":
    main()
