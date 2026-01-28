<div align="center">

<img src="resources/banner.png" alt="Paste of Shame" width="800" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">

# 🛡️ Paste of Shame

### **Stop embarrassing AI-generated content before you paste it**

*Your personal clipboard watchdog that catches LLM boilerplate in real-time*

<br>

<a href="https://github.com/NoxelS/paste-of-shame/releases/latest/download/PasteOfShame-macOS.dmg">
  <img src="https://img.shields.io/badge/Download%20for%20macOS-10.15+-blue?style=for-the-badge&logo=apple&logoColor=white&labelColor=000000" alt="Download for macOS">
</a>

<br>
<br>

[![Release](https://img.shields.io/github/v/release/NoxelS/paste-of-shame?style=for-the-badge&logo=github&color=success)](https://github.com/NoxelS/paste-of-shame/releases)
[![CI/Tests](https://img.shields.io/github/actions/workflow/status/NoxelS/paste-of-shame/ci.yml?style=for-the-badge&logo=githubactions&label=CI)](https://github.com/NoxelS/paste-of-shame/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/NoxelS/paste-of-shame?style=for-the-badge)](https://github.com/NoxelS/paste-of-shame/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)](https://www.python.org)

<h3>
  <a href="#-installation">Installation</a>
  <span> • </span>
  <a href="#-features">Features</a>
  <span> • </span>
  <a href="#-how-it-works">How It Works</a>
  <span> • </span>
  <a href="docs/MACOS_APP.md">Documentation</a>
</h3>

</div>

---

## 🎯 Why Paste of Shame?

Ever copy-pasted AI-generated content and **forgot to remove the telltale phrases**?

- *"As an AI language model, I cannot..."* ❌
- *"Certainly! Here is the code you requested..."* ❌  
- *"I hope this helps! Feel free to ask if..."* ❌

**Paste of Shame catches these embarrassing moments before they happen.**

### ✨ Core Principles

<table>
<tr>
<td align="center" width="33%">
  <h3>🔒 100% Local & Secure</h3>
  <p><strong>Zero network calls</strong><br/>Everything runs locally on your machine. Your clipboard data never leaves your computer. No tracking, no telemetry, no data collection.</p>
</td>
<td align="center" width="33%">
  <h3>⚡ Lightning Fast</h3>
  <p><strong>Instant detection</strong><br/>No AI/ML models, no API delays. Pure pattern matching scans 100KB text in under 200ms. Zero performance impact on your system.</p>
</td>
<td align="center" width="33%">
  <h3>🎁 Free Forever</h3>
  <p><strong>Open source (MIT)</strong><br/>Free to use, modify, and distribute. No subscriptions, no limits, no premium tiers.</p>
</td>
</tr>
</table>

---

## 📦 Installation

<div align="center">

### macOS Application

**Native menu bar app with instant notifications**

<a href="https://github.com/NoxelS/paste-of-shame/releases/latest/download/PasteOfShame-macOS.dmg">
  <img src="https://img.shields.io/badge/Download%20DMG-10.15+-0071e3?style=for-the-badge&logo=apple&logoColor=white" alt="Download DMG" height="50">
</a>

<br>
<sub>Universal Binary • ~10MB • macOS 10.15 (Catalina) or later</sub>

</div>

<br>

**Installation Steps:**

1. Download the DMG file above
2. Open the downloaded DMG
3. Drag **Paste of Shame.app** to your Applications folder
4. Launch from Applications or Spotlight (⌘+Space)
5. Click the 🫥 icon in your menu bar and select **Start Watching**

That's it! You'll get instant notifications when LLM boilerplate is detected in your clipboard.

### 🚀 Auto-Start on Login (Optional)

Make Paste of Shame launch automatically when you log in:

#### **Method 1: System Settings** (Recommended)

<table>
<tr>
<td width="60px" align="center">1️⃣</td>
<td>Open <strong>System Settings</strong> → <strong>General</strong> → <strong>Login Items</strong></td>
</tr>
<tr>
<td align="center">2️⃣</td>
<td>Click the <strong>"+"</strong> button under "Open at Login"</td>
</tr>
<tr>
<td align="center">3️⃣</td>
<td>Select <strong>"Paste of Shame"</strong> from Applications</td>
</tr>
<tr>
<td align="center">✅</td>
<td>Done! The app will now start automatically on every login</td>
</tr>
</table>

#### **Method 2: Terminal Command** (Advanced)

If you have the repository cloned:

```bash
cd /path/to/paste-of-shame
make install-launchagent
```

**To disable auto-start later:**
```bash
make uninstall-launchagent
```

<details>
<summary>💡 What does this do? (click to expand)</summary>

This creates a LaunchAgent plist file at:
```
~/Library/LaunchAgents/com.pasteofshame.app.plist
```

The LaunchAgent tells macOS to automatically launch Paste of Shame when you log in. It's a standard macOS mechanism for background applications.

**To verify it's installed:**
```bash
launchctl list | grep pasteofshame
```

**To manually uninstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.pasteofshame.app.plist
rm ~/Library/LaunchAgents/com.pasteofshame.app.plist
```

</details>

---

**Advanced: Command Line Installation**

<details>
<summary>Install via curl (click to expand)</summary>

```bash
# Download and install latest release
curl -L https://github.com/NoxelS/paste-of-shame/releases/latest/download/PasteOfShame-macOS.dmg -o PasteOfShame.dmg
open PasteOfShame.dmg
# Drag to Applications folder
```

</details>

---

## 🚀 Features

<table>
<tr>
<td width="50%">

### 🔍 Real-Time Monitoring
Watches your clipboard continuously with smart adaptive polling. Zero performance impact.

### 🎯 25+ Detection Patterns
Catches common LLM phrases across multiple categories:
- AI self-identification
- Polite boilerplate ("Certainly!", "Of course!")
- Refusal patterns ("I cannot assist...")
- Code submission markers
- Conclusion phrases

### 🛡️ Smart Suppression
Automatically ignores:
- Quoted text and email replies
- Code blocks and fenced content
- Legitimate documentation

</td>
<td width="50%">

### 🔔 Instant Notifications
Native desktop alerts when LLM content is detected. Configurable sound (silent by default) and visual indicators.

### 📊 Adjustable Sensitivity
Fine-tune detection threshold from 1-60 points to match your workflow. Configure via menu bar or config file.

### 🌍 Native macOS Integration
Beautiful menu bar app with:
- 🟢 Start/Stop watching
- 🎚️ Adjust threshold on-the-fly
- 🔇/🔊 Toggle notification sound
- ⚙️ Open config in your editor
- 🔄 Reload config instantly

### ⚡ Lightning Performance
Scans 100KB text in under 200ms. No AI models, no API calls, no network delays. Pure local pattern matching.

</td>
</tr>
</table>

---

## 🔬 How It Works

<div align="center">
<img src="https://img.shields.io/badge/1-Monitor_Clipboard-blue?style=for-the-badge" alt="Step 1"/>
<img src="https://img.shields.io/badge/2-Pattern_Matching-green?style=for-the-badge" alt="Step 2"/>
<img src="https://img.shields.io/badge/3-Score_Calculation-orange?style=for-the-badge" alt="Step 3"/>
<img src="https://img.shields.io/badge/4-Smart_Filtering-purple?style=for-the-badge" alt="Step 4"/>
<img src="https://img.shields.io/badge/5-Alert_User-red?style=for-the-badge" alt="Step 5"/>
</div>

<br/>

```mermaid
graph LR
    A[Clipboard Change] --> B[Pattern Matching]
    B --> C{Calculate Score}
    C --> D{Score > Threshold?}
    D -->|Yes| E[Check Suppression]
    D -->|No| F[Continue]
    E --> G{Quoted/Code?}
    G -->|No| H[🔔 Alert User]
    G -->|Yes| F
    H --> F
```

### Detection Categories

| Category | Examples | Weight |
|----------|----------|--------|
| 🤖 **AI Self-ID** | "As an AI language model", "I'm Claude/GPT" | High (0.4) |
| 🎭 **Polite Opening** | "Certainly!", "Of course!", "Absolutely!" | Medium (0.3) |
| 🚫 **Refusal** | "I cannot assist", "I'm unable to", "I don't have access" | High (0.35) |
| 📝 **Code Markers** | "Here is the code", "Below is the implementation" | Medium (0.25) |
| 💬 **Encouragement** | "Feel free to ask", "I encourage you to" | Low (0.2) |
| 🎬 **Conclusions** | "In conclusion", "To summarize", "I hope this helps" | Low (0.2) |

**Smart Suppression:**
- Ignores text inside `> quote blocks`
- Skips fenced code blocks (` ``` `)
- Filters legitimate documentation phrases

---

## 📚 Library Usage

Use Paste of Shame in your own Python projects:

```python
from pasteofshame import Detector, RulePack

# Initialize detector
detector = Detector(rule_pack=RulePack.builtin())

# Scan text
result = detector.scan("Certainly! Here is the code you requested.")

# Check results
if result.is_warning:
    print(f"⚠️  Score: {result.total_score}")
    for match in result.matches:
        print(f"  • {match.pattern} (score: {match.score})")
```

**Example Output:**
```
⚠️  Score: 0.55
  • Certainly! (score: 0.3)
  • Here is the code (score: 0.25)
```

---

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/NoxelS/paste-of-shame.git
cd paste-of-shame

# Install dependencies with uv
pip install uv
uv sync

# Run tests
uv run pytest

# Build macOS app (macOS only)
make build-app
make build-dmg
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pasteofshame --cov-report=html

# Performance benchmarks
uv run pytest tests/test_performance.py -v

# Type checking
uv run mypy pasteofshame

# Linting
uv run ruff check pasteofshame
uv run ruff format pasteofshame
```

### Building

```bash
# macOS app bundle
make build-app          # Development build
make build-dmg          # Production DMG installer

# Clean build artifacts
make clean-app
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- 🐛 Report bugs or issues
- 💡 Suggest new detection patterns
- 🔧 Submit pull requests
- 📝 Improve documentation
- ⭐ Star the repository

---

## 📄 License

MIT License - free to use, modify, and distribute.

See [LICENSE](LICENSE) for full details.

---

## 🙏 Acknowledgments

Built with:
- [py2app](https://py2app.readthedocs.io/) - macOS app bundling
- [rumps](https://github.com/jaredks/rumps) - macOS menu bar integration
- [pyperclip](https://github.com/asweigart/pyperclip) - Cross-platform clipboard access
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

Inspired by the need to catch embarrassing AI boilerplate before it reaches production.

---

<div align="center">

### ⭐ Star this repo if it saved you from an embarrassing paste!

Made with ❤️ by [Noel Schwabenland](https://github.com/NoxelS)

[Report Bug](https://github.com/NoxelS/paste-of-shame/issues) • [Request Feature](https://github.com/NoxelS/paste-of-shame/issues) • [Documentation](docs/MACOS_APP.md)

</div>
