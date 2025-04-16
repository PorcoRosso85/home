/*
* Copyright 2022, The Cozo Project Authors.
*
* This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
* If a copy of the MPL was not distributed with this file,
* You can obtain one at https://mozilla.org/MPL/2.0/.
 */

package main

import (
	"reflect"
	"testing"

	"github.com/cozodb/cozo-lib-go"
)

func TestDb(t *testing.T) {
	db, err := cozo.New("mem", "", map[string]interface{}{
		// "mutable": true,
		"immutable": false,
	})
	if err != nil {
		t.Fatal(err)
	}

	_, err = db.Run(":create s {a, b, c}", nil)
	if err != nil {
		t.Fatal(err)
	}

	// データ挿入クエリを分離
	_, err = db.Run("?[a, b, c] <- [[1, 2, 3]] :put s {a, b, c}", nil)
	if err != nil {
		t.Fatal(err)
	}

	{
		res, err := db.Run("?[a,b,c] := *s[a,b,c]", nil)
		if err != nil {
			t.Fatal(err)
		}

		if len(res.Rows) != 1 || len(res.Rows[0]) != 3 {
			t.Error("初期状態の関係チェックで行数が不正")
		}

		expected := []interface{}{int64(1), int64(2), int64(3)}
		if !reflect.DeepEqual(res.Rows[0], expected) {
			t.Errorf("期待値 %v に対して実際の値 %v", expected, res.Rows[0])
		}
	}
	// db, err := cozo.New("mem", "", nil)
	// if err != nil {
	// 	t.Error(err)
	// }
	// // 関係 's' を作成し、データを挿入します。
	// _, _ = db.Run("?[a,b,c] <- [[1,2,3]] :create s{a, b, c}", nil)
	// {
	// 	// 関係 's' が存在し、正しいデータを持っているか確認します。
	// 	res, _ := db.Run("?[a,b,c] := *s[a,b,c]", nil)
	// 	if len(res.Rows) != 1 || len(res.Rows[0]) != 3 {
	// 		t.Error("初期状態の関係チェックで行数が不正")
	// 	}
	// }

	{
		_, err := db.Run("?[x] <- [[1,2,3]]", nil)
		if err == nil {
			t.Error("不正なクエリでエラーが発生するはずが、しなかった")
		}
	}

	{
		// データベースを 'test.db' にバックアップし、新しい db2 に復元します。
		// 関係 's' がデータとともに正しく復元されているか確認します。
		_ = db.Backup("test.db")

		db2, _ := cozo.New("mem", "", nil)
		_ = db2.Restore("test.db")

		res, err := db2.Run("?[a,b,c] := *s[a,b,c]", nil)
		if err != nil {
			t.Error(err)
		}
		if len(res.Rows) != 1 || len(res.Rows[0]) != 3 {
			t.Error("バックアップと復元後の行数が不正")
		}
	}

	{
		// 関係 's' をエクスポートし、新しい db3 にインポートします。
		// データが正しくインポートされているか確認します。
		data, err := db.ExportRelations([]string{"s"})
		if err != nil {
			t.Error(err)
		}
		db3, _ := cozo.New("mem", "", nil)
		_, _ = db3.Run(":create s {a, b, c}", nil)

		res, err := db3.Run("?[a,b,c] := *s[a,b,c]", nil)
		if err != nil {
			t.Error(err)
		}
		if len(res.Rows) != 0 {
			t.Error("インポート前の行数が不正")
		}
		_ = db3.ImportRelations(data)

		res, err = db3.Run("?[a,b,c] := *s[a,b,c]", nil)
		if err != nil {
			t.Error(err)
		}

		if len(res.Rows) != 1 || len(res.Rows[0]) != 3 {
			t.Error("インポート後の行数が不正")
		}

		db4, _ := cozo.New("mem", "", nil)
		_, _ = db4.Run(":create s {a, b, c}", nil)

		// バックアップ 'test.db' から関係 's' を新しい db4 にインポートします。
		// バックアップからデータが正しくインポートされているか確認します (ImportRelationsFromBackup).
		res, err = db4.Run("?[a,b,c] := *s[a,b,c]", nil)
		if err != nil {
			t.Error(err)
		}
		if len(res.Rows) != 0 {
			t.Error("インポート前の行数が不正")
		}
		_ = db4.ImportRelationsFromBackup("test.db", []string{"s"})

		res, err = db4.Run("?[a,b,c] := *s[a,b,c]", nil) // ImportRelationsFromBackup 後のデータチェック
		if err != nil {
			t.Error(err)
		}

		if len(res.Rows) != 1 || len(res.Rows[0]) != 3 {
			t.Error("行数が不正")
		}
	}

	db.Close()
}
