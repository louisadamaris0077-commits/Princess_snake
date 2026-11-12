# PRINCESS SNAKE

A Kivy swipe-controlled snake game with a procedurally generated original Afro-inspired instrumental loop and eating sound effect.

## Files
- `main.py` — complete game
- `buildozer.spec` — Android packaging settings
- `.github/workflows/build-android.yml` — GitHub Actions APK build

## Build on GitHub
1. Upload the contents of this folder to a GitHub repository (keep `.github/workflows/build-android.yml` at that exact path).
2. Open the repository's Actions tab.
3. Select "Build Android APK".
4. Choose "Run workflow".
5. When successful, download the `princess-snake-apk` artifact and extract the APK from the ZIP.

The first Android build can take a while. The workflow creates a debug APK for testing and sharing.
