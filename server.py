# Server.py: Create server and handle client events.
# The server holds a state of the shared folder and a version of it.
# Upon receiving messages with states of client the server handle it and updates his state and version if needed.

import socket
import msgpack
import os

from threading import Thread
from state import SharedFolderState

PORT = 5055
ADDRESS = socket.gethostbyname ( socket.gethostname () )

# Read base path from the command line.
print("Please enter the full path to your local shared folder:")
base_path = input()

# Create base path if doesn't exist
try:
    os.makedirs(base_path)
except:
    pass

state_obj = SharedFolderState.from_real_dir(base_path,None)
state_obj.version = 0
clients = []

# Recv a message from the client and handle it
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
    server.bind((ADDRESS, PORT))
    server.listen()
    print(f"[SERVER] Listening to port {PORT} ")

    while True:
        client_socket, _ = server.accept()
        print("Sending to a new client the state")
        client_socket.send(msgpack.dumps(state_obj.to_dict()))

        clients.append(client_socket)

        thread = Thread(target=handle_client, args=(client_socket, ))
        thread.start()



if __name__ == "__main__":
    main()
