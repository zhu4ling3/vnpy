import logging


def retry_connect(cls):
    class Wrapper:
        def __init__(self, *args):
            self.__wrapper = cls(*args)

        def __getattr__(self, item):
            def wrapper(*args, **kwargs):
                try:
                    return getattr(self.__wrapper, item)(*args, **kwargs)
                except Exception as e:
                    logging.exception(e)
                    raise e

            return wrapper

    return Wrapper



def logging_level(func=None, level=logging.INFO):
    def decor(cls):
        class Wrapper:
            def __init__(self, *args):
                self.__level = level
                self.__wrapper = cls(*args)

                hdlr = None
                for h in logging.root.handlers:
                    if isinstance(h, logging.NullHandler) or self.__level < h.level:
                        continue
                    else:
                        hdlr = h
                        self.__handler = h
                        break
                if not hdlr:
                    hdlr = logging.StreamHandler()
                    hdlr.setLevel(self.__level)
                    self.__handler = hdlr


            def __getattr__(self, item):
                def wrapper(*args, **kwargs):
                    old = logging.root.level
                    logging.root.setLevel(self.__level)
                    logging.root.addHandler(self.__handler)
                    o = getattr(self.__wrapper, item)(*args, **kwargs)
                    logging.root.removeHandler(self.__handler)
                    logging.root.setLevel(old)
                    return o

                return wrapper

            # def __getattribute__(self, item):
            #
            #     def wrapper(*args, **kwargs):
            #         old = logging.root.level
            #         logging.root.setLevel(super(Wrapper, self).__getattribute__('level'))
            #         o = getattr(super(Wrapper, self).__getattribute__('wrapper'), item)(*args, **kwargs)
            #         logging.root.setLevel(old)
            #         return o
            #
            #     return wrapper

        return Wrapper

    if func:
        return decor(func)

    return decor