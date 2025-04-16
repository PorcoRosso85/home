package main

import "github.com/cozodb/cozo-lib-go" // Import the cozo library
func main() {
	// 1. Import the cozo library (already imported).

	// 2. Create a new in-memory Cozo database.
	db, err := cozo.New("mem", "", nil)
	if err != nil {
		panic(err) // Handle error appropriately in real application
	}
	// ここに接続テストを追加
	_, err = db.Run("?[] <- [[1]]", nil) // 最も単純な読み取り専用クエリ
	if err != nil {
		panic(err) // Handle error appropriately in real application
	}
	defer db.Close()
	// 3. Create a relation named 'my_relation'.
	_, err = db.Run(":create my_relation {id, name}", nil)
	if err != nil {
		panic(err) // Handle error appropriately in real application
	}
	// 4. Insert some data into 'my_relation'.
	_, err = db.Run("?[id, name] <- [[1, `Alice`], [2, `Bob`]] :insert my_relation {id, name}", nil)
	if err != nil {
		panic(err) // Handle error appropriately in real application
	}
	// 5. Query and retrieve data from 'my_relation'.
	res, err := db.Run("? := *my_relation{}", nil)
	if err != nil {
		panic(err) // Handle error appropriately in real application
	}
	// 6. Print the retrieved data to the console.
	println("Simple In-Memory Example:")
	for _, row := range res.Rows {
		println(row[0].(int), row[1].(string)) // Type assertion based on relation schema
	}
	// 7. Database is closed via defer db.Close()
	println("Example finished.")

}
