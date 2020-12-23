import socket
from sys import getsizeof as gso
import json
from hashlib import sha256

class Singleton(type):
    """ 
    The connection to Mongo must be one """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Client(metaclass=Singleton):
    def __init__(self):
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client_socket.connect(('192.168.56.102', 8765))
        pass

    """Класс состоит из статических методов,
    по одному методу на каждый из возможнных
    запросов пользователя """
    # All first query has mask like a "user_hash.use_method.sizes"

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('127.0.0.1', 8888))
            
    def create_note(self, owner, name, text): # 
    # Create socket
    # First query 
        msg = json.dumps({
            'owner':owner,
            'name':name,
            'text':text,
        })

        title = "hash.create_note.%s"%gso(msg)
        self.client_socket.sendall(title.encode('utf-8')) # Send a title with some information
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(msg.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else: 
            self.client_socket.close()
            return False
    def fill_youself(self, owner):
        """ The func returns a list of notes """
        msg = json.dumps({
            'owner':owner
        })
        #
        title = "hash.get_all.%s"%gso(msg) #get_all
        #
        self.client_socket.sendall(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            #owner 
            self.client_socket.sendall(msg.encode('utf-8'))
            #get array
            notes = []
            lenght = int(self.client_socket.recv(128).decode())
            for _ in range(lenght):
                size = self.client_socket.recv(64).decode()
                self.client_socket.send(b'0')
                note = self.client_socket.recv(int(size)).decode()
                notes.append(json.loads(note[:-2]))
                self.client_socket.send("+".encode('utf-8')) # Go next note
            return notes

        else:
            self.client_socket.close()
            return False


    def get_version(self, note_id): # Change Method 
        """ Метод возвращает текст старей версии записки """
        msg = json.dumps({
            '_id':note_id
        })
        title = "hash.get_version.%s"%gso(note_id)
        self.client_socket.sendall(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(msg.encode('utf-8'))
            size = int.from_bytes(self.client_socket.recv(16),'big')
            result = self.client_socket.recv(size).decode()
            return json.loads(result)
        else:
            self.client_socket.close()
            return


    def change_favorite(self, note_id, user, favorite):
        values = json.dumps({
            '_id':note_id,
            'user':user,
            'favorite': favorite,
        })

        title = "hash.change_favorite.%s"%gso(values)
        self.client_socket.sendall(title.encode('utf-8'))
        # Read an answer
        if self.client_socket.recv(1024).decode() == "Success":

            self.client_socket.sendall(values.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else:
            self.client_socket.close()
            return False


    def change_note(self, note_id, user, new_text, favorite):
        """ Send change request and new_text """
        new_note = json.dumps({
            '_id':note_id,
            'user': user, 
            'text':new_text,
            'favorite':favorite
        })
        # first request 
        title = "hash.change_note.%s"%gso(new_note)
        self.client_socket.sendall(title.encode('utf-8'))
        # Read an answer
        if self.client_socket.recv(1024).decode() == "Success":

            self.client_socket.sendall(new_note.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else:
            self.client_socket.close()
            return False


    def new_version(self, note_id, user, new_text, favorite, date):
        """ Запрос на создание новой версии заметки """
        #
        new_note = json.dumps({
            '_id': note_id,
            'user':user,
            'text':new_text,
            'favorite':favorite,
            'date': date,
        })

        title = "hash.new_version.%s"%gso(new_note)
        self.client_socket.sendall(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(new_note.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else:
            self.client_socket.close()
            return False


    def delete_share(self, _id, name):
        msg = json.dumps({
            "_id":_id, 
            'name':name
        })

        title = "hash.del_share.%s"%gso(msg)
        self.client_socket.send(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(msg.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else: 
            self.client_socket.close()
            return False

    def share(self, note_id, name, level):
        msg = json.dumps({
            '_id':note_id,
            'share':(name, level)
        })
        title = "hash.share.%s"%gso(msg)
        self.client_socket.sendall(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(msg.encode('utf-8'))
            self.client_socket.recv(32)
            return True
        else: 
            self.client_socket.close()
            return False


    def delete_notes(self, parent_id, note_id = None):
        # Preparing title
        if note_id is None:
            msg = json.dumps(parent_id)
        else:
            msg = json.dumps({
                'parent':parent_id,
                '_id'   :note_id,
            })
        title = "hash.delete_notes.%s"%gso(msg)
        # Send data
        self.client_socket.sendall(title.encode('utf-8'))
        if self.client_socket.recv(1024).decode() == "Success":
            self.client_socket.sendall(msg.encode('utf-8'))
            self.client_socket.recv(32)
        else: 
            self.client_socket.close()
            return False


    def close(self):
        self.client_socket.send('exit'.encode('utf-8'))
        self.client_socket.close()