"""
py2app build configuration for Nexus.app bundle.
Run: python setup.py py2app
Produces: dist/Nexus.app

After building, ad-hoc sign for sideloading:
  codesign --sign - --force --deep dist/Nexus.app

Users installing without Apple Developer signing:
  sudo xattr -rd com.apple.quarantine /Applications/Nexus.app
  open /Applications/Nexus.app
"""
from setuptools import setup

APP = ["nexus/main.py"]
DATA_FILES = [("resources", ["resources/Info.plist"])]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/AppIcon.icns",
    "plist": {
        "CFBundleName": "Nexus",
        "CFBundleDisplayName": "Nexus",
        "CFBundleIdentifier": "ai.nexus.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "LSMinimumSystemVersion": "14.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,
        "NSScreenCaptureUsageDescription": (
            "Nexus needs screen capture access to see what's on your screen and automate tasks."
        ),
        "NSAccessibilityUsageDescription": (
            "Nexus needs Accessibility access to read and interact with UI elements across all apps."
        ),
    },
    "packages": [
        "nexus",
        "anthropic",
        "ollama",
        "PyQt6",
        "pyautogui",
        "mss",
        "PIL",
        "sqlalchemy",
        "pynput",
        "AppKit",
        "Foundation",
        "ApplicationServices",
        "Quartz",
        "objc",
    ],
    "excludes": ["tkinter", "test", "unittest"],
}

setup(
    name="Nexus",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
