---
title: "JavaScript ES6+ 핵심 기능들"
meta_title: ""
description: "모던 JavaScript의 핵심 기능들을 예제와 함께 알아보고, 실무에서 어떻게 활용하는지 살펴봅니다."
date: 2025-07-29T15:45:00Z
image: "/images/service-2.png"
categories: ["JavaScript", "프론트엔드"]
author: "Kigo"
tags: ["JavaScript", "ES6", "모던자바스크립트", "프론트엔드"]
draft: false
---

JavaScript ES6(ECMAScript 2015)부터 많은 새로운 기능들이 추가되었습니다. 오늘은 실무에서 자주 사용되는 핵심 기능들을 알아보겠습니다.

## 1. let과 const

기존의 `var` 대신 블록 스코프를 가지는 `let`과 `const`를 사용합니다.

```javascript
// var의 문제점
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 3, 3, 3
}

// let으로 해결
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 0, 1, 2
}

// const로 상수 선언
const API_URL = 'https://api.example.com';
const config = {
  apiKey: 'your-api-key',
  timeout: 5000
};
```

## 2. 화살표 함수 (Arrow Functions)

더 간결한 함수 문법과 this 바인딩의 차이점:

```javascript
// 기존 함수
function add(a, b) {
  return a + b;
}

// 화살표 함수
const add = (a, b) => a + b;

// 배열 메서드와 함께 사용
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const evens = numbers.filter(n => n % 2 === 0);
const sum = numbers.reduce((acc, n) => acc + n, 0);

// this 바인딩의 차이
class Timer {
  constructor() {
    this.seconds = 0;
  }

  start() {
    // 화살표 함수는 상위 스코프의 this를 사용
    setInterval(() => {
      this.seconds++;
      console.log(this.seconds);
    }, 1000);
  }
}
```

## 3. 템플릿 리터럴 (Template Literals)

문자열 보간과 멀티라인 문자열:

```javascript
const name = 'Kigo';
const age = 30;

// 문자열 보간
const greeting = `안녕하세요, ${name}님! 나이가 ${age}세이시군요.`;

// 멀티라인 문자열
const html = `
  <div class="card">
    <h2>${name}</h2>
    <p>Age: ${age}</p>
  </div>
`;

// 태그드 템플릿
function highlight(strings, ...values) {
  return strings.reduce((result, string, i) => {
    const value = values[i] ? `<mark>${values[i]}</mark>` : '';
    return result + string + value;
  }, '');
}

const message = highlight`Hello ${name}, you are ${age} years old!`;
```

## 4. 구조 분해 할당 (Destructuring)

배열과 객체에서 값을 추출하는 간편한 방법:

```javascript
// 배열 구조 분해
const [first, second, ...rest] = [1, 2, 3, 4, 5];
console.log(first); // 1
console.log(rest);  // [3, 4, 5]

// 객체 구조 분해
const user = {
  name: 'Kigo',
  age: 30,
  email: 'kigo@example.com'
};

const { name, age, email } = user;

// 새로운 이름으로 할당
const { name: userName, age: userAge } = user;

// 기본값 설정
const { name, country = 'Korea' } = user;

// 함수 매개변수에서 사용
function greet({ name, age }) {
  return `Hello ${name}, you are ${age} years old!`;
}

greet(user);
```

## 5. 스프레드 연산자 (Spread Operator)

배열과 객체를 전개하는 문법:

```javascript
// 배열 합치기
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
const combined = [...arr1, ...arr2]; // [1, 2, 3, 4, 5, 6]

// 배열 복사
const original = [1, 2, 3];
const copy = [...original];

// 함수 호출에서 사용
function sum(a, b, c) {
  return a + b + c;
}
const numbers = [1, 2, 3];
console.log(sum(...numbers));

// 객체 합치기
const obj1 = { a: 1, b: 2 };
const obj2 = { c: 3, d: 4 };
const merged = { ...obj1, ...obj2 }; // { a: 1, b: 2, c: 3, d: 4 }

// 객체 속성 오버라이드
const user = { name: 'John', age: 30 };
const updatedUser = { ...user, age: 31 };
```

## 6. 기본 매개변수 (Default Parameters)

함수 매개변수의 기본값 설정:

```javascript
// 기본 매개변수
function greet(name = 'World', punctuation = '!') {
  return `Hello, ${name}${punctuation}`;
}

console.log(greet()); // "Hello, World!"
console.log(greet('Kigo')); // "Hello, Kigo!"
console.log(greet('Kigo', '?')); // "Hello, Kigo?"

// 함수를 기본값으로 사용
function getDefaultName() {
  return 'Anonymous';
}

function welcome(name = getDefaultName()) {
  return `Welcome, ${name}!`;
}
```

## 7. 모듈 (Modules)

ES6 모듈 시스템:

```javascript
// math.js
export const PI = 3.14159;

export function add(a, b) {
  return a + b;
}

export function multiply(a, b) {
  return a * b;
}

// 기본 내보내기
export default function subtract(a, b) {
  return a - b;
}

// main.js
import subtract, { PI, add, multiply } from './math.js';

// 모든 것을 가져오기
import * as math from './math.js';

console.log(math.PI);
console.log(math.add(2, 3));
```

## 8. 클래스 (Classes)

객체 지향 프로그래밍을 위한 클래스 문법:

```javascript
class Animal {
  constructor(name, species) {
    this.name = name;
    this.species = species;
  }

  speak() {
    return `${this.name} makes a sound`;
  }

  // 정적 메서드
  static getKingdom() {
    return 'Animalia';
  }
}

class Dog extends Animal {
  constructor(name, breed) {
    super(name, 'Canis lupus');
    this.breed = breed;
  }

  speak() {
    return `${this.name} barks`;
  }

  // getter
  get info() {
    return `${this.name} is a ${this.breed}`;
  }

  // setter
  set nickname(nick) {
    this.nick = nick;
  }
}

const dog = new Dog('Buddy', 'Golden Retriever');
console.log(dog.speak()); // "Buddy barks"
console.log(dog.info);    // "Buddy is a Golden Retriever"
```

## 9. Promise와 async/await

비동기 처리를 위한 현대적인 방법:

```javascript
// Promise
function fetchData(url) {
  return new Promise((resolve, reject) => {
    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => resolve(data))
      .catch(error => reject(error));
  });
}

// async/await 사용
async function getData() {
  try {
    const data = await fetchData('https://api.example.com/data');
    console.log(data);
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
}

// 여러 비동기 작업 병렬 처리
async function fetchMultipleData() {
  try {
    const [users, posts, comments] = await Promise.all([
      fetchData('/api/users'),
      fetchData('/api/posts'),
      fetchData('/api/comments')
    ]);

    return { users, posts, comments };
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}
```

## 마무리

ES6+ 기능들은 JavaScript를 더욱 강력하고 표현력 있는 언어로 만들어주었습니다. 이러한 기능들을 잘 활용하면 더 깔끔하고 유지보수하기 쉬운 코드를 작성할 수 있습니다.

모던 JavaScript의 다른 기능들도 궁금하시다면 댓글로 알려주세요! 🚀
