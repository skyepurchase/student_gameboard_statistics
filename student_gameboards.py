from typing import Dict, Union
from pprint import pprint
import psycopg2
import os

CONN = psycopg2.connect(dbname='rutherford',
                        user=os.environ.get("DB_USER"),
                        host='localhost',
                        port=65433,
                        password=os.environ.get("DB_PASS"))
CUR = CONN.cursor()


def getPercentageOfStudentGameboards(start_date: str = "2023-09-01", end_date: str = "2023-10-01"):
    CUR.execute("""
    WITH student_gameboard_pages AS (
        SELECT gameboards.id AS gameboard_id, owner_user_id AS student_id, contents_json->>'id' AS page_id, idx AS gameboard_question_index
        FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)
        WHERE creation_date >= %s::date
            AND creation_date < %s::date
            AND owner_user_id IN (
                SELECT DISTINCT user_id
                FROM question_attempts
                JOIN users ON users.id=question_attempts.user_id
                WHERE timestamp >= %s::date
                    AND timestamp < %s::date
                    AND role = 'STUDENT')),

    student_gameboard_parts AS (
        SELECT student_id, gameboard_id, question_id
        FROM student_gameboard_pages
        JOIN content_data ON student_gameboard_pages.page_id=content_data.page_id
            AND type<>'quick'),

    percentage_correct_gameboards AS (
        SELECT student_id, gameboard_id, 
            SUM(CASE WHEN correct THEN 1 ELSE 0 END) / COUNT(student_gameboard_parts.question_id) AS percentage
        FROM student_gameboard_parts
        JOIN question_attempts ON student_gameboard_parts.question_id=question_attempts.question_id
            AND student_gameboard_parts.student_id=question_attempts.user_id
        GROUP BY student_id, gameboard_id)

    SELECT average_percentage, COUNT(DISTINCT student_id) 
    FROM (
        SELECT student_id, AVG(percentage::float) * 100 as average_percentage
        FROM percentage_correct_gameboards
        GROUP BY student_id) as average_student_percentage
    GROUP BY average_percentage
    """, (start_date, end_date, start_date, end_date))

    res = CUR.fetchall()
    res_map = {}
    if res:
        for k, v in res:
            res_map[k] = v
    return res_map


def getPartsOfStudentWithSomeGameboards(start_date: str = "2023-09-01", end_date: str = "2023-10-01") -> Dict:
    CUR.execute("""
    WITH student_gameboard_pages AS (
        SELECT gameboards.id AS gameboard_id, owner_user_id AS student_id, contents_json->>'id' AS page_id, idx AS gameboard_question_index
        FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)
        WHERE creation_date >= %s::date
            AND creation_date < %s::date
            AND owner_user_id IN (
                SELECT DISTINCT user_id
                FROM question_attempts
                JOIN users ON users.id=question_attempts.user_id
                WHERE timestamp >= %s::date
                    AND timestamp < %s::date
                    AND role = 'STUDENT')),

    student_gameboard_parts AS (
        SELECT student_id, gameboard_id, question_id
        FROM student_gameboard_pages
        JOIN content_data ON student_gameboard_pages.page_id=content_data.page_id
            AND type<>'quick'),

    correct_gameboard_parts AS (
        SELECT student_id, gameboard_id, SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS num_correct,
            COUNT(student_gameboard_parts.question_id) AS total
        FROM student_gameboard_parts
        JOIN question_attempts ON student_gameboard_parts.question_id=question_attempts.question_id
            AND student_gameboard_parts.student_id=question_attempts.user_id
        GROUP BY student_id, gameboard_id)

    SELECT num_gameboards, COUNT(student_id)
    FROM (
        SELECT student_id, COUNT(gameboard_id) AS num_gameboards
        FROM correct_gameboard_parts
        WHERE num_correct = total
        GROUP BY student_id) AS num_correct_gameboards
    GROUP BY num_gameboards
    """, (start_date, end_date, start_date, end_date))

    res = CUR.fetchall()
    res_map = {}
    if res:
        for k, v in res:
            res_map[k] = v
    return res_map


def getPartsOfStudentGameboards(start_date: str = "2023-09-01", end_date: str = "2023-10-01") -> Union[int, None]:
    CUR.execute("""
    WITH student_gameboard_pages AS (
        SELECT gameboards.id AS gameboard_id, owner_user_id AS student_id, contents_json->>'id' AS page_id, idx AS gameboard_question_index
        FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)
        WHERE creation_date >= %s::date
            AND creation_date < %s::date
            AND owner_user_id IN (
                SELECT DISTINCT user_id
                FROM question_attempts
                JOIN users ON users.id=question_attempts.user_id
                WHERE timestamp >= %s::date
                    AND timestamp < %s::date
                    AND role = 'STUDENT')),

    student_gameboard_parts AS (
        SELECT student_id, gameboard_id, question_id
        FROM student_gameboard_pages
        JOIN content_data ON student_gameboard_pages.page_id=content_data.page_id
            AND type<>'quick')

    SELECT COUNT(DISTINCT student_id)
    FROM (
        SELECT student_id, gameboard_id, SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS num_correct,
            COUNT(student_gameboard_parts.question_id) AS total
        FROM student_gameboard_parts
        JOIN question_attempts ON student_gameboard_parts.question_id=question_attempts.question_id
            AND student_gameboard_parts.student_id=question_attempts.user_id
        GROUP BY student_id, gameboard_id) AS correct_gameboard_parts
    WHERE num_correct = total
    """, (start_date, end_date, start_date, end_date))

    res = CUR.fetchone()
    if res:
        return res[0]
    else:
        return None


def getNumStudentsWithSomeGameboards(start_date: str = "2023-09-01", end_date: str = "2023-10-01") -> Dict:
    CUR.execute("""
    WITH users_and_gameboards AS (
        SELECT owner_user_id, count(gameboards.id) as num_gameboards
        FROM gameboards
        WHERE creation_date >= %s::date
            AND creation_date < %s::date
            AND owner_user_id IN (
                SELECT DISTINCT user_id
                FROM question_attempts
                JOIN users ON users.id=question_attempts.user_id
                WHERE timestamp >= %s::date
                    AND timestamp < %s::date
                    AND role = 'STUDENT')
        GROUP BY owner_user_id)

    SELECT num_gameboards, COUNT(owner_user_id)
    FROM users_and_gameboards
    WHERE num_gameboards > 0
    GROUP BY num_gameboards;
    """, (start_date, end_date, start_date, end_date))

    res = CUR.fetchall()
    res_map = {}
    if res:
        for k, v in res:
            res_map[k] = v
    return res_map


def getNumStudentsWithGameboards(start_date: str = "2023-09-01", end_date: str = "2023-10-01") -> Union[int, None]:
    CUR.execute("""
    WITH valid_question_attempts AS (
        SELECT user_id
        FROM question_attempts
        WHERE timestamp >= %s::date
            AND timestamp < %s::date
        GROUP BY user_id),
    active_students AS (
        SELECT users.id as id
        FROM users
        JOIN valid_question_attempts ON users.id=valid_question_attempts.user_id
        WHERE role = 'STUDENT'
        GROUP BY users.id),
    users_and_gameboards AS (
        SELECT active_students.id, count(gameboards.id) as num_gameboards
        FROM active_students
        LEFT JOIN gameboards ON active_students.id=gameboards.owner_user_id
        WHERE creation_date >= %s::date
            AND creation_date < %s::date
        GROUP BY active_students.id)
    SELECT count(*)
    FROM users_and_gameboards
    WHERE num_gameboards > 0;
    """, (start_date, end_date, start_date, end_date))

    res = CUR.fetchone()
    if res:
        return res[0]
    else:
        return None


def getNumStudents(start_date: str = "2023-09-01", end_date: str = "2023-10-01") -> Union[int, None]:
    CUR.execute("""
    WITH active_students AS (
        SELECT users.id
        FROM users
        JOIN question_attempts ON users.id=question_attempts.user_id
        WHERE timestamp >= %s::date
            AND timestamp < %s::date
            AND role = 'STUDENT'
        GROUP BY users.id)
    SELECT count(*)
    FROM active_students;
    """, (start_date, end_date))

    res = CUR.fetchone()
    if res:
        return res[0]
    else:
        return None

if __name__=='__main__':
    date_ranges = [
#        ("Last Year", "2022-12-19", "2023-12-19"),
        ("Last Academic Year", "2022-09-01", "2023-09-01"),
        ("Last two years", "2021-12-19", "2023-12-19"),
        ("Last two academic years", "2021-09-01", "2023-09-01"),
        ("All Time", "2000-01-01", "2023-12-30"),
    ]
    for name, start, end in date_ranges:
        filename = name.replace(" ", "-").lower()

        print(name)
        print("---")
        num_students = getNumStudents(start, end)
        print(f"{num_students} active students.")
        student_gameboards = getNumStudentsWithGameboards(start, end)
        print(f"{student_gameboards} students with self-made gameboards.")
        complete_gameboards = getPartsOfStudentGameboards(start, end)
        print(f"{complete_gameboards} students complete some gameboards.")
        data = getPercentageOfStudentGameboards(start, end)

        if num_students is None or student_gameboards is None or complete_gameboards is None:
            print("Error! One of the queries failed!")
        continue

        gameboard_count = getNumStudentsWithSomeGameboards(start,end)
        if gameboard_count is not None:
            with open("physics/gameboard_count/" + filename + ".csv", "w") as out:
                out.write("gameboards,count\n")
                additional = 0
                for k, v in gameboard_count.items():
                    if k > 4:
                        additional += v
                    else:
                        out.write(f"{k},{v}\n")
                out.write(f"5+,{additional}")

        gameboard_completion = getPartsOfStudentWithSomeGameboards(start,end)
        if gameboard_completion is not None:
            with open("physics/gameboard_completion/" + filename + ".csv", "w") as out:
                out.write("gameboards,count\n")
                for k, v in gameboard_completion.items():
                    out.write(f"{k},{v}\n")
        quit()

        if data is not None:
            no_attempt = data[0] if 0 in data else 0
            complete = data[100] if 100 in data else 0
            print(f"{no_attempt} made no attempt")
            print(f"{complete} completed all gameboards\n\n")

            with open("physics/count/" + filename + ".csv", "w") as out:
                out.write("range,count\n")
                out.write(f"No Gameboard,{num_students-student_gameboards}\n")
                out.write(f"No Attempt,{student_gameboards-complete_gameboards}\n")
                out.write(f"Complete Some,{complete_gameboards-complete}")
                out.write(f"Complete All,{complete}")

            with open("ada/percentage/" + filename + ".csv", "w") as out:
                out.write("percentage,count\n")
                for k, v in data.items():
                    out.write(f"{k},{v}\n")

