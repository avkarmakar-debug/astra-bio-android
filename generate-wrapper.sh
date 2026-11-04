#!/bin/bash
# Generate Gradle wrapper (needed if gradlew is missing).
# Run this once before building locally or pushing to GitHub.

echo "Generating Gradle wrapper..."
gradle wrapper --gradle-version 8.9

echo "Done. You can now run:"
echo "  ./gradlew assembleDebug    # debug APK"
echo "  ./gradlew assembleRelease  # release APK"
