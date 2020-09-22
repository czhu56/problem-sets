import csv
import sys
import sqlite3

def main():
    if len(sys.argv) != 2:
        sys.exit("Give me a house name!")

    house = sys.argv[1].lower()
    houses = ["slytherin", "gryffindor", "ravenclaw", "hufflepuff"]
    if not house in houses:
        sys.exit("That's not a valid house")

    db_filename = "students.db"

    connection = sqlite3.connect(db_filename)
    cursor = connection.cursor()

    cmd = 'SELECT first, middle, last, birth FROM students WHERE lower(house) = "{}" ORDER BY last, first;'.format(house)
    cursor.execute(cmd)

    roster = cursor.fetchall()

    for student in roster:
        out = student[0]
        if student[1]:
            out = out + " " + student[1]
        out = out + " " + student[2]
        out = out + ", born " + str(student[3])
        print(out)

if __name__ == "__main__":
    main()