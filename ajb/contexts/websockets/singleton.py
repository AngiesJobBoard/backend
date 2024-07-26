import threading


class Singleton:
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
                instance._initialize(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

    def _initialize(self, *args, **kwargs):
        pass