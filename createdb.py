import csv
from paco import db
from paco import models

db.create_all()

# LOCKERS
file = open('data/CarrefourLocations.csv')
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

file.close()
