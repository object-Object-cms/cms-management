from tkinter import *
import json
import signal
import sqlite3
from tkinter import ttk
import tkinter.messagebox
from threading import Thread
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageTk, Image
from io import BytesIO
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
        c.execute("""
            create table if not exists articles (
                id text primary key,
                authorID integer,
                title text,
                description text,
                bannerimage text,
                category text,
                publishdate integer,
                content text
            )
        """)
        c.execute("""
            create table if not exists comments (
                id integer primary key,
                authorID integer,
                content text
            )
        """)
        c.execute("""
            create table if not exists specialpages (
                name text primary key,
                content text
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
        canvas.itemconfig(winid, width=event.width - 8)
        #frame.configure(width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)

def showAddFile(callback):
    fileToAdd = askopenfilename()
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Add File")
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
    mime = labelledInput("Mime Type")
    labelledInput("File", lambda e: Label(e, text=fileToAdd))

    def execute():
        mimeType = mime.get()
        
        with dbex() as cursor, open(fileToAdd, 'rb') as f:
            cursor.execute("insert into blobdata (type, content) values (?, ?)", (mimeType, f.read()))
        callback()
        subwin.destroy()
    Button(subwin, text="Add", command=execute).pack(side=TOP, pady=4)


def showManageFiles():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage Files")
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
        global _images
        _images = []
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []
        with dbq() as cursor:
            cursor.execute("select id, type, content from blobdata")
            Button(frame, text="Add", command=lambda: showAddFile(lambda: populate(frame)), width=50).grid(row=0, column=1, columnspan=2)
            i = 1
            for id_, type_, content in cursor.fetchall():
                l1 = Label(frame, text=f"{id_}", width=3, borderwidth="1",
                        relief="solid")
                l1.grid(row=i, column=0)
                l2 = Label(frame, text=f"{type_}")
                l2.grid(row=i, column=1)
                if type_.startswith("image/"):
                    try:
                        img = Image.open(BytesIO(content)).resize((250, 250), Image.LANCZOS)
                        _images.append(ImageTk.PhotoImage(img))
                        l3 = Label(frame, image = _images[-1])
                        l3.grid(row=i, column=2)
                    except Exception as e:
                        l3 = Label(frame, text="Cannot preview")
                        l3.grid(row=i, column=2)
                        print(e)
                else:
                    l3 = Label(frame, text="Cannot preview")
                    l3.grid(row=i, column=2)

                def downloadAction(_content):
                    out = asksaveasfilename()
                    with open(out, 'wb') as e:
                        e.write(_content)
                        tkinter.messagebox.showinfo(title = "Download", message = "File downloaded successfully")
                def _fabricate(_content):
                    return lambda: downloadAction(_content)

                b4 = Button(frame, text="Download", command=_fabricate(content))
                b4.grid(row=i, column=3)
                rowsLoaded.append(l1)
                rowsLoaded.append(l2)
                rowsLoaded.append(l3)
                rowsLoaded.append(b4)
                i += 1
            if i == 1:
                l1 = Label(frame, text="No files")
                l1.grid(row=1, column=1)
                rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        canvas.itemconfig(winid, width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)

def showAddLink(callback, idx):
    subwin = Toplevel(root)
    subwin.title(f"CMS - Admin Database Management - {'Edit' if idx != -1 else 'Add'} Link")
    appWidth = 200
    appHeight = 150

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)
    create = False
    with dbq() as cursor:
        cursor.execute("select content from specialpages where name = 'MENUBAR'")
        content = cursor.fetchone()
        if content is None:
            create = True
            content = []
        else:
            content = json.loads(content[0])

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    def labelledInput(name, initial = ""):
        lbFrame = Frame(subwin, height=5)
        i = Entry(lbFrame)
        i.insert(0, initial)
        Label(lbFrame, text=name).pack(side=LEFT)
        i.pack(side=RIGHT)
        lbFrame.pack(side=TOP, pady=4)
        return i
    name = labelledInput("Name", content[idx]['text'] if idx != -1 else 'Example')
    link = labelledInput("Page", content[idx]['url'] if idx != -1 else '/example')

    def execute():
        sName = name.get()
        sLink = link.get()
        obj = { "text": sName, "url": sLink }
        if idx != -1:
            content[idx] = obj
        else:
            content.append(obj)
        
        with dbex() as cursor:
            if create:
                cursor.execute("insert into specialpages (name, content) values ('MENUBAR', ?)", (json.dumps(content), ))
            else:
                cursor.execute("update specialpages set content = ? where name = 'MENUBAR'", (json.dumps(content), ))
        callback()
        subwin.destroy()
    Button(subwin, text='Edit' if idx != -1 else 'Add', command=execute).pack(side=TOP, pady=4)


def showManageLinks():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage Links")
    appWidth = 640
    appHeight = 480

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    subwin.columnconfigure(2, weight=1)
    rowsLoaded = []
    def populate(frame):
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []
        with dbq() as cursor:
            cursor.execute("select content from specialpages where name = 'MENUBAR'")
            Button(frame, text="Add", command=lambda: showAddLink(lambda: populate(frame), -1), width=20).grid(row=0, column=1, columnspan=2)
            i = 1
            content = cursor.fetchone()
            if content:
                content = json.loads(content[0])
                for index, value in enumerate(content):
                    l1 = Label(frame, text=f"{index}", width=3, borderwidth="1",
                            relief="solid")
                    l1.grid(row=i, column=0)
                    l2 = Label(frame, text=f"{value['text']}")
                    l2.grid(row=i, column=1)
                    l3 = Label(frame, text=f"{value['url']}")
                    l3.grid(row=i, column=2)
                    _fabricate = lambda e: lambda: showAddLink(lambda: populate(frame), e)
                    b4 = Button(frame, text="Edit", command=_fabricate(index))
                    b4.grid(row=i, column=3)
                    def _fabricate2(idx):
                        def _e():
                            del content[idx]
                            with dbex() as cursor:
                                cursor.execute("update specialpages set content = ? where name = 'MENUBAR'", (json.dumps(content), ))
                            populate(frame)
                        return _e
                                
                    b5 = Button(frame, text="Delete", command=_fabricate2(index))
                    b5.grid(row=i, column=4)
                    rowsLoaded.append(l1)
                    rowsLoaded.append(l2)
                    rowsLoaded.append(l3)
                    rowsLoaded.append(b4)
                    rowsLoaded.append(b5)
                    i += 1
            if i == 1:
                l1 = Label(frame, text="No content")
                l1.grid(row=1, column=1)
                rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        canvas.itemconfig(winid, width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)

def helperUpdateMainElement(element):
    with dbex() as cursor:
        cursor.execute("select content from specialpages where name = 'HOME'")
        content = cursor.fetchone()
        if not content: return
        content = json.loads(content[0])
        if not content['name'] == 'RootGrid':
            tkinter.messagebox.showwarning(title = "Error", message = "There's no main page. Please create it in the web UI")
            return
        for index, subProp in enumerate(content["props"]["subComponents"]):
            if subProp["id"] == element["id"]:
                content["props"]['subComponents'][index] = element
                break
        else:
            raise Exception("No elements altered")
        cursor.execute('update specialpages set content = ? where name = "HOME"', (json.dumps(content), ))
                

def helperGetMainElements(name):
    with dbq() as cursor:
        cursor.execute("select content from specialpages where name = 'HOME'")
        content = cursor.fetchone()
        if not content:
            return []
        content = json.loads(content[0])
        retList = []
        if not content['name'] == 'RootGrid':
            tkinter.messagebox.showwarning(title = "Error", message = "There's no main page. Please create it in the web UI")
            return
        for subProp in content["props"]["subComponents"]:
            if subProp["component"]["name"] == name:
                retList.append(subProp)
    return retList

def prop(e, n):
    return e["component"]["props"][n]

def showAddSlelement(callback, idx):
    subwin = Toplevel(root)
    subwin.title(f"CMS - Admin Database Management - {'Edit' if idx != -1 else 'Add'} Slider Element")
    appWidth = 200
    appHeight = 150

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    slider = helperGetMainElements("Slider")
    if not len(slider) > 0:
        tkinter.messagebox.showwarning(title = "Error", message = "There's no slider on the main page. Please add one from the web UI")
        return
    slider = slider[0]
    slides = prop(slider, "slides")

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    def labelledInput(name, initial = ""):
        lbFrame = Frame(subwin, height=5)
        i = Entry(lbFrame)
        i.insert(0, initial)
        Label(lbFrame, text=name).pack(side=LEFT)
        i.pack(side=RIGHT)
        lbFrame.pack(side=TOP, pady=4)
        return i
    name = labelledInput("Title", slides[idx]['title'] if idx != -1 else 'Title')
    desc = labelledInput("Sub Title", slides[idx]['description'] if idx != -1 else 'A more detailed title')
    image = labelledInput("Image URL", slides[idx]['image'] if idx != -1 else '$0')
    colorFr = Frame(subwin, height=5)
    Label(colorFr, text="Text Color").pack(side=LEFT)
    color = StringVar()
    if idx != -1: color.set(slides[idx]["textColor"])
    colorCb = ttk.Combobox(colorFr, textvariable=color)
    colorCb["values"] = ("black", "white")
    colorCb['state'] = 'readonly'
    colorCb.pack(side=RIGHT)
    colorFr.pack(side=TOP, pady=4)

    def execute():
        title = name.get()
        description = desc.get()
        imageURL = image.get()
        textColor = color.get()
        obj = { "title":  title, "description": description, "image": imageURL, "textColor": textColor }
        if idx != -1:
            slides[idx] = obj
        else:
            slides.append(obj)
        
        helperUpdateMainElement(slider)
        callback()
        subwin.destroy()
    Button(subwin, text='Edit' if idx != -1 else 'Add', command=execute).pack(side=TOP, pady=4)


def showManageSlider():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage Slider")
    appWidth = 640
    appHeight = 480

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    subwin.columnconfigure(2, weight=1)
    rowsLoaded = []
    def populate(frame):
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []

        slider = helperGetMainElements("Slider")
        if not len(slider) > 0:
            tkinter.messagebox.showwarning(title = "Error", message = "There's no slider on the main page. Please add one from the web UI")
            return
            
        slider = slider[0]
        slides = prop(slider, "slides")

        Button(frame, text="Add", command=lambda: showAddSlelement(lambda: populate(frame), -1), width=20).grid(row=0, column=1, columnspan=2)
        i = 1
        for index, value in enumerate(slides):
            l1 = Label(frame, text=f"{index}", width=3, borderwidth="1",
                    relief="solid")
            l1.grid(row=i, column=0)
            l2 = Label(frame, text=f"{value['title']}")
            l2.grid(row=i, column=1)
            l3 = Label(frame, text=f"{value['description']}")
            l3.grid(row=i, column=2)
            l4 = Label(frame, text=f"{value['image']}")
            l4.grid(row=i, column=3)
            l5 = Label(frame, text=f"{value['textColor']}")
            l5.grid(row=i, column=4)
            _fabricate = lambda e: lambda: showAddSlelement(lambda: populate(frame), e)
            b5 = Button(frame, text="Edit", command=_fabricate(index))
            b5.grid(row=i, column=5)
            def _fabricate2(idx):
                def _e():
                    del slides[idx]
                    helperUpdateMainElement(slider)
                    populate(frame)
                return _e
                        
            b6 = Button(frame, text="Delete", command=_fabricate2(index))
            b6.grid(row=i, column=6)
            rowsLoaded.append(l1)
            rowsLoaded.append(l2)
            rowsLoaded.append(l3)
            rowsLoaded.append(l4)
            rowsLoaded.append(l5)
            rowsLoaded.append(b5)
            rowsLoaded.append(b6)
            i += 1
        if i == 1:
            l1 = Label(frame, text="No content")
            l1.grid(row=1, column=1)
            rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        canvas.itemconfig(winid, width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)

def showAddNewsArticle(callback, idx):
    subwin = Toplevel(root)
    subwin.title(f"CMS - Admin Database Management - Edit News Reference")
    appWidth = 200
    appHeight = 150

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    boxes = helperGetMainElements("NewsBox")

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    def labelledInput(name, initial = ""):
        lbFrame = Frame(subwin, height=5)
        i = Entry(lbFrame)
        i.insert(0, initial)
        Label(lbFrame, text=name).pack(side=LEFT)
        i.pack(side=RIGHT)
        lbFrame.pack(side=TOP, pady=4)
        return i
    name = labelledInput("Title", prop(boxes[idx], 'title'))
    desc = labelledInput("Description", prop(boxes[idx], 'description'))
    link = labelledInput("Link URL", prop(boxes[idx], 'linkUrl'))
    linkText = labelledInput("Link Text", prop(boxes[idx], 'linkText'))

    def execute():
        title = name.get()
        description = desc.get()
        href = link.get()
        hrefText = linkText.get()
        obj = { "title":  title, "description": description, "linkUrl": href, "linkText": hrefText }
        boxes[idx]["component"]["props"] = obj
        
        helperUpdateMainElement(boxes[idx])
        callback()
        subwin.destroy()
    Button(subwin, text='Edit', command=execute).pack(side=TOP, pady=4)


def showManageNews():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage News")
    appWidth = 640
    appHeight = 480

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    subwin.columnconfigure(2, weight=1)
    rowsLoaded = []
    def populate(frame):
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []

        boxes = helperGetMainElements("NewsBox")

        i = 1
        for index, value in enumerate(boxes):
            l1 = Label(frame, text=f"{index}", width=3, borderwidth="1",
                    relief="solid")
            l1.grid(row=i, column=0)
            l2 = Label(frame, text=f"{prop(value, 'title')}")
            l2.grid(row=i, column=1)
            l3 = Label(frame, text=f"{prop(value, 'description')}")
            l3.grid(row=i, column=2)
            l4 = Label(frame, text=f"{prop(value, 'linkUrl')}")
            l4.grid(row=i, column=3)
            l5 = Label(frame, text=f"{prop(value, 'linkText')}")
            l5.grid(row=i, column=4)
            _fabricate = lambda e: lambda: showAddNewsArticle(lambda: populate(frame), e)
            b5 = Button(frame, text="Edit", command=_fabricate(index))
            b5.grid(row=i, column=5)
                        
            rowsLoaded.append(l1)
            rowsLoaded.append(l2)
            rowsLoaded.append(l3)
            rowsLoaded.append(l4)
            rowsLoaded.append(l5)
            rowsLoaded.append(b5)
            i += 1
        if i == 1:
            l1 = Label(frame, text="No content")
            l1.grid(row=1, column=1)
            rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        canvas.itemconfig(winid, width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
    vsb = Scrollbar(subwin, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    winid = canvas.create_window((4,4), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    frame.columnconfigure(1, weight=1)

    canvas.bind("<Configure>", canvas_resized)
    populate(frame)


def showAddFooterLink(callback, idx):
    subwin = Toplevel(root)
    subwin.title(f"CMS - Admin Database Management - {'Edit' if idx != -1 else 'Add'} Footer Link")
    appWidth = 200
    appHeight = 150

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    footer = helperGetMainElements("Footer")
    if not len(footer) > 0:
        tkinter.messagebox.showwarning(title = "Error", message = "There's no footer on the main page. Please add one from the web UI")
        return
    footer = footer[0]

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    def labelledInput(name, initial = ""):
        lbFrame = Frame(subwin, height=5)
        i = Entry(lbFrame)
        i.insert(0, initial)
        Label(lbFrame, text=name).pack(side=LEFT)
        i.pack(side=RIGHT)
        lbFrame.pack(side=TOP, pady=4)
        return i
    link = labelledInput("Link URL", prop(footer, 'links')[idx]['url'] if idx != -1 else 'https://example.com')
    linkText = labelledInput("Link Text", prop(footer, 'links')[idx]['text'] if idx != -1 else 'Link Text')

    def execute():
        href = link.get()
        hrefText = linkText.get()
        obj = { "url": href, "text": hrefText }
        if idx == -1:
            prop(footer, "links").append(obj)
        else:
            prop(footer, 'links')[idx] = obj
        
        helperUpdateMainElement(footer)
        callback()
        subwin.destroy()
    Button(subwin, text='Edit', command=execute).pack(side=TOP, pady=4)


def showManageFooter():
    subwin = Toplevel(root)
    subwin.title("CMS - Admin Database Management - Manage News")
    appWidth = 640
    appHeight = 480

    screenWidth = subwin.winfo_screenwidth()
    screenHeight = subwin.winfo_screenheight()

    x = (screenWidth / 2) - (appWidth / 2)
    y = (screenHeight / 2) - (appHeight / 2)

    subwin.geometry(f'{appWidth}x{appHeight}+{int(x)}+{int(y)}')
    subwin.columnconfigure(2, weight=1)
    rowsLoaded = []
    def populate(frame):
        nonlocal rowsLoaded
        if len(rowsLoaded) != 0:
            for e in rowsLoaded:
                e.grid_forget()
            rowsLoaded = []

        footer = helperGetMainElements("Footer")
        if not len(footer) > 0:
            tkinter.messagebox.showwarning(title = "Error", message = "There's no footer on the main page. Please add one from the web UI")
            return
        footer = footer[0]
        Button(frame, text="Add", command=lambda: showAddFooterLink(lambda: populate(frame), -1), width=20).grid(row=0, column=1, columnspan=2)
        lbFrame = Frame(frame, height=5)
        ent = Entry(lbFrame)
        ent.insert(0, prop(footer, "copyrightText"))
        Label(lbFrame, text="Copyright Text").pack(side=LEFT)
        ent.pack(side=LEFT)
        def updateCopyright():
            footer["component"]["props"]["copyrightText"] = ent.get()
            helperUpdateMainElement(footer)
            populate(frame)
        Button(lbFrame, text="Save", command=updateCopyright).pack(side=LEFT)
        lbFrame.grid(row=1, column=1, columnspan=2)

        i = 2
        for index, value in enumerate(prop(footer, "links")):
            l1 = Label(frame, text=f"{index}", width=3, borderwidth="1",
                    relief="solid")
            l1.grid(row=i, column=0)
            l2 = Label(frame, text=f"{value['url']}")
            l2.grid(row=i, column=1)
            l3 = Label(frame, text=f"{value['text']}")
            l3.grid(row=i, column=2)
            _fabricate = lambda e: lambda: showAddFooterLink(lambda: populate(frame), e)
            b5 = Button(frame, text="Edit", command=_fabricate(index))
            b5.grid(row=i, column=5)
            def _fabricate2(idx):
                def _e():
                    del prop(footer, "links")[idx]
                    helperUpdateMainElement(footer)
                    populate(frame)
                return _e
                        
            b6 = Button(frame, text="Delete", command=_fabricate2(index))
            b6.grid(row=i, column=6)

            rowsLoaded.append(l1)
            rowsLoaded.append(l2)
            rowsLoaded.append(l3)
            rowsLoaded.append(b5)
            rowsLoaded.append(b6)
            i += 1
        if i == 2:
            l1 = Label(frame, text="No content")
            l1.grid(row=1, column=1)
            rowsLoaded.append(l1)

    def onFrameConfigure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resized(event):
        canvas.itemconfig(winid, width=event.width - 8)

    canvas = Canvas(subwin, borderwidth=0)
    frame = Frame(canvas)
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

    root = Tk()
    root.title("CMS - Admin Database Management")

    # centrowanie okna na ekranie
    appWidth = 800
    appHeight = 150

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

    leftToRight(5, 
        Button(mainActionsFrame, text="Manage Users", command=showManageUsers),
        Button(mainActionsFrame, text="Manage Files", command=showManageFiles),
        Button(mainActionsFrame, text="Manage Links", command=showManageLinks),
        Button(mainActionsFrame, text="Manage Slider", command=showManageSlider),
        Button(mainActionsFrame, text="Manage News", command=showManageNews),
        Button(mainActionsFrame, text="Manage Footer", command=showManageFooter),
    )

    closeDatabase()

    mainActionsFrame.pack(side=TOP, padx=20, pady=20)
    root.mainloop()

if __name__ == "__main__": main()