package main

import (
	"errors"
	"fmt"
)

// 1. 基本的な型定義
func addNumbers(a int, b int) int {
	return a + b
}

// 2. 構造体による型定義
type Person struct {
	Name  string
	Age   int
	Email *string // ポインタでオプショナルを表現
}

// メソッド定義
func (p Person) String() string {
	email := "N/A"
	if p.Email != nil {
		email = *p.Email
	}
	return fmt.Sprintf("Person{Name: %s, Age: %d, Email: %s}", p.Name, p.Age, email)
}

// 3. インターフェースによる抽象化
type Repository interface {
	Add(key string, value interface{})
	Get(key string) (interface{}, bool)
}

// 実装
type MapRepository struct {
	items map[string]interface{}
}

func NewMapRepository() *MapRepository {
	return &MapRepository{
		items: make(map[string]interface{}),
	}
}

func (r *MapRepository) Add(key string, value interface{}) {
	r.items[key] = value
}

func (r *MapRepository) Get(key string) (interface{}, bool) {
	value, ok := r.items[key]
	return value, ok
}

// 4. ジェネリクス（Go 1.18+）
type GenericRepository[T any] struct {
	items map[string]T
}

func NewGenericRepository[T any]() *GenericRepository[T] {
	return &GenericRepository[T]{
		items: make(map[string]T),
	}
}

func (r *GenericRepository[T]) Add(key string, value T) {
	r.items[key] = value
}

func (r *GenericRepository[T]) Get(key string) (T, bool) {
	value, ok := r.items[key]
	return value, ok
}

// 5. エラー処理の型安全性
type MathError struct {
	Op  string
	Err string
}

func (e MathError) Error() string {
	return fmt.Sprintf("math error in %s: %s", e.Op, e.Err)
}

func safeDivide(a, b int) (int, error) {
	if b == 0 {
		return 0, MathError{Op: "divide", Err: "division by zero"}
	}
	return a / b, nil
}

// 6. 型アサーションと型スイッチ
func processValue(v interface{}) string {
	switch val := v.(type) {
	case string:
		return fmt.Sprintf("String: %s", val)
	case int:
		return fmt.Sprintf("Int: %d", val)
	case Person:
		return fmt.Sprintf("Person: %s", val.String())
	default:
		return fmt.Sprintf("Unknown type: %T", val)
	}
}

// 7. チャネルによる型安全な並行処理
func producer(ch chan<- int) {
	for i := 0; i < 5; i++ {
		ch <- i
	}
	close(ch)
}

func consumer(ch <-chan int) {
	for value := range ch {
		fmt.Printf("Received: %d\n", value)
	}
}

// 8. カスタム型による型安全性の向上
type UserID int
type ProductID int

func getUserByID(id UserID) (*Person, error) {
	// 実装
	return nil, errors.New("not implemented")
}

// コンパイルエラーになるコード（コメントアウト）
/*
func problematicFunction() {
    // 型エラー
    result := addNumbers("1", "2") // cannot use "1" (type string) as type int
    
    // 構造体の型エラー
    person := Person{
        Name: 123,        // cannot use 123 (type int) as type string
        Age:  "twenty",   // cannot use "twenty" (type string) as type int
    }
    
    // 異なるカスタム型の混同
    var userID UserID = 1
    var productID ProductID = 1
    getUserByID(productID) // cannot use productID (type ProductID) as type UserID
}
*/

func main() {
	// 正しい使用例
	fmt.Println(addNumbers(1, 2))

	email := "alice@example.com"
	person := Person{
		Name:  "Alice",
		Age:   30,
		Email: &email,
	}
	fmt.Println(person)

	// ジェネリックリポジトリ
	repo := NewGenericRepository[Person]()
	repo.Add("alice", person)

	if p, ok := repo.Get("alice"); ok {
		fmt.Printf("Found: %v\n", p)
	}

	// エラー処理
	if result, err := safeDivide(10, 2); err == nil {
		fmt.Printf("Result: %d\n", result)
	} else {
		fmt.Printf("Error: %v\n", err)
	}

	// 型スイッチ
	fmt.Println(processValue("hello"))
	fmt.Println(processValue(42))
	fmt.Println(processValue(person))

	// チャネル
	ch := make(chan int)
	go producer(ch)
	consumer(ch)
}