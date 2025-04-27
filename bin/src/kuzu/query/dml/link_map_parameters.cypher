// map関数とパラメータの関連付け
INSERT INTO HasParameter
SELECT f.id, p.id, TRUE
FROM Function f, Parameter p
WHERE f.title = "map" AND p.name = "array";

INSERT INTO HasParameter
SELECT f.id, p.id, TRUE
FROM Function f, Parameter p
WHERE f.title = "map" AND p.name = "callback";