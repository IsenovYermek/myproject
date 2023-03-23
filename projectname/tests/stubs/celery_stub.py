class Celery:
    def task(self, *args, **kwargs):
        def wrapper(func):
            def inner(*args, **kwargs):
                return func(*args, **kwargs)
            return inner
        return wrapper

app = Celery()