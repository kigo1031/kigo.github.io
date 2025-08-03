---
title: "Essential JavaScript ES6+ Features"
meta_title: ""
description: "Explore core features of modern JavaScript with examples and learn how to use them in real-world projects."
date: 2025-07-29T15:45:00Z
image: "/images/service-2.png"
categories: ["JavaScript", "Frontend"]
author: "Kigo"
tags: ["JavaScript", "ES6", "Modern JavaScript", "Frontend"]
draft: false
---

JavaScript ES6 (ECMAScript 2015) introduced many new features. Let's explore the essential features commonly used in real-world development.

## 1. let and const

Use `let` and `const` with block scope instead of `var`.

```javascript
// Problem with var
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 3, 3, 3
}

// Solution with let
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 0, 1, 2
}

// const for constants
const API_URL = 'https://api.example.com';
const config = {
  timeout: 5000,
  retries: 3
};
```

## 2. Arrow Functions

Concise function syntax with lexical `this` binding.

```javascript
// Traditional function
function add(a, b) {
  return a + b;
}

// Arrow function
const add = (a, b) => a + b;

// With single parameter
const square = x => x * x;

// With multiple statements
const processData = (data) => {
  const processed = data.map(item => item.value);
  return processed.filter(value => value > 0);
};

// Lexical this binding
class Timer {
  constructor() {
    this.seconds = 0;
  }

  start() {
    // Arrow function preserves 'this'
    setInterval(() => {
      this.seconds++;
      console.log(this.seconds);
    }, 1000);
  }
}
```

## 3. Template Literals

String interpolation and multi-line strings.

```javascript
const name = 'John';
const age = 30;

// String interpolation
const message = `Hello, ${name}! You are ${age} years old.`;

// Multi-line strings
const html = `
  <div class="user-card">
    <h2>${name}</h2>
    <p>Age: ${age}</p>
  </div>
`;

// Expression evaluation
const price = 19.99;
const tax = 0.08;
const total = `Total: $${(price * (1 + tax)).toFixed(2)}`;
```

## 4. Destructuring Assignment

Extract values from arrays and objects.

```javascript
// Array destructuring
const [first, second, ...rest] = [1, 2, 3, 4, 5];
console.log(first); // 1
console.log(rest);  // [3, 4, 5]

// Object destructuring
const user = {
  name: 'Alice',
  email: 'alice@example.com',
  age: 25
};

const { name, email } = user;
console.log(name); // 'Alice'

// Destructuring with default values
const { name: userName, country = 'Unknown' } = user;

// Function parameter destructuring
function createUser({ name, email, age = 18 }) {
  return {
    id: Date.now(),
    name,
    email,
    age
  };
}
```

## 5. Spread and Rest Operators

Spread arrays/objects and collect function parameters.

```javascript
// Spread operator with arrays
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
const combined = [...arr1, ...arr2]; // [1, 2, 3, 4, 5, 6]

// Spread operator with objects
const defaults = { theme: 'dark', language: 'en' };
const userPrefs = { language: 'ko', fontSize: 14 };
const settings = { ...defaults, ...userPrefs };
// { theme: 'dark', language: 'ko', fontSize: 14 }

// Rest parameters
function sum(...numbers) {
  return numbers.reduce((total, num) => total + num, 0);
}

sum(1, 2, 3, 4); // 10
```

## 6. Enhanced Object Literals

Concise property and method definitions.

```javascript
const name = 'Product';
const price = 29.99;

// Shorthand property names
const product = {
  name,    // instead of name: name
  price,   // instead of price: price

  // Method shorthand
  getDetails() {  // instead of getDetails: function()
    return `${this.name}: $${this.price}`;
  },

  // Computed property names
  [`${name.toLowerCase()}_id`]: 12345
};
```

## 7. Classes

Class-based object-oriented programming.

```javascript
class Vehicle {
  constructor(make, model) {
    this.make = make;
    this.model = model;
  }

  getInfo() {
    return `${this.make} ${this.model}`;
  }

  // Static method
  static compare(v1, v2) {
    return v1.make === v2.make;
  }
}

class Car extends Vehicle {
  constructor(make, model, doors) {
    super(make, model);
    this.doors = doors;
  }

  getDetails() {
    return `${this.getInfo()} with ${this.doors} doors`;
  }
}

const myCar = new Car('Toyota', 'Camry', 4);
console.log(myCar.getDetails()); // Toyota Camry with 4 doors
```

## 8. Modules

Import and export functionality between files.

```javascript
// math.js
export const PI = 3.14159;

export function add(a, b) {
  return a + b;
}

export function multiply(a, b) {
  return a * b;
}

// Default export
export default function subtract(a, b) {
  return a - b;
}

// main.js
import subtract, { PI, add, multiply } from './math.js';

console.log(PI);           // 3.14159
console.log(add(2, 3));    // 5
console.log(subtract(5, 2)); // 3
```

## 9. Promises and Async/Await

Handle asynchronous operations.

```javascript
// Promise
function fetchUser(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (id > 0) {
        resolve({ id, name: `User ${id}` });
      } else {
        reject(new Error('Invalid user ID'));
      }
    }, 1000);
  });
}

// Using Promise
fetchUser(1)
  .then(user => console.log(user))
  .catch(error => console.error(error));

// Using async/await
async function getUser(id) {
  try {
    const user = await fetchUser(id);
    console.log(user);
    return user;
  } catch (error) {
    console.error('Error:', error.message);
  }
}
```

## 10. Array Methods

Powerful array manipulation methods.

```javascript
const numbers = [1, 2, 3, 4, 5];

// map - transform elements
const doubled = numbers.map(n => n * 2);
// [2, 4, 6, 8, 10]

// filter - select elements
const evens = numbers.filter(n => n % 2 === 0);
// [2, 4]

// reduce - accumulate values
const sum = numbers.reduce((total, n) => total + n, 0);
// 15

// find - find first match
const found = numbers.find(n => n > 3);
// 4

// some/every - test conditions
const hasEven = numbers.some(n => n % 2 === 0);  // true
const allPositive = numbers.every(n => n > 0);   // true
```

## 11. Set and Map

New collection types.

```javascript
// Set - unique values
const uniqueNumbers = new Set([1, 2, 2, 3, 3, 4]);
console.log(uniqueNumbers); // Set {1, 2, 3, 4}

uniqueNumbers.add(5);
uniqueNumbers.delete(1);
console.log(uniqueNumbers.has(2)); // true

// Map - key-value pairs
const userRoles = new Map();
userRoles.set('john', 'admin');
userRoles.set('alice', 'user');
userRoles.set('bob', 'moderator');

console.log(userRoles.get('john')); // 'admin'
console.log(userRoles.size);        // 3

// Iterating
for (const [user, role] of userRoles) {
  console.log(`${user}: ${role}`);
}
```

## 12. Default Parameters

Set default values for function parameters.

```javascript
function createUser(name, role = 'user', active = true) {
  return {
    name,
    role,
    active,
    createdAt: new Date()
  };
}

const user1 = createUser('John');
// { name: 'John', role: 'user', active: true, createdAt: ... }

const user2 = createUser('Alice', 'admin', false);
// { name: 'Alice', role: 'admin', active: false, createdAt: ... }
```

## Real-World Example

Putting it all together in a practical example:

```javascript
class TodoManager {
  constructor() {
    this.todos = new Map();
    this.nextId = 1;
  }

  addTodo(text, priority = 'medium') {
    const todo = {
      id: this.nextId++,
      text,
      priority,
      completed: false,
      createdAt: new Date()
    };

    this.todos.set(todo.id, todo);
    return todo;
  }

  async saveTodos() {
    const todosArray = [...this.todos.values()];
    try {
      const response = await fetch('/api/todos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(todosArray)
      });

      if (!response.ok) {
        throw new Error('Failed to save todos');
      }

      return await response.json();
    } catch (error) {
      console.error('Save failed:', error);
      throw error;
    }
  }

  getFilteredTodos({ completed, priority } = {}) {
    return [...this.todos.values()]
      .filter(todo => {
        if (completed !== undefined && todo.completed !== completed) {
          return false;
        }
        if (priority && todo.priority !== priority) {
          return false;
        }
        return true;
      })
      .sort((a, b) => b.createdAt - a.createdAt);
  }
}

// Usage
const todoManager = new TodoManager();
todoManager.addTodo('Learn ES6+', 'high');
todoManager.addTodo('Build a project');
todoManager.addTodo('Write documentation', 'low');

const highPriorityTodos = todoManager.getFilteredTodos({ priority: 'high' });
console.log(highPriorityTodos);
```

## Conclusion

These ES6+ features make JavaScript more expressive and powerful. Start incorporating them into your projects gradually, focusing on the ones that provide the most immediate benefit to your coding style.

In the next post, we'll explore React Hooks and modern React development patterns.
