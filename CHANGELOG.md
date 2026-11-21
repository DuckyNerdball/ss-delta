# Changelog

The changes in each release of ss-delta. The downloads and each release's
full notes are on the [releases page](https://github.com/vita-recomps/ss-delta/releases);
[INSTALLING](docs/INSTALLING.md#updating) explains how to update.

## 0.4.1 (2026-11-21)

### Fixed

* **Windows: the setup stopped with "msiexec failed (1639)"** when the
  temp folder's path has a space, as under a Windows user name with a
  space. Windows Installer refused the folder the setup unpacks the Windows
  SDK into. One cause of
  [#9](https://github.com/vita-recomps/ss-delta/issues/9), possibly not the
  only one. Linux, macOS and Android are the same as 0.4.0.

## 0.4.0 (2026-11-21)

### New

* **Android:** an APK for Android 9 or newer on 64-bit ARM with Vulkan, made
  for Snapdragon handhelds (tested on an AYN Thor). Its setup screen builds
  the game on the device from your dump, with no PC: it downloads the
  firmware from Sony and compiles the native code with its own compiler, in
  about 15 minutes on a Snapdragon 8 Gen 2. After an app update it builds
  again by itself, without asking for the dump. On Adreno GPUs it offers to
  download Turnip. It has on-screen controls for phones without a gamepad,
  with a LOCK toggle for the lock-on. `ss-delta.exe --android` puts a game
  built on a PC on a device. The APK is signed with the project's release
  key, so later versions install over it.
* **Cheats** ([#7](https://github.com/vita-recomps/ss-delta/issues/7)) on
  every platform, on the settings menu's Cheats page: Infinite health,
  Unlimited offerings, Lasting offerings, One-hit kills, Max Lacrima and Max
  levels.
* **The Japanese Voice-over Pack**
  ([#8](https://github.com/vita-recomps/ss-delta/issues/8)), the game's
  separate PSN add-on, installs as an add-on. Once the game is built, an
  add-on goes in on its own without building again: `--dump`, the
  importer, **Add an add-on** on Android, or RecompLauncher's Add-ons step.
* **rePatch mods, such as the Undub patch**
  ([#8](https://github.com/vita-recomps/ss-delta/issues/8)), for Japanese
  voices from the start. They are kept beside the game, and **Mods
  (rePatch)** on the settings menu turns them off.
* **Xbox button labels** in the game's prompts, tutorial pictures and text
  (Button prompts), following your gamepad bindings.
* **Mouse camera** on Windows, Linux and macOS: Tab or a middle click
  captures the cursor and the mouse turns the camera (the Mouse page:
  Sensitivity, Invert vertical).
* **Skip intro logos**
  ([#6](https://github.com/vita-recomps/ss-delta/issues/6)), off by
  default: the game opens on its title screen after about 6 seconds instead
  of 20.

### Fixed

* A dump that holds only the 1.30 update
  ([#5](https://github.com/vita-recomps/ss-delta/issues/5)): the setup
  now stops before the downloads and says what to give it, instead of
  failing at the end with "Install app before patch".
* The settings menu's page names ran into each other in its tab bar.
* The settings menu froze when opened over one of the system's dialogs
  (the save list, "Do you want to load this saved data?").

## 0.3.1 (2026-11-19)

### New

* **RecompLauncher:** every release carries a `recomplauncher.json`, so
  [RecompLauncher](https://recomplauncher.com) can install the game, build
  it from your dump, show its main settings, back up the saves and rebuild
  after an update.
* **Exit from a gamepad:** the settings menu's last page, Exit.
* **`--progress`:** progress lines while building, for a launcher's
  progress bar.

### Fixed

* Laptops with an AMD and an NVIDIA GPU
  ([#4](https://github.com/vita-recomps/ss-delta/issues/4)): the build
  could stop near the end with "LoadLibrary failed with error 87". The
  game asks for the dedicated GPU again.

## 0.3.0 (2026-11-18)

### New

* **Linux and the Steam Deck:** a native `ss-delta.x86_64`, built in the
  Steam Runtime SDK; the importer can add the game to Steam. Quests run at
  60 fps on the Deck.
* **macOS on Apple Silicon:** a native app on Metal (MoltenVK), at 60 fps
  on all 50 quest maps; Game Mode in fullscreen.
* **Ad Hoc Play across platforms:** Windows, Linux and macOS copies play
  together over a LAN, with any of them as host.
* **One program, one folder:** the download is the game's folder. It
  builds itself from your dump the first time it starts, and keeps
  everything inside its folder (the separate setup of 0.1 and 0.2 is gone).
* **A command line for everything:** `--dump`, `--install`, `--build-only`,
  `--game`, `--add-to-steam`, `--fullscreen`/`--windowed`, `--set`.
* The importer reads your dump and doesn't ask again for what it already
  holds (the 1.30 update, the licence).

### Fixed

* Keyboard diagonals ran about 1.4 times as fast as straight movement.
* A room hosted over Wi-Fi (a Steam Deck or a Mac) couldn't be joined.
* Linux and macOS: "A network error has occurred" after leaving a room,
  and menus that stopped responding on macOS.
* Windows: downloads failed on PCs where Python couldn't check a server's
  certificate.

## 0.2.1 (2026-11-17)

### New

* **Language setting**
  ([#3](https://github.com/vita-recomps/ss-delta/issues/3)) on the
  settings menu's Game page: English, French, Spanish and Portuguese
  (Brazil) in the US game; English, French, Spanish, German and Italian in
  the EU game.

## 0.2.0 (2026-11-17)

### New

* **The EU version**
  ([#2](https://github.com/vita-recomps/ss-delta/issues/2)), PCSF00532
  at update 1.30. It is the same build as the US game, so the same
  recompiled code serves both.

## 0.1.0 (2026-11-16)

The first release
([#1](https://github.com/vita-recomps/ss-delta/issues/1)), for Windows: a
setup (`setup.bat`) that builds a playable folder from your own dump of
the US game (PCSA00152, update 1.30).

* The game's code, and the firmware modules it loads, recompiled ahead of
  time to C++ and run natively, without a JIT.
* 60 fps with the game's speed kept, and the 3D at full resolution
  (960×544 times the resolution multiplier).
* Rendering fixes, among them the white floors on NVIDIA GPUs.
* Ad Hoc Play for up to four copies, on one PC or across a LAN.
* The add-ons' content unlocked.
* An in-game settings menu, a commented `ss-delta.ini`, and Vita saves
  imported and exported.
