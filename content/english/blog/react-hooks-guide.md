---
title: "React Functional Components and Hooks Guide"
meta_title: ""
description: "Learn how to use React functional components and essential Hooks with practical examples."
date: 2025-08-01T16:30:00Z
image: "/images/service-2.png"
categories: ["Web Development"]
author: "Kigo"
tags: ["React", "Hooks", "JavaScript", "Frontend"]
draft: false
---

React Hooks, introduced in React 16.8, enable state management and lifecycle features in functional components. Let's explore the essential Hooks and their usage.

## useState - State Management

The most basic Hook for managing state in functional components.

```jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
      <button onClick={() => setCount(count - 1)}>
        Decrement
      </button>
      <button onClick={() => setCount(0)}>
        Reset
      </button>
    </div>
  );
}

// Managing object state
function UserProfile() {
  const [user, setUser] = useState({
    name: '',
    email: '',
    age: 0
  });

  const updateUser = (field, value) => {
    setUser(prevUser => ({
      ...prevUser,
      [field]: value
    }));
  };

  return (
    <form>
      <input
        type="text"
        placeholder="Name"
        value={user.name}
        onChange={(e) => updateUser('name', e.target.value)}
      />
      <input
        type="email"
        placeholder="Email"
        value={user.email}
        onChange={(e) => updateUser('email', e.target.value)}
      />
      <input
        type="number"
        placeholder="Age"
        value={user.age}
        onChange={(e) => updateUser('age', parseInt(e.target.value))}
      />
    </form>
  );
}
```

## useEffect - Side Effects

Handle side effects like data fetching, subscriptions, or manual DOM manipulation.

```jsx
import React, { useState, useEffect } from 'react';

function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Effect without dependencies - runs on every render
  useEffect(() => {
    console.log('Component rendered');
  });

  // Effect with empty dependency array - runs once on mount
  useEffect(() => {
    fetchUsers();
  }, []);

  // Effect with dependencies - runs when dependencies change
  useEffect(() => {
    document.title = `${users.length} users loaded`;
  }, [users.length]);

  // Effect with cleanup
  useEffect(() => {
    const timer = setInterval(() => {
      console.log('Timer tick');
    }, 1000);

    // Cleanup function
    return () => {
      clearInterval(timer);
    };
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/users');
      const userData = await response.json();
      setUsers(userData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

## useContext - Context API

Share data across components without prop drilling.

```jsx
import React, { createContext, useContext, useState } from 'react';

// Create context
const AuthContext = createContext();

// Provider component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const login = async (credentials) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      const userData = await response.json();
      setUser(userData);
      setIsLoggedIn(true);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = () => {
    setUser(null);
    setIsLoggedIn(false);
  };

  const value = {
    user,
    isLoggedIn,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for using auth context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// Using the context
function LoginButton() {
  const { isLoggedIn, login, logout, user } = useAuth();

  if (isLoggedIn) {
    return (
      <div>
        <span>Welcome, {user.name}!</span>
        <button onClick={logout}>Logout</button>
      </div>
    );
  }

  return (
    <button onClick={() => login({ email: 'user@example.com', password: 'password' })}>
      Login
    </button>
  );
}
```

## useReducer - Complex State Management

An alternative to useState for more complex state logic.

```jsx
import React, { useReducer } from 'react';

// Reducer function
function todoReducer(state, action) {
  switch (action.type) {
    case 'ADD_TODO':
      return {
        ...state,
        todos: [...state.todos, {
          id: Date.now(),
          text: action.payload,
          completed: false
        }]
      };

    case 'TOGGLE_TODO':
      return {
        ...state,
        todos: state.todos.map(todo =>
          todo.id === action.payload
            ? { ...todo, completed: !todo.completed }
            : todo
        )
      };

    case 'DELETE_TODO':
      return {
        ...state,
        todos: state.todos.filter(todo => todo.id !== action.payload)
      };

    case 'SET_FILTER':
      return {
        ...state,
        filter: action.payload
      };

    default:
      return state;
  }
}

function TodoApp() {
  const initialState = {
    todos: [],
    filter: 'all' // 'all', 'active', 'completed'
  };

  const [state, dispatch] = useReducer(todoReducer, initialState);
  const [inputValue, setInputValue] = useState('');

  const addTodo = () => {
    if (inputValue.trim()) {
      dispatch({ type: 'ADD_TODO', payload: inputValue });
      setInputValue('');
    }
  };

  const filteredTodos = state.todos.filter(todo => {
    if (state.filter === 'active') return !todo.completed;
    if (state.filter === 'completed') return todo.completed;
    return true;
  });

  return (
    <div>
      <div>
        <input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          placeholder="Add a todo..."
        />
        <button onClick={addTodo}>Add</button>
      </div>

      <div>
        <button
          onClick={() => dispatch({ type: 'SET_FILTER', payload: 'all' })}
          style={{ fontWeight: state.filter === 'all' ? 'bold' : 'normal' }}
        >
          All
        </button>
        <button
          onClick={() => dispatch({ type: 'SET_FILTER', payload: 'active' })}
          style={{ fontWeight: state.filter === 'active' ? 'bold' : 'normal' }}
        >
          Active
        </button>
        <button
          onClick={() => dispatch({ type: 'SET_FILTER', payload: 'completed' })}
          style={{ fontWeight: state.filter === 'completed' ? 'bold' : 'normal' }}
        >
          Completed
        </button>
      </div>

      <ul>
        {filteredTodos.map(todo => (
          <li key={todo.id}>
            <span
              style={{
                textDecoration: todo.completed ? 'line-through' : 'none',
                cursor: 'pointer'
              }}
              onClick={() => dispatch({ type: 'TOGGLE_TODO', payload: todo.id })}
            >
              {todo.text}
            </span>
            <button onClick={() => dispatch({ type: 'DELETE_TODO', payload: todo.id })}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## useMemo - Performance Optimization

Memoize expensive calculations.

```jsx
import React, { useState, useMemo } from 'react';

function ExpensiveComponent() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState([]);

  // Expensive calculation
  const expensiveValue = useMemo(() => {
    console.log('Calculating expensive value...');
    let result = 0;
    for (let i = 0; i < 1000000; i++) {
      result += i;
    }
    return result;
  }, [count]); // Only recalculate when count changes

  // Memoized filtered items
  const expensiveItems = useMemo(() => {
    console.log('Filtering items...');
    return items.filter(item => item.value > 50);
  }, [items]);

  return (
    <div>
      <p>Count: {count}</p>
      <p>Expensive Value: {expensiveValue}</p>
      <p>Filtered Items: {expensiveItems.length}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment Count
      </button>
      <button onClick={() => setItems([...items, { value: Math.random() * 100 }])}>
        Add Random Item
      </button>
    </div>
  );
}
```

## useCallback - Function Memoization

Memoize functions to prevent unnecessary re-renders.

```jsx
import React, { useState, useCallback, memo } from 'react';

// Child component that might re-render unnecessarily
const TodoItem = memo(({ todo, onToggle, onDelete }) => {
  console.log(`Rendering TodoItem ${todo.id}`);

  return (
    <li>
      <span
        style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}
        onClick={() => onToggle(todo.id)}
      >
        {todo.text}
      </span>
      <button onClick={() => onDelete(todo.id)}>Delete</button>
    </li>
  );
});

function TodoList() {
  const [todos, setTodos] = useState([]);
  const [inputValue, setInputValue] = useState('');

  // Memoized callback functions
  const handleToggle = useCallback((id) => {
    setTodos(prevTodos =>
      prevTodos.map(todo =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  }, []); // Empty dependency array since setTodos is stable

  const handleDelete = useCallback((id) => {
    setTodos(prevTodos => prevTodos.filter(todo => todo.id !== id));
  }, []);

  const addTodo = useCallback(() => {
    if (inputValue.trim()) {
      setTodos(prevTodos => [...prevTodos, {
        id: Date.now(),
        text: inputValue,
        completed: false
      }]);
      setInputValue('');
    }
  }, [inputValue]);

  return (
    <div>
      <input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addTodo()}
      />
      <button onClick={addTodo}>Add Todo</button>

      <ul>
        {todos.map(todo => (
          <TodoItem
            key={todo.id}
            todo={todo}
            onToggle={handleToggle}
            onDelete={handleDelete}
          />
        ))}
      </ul>
    </div>
  );
}
```

## useRef - DOM References and Mutable Values

Access DOM elements and store mutable values.

```jsx
import React, { useRef, useEffect, useState } from 'react';

function FocusInput() {
  const inputRef = useRef(null);
  const countRef = useRef(0);
  const [renderCount, setRenderCount] = useState(0);

  useEffect(() => {
    // Focus input on mount
    inputRef.current.focus();
  }, []);

  useEffect(() => {
    // Update ref value without causing re-render
    countRef.current += 1;
  });

  const handleClick = () => {
    // Access DOM element
    inputRef.current.focus();
    inputRef.current.select();

    // Log ref value
    console.log(`Component rendered ${countRef.current} times`);
  };

  return (
    <div>
      <input ref={inputRef} type="text" placeholder="Click button to focus" />
      <button onClick={handleClick}>Focus Input</button>
      <button onClick={() => setRenderCount(renderCount + 1)}>
        Force Re-render ({renderCount})
      </button>
      <p>Render count stored in ref: {countRef.current}</p>
    </div>
  );
}
```

## Custom Hooks

Create reusable stateful logic.

```jsx
import { useState, useEffect } from 'react';

// Custom hook for API data fetching
function useApi(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
}

// Custom hook for local storage
function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
}

// Using custom hooks
function UserProfile() {
  const { data: user, loading, error } = useApi('/api/user/profile');
  const [preferences, setPreferences] = useLocalStorage('userPreferences', {
    theme: 'light',
    language: 'en'
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Welcome, {user.name}!</h1>
      <div>
        <label>
          Theme:
          <select
            value={preferences.theme}
            onChange={(e) => setPreferences({
              ...preferences,
              theme: e.target.value
            })}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </div>
    </div>
  );
}
```

## Best Practices

### 1. Rules of Hooks

- Only call Hooks at the top level
- Only call Hooks from React functions
- Use ESLint plugin to enforce rules

### 2. Dependency Arrays

```jsx
// Good: Include all dependencies
useEffect(() => {
  fetchUser(userId);
}, [userId]);

// Bad: Missing dependencies
useEffect(() => {
  fetchUser(userId); // userId is used but not in dependencies
}, []);

// Good: Use callback if you need to avoid dependencies
const fetchUser = useCallback(async (id) => {
  const response = await fetch(`/api/users/${id}`);
  setUser(await response.json());
}, []);

useEffect(() => {
  fetchUser(userId);
}, [userId, fetchUser]);
```

### 3. Performance Optimization

```jsx
// Use memo for expensive child components
const ExpensiveChild = memo(({ data, onUpdate }) => {
  // Expensive rendering logic
  return <div>{/* Complex UI */}</div>;
});

// Use useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return heavyCalculation(data);
}, [data]);

// Use useCallback for event handlers passed to children
const handleClick = useCallback((id) => {
  // Handle click
}, []);
```

## Conclusion

React Hooks provide a powerful and flexible way to build components. Start with useState and useEffect, then gradually incorporate other Hooks as needed. Custom Hooks are particularly useful for sharing logic between components.

In the next post, we'll explore advanced React patterns and state management with Redux Toolkit.
