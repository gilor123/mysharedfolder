import socket
import msgpack
import os

from threading import Thread
from state import SharedFolderState
w
base_path = "C:/Users/User/Downloads/networking_project/Server_Folder"

# Create base path if doesn't exist
try:
    os.makedirs(base_path)
except:
    pass

state = SharedFolderState.from_real_dir(base_path)
state.version = 0

clients = []


def handle_client(client_socket):
    global state
    unpacker = msgpack.Unpacker(use_list=False, raw=False)

    while True:
        data = client_socket.recv(1024)
        if not data:
            break

        unpacker.feed(data)

        for unpacked in unpacker:
            # Client just sent a new state. Load it.
            client_state = SharedFolderState.from_dict(unpacked)

            if client_state.version == state.version:
                state = client_state
                state.version += 1
                state.write(base_path)

                # Update all clients with the new state.
                serialized_state = msgpack.dumps(state.to_dict())
                for client in clients:
                    client.send(serialized_state)

                print("Received new state from client, new version", state.version) 
            else:
                client_socket.send(msgpack.dumps(state.to_dict()))


def main():
    # Create server
    server = socket.socket()
    server.bind(("0.0.0.0", 5055))
    server.listen()
    print ("I'm listening")

    while True:
        client_socket, _ = server.accept()
        client_socket.send(msgpack.dumps(state.to_dict()))

        clients.append(client_socket)

        thread = Thread(target=handle_client, args=(client_socket, ))
        thread.start()





if __name__ == "__main__":
    main()
