# ASTRA-BIO Android (Path 3 — fully offline native app)

A native Android app that embeds the ASTRA-BIO analysis engine **inside the APK**
via [Chaquopy](https://chaquo.com/chaquopy/). The demo analysis runs with **zero
internet** — Python 3.11 + NumPy + SciPy ship with the app.

## What changed vs the web version

| Web (FastAPI) | Android (this app) | Why |
|---|---|---|
| `statsmodels` BH-FDR | hand-rolled `bh_fdr()` in `astra_engine.py` | statsmodels has no Chaquopy build |
| `matplotlib` charts | MPAndroidChart (native Kotlin) | matplotlib doesn't run on Android |
| `httpx` OSDR client | `urllib`-only `osdr_query.py` | httpx not available; stdlib works |
| `pandas` | plain lists/NumPy arrays | smaller APK, faster cold start |

## Requirements

- Android Studio (Ladybug or newer)
- JDK 17 (bundled with Android Studio)
- Android SDK 35 (Studio installs it automatically)
- A device or emulator (arm64 emulator or physical device recommended;
  x86_64 ABI is included so emulators work too)

## Build & run

1. **Open the project folder in Android Studio** — it will sync Gradle and
   download the Python runtime + NumPy + SciPy on first build.
   ⚠️ First build downloads several hundred MB; grab a coffee.
2. Connect a device (enable USB debugging) or start an emulator.
3. Click **Run ▶**.

Command line, if you prefer:

```bash
gradle wrapper            # once, to generate the wrapper jar
./gradlew installDebug    # builds and installs on the connected device
```

Release APK:

```bash
./gradlew assembleRelease
# -> app/build/outputs/apk/release/app-release.apk
```

## App features

- **Run Offline Demo** — full sample-data analysis: 3 phenotypes +
  transcriptomics (8 genes) + proteomics (20 proteins) + metabolomics
  (25 metabolites), with a native bar chart of group means.
- **Pick Earth CSV / Pick Space CSV** — upload your own paired measurements;
  shared numeric columns are compared automatically (Welch t-test, Cohen's d,
  fold change, 95% CI, BH-FDR).
- **OSDR accession lookup** — the only feature requiring internet.

CSV format for uploads:

```csv
growth_rate,MIC,biofilm_biomass
0.41,2.0,0.33
0.45,2.1,0.36
```

Both files must share the same numeric column names. Rows that aren't fully
numeric are skipped.

## APK size & ABI trade-off

Python + NumPy + SciPy add ~40–60 MB per ABI. `app/build.gradle` builds
`arm64-v8a`, `armeabi-v7a`, and `x86_64` (emulator). For the smallest release:

```gradle
ndk { abiFilters "arm64-v8a" }
```

or ship an `.aab` (Google Play) and let Play split per-device.

## Licensing — important before you publish

Chaquopy is free for open-source and non-commercial use; **commercial use
requires a license** from Chaquo Ltd. Review the current terms at
https://chaquo.com/chaquopy/ before distributing on Google Play.
NASA OSDR data are public; ASTRA-BIO code is yours to use as you see fit.

## Project layout

```
app/src/main/python/astra_engine.py   # all statistics (numpy + scipy only)
app/src/main/python/osdr_query.py     # stdlib-only OSDR client (online only)
app/src/main/java/com/astrabio/app/MainActivity.kt
app/build.gradle                      # Chaquopy + pip config lives here
```


## Build the APK without Android Studio (GitHub Actions — easiest)

If you do not want to install Android Studio, use GitHub's free cloud builders:

1. **Create a GitHub repository** (free account at github.com)
2. **Upload this entire `02_Android_App_Chaquopy/` folder** to that repo
3. Go to **Actions** tab → click **"Build ASTRA-BIO APK"** → **Run workflow**
4. Wait ~15 minutes (first run downloads Python + NumPy + SciPy)
5. Download the APK from the **Artifacts** section:
   - `astra-bio-debug-apk` → `app-debug.apk` (install and test)
   - `astra-bio-release-apk` → `app-release-unsigned.apk` (unsigned release)

### If gradlew is missing

The `gradlew` script may not be in the zip. Fix it locally or in CI:

```bash
# Option A: locally (needs gradle installed)
bash generate-wrapper.sh

# Option B: the GitHub Actions workflow handles it automatically
```

### Install the APK on your phone

```bash
# Enable USB debugging on your phone, then:
adb install app/build/outputs/apk/debug/app-debug.apk

# Or transfer the file to your phone and tap it to install
# (you may need to allow "Install from unknown sources")
```
