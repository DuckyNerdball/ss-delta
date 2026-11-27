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

What a no-JIT build gives up: no fallback if unmapped code ever ran (all
ten modules have 0 functions left to the JIT; [05-recompiler](05-recompiler.md)).
The firmware ELF dump (`--dump-elfs`) needs the JIT, but it runs on the PC
during the setup, as now.

## What the code needs (survey 2026-11-19)

| Component | State | Work |
|---|---|---|
| Fork, iOS | no iOS code (matches for `IOS` are only Android build leftovers) | a CMake `iOS` branch for `add_game`, SDL3's UIKit entry point, an app bundle with `Info.plist`, built without dynarmic |
| Dependencies | Boost, OpenSSL, curl built from source for Android (14b) | the same for `arm64-apple-ios`; MoltenVK's iOS framework (**hypothesis**: upstream's macOS MoltenVK setup covers iOS with its iOS build) |
| Audio (cubeb) | AudioUnit backend on macOS | **hypothesis**: works on iOS, with an `AVAudioSession` category set |
| Guest memory (`mem/src/mem.cpp`) | reserves `TOTAL_MEM_SIZE = GiB(4)` with `mmap`, `1 << 34` as a hint | **the main risk**: whether iOS grants a 4 GiB reservation, with or without the entitlements (below) |
| Write tracking | `PROT_NONE` faults, 16 KiB pages handled (08-macos) | **hypothesis**: as on macOS. Debugging gets awkward: an attached debugger stops on every tracked write |
| Renderer | MoltenVK on the M5: raster order groups for programmable blending, `double-buffer` mapping | **hypothesis**: the M4's GPU is the same family as the M5's and renders as the Mac does |
| AOT loader | `dlopen` (POSIX) | the modules inside the bundle, signed with the app. At the app's root rather than in `Frameworks/`, as SunPad does: LiveContainer can't load an app with a `Frameworks/` folder (DiOShonored's notes) |
| Paths | everything next to the executable (D22); Android: the app's folders | the app's `Documents/` for `ss-delta.ini`, the log, the shader cache and `fs/`. `UIFileSharingEnabled` and `LSSupportsOpeningDocumentsInPlace` make it visible in Finder and Files |
| Importer | the kit's Python setup | not on the device: the frontend reports what's missing, as on Android |
| Lifecycle | Android pauses on `onPause` (14d) | stop rendering when the app goes to the background: iOS kills apps that use the GPU there |
| Controls | SDL3 gamepads, touch as the front touch, Android's touch on-screen controls (`game-frontend`, 14f) | gamepads through the Game Controller framework (SDL3), the Magic Keyboard, touch, and adapting the shared on-screen controls for iPad aspect ratios |
| Ad Hoc Play | `local` and `lan` modes | `lan` needs the Local Network permission (`NSLocalNetworkUsageDescription`), as on macOS |
| Frame pacing | real-time threads on macOS (fork `09587ca1`) | **hypothesis**: the same Mach thread policy works on iOS. 60 fps is every second refresh at 120 Hz |

### The modules for iOS

* The modules import only `abort`, `sched_yield` and `powf` (where
  overrides use `<cmath>`) and export only `armrecomp_aot_init` (plus
  `armrecomp_aot_features` when overrides are active; D25, D30). They need
  a compiler for `aarch64-ios`, a
  few C headers, a Mach-O linker and a `libSystem.tbd` stub marked as
  iOS. The `LC_BUILD_VERSION` platform must be iOS, or dyld refuses to
  load the library.
* Two projects already do this off the Mac (survey below):
  * LASRecomp: zig (`zig cc -target aarch64-ios.16.4`) with zig's Darwin
    headers, linked by **rust-lld** (`-flavor darwin -platform_version
    ios`, `-undefined dynamic_lookup`), pinned per host, with a committed
    `libSystem.B.tbd`;
  * PadMint: upstream LLVM 21 (`clang`, `ld64.lld`) with a sysroot built
    from **Apple's open-source headers** (apple-oss-distributions Libc,
    xnu, libpthread and others, pinned) and generated `.tbd` stubs.
* **To decide in 15a**: whether zig's own Mach-O linker links an iOS
  dylib (it does for macOS, D21; LASRecomp chose rust-lld without saying
  why), and where the headers come from. PadMint rejected Apple's SDK
  off a Mac on licence grounds. **Hypothesis**: zig's Darwin headers come
  from Apple's SDK, which raises the same question; check before relying
  on them. Our modules need very few headers, so the open-source set is
  small.
* Fallback for development: Xcode's clang on the Mac.
* Unwind tables are needed, because escapes throw C++ exceptions through
  module frames (as on every host).

## Getting the modules into the IPA (D26)

A release can't contain the modules (D2), and iOS loads only code signed
inside the bundle. So a playable IPA exists only after the player's own
setup has built the modules, and an IPA in the release would be useful
only as an input to that setup. The flow ([D26](decisions.md)):

1. CI (GitHub's macOS runners) builds the **base app**: the frontend with
   no game code, unsigned except for an ad hoc signature on its
   executable that carries the entitlements, so sideloaders pick them up
   (as SpeedBreaker, MHGURecomp and LASRecomp do). It is a release asset,
   not something players download by hand.
2. The **desktop setup** (Windows, Linux or macOS, the D22 folders) has an
   iOS output. It downloads the base app pinned by SHA-256 (as it pins
   zig and the firmware), builds the modules from the player's dump, puts
   them into the bundle and writes an **unsigned IPA**.
3. The player installs it with a sideloader (AltStore Classic, SideStore,
   Sideloadly), which signs the whole bundle with their Apple ID. The same
   IPA serves every weekly re-sign; the setup runs again only when the
   game or the port changes.

The setup signs nothing and never sees the player's Apple ID. A player
with a paid account can sign it themselves (zsign or codesign).

**Hypotheses to check**: the sideloaders sign loose `.dylib` files at the
app's root (SunPad's layout suggests so); a ~100 MB eboot module is no
problem for them; AltStore Classic keeps `increased-memory-limit` with a
free Apple ID while SideStore 0.7 drops it (LASRecomp's table).

The game data (about 3.2 GB) stays out of the IPA. The player copies it
into the app's `Documents/` through Finder, Apple Devices on Windows, or
Files (a USB-C drive works too). **Hypothesis**: it survives the weekly
re-sign as long as the bundle ID stays the same.

## How other recomps ship for iOS (survey 2026-11-19)

Read from their READMEs, workflows, scripts and release notes; no IPA was
downloaded or run. Stars and dates as of 2026-11-19.

**No game code distributed** (D2's constraint):

* **LASRecomp** (Link's Awakening, Switch; PR #238, merged 2026-11-11):
  "No game code ships, and on iOS that means no public `.ipa` at all."
  * The release carries an iOS kit (`.laskit`): an unsigned base app
    built on a Mac, zig, rust-lld (pinned per host), zig's Darwin headers
    and a committed `libSystem.B.tbd`. The kit refuses a kit from another
    release.
  * The desktop program (`--build-ios`, or a page in its window) on
    Windows, Linux or macOS generates the game code, compiles one dylib
    and writes an unsigned IPA to Downloads.
  * Only `increased-memory-limit` ("free with any team"); extended
    virtual addressing deliberately not requested. Their table of what
    keeps the memory entitlement with a free account: AltStore Classic
    2.2+ and Impactor yes, an Xcode Personal Team yes, SideStore 0.7 no.
  * Game files over Finder, Apple Devices or a USB-C drive. Tested on an
    iPhone 15 Pro, an iPhone 17 and an M4 iPad Pro (iOS 27.0.1).
* **PadMint** (the builder for about 34 ports by one author: KartPad,
  BlueWake, SunPad, SnapPad, HarkinianPad and others):
  * each game's release publishes an unsigned engine IPA with no game
    code;
  * PadMint, on the player's computer, compiles only the game-derived
    code into one dylib (upstream LLVM 21, `ld64.lld`, the open-source
    sysroot above), inserts it into a copy of that IPA with Python's
    `zipfile` and leaves signing to the sideloader;
  * Apple's SDK may only be used on Apple computers (their D12, D15), so
    Windows and Linux use the open-source sysroot. An Apple Silicon Mac
    builds all 34 games; Windows 9 and Linux 2, both experimental;
  * proven on a device: a dylib built on Windows 11 ARM64, loaded from
    the app's root on an iPad Pro, SunPad played at 30 fps with saves.
    That test used a development profile, not a sideloader.
* SnapPad, HarkinianPad and AnnePad (same author) withdrew their earlier
  public IPAs ("Every copy contains code made from your ROM: keep it to
  yourself").
* DiOShonored (Dishonored, early): a shell IPA; the player builds on a
  Mac, or on Linux with the Darwin SDK extracted from an Xcode `.xip`
  they supply (xtool). The route PadMint rejected.
* ACNH-Universal: a spec only, for the owner's own iPad.

**A public IPA with the recompiled game code inside** (the route D18
rejects): unleashed-recompiled-ios, SpeedBreaker (709★), Theft4,
nfsmw-ios, MHGURecomp-iOS, LamaCelata2-iOS, skate3-ios-setup, and
DKC1Recomp, which published one such IPA and then stopped. All of them
build on a Mac with Xcode; none builds anything on the player's machine.
Several say in their own docs that the generated code is derived from
the game and not to be shared. Useful details from them:

* SpeedBreaker's packaging: a reproducible zip, a scan for personal
  strings (home paths, team IDs, profiles), entitlements checked against
  the file after signing.
* HaloPad (PadMint family) and SpeedBreaker show a message, or run
  without the entitlements, rather than crash.

No project compiles or generates code on the device, and every one says
it needs no JIT.

## Memory and entitlements

* `com.apple.developer.kernel.increased-memory-limit` raises the per-app
  memory limit. Reportedly Apple grants it to free teams too. SideStore
  drops it when signing with a free Apple ID, while AltStore 2.3 and
  later reportedly keeps it.
* `com.apple.developer.kernel.extended-virtual-addressing` raises the
  address-space cap. Reportedly it is for paid accounts only.
* Whether the 4 GiB guest reservation fits without the second one decides
  whether a free Apple ID is enough. Other ports suggest it does on recent
  devices:
  * XenonRecomp-based ports reserve a 4 GB guest block: SpeedBreaker
    measured 4 GB plus about 3 GB more address space;
  * unleashed-recompiled-ios runs on an iPhone 15 with no memory
    entitlements;
  * nfsmw-ios runs inside LiveContainer, where entitlements don't apply,
    on an M4 iPad Pro;
  * HaloPad reserves the full 32-bit space and ran on an iPad Pro without
    either entitlement;
  * skate3-ios-setup found extended virtual addressing "not needed on an
    A15".

  Still a **hypothesis** for us: answer it first, on the iPad, with a
  small test app. If the block doesn't fit, show a message instead of
  crashing, as SpeedBreaker does.
* Free accounts and `increased-memory-limit`: ACNH-Universal's desk study
  says a free Apple ID gets neither entitlement; LASRecomp and SpeedBreaker
  report from devices that the memory limit works with the right
  sideloader. The iPad test settles it for us.
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
   a module for `aarch64-ios` against a stub `.tbd`, and choose the linker
   and the headers' source.
2. Xcode on the Mac. A test app that reserves memory as `mem.cpp` does,
   installed on the iPad with and without `increased-memory-limit`.
3. The fork for the iOS Simulator, no dynarmic: title, then a quest on
   native code.
4. On the iPad: ST03A on native code, then the map sweep against
   Windows' pictures.
5. The base app in CI, the setup's iOS output, the sideloaders checked
   (D26).
6. Touch and on-screen controls, the lifecycle, 120 Hz, thermals.

Sources for the entitlement and JIT reports (2025–2026, not checked
here):
[SideStore issue #1616](https://github.com/SideStore/SideStore/issues/1616),
[NX2Apple's ENTITLEMENTS.md](https://github.com/LNPANDY/NX2Apple/blob/main/ENTITLEMENTS.md),
[the libretro forum on JIT in iOS 26](https://forums.libretro.com/t/what-is-the-current-situation-with-ra-on-ios-26-and-jit-support/49244),
[StikDebug](https://github.com/StephenDev0/StikDebug).

The projects in the survey:
[LASRecomp](https://github.com/peiikai/LASRecomp) and its
[PR #238](https://github.com/peiikai/LASRecomp/pull/238),
[PadMint](https://github.com/chrissotraidis/padmint) (its
[DECISIONS.md](https://github.com/chrissotraidis/padmint/blob/HEAD/docs/DECISIONS.md)),
[SunPad](https://github.com/chrissotraidis/sunpad),
[KartPad](https://github.com/chrissotraidis/kartpad),
[HaloPad](https://github.com/chrissotraidis/projectreach),
[SnapPad](https://github.com/chrissotraidis/snappad),
[HarkinianPad](https://github.com/chrissotraidis/harkinianpad),
[DiOShonored](https://github.com/ometavr/dioshonored),
[ACNH-Universal PR #144](https://github.com/iannitram/ACNH-Universal/pull/144),
[unleashed-recompiled-ios](https://github.com/ITSeniy/unleashed-recompiled-ios),
[SpeedBreaker](https://github.com/SpeedBreakerProject/speedbreaker),
[Theft4](https://github.com/KoreanSeats1/Theft4),
[nfsmw-ios](https://github.com/bep1s69/nfsmw-ios),
[MHGURecomp-iOS](https://github.com/WiseManChris/MHGURecomp-iOS),
[LamaCelata2-iOS](https://github.com/Ke619/LamaCelata2-iOS),
[skate3-ios-setup](https://github.com/andrewnakas/skate3-ios-setup),
[DKC1Recomp](https://github.com/elliotttate/DKC1Recomp).
