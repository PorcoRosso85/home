// map関数のパラメータの挿入
INSERT INTO Parameter (name, type, description, required, immutable)
VALUES ("array", "array", "変換する配列", TRUE, TRUE);

INSERT INTO Parameter (name, type, description, required, immutable)
VALUES ("callback", "function", "各要素に適用する関数", TRUE, TRUE);