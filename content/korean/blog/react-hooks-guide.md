---
title: "React 함수형 컴포넌트와 Hooks 사용법"
meta_title: ""
description: "React의 함수형 컴포넌트와 주요 Hooks들의 사용법을 예제와 함께 알아봅니다."
date: 2025-08-01T16:30:00Z
image: "/images/service-2.png"
categories: ["웹개발"]
author: "Kigo"
tags: ["React", "Hooks", "JavaScript", "프론트엔드"]
draft: false
---

React 16.8에서 도입된 Hooks는 함수형 컴포넌트에서도 상태 관리와 생명주기 기능을 사용할 수 있게 해주었습니다. 오늘은 주요 Hooks들의 사용법을 알아보겠습니다.

## useState - 상태 관리

가장 기본적인 Hook으로, 함수형 컴포넌트에서 상태를 관리할 수 있습니다.

```jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>현재 카운트: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        증가
      </button>
      <button onClick={() => setCount(count - 1)}>
        감소
      </button>
    </div>
  );
}
```

## useEffect - 사이드 이펙트 처리

컴포넌트의 생명주기와 관련된 작업을 처리합니다.

```jsx
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 사용자 정보 로드
    const fetchUser = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/users/${userId}`);
        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]); // userId가 변경될 때마다 실행

  if (loading) return <div>로딩 중...</div>;
  if (!user) return <div>사용자를 찾을 수 없습니다.</div>;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}
```

## useContext - 전역 상태 관리

컴포넌트 트리 전체에서 데이터를 공유할 때 사용합니다.

```jsx
import React, { createContext, useContext, useState } from 'react';

// 테마 컨텍스트 생성
const ThemeContext = createContext();

// 테마 제공자 컴포넌트
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// 테마를 사용하는 컴포넌트
function ThemedButton() {
  const { theme, toggleTheme } = useContext(ThemeContext);

  return (
    <button
      onClick={toggleTheme}
      style={{
        backgroundColor: theme === 'light' ? '#fff' : '#333',
        color: theme === 'light' ? '#333' : '#fff'
      }}
    >
      {theme === 'light' ? '다크 모드' : '라이트 모드'}
    </button>
  );
}
```

## useMemo - 성능 최적화

비용이 큰 계산의 결과를 메모이제이션합니다.

```jsx
import React, { useState, useMemo } from 'react';

function ExpensiveComponent({ items }) {
  const [filter, setFilter] = useState('');

  // 필터링된 아이템들을 메모이제이션
  const filteredItems = useMemo(() => {
    console.log('필터링 계산 실행');
    return items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);

  return (
    <div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="검색어 입력"
      />
      <ul>
        {filteredItems.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

## useCallback - 함수 메모이제이션

함수를 메모이제이션하여 불필요한 리렌더링을 방지합니다.

```jsx
import React, { useState, useCallback } from 'react';

function TodoList() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');

  // 할 일 추가 함수를 메모이제이션
  const addTodo = useCallback(() => {
    if (newTodo.trim()) {
      setTodos(prev => [...prev, {
        id: Date.now(),
        text: newTodo,
        completed: false
      }]);
      setNewTodo('');
    }
  }, [newTodo]);

  // 할 일 토글 함수를 메모이제이션
  const toggleTodo = useCallback((id) => {
    setTodos(prev => prev.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  }, []);

  return (
    <div>
      <input
        value={newTodo}
        onChange={(e) => setNewTodo(e.target.value)}
        placeholder="새 할 일 입력"
      />
      <button onClick={addTodo}>추가</button>

      <ul>
        {todos.map(todo => (
          <TodoItem
            key={todo.id}
            todo={todo}
            onToggle={toggleTodo}
          />
        ))}
      </ul>
    </div>
  );
}
```

## 마무리

React Hooks는 함수형 컴포넌트의 가능성을 크게 확장시켜주었습니다. 각 Hook의 특성을 이해하고 적절히 사용하면 더 깔끔하고 효율적인 React 애플리케이션을 만들 수 있습니다.

다음에는 Custom Hooks 만들기에 대해 다뤄보겠습니다! 🎣
