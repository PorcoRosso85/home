-- サンプル分析クエリ
-- SQLiteのテーブルに対してKuzuDBで実行するCypherクエリの例

-- 全学生の一覧
LOAD FROM db.person 
RETURN * 
ORDER BY age DESC;

-- 年齢が25歳以上の学生
LOAD FROM db.person 
WHERE age >= 25 
RETURN name, age;

-- コースと受講者数の集計
LOAD FROM db.enrollment e
JOIN db.course c ON e.course_id = c.id
RETURN c.name AS course, COUNT(*) AS students
GROUP BY c.name
ORDER BY students DESC;

-- 成績Aを取った学生とコース
LOAD FROM db.enrollment e
JOIN db.person p ON e.student_name = p.name
JOIN db.course c ON e.course_id = c.id
WHERE e.grade = 'A'
RETURN p.name AS student, c.name AS course, p.age
ORDER BY p.name;

-- 学生ごとの受講コース数と平均年齢
LOAD FROM db.enrollment e
JOIN db.person p ON e.student_name = p.name
RETURN p.name AS student, COUNT(*) AS courses, p.age
GROUP BY p.name, p.age
ORDER BY courses DESC;