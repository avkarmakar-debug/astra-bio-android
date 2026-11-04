# Build the ASTRA-BIO APK — Step by Step

## Fastest path: GitHub Actions (no local tools needed)

### Step 1: Push to GitHub

1. Go to [github.com](https://github.com) and create a free account
2. Click **New Repository** → name it `astra-bio-android` → make it public → **Create**
3. On your computer, unzip the Android project folder
4. Open a terminal in that folder and run:

```bash
git init
git add .
git commit -m "Initial ASTRA-BIO Android app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/astra-bio-android.git
git push -u origin main
```

(Replace `YOUR_USERNAME` with your actual GitHub username.)

### Step 2: Trigger the build

1. In your browser, go to `https://github.com/YOUR_USERNAME/astra-bio-android`
2. Click the **Actions** tab at the top
3. Click **"Build ASTRA-BIO APK"** on the left
4. Click the **Run workflow ▾** button → **Run workflow**
5. Wait. The first build takes 15–25 minutes because GitHub downloads the Android SDK, Python runtime, NumPy and SciPy.

### Step 3: Download the APK

1. When the workflow finishes (green checkmark), click it
2. Scroll down to **Artifacts**
3. Download `astra-bio-debug-apk`
4. Unzip it — you get `app-debug.apk`

### Step 4: Install on your phone

1. Transfer `app-debug.apk` to your phone (email, Google Drive, USB cable, etc.)
2. On your phone, open the file
3. You may see "Install unknown apps" — allow it for your file manager/browser
4. Tap **Install**
5. Open the app — rocket icon, dark theme, "ASTRA-BIO"

Tap **"▶ Run Offline Demo"** — it works with zero internet.

---

## Alternative: Build locally with Android Studio

1. Download and install [Android Studio](https://developer.android.com/studio)
2. Open the project folder (`02_Android_App_Chaquopy/`)
3. Wait for Gradle sync (first time: several hundred MB download, 10–20 min)
4. Connect your phone with USB debugging enabled
   - Or start an emulator: Tools → Device Manager → Create Device
5. Click **Run ▶** (green triangle)
6. The app installs and launches automatically

---

## Alternative: Build locally with command line (needs Android SDK)

```bash
# If gradlew is missing, generate it first:
gradle wrapper --gradle-version 8.9

# Then build:
./gradlew assembleDebug

# APK will be at:
# app/build/outputs/apk/debug/app-debug.apk
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "gradlew: command not found" | Run `gradle wrapper --gradle-version 8.9` first, or use GitHub Actions |
| "Could not find com.chaquo.python" | Check internet connection; Chaquopy downloads from its Maven repo |
| Build takes forever | Normal for first build — Python + NumPy + SciPy are large |
| "App not installed" on phone | Uninstall any previous version first; or check "Install unknown apps" permission |
| GitHub Actions fails | Check the build log — usually a network timeout on first run; just re-run |
