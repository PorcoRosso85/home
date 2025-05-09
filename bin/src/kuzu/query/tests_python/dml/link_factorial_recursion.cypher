// factorial関数と再帰情報の関連付け
INSERT INTO HasRecursionInfo
SELECT f.id, r.id
FROM Function f, RecursionInfo r
WHERE f.title = "factorial" AND r.isRecursive = TRUE;