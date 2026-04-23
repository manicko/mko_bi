# регистр логик обработки
# registry.py
PROCESSORS = {}


def register(name: str):
    def wrapper(cls):
        PROCESSORS[name] = cls
        return cls

    return wrapper
