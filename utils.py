def state(object, new, iter = False):
    if iter:
        for sub in object.winfo_children():
            state(sub, new)
    else:
        object['state'] = new

class CursorClosable:
    def __init__(self, connection, doCommit):
        self.cursor = connection.cursor()
        self.connection = connection if doCommit else None
    def __enter__(self):
        return self.cursor
    def __exit__(self, type, value, traceback):
        self.cursor.close()
        if self.connection: self.connection.commit()
