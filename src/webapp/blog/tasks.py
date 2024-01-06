from .. import celery


@celery.task()
def log(msg):
    return msg


@celery.task()
def multiply(x, y):
    return x * y


@celery.task()
def substract(x, y):
    return x - y

