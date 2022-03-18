from datetime import datetime
import time

a = datetime.utcnow
time.sleep(1)
b = datetime.utcnow

a = datetime.utcnow()
a = datetime.fromisoformat(a.isoformat())
time.sleep(1)
b = datetime.utcnow()
b = datetime.fromisoformat(b.isoformat())

print((b-a).total_seconds())


'''
first_time = datetime.now()
time.sleep(1)
later_time = datetime.now()
difference = later_time - first_time
'''