# Android YouTube Transcript Downloader

This is the Android version of the YouTube Transcript Downloader app.

## Requirements

- Android Studio Otter | 2025.2.1 Patch 1 or higher
- Android SDK 26+ (Android 8.0 Oreo or higher)
- Kotlin 2.1.0
- Gradle 8.7.3

## Features

- Download transcripts from YouTube videos and playlists
- Material Design 3 UI
- Select starting video for playlists
- Real-time progress tracking
- Saves transcripts to Downloads/YouTubeTranscripts folder
- 5-second rate limiting to prevent IP blocking

## Setup

1. Open Android Studio
2. Click "Open an Existing Project"
3. Navigate to the `android-app` folder
4. Wait for Gradle sync to complete
5. Run on an emulator or physical device

## Building

### Debug Build
```bash
./gradlew assembleDebug
```

### Release Build
```bash
./gradlew assembleRelease
```

## Permissions

The app requires:
- INTERNET - To fetch YouTube data and transcripts
- WRITE_EXTERNAL_STORAGE - To save transcript files (Android 10 and below)

## Usage

1. Launch the app
2. Paste a YouTube video or playlist URL
3. Tap "Load" to fetch video information
4. For playlists, select which video to start from
5. Tap "Start Download" to begin downloading transcripts
6. Files are saved to Downloads/YouTubeTranscripts folder

## Technical Details

- **Language**: Kotlin
- **Min SDK**: 26 (Android 8.0)
- **Target SDK**: 35 (Android 15)
- **Architecture**: MVVM with Coroutines
- **Networking**: OkHttp, Retrofit
- **UI**: Material Design 3, View Binding
- **HTML Parsing**: JSoup

## Notes

- The app implements a 5-second delay between transcript downloads to avoid YouTube rate limiting
- Transcripts are only available for videos with captions enabled
- The app uses web scraping to fetch data, which may break if YouTube changes its HTML structure

## License

MIT License
