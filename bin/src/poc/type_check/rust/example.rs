///
/// 型安全性検証用Rustサンプル
/// 統一規約に基づく実装での型チェック動作確認
///

use std::collections::HashMap;

// 1. 基本的な型定義（Rustは常に静的型付け）
fn add_numbers(a: i32, b: i32) -> i32 {
    a + b
}

// 2. 構造体による型定義
#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
    email: Option<String>,
}

impl Person {
    fn new(name: String, age: u32) -> Self {
        Person {
            name,
            age,
            email: None,
        }
    }
    
    fn with_email(mut self, email: String) -> Self {
        self.email = Some(email);
        self
    }
}

// 3. 列挙型による型安全な状態管理
#[derive(Debug)]
enum Result<T, E> {
    Ok(T),
    Err(E),
}

// 4. ジェネリック型とトレイト境界
struct Repository<T> {
    items: HashMap<String, T>,
}

impl<T: Clone> Repository<T> {
    fn new() -> Self {
        Repository {
            items: HashMap::new(),
        }
    }
    
    fn add(&mut self, key: String, value: T) {
        self.items.insert(key, value);
    }
    
    fn get(&self, key: &str) -> Option<&T> {
        self.items.get(key)
    }
}

// 5. 所有権と借用による安全性
fn take_ownership(s: String) -> String {
    // sの所有権を取得
    s.to_uppercase()
}

fn borrow_reference(s: &str) -> String {
    // sを借用（読み取り専用）
    s.to_uppercase()
}

// 6. パターンマッチングによる網羅的チェック
fn process_option(opt: Option<i32>) -> i32 {
    match opt {
        Some(value) => value * 2,
        None => 0,
    }
}

// 7. ライフタイムによるメモリ安全性
struct PersonRef<'a> {
    name: &'a str,
    age: u32,
}

impl<'a> PersonRef<'a> {
    fn new(name: &'a str, age: u32) -> Self {
        PersonRef { name, age }
    }
}

// 8. エラー処理の型安全性
#[derive(Debug)]
enum MathError {
    DivisionByZero,
    Overflow,
}

fn safe_divide(a: i32, b: i32) -> std::result::Result<i32, MathError> {
    if b == 0 {
        Err(MathError::DivisionByZero)
    } else if a == i32::MIN && b == -1 {
        Err(MathError::Overflow)
    } else {
        Ok(a / b)
    }
}

// コンパイルエラーになるコード（コメントアウト）
/*
fn problematic_function() {
    // これらはコンパイルエラー
    let result = add_numbers("1", "2"); // mismatched types
    let person = Person { name: 123, age: "twenty", email: None }; // mismatched types
    
    // 所有権違反
    let s = String::from("hello");
    take_ownership(s);
    println!("{}", s); // value borrowed here after move
}
*/

fn main() {
    // 正しい使用例
    println!("{}", add_numbers(1, 2));
    
    let person = Person::new("Alice".to_string(), 30)
        .with_email("alice@example.com".to_string());
    println!("{:?}", person);
    
    let mut repo = Repository::new();
    repo.add("alice".to_string(), person.clone());
    
    // パターンマッチング
    match safe_divide(10, 2) {
        Ok(result) => println!("Result: {}", result),
        Err(e) => println!("Error: {:?}", e),
    }
    
    // ライフタイム
    let name = "Bob";
    let person_ref = PersonRef::new(name, 25);
    println!("PersonRef: {} is {}", person_ref.name, person_ref.age);
}