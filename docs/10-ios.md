# 10 — iOS and iPadOS, targeting an M4 iPad Pro

Research started 2026-11-19, while Phases 11–14 are still open. The
owner asked whether an iOS port is possible. They want an IPA for
sideloading, not an App Store release. The test device is an **M4 iPad
Pro**. The owner prefers to do as much as possible on the MacBook Air
(M5) to keep code signing out of the way.

Claims not yet checked on the iPad, the Mac or in the code are marked
**hypothesis**. This survey was written on the Windows test PC from the
docs, the fork's sources and published reports, without an iOS build.

## The target

| | iPad Pro (M4) | MacBook Air (M5) | AYN Thor Max |
|---|---|---|---|
| CPU | Apple M4, arm64 only | Apple M5, arm64 only | Snapdragon 8 Gen 2, arm64 |
| GPU | Apple GPU (Metal, MoltenVK) | Apple GPU (Metal, MoltenVK) | Adreno 740 |
| Memory | 8 GB (256/512 GB models) or 16 GB (1/2 TB) | 24 GB | 16 GB |
| Screen | 11″ or 13″ OLED, 120 Hz ProMotion, about 1.43:1 | 15.3″ Retina | 1920×1080, 120 Hz |
| OS | iPadOS 26 | macOS 27 | Android 13 |
| Host page size | 16 KiB (**hypothesis**, as on every arm64 Apple OS) | 16 KiB | 4 KiB |

What differs from the earlier targets:

1. **No JIT for sideloaded apps.** iOS gives an app executable memory it
   writes itself only when a debugger is attached (StikDebug and
   similar), and iOS 26 restricts even that on newer devices. Emulators
   that depend on a JIT, upstream Vita3K's among them, are stuck there.
   **This port doesn't need one** (below).
2. **Only signed code in the bundle runs.** An app can `dlopen` a
   library only if it is inside the app and signed with it. Android's
   way of copying modules in after install (14d) doesn't exist here.
3. **No compiler, Python or shell on the device**, as on Android.
4. **Per-app memory limits** and a capped virtual address space. Both
   can be raised by entitlements, which depend on the kind of Apple ID
   that signs the app.
5. **Signing expires.** A free Apple ID signs for 7 days and allows 3
   sideloaded apps at once. A paid developer account ($99 a year) signs
   for a year.

## Why it is possible: no JIT needed

* D11: every thread runs on recompiled code (NativeCPU).
  `VITA3K_DYNARMIC=OFF` builds the frontend with no dynarmic at all.
  Phase 6's exit was met with that build: a quest from the player's own
  dump, 0 JIT instructions.
* 08-macos: the map sweep on the M5, all 50 maps on native code, 0
  calls from recompiled code back to the JIT.
* The arm64 Apple work is done:
  * the modules compile for arm64 with zig (D21), and 23,280 + 684
    dynarmic tests pass on arm64 hosts;
  * write tracking handles 16 KiB host pages;
  * MoltenVK works with `double-buffer` mapping;
  * real-time threads fixed frame pacing.
* Android (D25) worked out the "a PC builds the modules" model and the
  frontend's glue for a platform without an executable in a folder.

What a no-JIT build gives up: no fallback. The 17 font functions whose
NEON forms the translator lacks (D11) would stop the game if one ever
ran. None has in any session so far. The firmware ELF dump
(`--dump-elfs`) needs the JIT, but it runs on the PC during the setup,
as now.

## What the code needs (survey 2026-11-19)

| Component | State | Work |
|---|---|---|
| Fork, iOS | no iOS code (matches for `IOS` are only Android build leftovers) | a CMake `iOS` branch for `add_game`, SDL3's UIKit entry point, an app bundle with `Info.plist`, built without dynarmic |
| Dependencies | Boost, OpenSSL, curl built from source for Android (14b) | the same for `arm64-apple-ios`; MoltenVK's iOS framework (**hypothesis**: upstream's macOS MoltenVK setup covers iOS with its iOS build) |
| Audio (cubeb) | AudioUnit backend on macOS | **hypothesis**: works on iOS, with an `AVAudioSession` category set |
| Guest memory (`mem/src/mem.cpp`) | reserves `TOTAL_MEM_SIZE = GiB(4)` with `mmap`, `1 << 34` as a hint | **the main risk**: whether iOS grants a 4 GiB reservation, with or without the entitlements (below) |
| Write tracking | `PROT_NONE` faults, 16 KiB pages handled (08-macos) | **hypothesis**: as on macOS. Debugging gets awkward: an attached debugger stops on every tracked write |
| Renderer | MoltenVK on the M5: raster order groups for programmable blending, `double-buffer` mapping | **hypothesis**: the M4's GPU is the same family as the M5's and renders as the Mac does |
| AOT loader | `dlopen` (POSIX) | the modules inside the bundle (`Frameworks/`), signed with the app |
| Paths | everything next to the executable (D22); Android: the app's folders | the app's `Documents/` for `ss-delta.ini`, the log, the shader cache and `fs/`. `UIFileSharingEnabled` and `LSSupportsOpeningDocumentsInPlace` make it visible in Finder and Files |
| Importer | the kit's Python setup | not on the device: the frontend reports what's missing, as on Android |
| Lifecycle | Android pauses on `onPause` (14d) | stop rendering when the app goes to the background: iOS kills apps that use the GPU there |
| Controls | SDL3 gamepads, touch as the front touch | gamepads through the Game Controller framework (SDL3), the Magic Keyboard, touch. A touch-only player needs on-screen controls (to design) |
| Ad Hoc Play | `local` and `lan` modes | `lan` needs the Local Network permission (`NSLocalNetworkUsageDescription`), as on macOS |
| Frame pacing | real-time threads on macOS (fork `09587ca1`) | **hypothesis**: the same Mach thread policy works on iOS. 60 fps is every second refresh at 120 Hz |

### The modules for iOS

* The modules import only `abort` and `sched_yield` and export only
  `armrecomp_aot_init` (D25). **Hypothesis**: zig (`aarch64-ios`) builds
  them without Apple's SDK, using the Android trick: zig's macOS libc
  headers (the same ABI for those functions) and a hand-written
  `libSystem.tbd` stub marked as iOS. The `LC_BUILD_VERSION` platform
  must be iOS, or dyld refuses to load the library.
* Fallback: Xcode's clang on a Mac.
* Unwind tables are needed, because escapes throw C++ exceptions through
  module frames (as on every host).

## Getting the modules into the IPA (D2, D18)

A release can't contain the modules (D2), and iOS loads only code signed
inside the bundle. The proposed flow for players:

1. The release ships a **base IPA**: the frontend, with no game code.
2. The setup on the player's PC or Mac builds the modules for iOS from
   their dump, as for Android, and puts them into
   `Payload/<app>.app/Frameworks/`. That makes a personal IPA.
3. A sideloader (AltStore, SideStore, Sideloadly) re-signs the whole
   bundle with the player's Apple ID and installs it.

**Hypotheses to check**: the sideloaders sign loose `.dylib` files in
`Frameworks/`, or each module has to be wrapped as a `.framework`; a
~100 MB eboot module is no problem for them.

The game data (about 3.2 GB) stays out of the IPA. The player copies it
into the app's `Documents/` through Finder or Files. **Hypothesis**: it
survives the weekly re-sign as long as the bundle ID stays the same.

## Memory and entitlements

* `com.apple.developer.kernel.increased-memory-limit` raises the per-app
  memory limit. Reportedly Apple grants it to free teams too. SideStore
  drops it when signing with a free Apple ID, while AltStore 2.3 and
  later reportedly keeps it.
* `com.apple.developer.kernel.extended-virtual-addressing` raises the
  address-space cap. Reportedly it is for paid accounts only.
* Whether the 4 GiB guest reservation fits without the second one decides
  whether a free Apple ID is enough. Answer it first, on the iPad, with a
  small test app.
* The game's resident memory has never been measured on any platform.
  Measure it on the Mac first. Which iPad model (8 or 16 GB) is used
  matters for the limit.

## Developing on the Mac (the owner's choice)

The Mac does the builds and drives the iPad. During development, the
Mac's Xcode signs and installs, so no sideloader is involved. Sideloaders
only matter for the player-facing release.

* **Xcode** (the full app, not only the Command Line Tools) for the iOS
  SDK and the Simulator. Builds run headless over SSH with
  `xcodebuild`.
* **The iOS Simulator** for most of the porting: CMake, the UIKit entry
  point, paths, loading the modules, booting to the title and a quest on
  native code, file sharing, the lifecycle. It needs no Apple ID and is
  driven over SSH with `xcrun simctl` (install, launch, screenshots,
  files in the app's container). The modules are then built for the
  Simulator platform. It doesn't show memory limits, real performance or
  exact rendering (**hypothesis**: its Metal lacks some features).
* **Optional**: the same iOS build as a "Designed for iPad" app on the
  Mac itself, on the M5's real Metal (**hypothesis**: works with a free
  team).
* **The iPad** for what only it answers: the address-space reservation,
  the memory limit, rendering and performance, touch, thermals.
  `xcrun devicectl` installs, launches, and copies files into and out of
  the app's container over a cable or Wi-Fi. It is the counterpart of
  `adb` for the Thor, and the game data goes over the same way.
* **Free Apple ID**: each install expires after 7 days. Installing again
  from the Mac fixes it (one command), and the app's data stays.
  **Hypothesis**: signing over SSH needs the login keychain unlocked
  first (`security unlock-keychain`).

What the owner does once, on the Mac's screen:

1. Install Xcode, then the iOS platform
   (`xcodebuild -downloadPlatform iOS` works over SSH).
2. Xcode → Settings → Accounts: add an Apple ID. This creates the
   personal team and the development certificate.
3. Connect the iPad over USB-C and trust the Mac. Turn on Developer Mode
   on the iPad (Settings → Privacy & Security; it appears after the first
   Xcode connection and needs a restart).

## Next steps

Phase 15 in [03-plan](03-plan.md), in this order:

1. Without the iPad: measure the game's resident memory on the Mac; build
   a zig `aarch64-ios` module against a stub `.tbd`.
2. Xcode on the Mac. A test app that reserves memory as `mem.cpp` does,
   installed on the iPad with and without `increased-memory-limit`.
3. The fork for the iOS Simulator, no dynarmic: title, then a quest on
   native code.
4. On the iPad: ST03A on native code, then the map sweep against
   Windows' pictures.
5. The base IPA in CI, the setup's IPA step, the sideloaders checked.
6. Touch and on-screen controls, the lifecycle, 120 Hz, thermals.

Sources for the entitlement and JIT reports (2025–2026, not checked
here):
[SideStore issue #1616](https://github.com/SideStore/SideStore/issues/1616),
[NX2Apple's ENTITLEMENTS.md](https://github.com/LNPANDY/NX2Apple/blob/main/ENTITLEMENTS.md),
[the libretro forum on JIT in iOS 26](https://forums.libretro.com/t/what-is-the-current-situation-with-ra-on-ios-26-and-jit-support/49244),
[StikDebug](https://github.com/StephenDev0/StikDebug).
