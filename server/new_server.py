import socket
import json
import sys
from select import select

from mongo import Mongo


to_monitor = []
status = {}


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
server_socket.bind(('127.0.0.1', 8888))
server_socket.listen(25)

mongo = Mongo() # Connect with database object

def accept_connection(server_socket):
    client_socket, addr = server_socket.accept()

    print("Connection from ",addr)
    to_monitor.append(client_socket)

def handler(client_socket):
    """ Mayor logic """
    try: # If excaption appears server closes the connect with client
        title = client_socket.recv(1024).decode()

        if not title:
            to_monitor.remove(client_socket)
            client_socket.close()
            return # Extra exit
        
        if title == 'exit':
            print("Goodbye")
            to_monitor.remove(client_socket)
            client_socket.close()
            return
        
        #
        # Hash Checking
        # Unpacking title
        _hash, command, size = title.split('.')
        size = int(size)

        client_socket.send(b'Success')

        if command == "create_note": # Create a new note in DataBase
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.create_note(data)
            client_socket.send(str(status).encode('utf-8'))
            # Send status back

        elif command == "get_all": # Returns all notes to user
            print('Command is :', command)
            data = client_socket.recv(size)
            notes = mongo.get_all(data)
            client_socket.send(str(len(notes)).encode('utf-8'))
            
            for note in notes:
                note['_id'] = str(note['_id']) # ObjectId do not work with json
                j_note = json.dumps(note)
                size = sys.getsizeof(j_note) # Get size of json note
                #print("size is", size)
                client_socket.send(str(size).encode('utf-8'))
                client_socket.recv(8)
                client_socket.send(("{}+\n".format(j_note)).encode('utf-8')) # Send note
                if client_socket.recv(32).decode() == "+": continue
                else: break
            # The end?

        elif command == "change_note": # Change note information 
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.change_note_text(data)
            client_socket.send(str(status).encode('utf-8'))
            # Send status back

        elif command == "change_favorite": # Change favorite status
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.change_favorite(data)
            client_socket.send(str(status).encode('utf-8'))

        elif command == "new_version": # Create new version of the note
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.new_version(data)
            client_socket.send(str(status).encode('utf-8'))

        elif command == "get_version": # Returns some version of the note
            print('Command is :', command)
            data = client_socket.recv(size)
            response = json.dumps(mongo.get_version(data))
            size = sys.getsizeof(response) # Get size of object
            client_socket.send(size.to_bytes(2, byteorder='big')) # Send bytes of sizes 
            client_socket.send(response.encode('utf-8'))

        elif command == "delete_notes": # Delete note or notes
            print('Command is :', command)
            data = json.loads(client_socket.recv(size))
            if type(data) is str:
                status = mongo.delete_all(data)
            else:
                status = mongo.delete_one(data)
            client_socket.send(str(status).encode('utf-8'))

        elif command == "share": # Sharing to other users 
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.share(json.loads(data)) # Change 
            client_socket.send(str(status).encode('utf-8'))

        elif command == "del_share": # Delete user from share list
            print('Command is :', command)
            data = client_socket.recv(size)
            status = mongo.del_share(data)
            client_socket.send(str(status).encode('utf-8'))
    except: 
        client_socket.close()


def checker():
    return True


def authenticator(client_socket):
    """ Auth """
    request = client_socket.recv(4096)
    if request:
        response = 'Hello, World\n'.encode()
        client_socket.send(response)
    else:
        to_monitor.remove(client_socket)
        client_socket.close()


def event_loop():
    while True:

        ready_to_read, _, _ = select(to_monitor, [], [])
        # Genius 
        for sock in ready_to_read:
            if sock is server_socket:
                accept_connection(sock)
            else: # Проверка подключение или запрос 
                # if status[sock]: # Если запрос
                #     handler(sock)
                # else: # Если подключение 
                #     authenticator(sock)
                handler(sock)

if __name__ == "__main__":
    to_monitor.append(server_socket)
    event_loop()