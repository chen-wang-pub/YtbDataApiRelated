from celery_tutorial import add
if __name__ == '__main__':
    import time
    result = add.delay(4, 4)

    while not result.ready():
        time.sleep(2)
        print('waiting')
    print(result.get(timeout=1))