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
defaultContentLanguage = 'ko'
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

I've finally started my development blog! I'll continue to fill it with good content.

If you have any questions or suggestions for improvement after viewing the blog, please feel free to [contact](/en/contact) me. Let's grow together as developers! 🚀

---

*This blog is built with Hugo + HugoPlate theme + GitHub Pages.*
