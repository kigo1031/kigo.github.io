---
title: "Complete Hugo Blog Posting Guide - Tips from Real Experience"
meta_title: ""
description: "A practical blogging guide for Hugo and GitHub Pages users. Sharing know-how gained through trial and error."
date: 2025-08-03T15:00:00+09:00
image: "/images/service-2.png"
categories: ["Development Tools", "Web Development"]
author: "Kigo"
tags: ["Hugo", "GitHub Pages", "Blog", "Markdown", "Static Site"]
draft: false
---

Based on the trial and error I experienced while running a Hugo blog, I'll share efficient posting methods and useful tips. This will be especially helpful if you're using it with GitHub Pages.

## Why Hugo?

When I first started blogging, there were several options:
- **WordPress**: Heavy and complex
- **Jekyll**: GitHub Pages default but Ruby dependency
- **Gatsby**: React-based but overkill
- **Hugo**: Fast and simple, Go-based

I chose Hugo because of its **speed** and **simplicity**. Build times are really fast, and configuration is intuitive.

## Understanding Blog Structure

### Basic Directory Structure

```
your-blog/
├── content/           # Where posts go
│   ├── korean/
│   │   └── blog/     # Korean posts
│   └── english/
│       └── blog/     # English posts
├── static/           # Static files like images, CSS
│   └── images/
├── layouts/          # Template files
├── config/           # Configuration files
└── themes/           # Theme folder
```

### Important Configuration Files

1. **hugo.toml**: Basic site configuration
2. **config/_default/params.toml**: Detailed parameters
3. **config/_default/menus.en.toml**: Menu structure

## Creating New Posts

### 1. Using Hugo Commands (Recommended)

```bash
# Korean post
hugo new content/korean/blog/post-title.md

# English post
hugo new content/english/blog/post-title.md
```

This automatically generates the Front Matter.

### 2. Manual Creation

When creating files manually, use this template:

```yaml
---
title: "Post Title"
meta_title: ""  # Uses title if empty
description: "SEO-important description"
date: 2025-08-03T15:00:00+09:00
image: "/images/service-1.png"  # Thumbnail
categories: ["Category1", "Category2"]
author: "Kigo"
tags: ["tag1", "tag2"]
draft: false  # true for unpublished
---
```

## Front Matter Optimization Tips

### Required Fields

```yaml
title: "Clear and search-friendly title"
description: "Summary shown in Google search (under 155 chars)"
date: 2025-08-03T15:00:00+09:00  # Timezone required
categories: ["Use existing categories"]
tags: ["3-5 highly relevant tags"]
draft: false
```

### Date Format Notes

```yaml
# ✅ Correct format
date: 2025-08-03T15:00:00+09:00

# ❌ Wrong format
date: 2025-08-03
date: "August 3, 2025"
```

### Maintaining Category Consistency

Check existing categories and use them consistently:

```bash
# Check existing categories
find content -name "*.md" -exec grep -h "categories:" {} \; | sort | uniq
```

## Practical Markdown Writing Tips

### 1. Title Structure Optimization

```markdown
# Post Title (H1 is auto-generated, don't use)

## Main Section (H2)

### Sub Section (H3)

#### Details (H4)
```

### 2. Code Block Usage

```markdown
```java
// Specify language for highlighting
public class Example {
    public static void main(String[] args) {
        System.out.println("Hello Hugo!");
    }
}
```

```bash
# Terminal commands
hugo server -D
```

### 3. Image Optimization

```markdown
![Meaningful description](/images/screenshot.png)

<!-- Use HTML for image size control -->
<img src="/images/large-image.png" alt="Description" width="600">
```

### 4. Link Writing

```markdown
[Internal link](/blog/other-post/)
[External link](https://example.com){:target="_blank"}
```

## Image Management Strategy

### File Structure

```
static/images/
├── posts/           # Images per post
│   ├── 2025-08/
│   └── hugo-guide/
├── common/          # Common images
└── thumbnails/      # Thumbnails
```

### Image Optimization

```bash
# Optimize with ImageMagick
convert original.png -quality 85 -resize 800x600 optimized.jpg

# Convert to WebP (space saving)
cwebp original.png -q 80 -o optimized.webp
```

## Development Workflow

### 1. Run Development Server

```bash
hugo server -D --navigateToChanged
# -D: Include draft posts
# --navigateToChanged: Auto-refresh on file changes
```

### 2. Real-time Preview

The browser automatically refreshes when you save files. It's really convenient!

### 3. Build and Deploy

```bash
# Production build
hugo --minify

# Deploy to GitHub Pages (when using GitHub Actions)
git add .
git commit -m "New post: Hugo Blog Guide"
git push origin main
```

## Common Mistakes

### 1. Front Matter Syntax Errors

```yaml
# ❌ Quote mismatch
title: "Hugo Guide'

# ❌ Array syntax error
tags: [tag1, tag2, tag3

# ✅ Correct format
title: "Hugo Guide"
tags: ["tag1", "tag2", "tag3"]
```

### 2. Image Path Errors

```markdown
<!-- ❌ Absolute path -->
![Image](file:///Users/name/blog/static/images/pic.png)

<!-- ❌ Relative path -->
![Image](../static/images/pic.png)

<!-- ✅ Correct path -->
![Image](/images/pic.png)
```

### 3. Date Order Issues

If posts don't appear in the intended order, check the dates. Hugo sorts by date.

## Performance Optimization Tips

### 1. Image Lazy Loading

If supported by the theme:

```markdown
![Image](/images/large-pic.png){: loading="lazy"}
```

### 2. Build Optimization

```bash
# Measure build time
time hugo --minify

# Find large files
find public -type f -size +1M -ls
```

### 3. Search Optimization

```yaml
# config/_default/params.toml
[search]
enable = true
include_sections = ["blog"]
show_description = true
```

## Useful Hugo Commands

```bash
# Create new site
hugo new site my-blog

# Add theme
git submodule add https://github.com/theme/repo themes/theme-name

# Content statistics
hugo list all

# Detailed build info
hugo --verbose

# Check configuration
hugo config
```

## Backup Strategy

### 1. Using Git

```bash
# Track all changes
git add .
git commit -m "Add post: $(date)"
git push
```

### 2. Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d)
tar -czf "blog-backup-$DATE.tar.gz" content static config
```

## Troubleshooting

### Fixing Build Errors

```bash
# Check detailed error messages
hugo --verbose --debug

# Clear cache
hugo --gc
rm -rf public resources
```

### Template Issues

```bash
# Check template syntax
hugo --templateMetrics
```

## Conclusion

Hugo blogs may seem complex at first, but once you get used to them, they're really efficient. Especially:

1. **Fast Build Speed** - Hundreds of posts in seconds
2. **Flexible Structure** - Customizable as you want
3. **Search Optimization** - SEO-friendly static sites
4. **Free Hosting** - Perfect GitHub Pages compatibility

I hope this guide helps with your Hugo blog management. If you have any questions, feel free to ask in the comments!

---

**Reference Links:**
- [Hugo Official Documentation](https://gohugo.io/documentation/)
- [GitHub Pages Guide](https://pages.github.com/)
- [Markdown Syntax Guide](https://www.markdownguide.org/)
