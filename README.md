# Bevy in App

Integrate the [Bevy engine](https://github.com/bevyengine/bevy) into existing iOS | Android apps.

If you want to add a mini-game to an existing app, or implement some dynamic UI components, charts ..., or just want to take advantage of the **Motion Sensors** on your phone for some cool gameplay, you can't use `WinitPlugin`. Because `winit` will take over the entire app initialization process and windowing, but we need to create `bevy::App` in an existing app instance, and we may also want `bevy::App` to run in an `iOS UIView` or `Android SurfaceView` of any size.

This repository implements such a scenario and uses the phone's motion sensor to play breakout mini-games.

## Screenshot

| ![Bevy in iOS App](assets/bevy_in_ios.png) | ![Bevy in Android App](assets/bevy_in_android.png) |
| ------------------------------------------ | -------------------------------------------------- |

## Development and Building

Two python scripts are provided to help during developing and building.

### config.py

This script will configure the `.cargo/config.toml` file with the correct settings to build for iOS, Android or native using just `cargo build --lib`.  As an added bonus any IDEs you use (tested with CLion and VSCode) will also pick-up these settings and it will allow them to highlight any code that is protected by target- or arch-`#[cfg(...)]` statements.

### build.py

This script is designed to be called from Xcode or Android Studio to build the game library as a dependency.

## Android Set-up

### Set up Android environment

Assuming your computer already has Android Studio installed, go to `Android Studio` > `Tools` > `SDK Manager` > `Android SDK` > `SDK Tools`. Check the following options for installation and click OK.

- [x] Android SDK Build-Tools
- [x] Android SDK Command-line Tools
- [x] NDK (Side by side)

Then, set the following environment variable:

```sh
export NDK_HOME=/path/to/android_sdk/ndk/23.1.7779620
```
