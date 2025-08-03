---
title: "Starting a Development Blog with Hugo and GitHub Pages"
meta_title: ""
description: "I've summarized the process of creating a development blog using Hugo static site generator and GitHub Pages."
date: 2025-08-03T10:00:00Z
image: "/images/banner.png"
categories: ["Development", "Blog"]
author: "Kigo"
tags: ["Hugo", "GitHub Pages", "Blog", "Static Site"]
draft: false
---

Hello! I've finally started a development blog. In this post, I'd like to summarize the process of creating a blog using Hugo and GitHub Pages.

## Why Did I Choose Hugo?

When choosing a blog platform, I considered several options:

- **Gatsby**: Familiar because it's React-based, but complex
- **Jekyll**: Default support for GitHub Pages, but Ruby environment
- **Hugo**: Go-based, fast and simple
- **Hexo**: Node.js-based, familiar but performance is lacking

The reasons I ultimately chose Hugo:

1. **Fast Build Speed**: Lightning-fast builds leveraging Go language advantages
2. **Simple Configuration**: Can start immediately without complex setup
3. **Rich Themes**: Various and beautiful themes
4. **GitHub Pages Compatibility**: Easy deployment

## Choosing HugoPlate Theme

Among various Hugo themes, I chose [HugoPlate](https://github.com/zeon-studio/hugoplate).

### Advantages of HugoPlate

- **TailwindCSS-based**: Easy styling
- **Responsive Design**: Mobile-friendly
- **SEO Optimized**: Built-in search engine optimization
- **Dark Mode Support**: Eye-friendly dark mode
- **Fast Performance**: 95+ Google PageSpeed score

## Blog Setup Process

### 1. Basic Configuration

```toml
# hugo.toml
baseURL = "https://kigo1031.github.io"
title = "Kigo's Blog"
defaultContentLanguage = 'en'
```

### 2. Korean Language Support Setup

```toml
# config/_default/languages.toml
[ko]
languageName = "한국어"
languageCode = "ko-kr"
contentDir = "content/korean"
weight = 1
```

### 3. GitHub Actions Deployment Setup

```yaml
# .github/workflows/deploy.yml
name: Deploy Hugo site to Pages
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'
      # ... build and deployment steps
```

## Korean Customization

### Menu Localization

- Home → 홈
- About → 소개
- Blog → 블로그
- Contact → 연락처

### Content Structure

```
content/korean/
├── _index.md          # Homepage
├── about/
│   └── _index.md      # About page
├── blog/
│   └── *.md           # Blog posts
└── contact/
    └── _index.md      # Contact page
```

## Future Plans

Topics I plan to cover in this blog:

- **Web Development**: React, Vue, TypeScript, etc.
- **Backend**: Node.js, Python, databases
- **DevOps**: Docker, CI/CD, cloud
- **Development Tools**: VS Code, Git, productivity tools
- **Learning Records**: New technology learning reviews

## Conclusion

I've finally started my Korean development blog! I'll continue to fill it with good content.

If you have any questions or suggestions for improvement after viewing the blog, please feel free to [contact](/en/contact) me. Let's grow together as developers! 🚀

---

*This blog is built with Hugo + HugoPlate theme + GitHub Pages.*

안녕하세요! 드디어 개발 블로그를 시작하게 되었습니다. 이번 포스트에서는 Hugo와 GitHub Pages를 활용해서 블로그를 만든 과정을 정리해보려고 합니다.

## 왜 Hugo를 선택했을까?

블로그 플랫폼을 선택할 때 여러 옵션들을 고려했습니다:

- **Gatsby**: React 기반이라 익숙하지만 복잡함
- **Jekyll**: GitHub Pages의 기본 지원이지만 Ruby 환경
- **Hugo**: Go 기반으로 빠르고 간단함
- **Hexo**: Node.js 기반으로 친숙하지만 성능이 아쉬움

최종적으로 Hugo를 선택한 이유는:

1. **빠른 빌드 속도**: Go 언어의 장점을 살린 초고속 빌드
2. **간단한 설정**: 복잡한 설정 없이 바로 시작 가능
3. **풍부한 테마**: 다양하고 예쁜 테마들
4. **GitHub Pages 호환**: 쉬운 배포

## HugoPlate 테마 선택

여러 Hugo 테마 중에서 [HugoPlate](https://github.com/zeon-studio/hugoplate)를 선택했습니다.

### HugoPlate의 장점

- **TailwindCSS 기반**: 쉬운 스타일링
- **반응형 디자인**: 모바일 친화적
- **SEO 최적화**: 검색 엔진 최적화 내장
- **다크모드 지원**: 눈에 편한 다크모드
- **빠른 성능**: 95+ Google PageSpeed 점수

## 블로그 설정 과정

### 1. 기본 설정

```toml
# hugo.toml
baseURL = "https://kigo1031.github.io"
title = "Kigo's Blog"
theme = "hugoplate"
```

### 2. GitHub Actions 설정

```yaml
# .github/workflows/deploy.yml
name: Deploy Hugo site to Pages
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'
      # ... 빌드 및 배포 단계
```

### 3. 컨텐츠 작성

```markdown
---
title: "포스트 제목"
date: 2025-08-03
categories: ["Development"]
tags: ["Hugo", "Blog"]
---

포스트 내용...
```

## 앞으로의 계획

이 블로그에서 다룰 예정인 주제들:

- **웹 개발**: React, Vue, TypeScript 등
- **백엔드**: Node.js, Python, 데이터베이스
- **DevOps**: Docker, CI/CD, 클라우드
- **개발 도구**: VS Code, Git, 생산성 도구들
- **학습 기록**: 새로운 기술 학습 후기

## 마무리

드디어 개발 블로그를 시작했습니다! 앞으로 꾸준히 좋은 내용들로 채워나가겠습니다.

블로그를 보시고 궁금한 점이나 개선할 점이 있다면 언제든 연락 주세요. 함께 성장하는 개발자가 되어요! 🚀

---

*이 블로그는 Hugo + HugoPlate 테마 + GitHub Pages로 구성되어 있습니다.*
