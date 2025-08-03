---
title: "Docker로 개발 환경 구축하기"
meta_title: ""
description: "Docker를 활용한 일관된 개발 환경 구축 방법과 컨테이너 기반 개발 워크플로우를 알아봅니다."
date: 2025-07-30T11:20:00Z
image: "/images/service-1.png"
categories: ["DevOps", "컨테이너"]
author: "Kigo"
tags: ["Docker", "DevOps", "컨테이너", "개발환경"]
draft: false
---

개발을 하다 보면 "내 컴퓨터에서는 잘 됐는데?"라는 말을 자주 듣게 됩니다. Docker를 사용하면 이런 문제를 해결하고 일관된 개발 환경을 구축할 수 있습니다.

## Docker란?

Docker는 컨테이너 기반의 가상화 플랫폼입니다. 애플리케이션과 그 실행에 필요한 모든 것을 하나의 컨테이너로 패키징할 수 있습니다.

### Docker의 장점

- **일관성**: 어디서든 동일한 환경
- **격리**: 각 컨테이너는 독립적으로 실행
- **이식성**: 어느 플랫폼에서든 실행 가능
- **효율성**: 가상머신보다 가벼움

## 기본 Docker 명령어

### 이미지 관리

```bash
# 이미지 검색
docker search nginx

# 이미지 다운로드
docker pull nginx:latest

# 이미지 목록 확인
docker images

# 이미지 삭제
docker rmi nginx:latest
```

### 컨테이너 관리

```bash
# 컨테이너 실행
docker run -d -p 80:80 --name my-nginx nginx

# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인
docker ps -a

# 컨테이너 중지
docker stop my-nginx

# 컨테이너 삭제
docker rm my-nginx
```

## Dockerfile 작성

Node.js 애플리케이션을 위한 Dockerfile 예시:

```dockerfile
# 베이스 이미지 설정
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --only=production

# 앱 소스 복사
COPY . .

# 포트 노출
EXPOSE 3000

# 애플리케이션 실행
CMD ["npm", "start"]
```

## Docker Compose로 멀티 컨테이너 관리

여러 서비스를 함께 실행할 때는 Docker Compose를 사용합니다:

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - db

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Docker Compose 명령어

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart
```

## 개발 환경 구축 예시

### 1. 개발용 Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

# 개발 도구 설치
RUN apk add --no-cache git

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

# 개발 서버 실행
CMD ["npm", "run", "dev"]
```

### 2. .dockerignore 파일

```gitignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.env.local
Dockerfile
.dockerignore
```

## 유용한 Docker 팁

### 볼륨 마운트

```bash
# 로컬 디렉토리를 컨테이너에 마운트
docker run -v $(pwd):/app -p 3000:3000 my-app

# 데이터 볼륨 사용
docker volume create my-data
docker run -v my-data:/data my-app
```

### 환경 변수 설정

```bash
# 환경 변수 전달
docker run -e NODE_ENV=production my-app

# .env 파일 사용
docker run --env-file .env my-app
```

### 네트워크 설정

```bash
# 사용자 정의 네트워크 생성
docker network create my-network

# 네트워크에 컨테이너 연결
docker run --network my-network my-app
```

## 마무리

Docker는 현대 개발에서 필수적인 도구가 되었습니다. 처음에는 복잡해 보일 수 있지만, 익숙해지면 개발 효율성을 크게 향상시킬 수 있습니다.

컨테이너 기반 개발에 관심이 있으시다면 Docker부터 시작해보세요! 🐳
