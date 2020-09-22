import csv
import sys
import sqlite3

def main():
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".csv"):
        sys.exit("Excpected a csv file as an argument")

    csv_filename = sys.argv[1]
    db_filename = "students.db"

    connection = sqlite3.connect(db_filename)
    cursor = connection.cursor()

    csv_file = open(csv_filename, "r")
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        name = row['name']
        house = row['house']
        birth = row['birth']

        names = name.split(" ")
        if (len(names)) == 2:
            first = names[0]
            last = names[1]

            cmd = "INSERT INTO students (first, middle, last, house, birth) VALUES('{}', NULL, '{}', '{}', '{}')".format(first, last, house, birth)
            cursor.execute(cmd)
        else:
            first = names[0]
            middle = names[1]
            last = names[2]
            cmd = "INSERT INTO students (first, middle, last, house, birth) VALUES('{}', '{}', '{}', '{}', '{}')".format(first, middle, last, house, birth)
            cursor.execute(cmd)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    main()