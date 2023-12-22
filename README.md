# Statistics on Student Gameboard Usage

## Exploration

First exploration was getting 10 students registered after the september intake this year,

```
SELECT given_name
FROM users
WHERE registration_date >= '2023-09-01'::date
    AND role = 'STUDENT'
```

and the number of students in this period: 66935.

```
SELECT count(*)
FROM users
WHERE registration_date >= '2023-09-01'::date
    AND role = 'STUDENT'
```

Then finding gameboards that were created by these students,

```
SELECT title, given_name
FROM users
JOIN gameboards ON users.id=gameboards.owner_user_id
WHERE registration_date >= '2023-09-01'::date
    AND role = 'STUDENT'
```

and the number of gameboards that were created as such: 13093.

```
SELECT count(*)
FROM users
JOIN gameboards ON users.id=gameboards.owner_user_id
WHERE registration_date >= '2023-09-01'::date
    AND role = 'STUDENT'
```

Then a look at gameboard parts so that later can see how many parts are fully complete or what portion of parts are
completed.

```
WITH gameboard_pages AS (
        SELECT id AS gameboard_id, contents_json->>'id' AS page_id, idx AS gameboard_question_index
        FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)),
    gameboard_parts AS (
        SELECT gameboard_id, gameboard_question_index, content_data.*
        FROM gameboard_pages
        JOIN content_data ON gameboard_pages.page_id=content_data.page_id
            AND type<>'quick')
SELECT gameboards.title, gameboard_question_index, given_name
FROM users
JOIN gameboards ON users.id=gameboards.owner_user_id
JOIN gameboard_parts ON gameboard_pats.gameboard_id=gameboards.id
WHERE registration_date >= '2023-09-01'::date
    AND role = 'STUDENT'
ORDER BY gameboard_id, gameboard_question_index
```

## How many students have self-made gameboards

A left join of `STUDENT` users with the gameboards on `owner_user_id` give a table with nullable gameboard entries for
those students that did not create a gameboard.
grouping by the students and counting the created gameboards means students who didn't create gameboards have a 0.

We only want to consider students that were active in the period, as it is unfair to consider students that would never
have interacted with the site anyway.

### Setup

First sanity check that the number of active students, looking at the month of September.

```
WITH active_students AS (
    SELECT users.id
    FROM users
    JOIN question_attempts ON users.id=question_attempts.user_id
    WHERE timestamp >= '2023-09-01'::date
        AND timestamp >= '2023-09-01'::date
        AND role = 'STUDENT'
    GROUP BY users.id)
SELECT count(*)
FROM active_students;
```

In September: 57932 active users.

The number of active students that created a gameboard in September was 2638.

```
WITH active_students AS (
    SELECT users.id as id
    FROM users
    JOIN question_attempts ON users.id=question_attempts.user_id
    WHERE timestamp >= '2023-09-01'::date
        AND timestamp >= '2023-09-01'::date
        AND role = 'STUDENT'
    GROUP BY users.id),
users_and_gameboards AS (
    SELECT active_students.id, count(gameboards.id) as num_gameboards
    FROM active_students
    LEFT JOIN gameboards ON active_students.id=gameboards.owner_user_id
    WHERE creation_date >= '2023-09-01'::date
        AND creation_date < '2023-10-01'::date
    GROUP BY active_students.id)
SELECT count(*)
FROM users_and_gameboards
WHERE num_gameboards > 0
```

This means that in September only 4.6% of the active students created at least one gameboard.

#### Optimisation

The above method

Create a `valid_question_attempt` table that is used in the `JOIN` rather than the full `question_attempts` table then
removing rows.

### Statistics

The following results where obtained:

```
PHYSICS
Range                   Total   With Gameboard  Percentage 
All time                475039  94334           19.9
Last year               139992  14897           10.6
Last academic year      114058  12829           11.2
Last two years          207110  23848           11.5
Last two academic years 177250  20785           11.7

ADA
Range                   Total   With Gameboard  Percentage
Last year               4356    656             15.1
```

## How many students have completed self-made gameboards

We can get the individual parts for all the gameboards, 

```
WITH gameboard_pages AS (
    SELECT gameboards.id AS gameboard_id, contents_json->>'id' AS page_id, idx AS gameboard_question_index
    FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)),

gameboard_parts AS (
    SELECT gameboard_id, question_id
    FROM gameboard_pages
    JOIN content_data ON gameboard_pages.page_id=content_data.page_id))

SELECT *
FROM gameboard_parts
ORDER BY gameboard_id, question_id
```

But this includes all non-active and non-student gameboards.
Instead a `WHERE` clause is added to make sure that the `owner_user_id`s are active students is added.

```
student_gameboard_pages AS (
    SELECT gameboards.id AS gameboard_id, owner_user_id AS student_id, contents_json->>'id' AS page_id, idx AS
    gameboard_question_index
    FROM gameboards, UNNEST(contents) WITH ORDINALITY AS subtable(contents_json, idx)
    WHERE creation_date >= %s::date
        AND creation_date < %s::date
        AND owner_user_id IN (
            SELECT DISTINCT user_id
            FROM question_attempts
            JOIN users ON users.id=question_attempts.user_id
            WHERE timestamp >= %s::date
                AND timestamp < %s::date
                AND role = 'STUDENT'))
```

The `gameboard_parts` is altered to `student_gameboard_parts` to include `student_id`.
Using this a query to find the number of students that completed at least one gameboard is:

```
SELECT COUNT(DISTINCT student_id)
FROM (
    SELECT student_id, gameboard_id, SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS num_parts_correct,
        COUNT(student_gameboard_parts.question_id) AS total_parts
    FROM student_gameboard_parts
    JOIN question_attempts ON student_gameboard_parts.question_id=question_attempts.question_id
        AND student_gameboard_parts.student_id=question_attempts.user_id
    GROUP BY student_id, gameboard_id) AS correct_gameboard_parts
WHERE num_parts_correct = total_parts
```

### Statistics

```
PHYSICS
Range                   Total   With Gameboard  Percentage Complete Percentage  All     Percentage
September                57932   2638            4.6       532      20.2
All time                475039  94334           19.9       19350    20.5        5177    5.5
Last year               139992  14897           10.6       3400     22.8        846     5.7
Last academic year      114058  12829           11.2       2954     23.0        707     5.5
Last two years          207110  23848           11.5       5612     23.5        1340    5.6
Last two academic years 177250  20785           11.7       4873     23.4        1171    5.6

ADA
Range                   Total   With Gameboard  Percentage Complete Percentage  All     Percentage
Last year               4356    656             15.1       129      19.7        50      7.6
```

These statistics are presented in the pie charts

## Average percentage completion of student created gameboard

Using the same setup as before but bringing out inner table to find the percentage completion for each `student,
gameboard` pair.

```
percentage_correct_gameboard AS (
    SELECT student_id, gameboard_id,
        SUM(CASE WHEN correct THEN 1 ELSE 0 END) / COUNT(student_gameboard_parts.question_id) AS percentage
    FROM student_gameboard_parts
    JOIN question_attempts ON student_gameboard_parts.question_id=question_attempts.question_id
        AND student_gameboard_parts.student_id=question_attempts.user_id
    GROUP BY student_id, gameboard_id)
```

Using this we can extract the average gamebaord completion by student.

```
(SELECT student_id, AVG(percentage::float) * 100 AS average_percentage
FROM percentage_correct_gameboard
GROUP BY student_id) AS average_student_percentage
```

Finally can count the number of students thats at each percentage completed

```
SELECT average_percentage, COUNT(DISTINCT student_id)
FROM average_student_percentage
GROUP BY average_percentage
```

The results of these are presented in the scatter plots.
