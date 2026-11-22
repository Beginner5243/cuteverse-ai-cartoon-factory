# CUTEVERSE AI CARTOON FACTORY

Zero-budget (₹0), mobile-browser-friendly cartoon video pipeline using GitHub Actions, Python, Pillow, FFmpeg, and `edge-tts`, supporting English (`en`), Hindi (`hi`), and Gujarati (`gu`) in vertical `1080x1920` (9:16, 30 FPS, H.264) MP4 format.

## Acceptance Test Checklist
1. Open the repository on GitHub in your mobile browser.
2. Go to **Actions** → **CuteVerse Cartoon Pipeline** → **Run workflow**.
3. Run with `episode=1`, `language=en`, `duration=30`.
4. Download the `cuteverse-ep-001-en` artifact and verify `output/videos/ep_001_en.mp4`, `output/subtitles/ep_001_en.srt`, `output/thumbnails/ep_001_en.jpg`, `episodes/scripts/ep_001_en_script.txt`, `episodes/storyboards/ep_001_en_storyboard.json`, `output/logs/ep_001_en.log`, and `output/reports/ep_001_en_quality.json`.
5. 
