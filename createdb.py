import csv
import os

from loadenv import load_env

load_env()

from paco import db
from paco import models



db.create_all()

# LOCKERS
file = open('data/CarrefourLocations.csv', encoding="utf-8")
csvreader = csv.reader(file)

header = next(csvreader)

for row in csvreader:
    locker = models.Locker(name=row[1],
                           address=row[2],
                           zip_code=row[3],
                           town=row[4],
                           province=row[5],
                           region=row[6],
                           latitude=float(row[7]),
                           longitude=float(row[8]))
    db.session.add(locker)
    db.session.commit()
    # Standard Locker 20 small 10 medium 3 large
    for i in range(1, 21):
        locker_space = models.LockerSpace(id=i,
                                          locker_id=locker.id,
                                          dimension=1)
        db.session.add(locker_space)

    for i in range(21, 31):
        locker_space = models.LockerSpace(id=i,
                                          locker_id=locker.id,
                                          dimension=2)
        db.session.add(locker_space)

    for i in range(31, 34):
        locker_space = models.LockerSpace(id=i,
                                          locker_id=locker.id,
                                          dimension=3)
        db.session.add(locker_space)
db.session.commit()

file.close()
