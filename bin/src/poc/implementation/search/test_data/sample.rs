// Rust sample
struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }
    
    fn greet(&self) {
        println!("Hello, I'm {}", self.name);
    }
}

fn main() {
    let person = Person::new("Alice".to_string(), 30);
    person.greet();
}