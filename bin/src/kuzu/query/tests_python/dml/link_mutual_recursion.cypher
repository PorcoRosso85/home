// 相互再帰関係の設定
INSERT INTO MutuallyRecursiveWith
SELECT f1.id, f2.id
FROM Function f1, Function f2
WHERE f1.title = "isEven" AND f2.title = "isOdd";

INSERT INTO MutuallyRecursiveWith
SELECT f1.id, f2.id
FROM Function f1, Function f2
WHERE f1.title = "isOdd" AND f2.title = "isEven";