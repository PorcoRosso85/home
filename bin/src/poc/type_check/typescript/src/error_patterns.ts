/**
 * TypeScript Error Patterns Demonstration
 * 
 * This file demonstrates 5 common error patterns that TypeScript's
 * static type checker should detect and report.
 */

// ======================================
// 1. Type Mismatch - string variable assigned a number
// ======================================
function typeMismatchError() {
    // Declaring a variable with string type
    let message: string = "Hello, TypeScript!";
    
    // ERROR: Type 'number' is not assignable to type 'string'
    message = 42; // Attempting to assign a number to a string variable
    
    return message;
}

// ======================================
// 2. Null Access - accessing property on nullable value
// ======================================
interface User {
    name: string;
    email: string;
}

function nullAccessError() {
    // Function that may return null
    function getUser(id: number): User | null {
        if (id === 0) {
            return null;
        }
        return { name: "John Doe", email: "john@example.com" };
    }
    
    const user = getUser(0); // This returns null
    
    // ERROR: Object is possibly 'null'
    console.log(user.name); // Accessing property on nullable value without null check
    
    // Also demonstrating undefined access
    let optionalUser: User | undefined;
    
    // ERROR: Variable 'optionalUser' is used before being assigned
    // ERROR: Object is possibly 'undefined'
    console.log(optionalUser.email); // Accessing property on undefined value
}

// ======================================
// 3. Unknown Property - accessing non-existent property
// ======================================
interface Product {
    id: number;
    name: string;
    price: number;
}

function unknownPropertyError() {
    const product: Product = {
        id: 1,
        name: "Laptop",
        price: 999.99
    };
    
    // ERROR: Property 'description' does not exist on type 'Product'
    console.log(product.description); // Accessing non-existent property
    
    // ERROR: Property 'category' does not exist on type 'Product'
    product.category = "Electronics"; // Attempting to add non-existent property
}

// ======================================
// 4. Missing Arguments - calling function with fewer arguments
// ======================================
function missingArgumentsError() {
    // Function requiring two arguments
    function calculateArea(width: number, height: number): number {
        return width * height;
    }
    
    // ERROR: Expected 2 arguments, but got 1
    const area1 = calculateArea(10); // Missing the second argument
    
    // ERROR: Expected 2 arguments, but got 0
    const area2 = calculateArea(); // Missing both arguments
    
    // Also demonstrating with a more complex function
    function createUser(name: string, email: string, age: number): User {
        return { name, email }; // Note: age is not used, but still required
    }
    
    // ERROR: Expected 3 arguments, but got 2
    const newUser = createUser("Alice", "alice@example.com"); // Missing age argument
}

// ======================================
// 5. Readonly Assignment - assigning to readonly property
// ======================================
interface Config {
    readonly apiUrl: string;
    readonly maxRetries: number;
    timeout: number; // This one is mutable
}

function readonlyAssignmentError() {
    const config: Config = {
        apiUrl: "https://api.example.com",
        maxRetries: 3,
        timeout: 5000
    };
    
    // ERROR: Cannot assign to 'apiUrl' because it is a read-only property
    config.apiUrl = "https://new-api.example.com"; // Attempting to modify readonly property
    
    // ERROR: Cannot assign to 'maxRetries' because it is a read-only property
    config.maxRetries = 5; // Attempting to modify readonly property
    
    // This is OK - timeout is not readonly
    config.timeout = 10000;
    
    // Also demonstrating with readonly array
    const readonlyNumbers: readonly number[] = [1, 2, 3, 4, 5];
    
    // ERROR: Property 'push' does not exist on type 'readonly number[]'
    readonlyNumbers.push(6); // Attempting to modify readonly array
    
    // ERROR: Index signature in type 'readonly number[]' only permits reading
    readonlyNumbers[0] = 10; // Attempting to modify element in readonly array
}

// ======================================
// Bonus: Demonstrating all errors in one function
// ======================================
function demonstrateAllErrors() {
    // 1. Type Mismatch
    let count: number = 0;
    count = "zero"; // ERROR: Type 'string' is not assignable to type 'number'
    
    // 2. Null Access
    const nullableValue: string | null = null;
    console.log(nullableValue.length); // ERROR: Object is possibly 'null'
    
    // 3. Unknown Property
    const point = { x: 10, y: 20 };
    console.log(point.z); // ERROR: Property 'z' does not exist
    
    // 4. Missing Arguments
    function multiply(a: number, b: number) { return a * b; }
    multiply(5); // ERROR: Expected 2 arguments, but got 1
    
    // 5. Readonly Assignment
    const readonlyObj = { value: 42 } as const;
    readonlyObj.value = 100; // ERROR: Cannot assign to 'value' because it is a read-only property
}