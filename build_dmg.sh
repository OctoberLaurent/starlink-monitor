#!/bin/bash
# Build a distribution DMG for StarlinkMonitor.app
set -e
cd "$(dirname "$0")"

APP="dist/StarlinkMonitor.app"
DMG="dist/StarlinkMonitor.dmg"
VOL="Starlink Monitor"
STAGING="$(mktemp -d -t starlinkdmg)"
echo "Staging: $STAGING"

cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

# Background + layout via AppleScript (optional, default icon layout otherwise)
mkdir -p "$STAGING/.background"
cp icon.png "$STAGING/.background/background.png"

# Create a read-write DMG, then convert to a compressed one.
hdiutil create -volname "$VOL" -srcfolder "$STAGING" \
    -ov -format UDRW "$DMG.tmp.dmg"

# Window customization (best-effort, non-fatal)
MOUNT=$(hdiutil attach "$DMG.tmp.dmg" -readwrite -nobrowse | grep -o '/Volumes/.*' | head -1)
echo "Mounted at: $MOUNT"

osascript <<EOF || echo "(Finder customization skipped)"
tell application "Finder"
  set dmg to disk "$VOL"
  open dmg
  set current view of container window of dmg to icon view
  set bounds of container window of dmg to {100, 100, 760, 500}
  set position of item "StarlinkMonitor.app" of dmg to {160, 180}
  set position of item "Applications" of dmg to {500, 180}
  close dmg
end tell
EOF

# Let Finder save the layout
sleep 2
hdiutil detach "$MOUNT" -force || true

# Convert to compressed (UDZO) — final DMG
rm -f "$DMG"
hdiutil convert "$DMG.tmp.dmg" -format UDZO -imagekey zlib-level=9 -o "$DMG"
rm -f "$DMG.tmp.dmg"
rm -rf "$STAGING"

echo "✅ DMG created: $DMG"
du -sh "$DMG"