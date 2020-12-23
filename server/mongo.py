from bson.objectid import ObjectId
import pymongo
import json 

class Singleton(type):
    """ 
    The connection to Mongo must be one """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Mongo(metaclass=Singleton):
    """Взаимодействие с БД """
    def __init__(self):
        client = pymongo.MongoClient('127.0.0.1', 27017)
        db = client['MainDB']
        self.collection = db['notes']
        print("I am here")

    @staticmethod
    def get_date():
        import datetime
        date = datetime.datetime.now()
        return [date.year, date.month, date.day, date.hour, date.minute]

    def create_note(self, values):
        """ Метод создает новую запись в БД """
        value = json.loads(values)
        data = {
            'owner': value['owner'],
            'name' : value['name'],
            'text' : value['text'],
            'date' : self.get_date(),
            'newest': True,
            'old': list(),
            'favorite': [[value['owner'], False],],
            'share':list(),
        }
        self.collection.insert_one(data)
        return True

    def get_all(self, values):
        """ Функция возвращает список всех записок для owner """
        value = json.loads(values)
        result = []
        # Все карточки владельце
        for note in self.collection.find({'owner':value['owner'], 'newest':True}):
            result.append(note)
        # Все share-карточки
        for note in self.collection.find({}):
            try: 
                if note['share'][0][0] == value['owner']:
                    result.append(note)
            except (KeyError, IndexError): continue
        return result 

    def change_note_text(self, values):
        value = json.loads(values)
        print('ID is {}'.format(value['_id']))
        # Get favorites list
        favorite = self.collection.find_one({'_id':ObjectId(value['_id'])})['favorite']
        # Change favorite flag of sender user
        print('Favorite list is %s'%favorite)
        for i in range(len(favorite)):
            if favorite[i][0] == value['user']:
                favorite[i][1] = value['favorite']

        # Updating 
        self.collection.update_one(
            {'_id':ObjectId(value['_id'])}, 
                {'$set':{
                        'text':value['text'],
                        'favorite':favorite,
                        'date': self.get_date()
                        }})

    def change_favorite(self, values):
        value = json.loads(values)
        favorite = self.collection.find_one({'_id':ObjectId(value['_id'])})['favorite']
        for i in range(len(favorite)):
            if favorite[i][0] == value['user']:
                favorite[i][1] = value['favorite']
        self.collection.update_one(
            {'_id':ObjectId(value['_id'])},
                {'$set':{
                    'favorite':favorite
                }})

    def new_version(self, values):
        value = json.loads(values)
        # Step 1: Create new note and get its data 
        name = self.collection.find_one({'_id':ObjectId(value['_id'])})['name']
        text = self.collection.find_one({'_id':ObjectId(value['_id'])})['text']
        old_version = self.collection.insert_one({
                        'name': name,
                        'text': text,
                        'date': value['date'],
                    }).inserted_id
        # Step 2: Update newest card
        # Get list old version
        old = self.collection.find_one({'_id':ObjectId(value['_id'])})['old']
        print("The old is :",old)
        old.append((str(old_version), value['date']))
        # Get favorite list 
        favorite = self.collection.find_one({'_id':ObjectId(value['_id'])})['favorite']
        for i in range(len(favorite)):
            if favorite[i][0] == value['user']:
                favorite[i][1] = value['favorite']

        # Update the current note
        self.collection.update_one(
            {'_id':ObjectId(value['_id'])}, # Find note
                    {'$set':{                    # Change note
                        'text': value['text'],
                        'date': self.get_date(),
                        'favorite': favorite,
                        'old': old,
                    }})

    def get_version(self, values):
        value = json.loads(values)
        return self.collection.find_one({'_id':ObjectId(value['_id'])})['text']
        
    def delete_all(self, note_id):
        # Step 1. Delete all old version
        old = self.collection.find_one({'_id':ObjectId(note_id)})['old']
        for i in range(len(old)): # Delete all children
            self.collection.delete_one({'_id':ObjectId(old[i][0])})
        # Step 2. Delete main note
        self.collection.delete_one({'_id':ObjectId(note_id)})
        return True

    def delete_one(self, ids):
        # Step 1: Delete the id with 'note_id'
        self.collection.delete_one({'_id':ObjectId(ids['_id'])})
        # Step 2: Delete all links from parent 
        old = self.collection.find_one({'_id':ObjectId(ids['parent'])})['old']
        for i in range(len(old)):
            if ids['_id'] == old[i][0]: 
                old.pop(i);break 
        # Change the old to parent
        self.collection.update_one(
            {'_id':ObjectId(ids['parent'])},
                {'$set': {
                    'old':old,
                }})
        return True


    def share(self, values):
        value = json.loads(values)
        # Get share list
        share_list = self.collection.find_one({'_id':ObjectId(value['_id'])})['share']
        if len(list(filter(lambda x: x[0] == value['share'][0], share_list))) != 0:
            for i in range(len(share_list)):
                if share_list[i][0] == value['share'][0]:
                    print('Changed value')
                    print(value['share'][1])
                    share_list[i][1] = value['share'][1]
        else: 
            share_list.append(value['share'])
        # favorite status
        favorite = self.collection.find_one({'_id':ObjectId(value['_id'])})['favorite']
        if len(list(filter(lambda x: x[0] == value['share'][0], favorite))) == 0:
            favorite.append([value['share'][0], False])
        # Update BD 
        self.collection.update_one(
            {'_id':ObjectId(value['_id'])},
                {'$set':{
                    'share':share_list,
                    'favorite':favorite
                }})
        
    def del_share(self, values):
        value = json.loads(values)
        # Get and change share_list
        share_list = self.collection.find_one({'_id':ObjectId(value['_id'])})['share']
        print(share_list)
        share_list = list(filter(lambda x: x[0] != value['name'], share_list))
        print(share_list)
        # Update mongo
        self.collection.update_one(
            {'_id':ObjectId(value['_id'])},
                {'$set':{
                    'share':share_list, 
                }})