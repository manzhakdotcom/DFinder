# -*- coding: utf-8 -*-
import fdb
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import *
import configparser
import os
import sys


class Config:
    def __init__(self):
        self.file = 'settings.ini'

    def is_file(self, file):
        if not os.path.exists(file):
            return False
        else:
            return True

    def create_config_file(self, config):
        config['Название участка'] = {'ip': '127.0.0.1',
                                      'path': 'c:\\Неман\\Участок\\Events\\',
                                      'file': 'COR_Название_Участка.GDB'
                                      }
        with open(self.file, "w", encoding='utf-8') as config_file:
            config.write(config_file)
        return config

    def get_data(self, config):
        config.read(self.file, encoding='utf-8')
        data = {}
        for section in config.sections():
            data[section] = {}
            for (key, val) in config.items(section):
                data[section][key] = val
        return data

    def options(self):
        config = configparser.ConfigParser()
        if self.is_file(self.file):
            return self.get_data(config)
        else:
            MsgBox = messagebox.askquestion('Создать файл', 'Файл '
                                            + self.file
                                            + ' отсуствует. Создать файл с примером настроек?',
                                            icon='warning')
            if MsgBox == 'yes':
                self.create_config_file(config)
                messagebox.showinfo('Сообщение', 'Файл '
                                    + self.file
                                    + ' создан. Настройте его и запустите программу.')
                sys.exit(1)
            elif MsgBox == 'no':
                messagebox.showinfo('Сообщение', 'Без файла '
                                    + self.file
                                    + ' с настройками программа работать не будет.')
                sys.exit(1)


class Stuff:
    def path(self, key):
        path = key['ip'] + ':' + key['path'] + key['file']
        return path.encode('cp1251')

    def get_stuff_from_db(self, key):
        try:
            conn = fdb.connect(dsn=self.path(key), user='NEMAN', password='NEMAN')
            cur = conn.cursor()
            cur.execute("""SELECT FIRST 2 DUTYFIO, ORDERGIVINGTIME 
                           FROM ORDERS 
                           WHERE ORDERTYPENUMBER=0 
                           ORDER BY ORDERGIVINGTIME 
                           DESC""")
            data = []
            for row in cur:
                data.append(row)
            conn.close()
            cur.close()
            return data
        except Exception as err:
            messagebox.showwarning('Предупреждение', 'Файл '
                                   + key['file']
                                   + ' не найден!\nВозможно неправильный путь к файлу или ошибка:\n'
                                   + str(err))
            return []

    def stuff(self, data):
        stuff = {}
        for (value, key) in data.items():
            stuff[value] = self.get_stuff_from_db(key)
        return stuff


class VerticalScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        canvas = Canvas(self, bd=0, highlightthickness=0)
        vscrollbar = Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        hscrollbar = Scrollbar(self, orient=HORIZONTAL, command=canvas.xview)
        hscrollbar.pack(fill=X, side=BOTTOM, expand=FALSE)
        canvas.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)


class App:
    def __init__(self, root):
        self.root = root
        self.root.bind('<F1>', self.top_level_about)
        self.root.bind('<Control-q>', self.close)
        self.root.bind('<Control-f>', self.update_frame)
        self.menu()
        self.elements()

    def menu(self):
        self.root.option_add('*tearOff', False)
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file = Menu(menubar)
        about = Menu(menubar)

        menubar.add_cascade(menu=file, label='Файл')
        menubar.add_cascade(menu=about, label='?')

        file.add_command(label='Получить', command=self.update_frame, accelerator="Ctrl+F")
        file.add_separator()
        file.add_command(label='Выйти', command=self.close, accelerator="Ctrl+Q")

        about.add_command(label='О программе', command=self.top_level_about, accelerator="F1")

    def close(self, event=None):
        self.root.destroy()

    def elements(self):
        self.frame_scroll()

        self.label_info = Label(self.frame.interior,
                                text='Нажмите <Получить> или <CTRL+F>\nи дождитесь результата.',
                                fg="#333")
        self.label_info.pack(ipadx=20, ipady=150)

        self.bottom_frame = Frame(self.root)
        self.bottom_frame.pack(fill=X, side=BOTTOM)

        self.button = Button(self.bottom_frame, text='Получить', command=self.update_frame)
        self.button.pack(padx=10, pady=10, ipadx=10, ipady=3)

    def update_frame(self, event=None):
        self.button.configure(text='Загрузка...')
        self.button.update()
        self.frame.destroy()
        self.frame_scroll()
        self.content()
        self.button.configure(text='Обновить')
        self.button.update()

    def frame_scroll(self):
        self.frame = VerticalScrolledFrame(self.root)
        self.frame.pack(fill=BOTH, expand=True, side=TOP)

    def content(self):
        label = Label(self.frame.interior, text='Список диспетчеров:', font=('Helvetica', 10, 'bold'))

        stuff = Stuff().stuff(Config().options())
        labels = []
        for value, key in stuff.items():
            if 0 != len(key):
                str = '\n'
                for item in key:
                    str += item[1].strftime('%H:%M %Y.%m.%d') + ' - ' + item[0] + '\n'
                value = '<' + value + '>' + str
            else:
                value = '<' + value + '>' + '\nНет данных'
            labels.append(Label(self.frame.interior, text=value))

        label.pack()
        for i in range(len(labels)):
            labels[i].pack()

    def top_level_about(self, event=None):
        win = Toplevel(self.root)
        win.resizable(0, 0)
        center(win, 220, 115, 0)
        win.iconbitmap(os.getcwd() + os.path.sep + 'icon.ico')
        win.title('О программе')

        frame = Frame(win)
        frame.pack()

        label1 = Label(frame, text='Программа выводит\nсписок диспетчеров ЦУП,\nкоторые приняли смену.')
        label2 = Label(frame, text='Автор © Манжак С.С.')
        label3 = Label(frame, text='Версия v' + self.root.version + ' Win 32')

        label1.grid(row=0, column=0, pady=10)
        label2.grid(row=1, column=0)
        label3.grid(row=2, column=0)

        win.focus_set()
        win.grab_set()
        win.wait_window()


def center(root, width, height, offset):
    x = round(root.winfo_screenwidth() / 2 - width / 2 + offset)
    y = round(root.winfo_screenheight() / 2 - height / 2 + offset)
    root.geometry('{}x{}+{}+{}'.format(width, height, int(x), int(y)))


def main():
    root = Tk()
    root.version = '0.0.2'
    root.resizable(0, 0)
    center(root, 300, 400, 0)
    root.title('Поиск диспетчеров')
    root.iconbitmap(os.getcwd() + os.path.sep + 'icon.ico')
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
