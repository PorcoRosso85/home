// map関数と戻り値型の関連付け
INSERT INTO ReturnsType
SELECT f.id, r.id
FROM Function f, ReturnType r
WHERE f.title = "map" AND r.type = "array";