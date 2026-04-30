# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Web Scraping Protocol (per Callunk)

When asked to scrape/extract data from any website, ALWAYS use the **stealth-browser + Tavily search combo**:
1. **Tavily Search** first — to find relevant pages, URLs, and summary info
2. **Stealth Browser** (puppeteer-extra + stealth plugin) — to access blocked/protected sites and extract detailed data
3. Cross-reference results from both for completeness

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
