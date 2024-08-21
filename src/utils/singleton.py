from typing import Dict, Type


class Singleton(type):
    __instances: Dict[Type, Type] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]
