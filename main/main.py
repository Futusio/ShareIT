from tkinter import * 
from random import randint as rn
import socket
import sys
from tkinter import messagebox
import datetime

from client import Client

global_owner = ""

def check_favorite(lst):
    return list(filter(lambda x: x[0]==global_owner, lst))[0][1]

def close_connect():
    connection.close()
    main_window.destroy()


class Share(Frame):
    """ Окошко добавления и просмотра списка пользователей для заметки
    Вторая из двух главных фич программы """
    def __init__(self, note, root, parent=None):
        super().__init__(parent)
        self.root=root
        self.root.attributes('-disabled',True)
        self.root.after_idle(self.root.attributes,'-disabled',True)
        #
        self._note = note  # The Note object tkinter to update its data 
        self.note = note.note # The dict from DB with note text
        self.menu = None
        self.level = 0
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.cls)
        #
        self.initUi()
        self._initUi()

    def initUi(self):
        # frames 
        self.main_frame = LabelFrame(self, text='Share List')
        self.top = Frame(self.main_frame)
        bottom = Frame(self.main_frame)
        # Widgets 
        # Get all people whos was shared
        self.update_menu()
        # buttons
        del_button = Button(self.top, text='✕', command=self.del_user)
        quit_button = Button(bottom, text='⟸', command=self.cls)
        new_button = Button(bottom, text='Share', command=self.forward)
        # unpacking 
        del_button.pack(side='right', fill='x', expand=1)
        quit_button.pack(side='left', fill='x', expand=1)
        new_button.pack(side='right',fill='x', expand=1)
        self.top.pack(side='top', fill='x')
        bottom.pack(side='bottom', fill='x')
        self.main_frame.grid()

    def callback(self, *events): 
        """ CallBack to text, allows enter only eng abc """
        enables = [chr(i) for i in range(97,123)] + [chr(i) for i in range(65,91)]
        try: 
            if self.text.get()[-1] not in enables or len(self.text.get()) > 8:
                self.text.set(self.text.get()[:-1])
        except IndexError: pass

    def _initUi(self):
        # Frames 
        self._main_frame = LabelFrame(self, text='ShareIT')
        top = Frame(self._main_frame)
        middle = Frame(self._main_frame)
        bottom = Frame(self._main_frame)
        # Widgets 
        enter_text = Label(top, text='Name:')
        #self.enter_field = Entry(top)
        level_text = Label(middle, text='Level:')
        variable = StringVar(middle)
        variable.set("ReadOnly")
        menu = OptionMenu(middle, variable, 'ReadOnly', 'AllFutures', command=self.change_level)
        quit_button = Button(bottom, text="⟸", command=self.back)
        share_button = Button(bottom, text="ShareIT", command=self.share_it)
        # Validation
        self.text = StringVar()
        self.text.trace('w', self.callback)
        self.enter_field  = Entry(top, textvariable=self.text) 
        # Unpacking 
        enter_text.pack(side='left')
        self.enter_field.pack(side='right')# fill='x')#, expand=1)
        level_text.pack(side='left', fill='x')
        menu.pack(side='right', fill='x')
        quit_button.pack(side='left', fill='x', expand=1)
        share_button.pack(side='right', fill='x', expand=1)
        # Frames 
        top.pack(side='top', fill='x')
        bottom.pack(side='bottom', fill='x')
        middle.pack(side='bottom', fill='x', pady=3)

    def update_menu(self):
        """ Updating menu when added or deleted any notes """
        if self.menu is not None: 
            self.menu.destroy()
        variable = StringVar(self.top)
        try: 
            share = list(map(lambda x: x[0], self._note.note['share']))
            self.current_user = share[0]
            variable.set(share[0])
        except (KeyError, IndexError):
            self.current_user = 'empty'
            share = ["empty"]
            variable.set("empty")
        self.menu = OptionMenu(self.top, variable, *share, command = self.change_user)
        self.menu.pack(side='left',fill='x')


    # EVENTS
    def change_user(self, event):
        self.current_user = event
        self.parent.lift()

    def del_user(self):
        """ Удаляет пользователя из ShareList """
        if self.current_user == 'empty':
            messagebox.showerror('Error',"The share list is empty")
        else:
            if messagebox.askquestion("Unshare?", "Do you realy want to unshare the {}?".format(self.current_user)) == 'yes':
                connection.delete_share(self.note['_id'], self.current_user)
                messagebox.showinfo("Success", 'The {} was unshared'.format(self.current_user))
                self._note.note['share'] = list(filter(lambda x: x[0] != self.current_user, self.note['share']))
                #self.note['share'] = list(filter(lambda x: x[0] != self.current_user, self.note['share']))
                self.update_menu()
            else: 
                pass
        self.parent.lift()

    def change_level(self, event):
        if event == "ReadOnly":
            self.level   = 0
        else: self.level = 1

    def share_it(self):
        """ Sharing """
        if self.enter_field.get() == global_owner: 
            messagebox.showerror('Error',"Do not use your name!")
            self.text.set("")
            return
        elif self.enter_field.get() == "":
            messagebox.showerror('Error',"The name must not be blank")
            return
        if connection.share(self.note['_id'], self.enter_field.get(), self.level):
            messagebox.showinfo('Success',"The note was shared")
            self._note.note['share'].append([self.enter_field.get(), self.level])
            #self._note.note['share'] = list(filter(lambda x: x[0] != self.current_user, self.note['share']))
            #self.note['share'] = list(filter(lambda x: x[0] != self.current_user, self.note['share']))
            self.update_menu()
            self.back()
        else:
            messagebox.showerror('Error',"Unknown error!")
            self.parent.lift()

    def forward(self):
        """ Opens second screen """
        self.main_frame.grid_remove()
        self._main_frame.grid()

    def back(self):
        """ Opens first screen """
        self._main_frame.grid_remove()
        self.main_frame.grid()
    
    def cls(self):
        """ Close the window """
        self.root.attributes('-disabled',False)
        self.root.after_idle(self.root.attributes,'-disabled',False)
        self.parent.destroy()

class MinimalNote(Frame):
    """ Виджит отображающий миниатюры заметок """
    def __init__(self, row, note, window, root, main, *args):
        """
        row - ряд для размещения виджета 
        note - заметка
        window - frame
        root - Tk()
        master - для вызова методов master ( filler )
        """
        super().__init__(row)#, width=100) # По рофлу сними)
        # valuables
        self.note = note
        self.favorite = check_favorite(self.note['favorite'])
        self.main = main
        self.root = root
        self.window = window
        self.name = self.note['name']
        self.owner = self.note['owner']
        self.text = self.note['text']
        self.date = self.get_date(self.note['date'])
        self.tag = "note_%s"%note['_id']
        # SetUp
        self.initUi()
        # Event
        self.bind_class(self.tag, '<Double-Button-1>', self.test) # Maybe simple click, not double?
        self.bind("<Enter>" , self.one)
        self.bind("<Leave>", self.two)

    def get_date(self, date):
        """ Функция приводит дату к боеле читабельному виду """
        date = list(map(lambda x: str(x), date))
        if len(date[1]) == 1:
            date[1] = '0' + date[1]
        if len(date[2]) == 1:
            date[2] = '0' + date[2]
        return "{}.{}.{}".format(date[2],date[1],date[0])

    def cut_text(self, text, lenght):
        if len(text) > lenght:
            return text[:lenght] + "..."
        return text

    def one(self, event): #  Use
        self['bg'] = 'blue'

    def two(self, event):
        self['bg'] = 'gray'

    def test(self, event):
        self.window.grid_remove()
        self.note = Note(self.window, self.root, self.main, self.note)
        self.note.grid(padx=10,pady=1)

    def initUi(self):
        # Settings
        self['bd'] = 1
        self['bg']='gray'
        # Create Frames
        title = Frame(self, bg='white')
        note = Text(self, width=10, height=4, wrap=WORD, cursor='arrow', relief=FLAT)
        cellar = Frame(self, bg='white')
        # Fillers
        show_name = self.cut_text(self.name,8) # cut at 8
        show_name += " ★" if self.favorite else ""
        name_label = Label(title, text=show_name, bg='white')
        owner_label = Label(title, text=self.owner, bg='white')
        note.insert(1.0, self.cut_text(self.text,32))
        date_label = Label(cellar, text="Changed: %s"%self.date, bg='white')
        # Packing 
        name_label.pack(side='left')
        owner_label.pack(side='right')
        date_label.pack(fill='x', expand=TRUE)
        title.pack(fill='x',expand=TRUE)
        note.pack(fill='x',expand=TRUE)
        cellar.pack(fill='x',expand=TRUE)
        # Set Tag
        title.bindtags(self.tag)
        note.bindtags(self.tag)
        cellar.bindtags(self.tag)
        name_label.bindtags(self.tag)
        owner_label.bindtags(self.tag)
        date_label.bindtags(self.tag)
        self.bindtags(self.bindtags() + (self.tag,))

class Note(Frame):
    """Окно заметки. Создается как для создания новой заметки, так и для 
    просмотра/редактирования ранее созданной."""
    def __init__(self, window, root, main, note=None): # Исправить owner по умолчанию 
        """        window - главное окно программы, необходимо передать
        root - корень программы, куда будет накладывать текущее окно
        name, text, date - информация о заметки, передается в случае
        note - json заметки
        просмотра/редактирования ранее созданной"""
        super().__init__(root)
        self.main = main
        self.create = False if note is None else True # Новую или существующую заметку
        self.note = note
        if note is not None:
            self.favorite = check_favorite(note['favorite'])
            self.rights() # Права
        self.root = root
        self.window = window
        self.initUi()

    def rights(self):
        """ Зависит от ReadOnly or AllFutures """
        if self.note['owner'] == global_owner:
            self.right = True
        else:
            if list(filter(lambda x: x[0]==global_owner, self.note['share']))[0][1]:
                self.right = True
            else:
                self.right = False

    def cut_text(self,text,lenght):
        """ The method returns cutted text """
        if len(text) >= lenght:
            return text[:lenght] + '...'
        return text

    def date_validate(self, date): # Is it a poem?)
        """ The func returns a validate date to show it """
        date = list(map(lambda x: str(x), date))
        if len(date[1]) == 1:
            date[1] = '0' + date[1]
        if len(date[2]) == 1:
            date[2] = '0' + date[2]
        if len(date[3]) == 1:
            date[3] = '0' + date[3]
        if len(date[4]) == 1:
            date[4] = '0' + date[4]
        return "{}.{}.{} {}:{}".format(date[2],date[1],date[0], date[3], date[4])

    def initUi(self):
        # Frames block
        title = Frame(self,relief=RIDGE , bd=1)
        self.text_box = Text(self, width=35, height=23)
        celery = Frame(self)
        # Title widgets
        quit_button = Button(title, text='⟸', command=self.quit)
        quit_button.pack(side='left')
        if self.create: # Если открываем существующую заметку
            name_label = Label(title,text=self.cut_text(self.note['name'], 8))
            version_label=Label(title, text='Version:')
            # Get Dates #  Изменить порядок записсей
            self.version_list = [self.date_validate(self.note['date'])] + [self.date_validate(i[1]) for i in self.note['old']]
            variable = StringVar(title)
            variable.set(self.version_list[0])
            menu = OptionMenu(title, variable, *self.version_list, command=self.change_version)
            #menu.config(font=("", 8))
            # Custom Pack
            name_label.pack(side='left')
            menu.pack(side='right', padx=3)
            version_label.pack(side='right')
            self.favorite_btn = Button(title, text='★', command=self.change_favorite)
            self.favorite_btn.pack(side='left', padx=3)
            if self.favorite: self.favorite_btn['relief'] = SUNKEN
        else: # Если создаем новую
            name_label = Label(title, text='Name:')
            self.enter_name = Entry(title)
            self.enter_name.pack(side='right', padx=3)
            name_label.pack(side='right')
        # Fill text_box
        if self.create:
            self.text_box.insert(1.0, self.note['text'])
        # Bottom Frame Widgets
        save_command = self.save_new_note if self.note is None else self.save_old_note
        self.save_button = Button(celery, text='SaveIT', command=save_command)
        self.share_button = Button(celery, text='ShareIT', command=self.make_share)
        self.delete_button = Button(celery, text="DeleteIT", command=self.delete_all_notes)
        # rights
        # Unpacking frames       
        title.pack(side='top', fill='x',pady=3)
        self.text_box.pack(fill='both')
        celery.pack(side='bottom',fill='x',pady=10)
        # Unpacking celery
        self.save_button.pack(side='left',fill='both',padx=1, expand=True)
        if self.create: 
            if not self.right: 
                self.save_button['state'] = DISABLED
                self.share_button['state']= DISABLED
            self.delete_button.pack(side='right', fill='x',padx=1, expand=True)
            self.share_button.pack(side='right',fill='x',padx=1, expand=True)
        # Events

# EVENTS 
    def make_share(self):
        rt = Toplevel()
        rt.resizable(False,False)
        rt.transient(self.root)
        #
        values = (self.root.winfo_x(), self.root.winfo_y())
        rt.geometry('+{}+{}'.format(
                            int(values[0] + self.root.winfo_width()/3),
                            int(values[1] + self.root.winfo_height()/3)))
        #
        main = Share(self, self.root, rt)
        rt.iconbitmap('icon.ico')
        rt.title("Share")
        main.pack()
        rt.mainloop()

    def change_version(self, event):
        """The method is changing note text with using version """
        if self.date_validate(self.note['date']) == event: # If newest note
            self.text_box.delete(1.0, END)
            self.text_box.insert(1.0, self.note['text'])
            if self.right:
                self.share_button['state'] = ACTIVE
                self.save_button['state']  = ACTIVE
            self.delete_button['command'] = self.delete_all_notes
        for i in self.note['old']: # For others notes 
            if self.date_validate(i[1]) == event:
                self.current_id = i[0]
                version_text = connection.get_version(i[0])
                self.text_box.delete(1.0, END)
                self.text_box.insert(1.0, version_text)
                self.save_button['state'] = DISABLED
                self.share_button['state']= DISABLED
                self.delete_button['command'] = self.delete_one_note

    def change_favorite(self):
        """ 
        Метод изменяет значения флага favorite при
        клаце на кнопку """
        if self.favorite_btn['relief'] == SUNKEN:
            self.favorite_btn['relief'] = RAISED
            self.favorite = False
        else:
            self.favorite = True
            self.favorite_btn['relief'] = SUNKEN
        connection.change_favorite(self.note['_id'], global_owner, self.favorite)
    
    def delete_all_notes(self): #[!] Принять результатаы от сервера!!!
        """ Delete all version of the note"""
        if messagebox.askquestion('Wait','Delete the note with all its version?') == 'yes':
            if self.note['owner'] == global_owner:
                connection.delete_notes(self.note['_id'])
            else: 
                connection.delete_share(self.note['_id'], global_owner)
            self.quit()
        else:
            pass

    def delete_one_note(self):
        """ Delete current version of the note """
        if messagebox.askquestion('Wait','Delete the current note version?') == 'yes':
            if self.note['owner'] == global_owner:
                connection.delete_notes(self.note['_id'], self.current_id)
                self.quit()
            else: 
                messagebox.showerror('Error','You may delete only all notes, not versions')
        else:
            pass

    def save_old_note(self): # Рассмотреть возможность передачи объекта, а не его полей
        if messagebox.askquestion('Wait', 'Keep the current version?') == 'yes':
            connection.new_version(self.note['_id'], global_owner, self.text_box.get(1.0, END), self.favorite, self.note['date'])
        else: 
            connection.change_note(self.note['_id'], global_owner, self.text_box.get(1.0, END), self.favorite)
        self.quit()

    def save_new_note(self):
        """Data validation and socket request"""
        if not self.enter_name.get().replace(' ', ''):
            messagebox.showerror('Error', 'The name field have not to be empty')
            return
        elif self.text_box.get(1.0, END).isspace():
            messagebox.showerror('Error', "The note must not to be blank")
            return 
        # If the data is valid - create socket 
        if connection.create_note(global_owner, self.enter_name.get().strip(), self.text_box.get(1.0, END)):
            messagebox.showinfo("Success","The new note was created")
            self.quit() # Add new note to minimal list later
        else: 
            messagebox.showerror('Error', "Unknown error\nTry again")


    def quit(self):
        self.main.changer()
        self.grid_remove()
        self.window.grid() 

class Main():
    def __init__(self, parent=None):
        self.place_width, self.first = 0, True
        self.parent = parent
        self.flags = [0,0,0] # Три флага реверсивности сортировки
        self.flag = False # Флаг принимает значения True после первой инициализации
        # Написать метод получения данных для объекта и вставить сюда
        # self.get_notes(17)
        self.initUi()


    def changer(self):
        self.notes = connection.fill_youself(global_owner)
        self.fill_notes = self.notes
        self.filler(self.fill_notes)


    def clear(self):
        """ Метод очищает виджет контейнер """
        try: 
            for i in self.rows:
                i.pack_forget()
        except AttributeError:
            return


    def change_filter(self, event):
        """ The event appears when user change filter """
        self.clear()
        if event == "Yours":
            self.fill_notes = list(filter(lambda x: x['owner']==global_owner, self.notes))
        elif event == "All notes":
            self.fill_notes = self.notes
        elif event == "Sharing":
            self.fill_notes = list(filter(lambda x: x['owner'] != global_owner, self.notes))
        elif event == "Favorite":
            self.fill_notes = list(filter(lambda x: check_favorite(x['favorite']) == True, self.notes))
        self.filler(self.fill_notes)


    def change_sort(self, event): # Избавиться от флага и ввести замыкание
        """Метод вызывается в случае смены принципа сортировки
        Сортирует исходный массив """
        self.clear() # Очистим форум
        if event == "Name": # Сортировка по имени
            if self.flags[0] == 1: # Двойной выбор делает обратную сортировку
                self.fill_notes.sort(key=lambda x:x['name'], reverse=True)
                self.flags[0] = 0
            else: # Первый выбор сортирует прямо
                self.flags[1], self.flags[2] = 0, 0
                self.fill_notes.sort(key=lambda x:x['name'])
                self.flags[0] = 1
        elif event == "Date": # Если выбираем сортировку по дате
            if self.flags[1] == 1:
                self.fill_notes.sort(key=lambda x:x['date'], reverse=True)
                self.flags[1] = 0
            else:
                self.flags[0], self.flags[2] = 0, 0
                self.fill_notes.sort(key=lambda x:x['date'])
                self.flags[1] = 1
        elif event == "Owner": # Сортировка по владельцу
            if self.flags[2] == 1:
                self.fill_notes.sort(key=lambda x:x['owner'], reverse=True)
                self.flags[2] == 0
            else:
                self.flags[0], self.flags[1] = 0, 0
                self.fill_notes.sort(key=lambda x:x['owner'])
                self.flags[2] = 1
        # И вызываем filler
        self.filler(self.fill_notes)


    def generate(self):
        """
        Функция возвращает две пустые заметки
        для динамического вычисления необходимого пространства
        на экране
        """
        note = { # Шаблон заметки
            '_id' : '0',
            'name':'0000000000',
            'owner':global_owner,
            'text' :'0000000000000000000000000000000000000000',
            'date' :[2020, 10,10,20,40],
            'favorite':[[global_owner, True],],
        }
        row = Frame(self.frame) # Необходимо получить его длину
        self.rows.append(row)
        self.one = MinimalNote(self.rows[0], note, self.window, self.parent, self)
        self.two = MinimalNote(self.rows[0], note, self.window, self.parent, self)
        row.pack(side='top')
        self.one.pack(side='left', fill='x', padx=10, pady=10)
        self.two.pack(side='right', fill='x')


    def filler(self, notes):
        """ Метод заполняет Frame виджетами """
        self.clear()
        self.rows = [] # В строке по две заметки
        index = 0
        extra = 0 if len(notes)%2 == 0 else 1
        if self.first: self.generate()
        for _ in range(int(len(notes)/2)+extra):
            #print("Len is %s"%len(notes))
            if len(notes) == 0: break # Так как в range есть +1, иногда эту итерацию нужно избежать
            row = Frame(self.frame)
            self.rows.append(row)
            row.pack(side='top')
            for j in range(2): # WHY THE SHIT IS NOT WORKING
                #print(notes[index])
                a = MinimalNote(row, notes[index], self.window, self.parent, self)
                if j%2==0:
                    a.pack(side='left', fill='x', padx=10, pady=10)
                else:
                    a.pack(side='right', fill='x')
                if index == len(notes)-1: break # Резкий выход
                index += 1
        if self.flag:
            self.canv.update()
            self.canv.config(scrollregion=self.canv.bbox('all'))


    def go_back(self):
        self.parent.destroy()
        connection.close()
        auth()


    def initUi(self):
        # Отрефакторить 
        self.window = Frame(self.parent)
        # Title frame
        top_frame = Frame(self.window, relief=RAISED, bd=1)
        leave_btn = Button(top_frame, text='⟸', command=self.go_back)
        name_label = Label(top_frame, text=global_owner)
        status_label = Label(top_frame, text="Version:")
        self.status_label_mode = Label(top_frame, text="0.1 Stable", fg='red')
        top_frame.pack(side='top', fill='x',pady=1)
        leave_btn.pack(side='left')
        name_label.pack(side='left')
        self.status_label_mode.pack(side='right')
        status_label.pack(side='right')
        # Container
        main_frame = Frame(self.window, bg='gray', bd=1)
        main_frame.pack(pady=25)
        # Фрейм составной 
        mode_frame = Frame(main_frame, relief=RAISED, bd=1)
        mode_frame.pack(side='top', fill='x')
        # Наполняем фрейм
        info_lab = Label(mode_frame, text="Sorted by:")
        variable_sort = StringVar(mode_frame)
        variable_sort.set('Name')
        sorted_menu = OptionMenu(mode_frame, variable_sort, 'Name', 'Date', 'Owner', command=self.change_sort)
        # Filter
        sort = Label(mode_frame, text="Filter:")
        variable_filter = StringVar(mode_frame)
        variable_filter.set('All notes')
        filter_menu = OptionMenu(mode_frame, variable_filter, 'All notes','Favorite','Yours','Sharing', command=self.change_filter)
        # Pack
        info_lab.pack(side='left', fill='x')
        sorted_menu.pack(side='left', fill='x')
        filter_menu.pack(side='right', fill='x')
        sort.pack(side='right', fill='x')
        # Разбираемся с скроллингом 
        self.canv = Canvas(main_frame)#, width=325, height=300)
        self.canv.pack(side="left", fill='x')
        self.frame = Frame(self.canv)
        self.frame.pack(expand=1)
        # Fill Widget
        self.changer()
        #
        scr = Scrollbar(main_frame, orient="vertical", takefocus=False)
        scr.pack(side="left", fill="y")
        scr["command"] = self.canv.yview
        #
        self.canv.create_window((0, 0), window=self.frame, anchor="nw")
        self.canv.update()

        self.canv['width'] = self.rows[0].winfo_width()
        self.place_width = self.rows[0].winfo_width()
        self.canv.config(yscrollcommand=scr.set, scrollregion=self.canv.bbox('all'))#(0, 0, 300, self.long))
        if self.first:
            self.first = False
            self.rows[0].destroy()
            self.one.destroy()
            self.two.destroy()

        # Разобрались с окошком осталось кнопку и еще один фрейм
        add_button = Button(self.window, text="New Note", command=self.clicked)
        add_button.pack(side='bottom', fill='x')
        # flag
        self.flag = True


    def clicked(self): # New_Note button clicked
        self.window.grid_remove()
        self.note = Note(self.window, self.parent, self)
        self.note.grid(padx=10,pady=1)


class Authorization(Frame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUi()
        self.parent = parent

    def callback(self, *events): 
        """ CallBack to text, allows enter only eng abc """
        enables = [chr(i) for i in range(97,123)] + [chr(i) for i in range(65,91)]
        try: 
            if self.text.get()[-1] not in enables or len(self.text.get()) > 8:
                self.text.set(self.text.get()[:-1])
        except IndexError: pass

    def initUi(self):
        frame = LabelFrame(self, text='Authorization')
        top = Frame(frame)
        #
        label = Label(top, text="login:")
        self.text = StringVar()
        self.text.trace('w', self.callback)
        self.enter_field  = Entry(top, textvariable=self.text) 
        btn = Button(frame, text='Enter', command=self.ok_btn)
        #
        frame.pack(padx=5, pady=5)
        top.pack(side='top', padx=5)
        label.pack(side='left')
        self.enter_field.pack(side='right')
        btn.pack(side='bottom',fill='x', pady=5,padx=5)

    def ok_btn(self):
        global global_owner, connection
        global_owner = self.enter_field.get().title()
        connection = Client()
        connection.connect()
        self.parent.destroy()
        window()
        

def auth():
    root = Tk()
    #
    #
    main = Authorization(root)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("+{}+{}".format(int((w/2)-150), int((h/2)-100)))
    main.pack()
    root.iconbitmap('icon.ico')
    root.title('Authorization')
    root.mainloop()


def window():
    global global_owner
    global main_window
    main_window = Tk()
    w, h = main_window.winfo_screenwidth(), main_window.winfo_screenheight()
    main_window.geometry("+{}+{}".format(int((w/2)-100), int((h/2)-200)))
    main_window.resizable(0,0)
    main_window.protocol("WM_DELETE_WINDOW", close_connect)
    main_window.iconbitmap('icon.ico')
    main_window.title("ShareIT")

    #
    main = Main(main_window)
    main.window.grid(padx=10, pady=1)
    #
    main_window.mainloop()

if __name__=="__main__":
    auth()