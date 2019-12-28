import os
# very simple mutex implementation using atomic file operations
# does not keep track of owner of the mutex only if it is locked or not
class FileLock:
    def lock(self, name):
        try:
            os.open(name+'.lock', os.O_CREAT | os.O_EXCL)
            return True
        except FileExistsError:
            return False
    def unlock(self, name):
        os.remove(name+'.lock')
