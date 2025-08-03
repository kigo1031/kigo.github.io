# Hugo Blog Template

Backend developer focused Hugo blog using HugoPlate theme.

## 🚀 Quick Start

1. **Clone this repository**
```bash
git clone https://github.com/kigo1031/kigo.github.io.git
cd kigo.github.io
```

2. **Configure your settings**
```bash
# Copy template files
cp hugo.toml.example hugo.toml
cp config/_default/params.toml.example config/_default/params.toml

# Edit your personal settings
nano hugo.toml
nano config/_default/params.toml
```

3. **Run the development server**
```bash
hugo server -D
```

## ⚙️ Configuration

### Required Settings

**hugo.toml:**
- `baseURL`: Your GitHub Pages URL
- `title`: Your blog title
- `shortname`: Your Disqus shortname

**config/_default/params.toml:**
- `logo` & `logo_darkmode`: Your logo files
- `logo_text`: Fallback text
- `author`: Your name
- `description`: Blog description
- `keywords`: SEO keywords

## 🛡️ Security

Personal configuration files are gitignored to protect sensitive information:
- `hugo.toml`
- `config/_default/params.toml`

Template files (`.example`) are provided for reference.

## 📝 Features

- ✅ Korean/English multilingual support
- ✅ Backend development focused content
- ✅ Disqus comment system
- ✅ Custom KIGO branding
- ✅ SVG favicon support
- ✅ SEO optimized
- ✅ Responsive design

## 🔧 Tech Stack

- Hugo v0.148.2+
- HugoPlate theme
- TailwindCSS
- Font Awesome icons
