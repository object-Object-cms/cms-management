from tkinter import *
import requests
import json
import traceback
import signal
import sys
import sqlite3
import tkinter.messagebox
from threading import Thread
from tkinter.filedialog import askopenfilename
from utils import state, CursorClosable
from string import ascii_letters, digits
from random import choice
from hashlib import sha256

def dbex():
    return CursorClosable(database, True)

def dbq():
    return CursorClosable(database, False)

randsec = lambda: ''.join([choice(ascii_letters + ascii_letters.upper() + digits) for x in range(32)])
sha = lambda e: sha256(e.encode('utf-8')).hexdigest()

def initDB():
    with dbex() as c:
        c.execute("""
            create table if not exists userdata (
                uid integer primary key autoincrement,
                accesslevel integer,
                username text unique,
                salt text,
                hash text
            )
        """)
        c.execute("""
            create table if not exists blobdata (
                id integer primary key autoincrement,
                type text,
                content blob
            )
        """)

def showAddUser(callback):
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Add User")
    appWidth = 200
    appHeight = 150

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    def labelledInput(name, factory=Entry):
        lbFrame = Frame(subwin, height=5)
        i = factory(lbFrame)
        Label(lbFrame, text=name).pack(side=LEFT)
        i.pack(side=RIGHT)
        lbFrame.pack(side=TOP, pady=4)
        return i
    uname = labelledInput("Username")
    passw = labelledInput("Password")
    aclvl = labelledInput("Access Level", lambda e: Spinbox(e, from_=0, to=100))
    def execute():
        for x in [uname, passw]:
            x.configure(bg="red" if len(x.get()) < 5 else "green")
        username = uname.get()
        password = passw.get()
        accesslv = aclvl.get()
        if len(username) < 5:
            return
        if len(password) < 5:
            return
        salt = randsec()
        hash_ = sha(password + salt)
        with dbex() as cursor:
            try:
                cursor.execute("insert into userdata (accesslevel, username, salt, hash) values (?, ?, ?, ?)", (int(accesslv), username, salt, hash_))
            except:
                uname.configure(bg="red")
                tkinter.messagebox.showwarning(title = "Error", message = "This user already exists")
                return
        callback()
        subwin.destroy()
    Button(subwin, text="Add", command=execute).pack(side=TOP, pady=4)


def showManageUsers():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage Users")
    appWidth = 640
    appHeight = 480

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    subwin.columnconfigure(1, weight=1)
    rowsLoaded = []
    def populate(frame):
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []
        with dbq() as cursor:
            cursor.execute("select uid, username, accesslevel from userdata")
            Button(frame, text="Add", command=lambda: showAddUser(lambda: populate(frame)), width=20).grid(row=0, column=1)
            i = 1
            for uid, uname, accesslevel in cursor.fetchall():
                l1 = Label(frame, text=f"{uid}", width=3, borderwidth="1",
                        relief="solid")
                l1.grid(row=i, column=0)
                l2 = Label(frame, text=f"{uname}")
                l2.grid(row=i, column=1)
                def updateAccessLevel(uid):
                    with dbex() as cs:
                        cs.execute("update userdata set accesslevel = ? where uid = ?", (int(why.get()), uid))
                def delete(uid):
                    with dbex() as cs:
                        cs.execute("delete from userdata where uid = ?", (uid,))
                    populate(frame)

                why = DoubleVar(root, value=accesslevel)
                s3 = Spinbox(frame, from_=0, to=100, increment=1, textvariable=why, command=lambda: updateAccessLevel(uid))
                s3.grid(row=i, column=2, padx=10)
                b4 = Button(frame, text="Delete", command=lambda: delete(uid))
                b4.grid(row=i, column=3, padx=10)

                rowsLoaded.append(l1)
                rowsLoaded.append(l2)
                rowsLoaded.append(s3)
                rowsLoaded.append(b4)
                i += 1
            if i == 1:
                l1 = Label(frame, text="No users")
                l1.grid(row=1, column=1)
                rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        print(winid)
        canvas.itemconfig(winid, width=event.width - 8)
        #frame.configure(width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0, bg="red")
    frame = Frame(canvas, bg="green")
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)

def main():
    global root
    global database
    database = None

    def openDatabase():
        global database
        if database:
            database.close()
        fname = askopenfilename()
        if not fname:
            return
        database = sqlite3.connect(fname)
        initDB()

        state(openDBButton, "disabled")
        state(closeDBButton, "normal")
        state(mainActionsFrame, "normal", True)

    def closeDatabase():
        global database
        if database:
            database.close()
        database = None

        state(openDBButton, "normal")
        state(closeDBButton, "disabled")
        state(mainActionsFrame, "disabled", True)

    def openFileManagementAction():
        pass

    root = Tk()
    root.title("CMS - Admin Database Management")

    # centrowanie okna na ekranie
    appWidth = 640
    appHeight = 480

    screenWidth = root.winfo_screenwidth()
    screenHeight = root.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    root.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')

    def leftToRight(padding, *params):
        for p in params: p.pack(side=LEFT, padx=padding)

    dbConfigButtonsFrame = Frame(root)
    openDBButton = Button(dbConfigButtonsFrame, text="Open DB", command=openDatabase)
    closeDBButton = Button(dbConfigButtonsFrame, text="Close DB", command=closeDatabase)

    leftToRight(20, openDBButton, closeDBButton)
    dbConfigButtonsFrame.pack(side=TOP, padx=20, pady=20)

    mainActionsFrame = Frame(root)
    manageUsersButton = Button(mainActionsFrame, text="Manage Users", command=showManageUsers)
    manageFilesButton = Button(mainActionsFrame, text="Manage Files", command=openFileManagementAction)
    leftToRight(30, manageUsersButton, manageFilesButton)

    closeDatabase()

    mainActionsFrame.pack(side=TOP, padx=20, pady=20)
    root.mainloop()

def kill(a, b):
    root.quit()
    root.update()

signal.signal(signal.SIGINT, kill)
main = Thread(target=main)
main.start()
main.join()
