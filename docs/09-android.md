# 09 — Android, targeting the AYN Thor

Research started 2026-11-19, while Phases 11–13 (Linux, macOS, launcher
standards) are still open. The target is the AYN Thor Max: it is the only
Android device available. A port that runs well on a Snapdragon 8 Gen 2
runs on most current Android handhelds of that class (Odin 2, Retroid
Pocket 5/Mini and others), but only the Thor is tested.

Claims not yet checked on the Thor or in the code are marked
**hypothesis**. This first survey was written on the Windows test PC from
the fork's and the kit's sources, before the Thor was reachable over adb.

## The target

| | AYN Thor Max | MacBook Air (M5) | Test PC (Radeon 760M) |
|---|---|---|---|
| SoC | Snapdragon 8 Gen 2 | Apple M5 | Ryzen 5 7640HS |
| CPU | 8 cores: 1 × Cortex-X3, 2 × A715, 2 × A710, 3 × A510, **arm64** | 10 cores, arm64 only | Zen 4, 6C/12T |
| GPU | Adreno 740 (Qualcomm's Vulkan driver, or Mesa Turnip through adrenotools) | Apple GPU (Metal, MoltenVK) | RDNA 3, 8 CUs |
| Memory | 16 GB LPDDR5X | 24 GB unified | 2 × 16 GB DDR5-5600 |
| Storage | 1 TB UFS 4.0 | 1 TB | NVMe |
| Screens | 6″ AMOLED 1920×1080 at 120 Hz, plus a 3.92″ AMOLED 1240×1080 at 60 Hz (second screen, touch) | 15.3″ Retina | any |
| Controls | built-in gamepad: two sticks, D-pad, face buttons, L1/R1, analog L2/R2 | keyboard, trackpad | keyboard, gamepad |
| OS | Android 13, AYN's dual-screen launcher | macOS 27 | Windows 11 |
| Host page size | 4 KiB | 16 KiB | 4 KiB |

The table's Thor column is AYN's published specification. The device
itself, read over adb on 2026-11-19:

* `AYN Thor`, board `kalama`, SoC **QCS8550** (the 8 Gen 2's IoT
  variant), build `Thor_V1.0.0.377_20260206`, Android 13 (API 33), security patch
  2024-01-01, kernel 5.15.123 (`android13-8`), a `user` build (not
  debuggable: `run-as` works only on our own debuggable APK).
* CPU: cpu0–2 Cortex-A510 at 2.016 GHz, cpu3–4 A715 and cpu5–6 A710 at
  2.803 GHz, cpu7 Cortex-X3 at 3.187 GHz. The ABI list includes
  `armeabi-v7a`, so some cores still have AArch32. That makes no
  difference here, because nothing runs the guest's A32 code directly.
  Features include `atomics` (LSE), `fphp`, `asimddp`, `i8mm`, `bf16`.
  `nproc` in the shell says 6, though all 8 are online.
* **Page size 4096.** 15.6 GB visible, 12.6 GB available at idle; 891 GB
  free.
* Screens: both panels are portrait-native and rotated by the system. The
  main screen ("Built-in Screen") is 1080×1920 with 60 and 120 Hz modes
  (120 Hz is the default mode, but 60 Hz was active when read). The
  second ("Screen-2", display 4) is 1080×1240 at 120 or 60 Hz, a
  presentation display with touch.

**Vulkan, Qualcomm's driver** (`cmd gpu vkjson`): Adreno (TM) 740,
Vulkan 1.3.128, driver `0x802a4035`, compiler E031.41.03.47, built
2023-12-27. 113 device extensions. Has: `bufferDeviceAddress`,
`uniformBufferStandardLayout` (so `double-buffer` mapping is available),
`depthClamp`, `VK_ANDROID_external_memory_android_hardware_buffer`,
`VK_KHR_external_memory_fd`, `VK_EXT_depth_clip_enable`, BC and ASTC
textures, `shaderFloat16`/`Int8`, `VK_GOOGLE_display_timing`. Lacks:
**`VK_EXT_fragment_shader_interlock`**, **both
`rasterization_order_attachment_access` extensions**,
`VK_EXT_external_memory_host`, `shaderFloat64`, graphics pipeline
libraries, `VK_KHR_present_wait`. `maxStorageBufferRange` is 128 MiB.

What the missing interlock means: on the test PC and the Mac (raster
order groups) the renderer reads the framebuffer in shaders through
shader interlock (log: "Using shader interlock for accurate framebuffer
fetch emulation"). With neither interlock nor raster-order access it
takes Vita3K's other path, subpass input attachments without
coherence (`direct_fragcolor`, `renderer.cpp`'s `late_init`). The game has
never run on that path in this project. It can be tried on the test PC
by turning interlock off (a debugging switch to add), which separates
"the path" from "the Adreno".

What differs from all three earlier targets:

1. **No executable and no folder of its own.** An Android app is an APK,
   started as an `Activity`. Native code is a shared library (`.so`)
   loaded through JNI, and SDL3's `SDLActivity` calls its `SDL_main`. Our
   frontend's "everything next to the executable" (D22) has no executable
   to sit next to.
2. **No compiler, no Python, no shell for the player.** Every desktop setup
   (D18, D20, D21) generates and compiles the modules on the player's
   machine. On Android that would mean packing Python, capstone and a
   compiler into the APK. **Owner's choice (2026-11-19): a PC builds the
   modules first; an on-device build may follow as its own step.**
3. **Qualcomm's Vulkan driver.** Mobile Vulkan drivers are the least
   tested target of Vita3K's renderer. Turnip (Mesa) can replace the
   system driver per app through adrenotools, which the fork's
   `util/src/android_driver.cpp` already supports.
4. **Storage rules.** Shared storage (`/sdcard`) is mounted `noexec`, so a
   `.so` there can't be `dlopen`ed. Apps targeting API 29+ may not
   `exec()` files from their own data folder either (W^X).
5. **Two screens and a 120 Hz main screen.**

## Routes

1. **Our single-game frontend as an APK**: `game-frontend` and
   `games/ss-delta` built as `libss-delta.so` for `arm64-v8a`, behind a
   small `SDLActivity` subclass, with the recompiled modules built for
   Android arm64. This is the target.
2. **Upstream Vita3K's Android app with our patches**: the fork already
   contains it (`android/`, a Kotlin/Compose UI with a game list, an
   installer, settings, an on-screen overlay, trophies, ~3,000 lines of
   JNI). Rejected as the product, for the same reasons the Qt interface
   is gone on the desktop (D10). Upstream's release APK is the baseline,
   and its JNI code shows how to boot, find storage and load drivers.
3. **The Windows build under an x86 layer** (Winlator, Box64 with Wine):
   the whole emulator emulated twice. Rejected.

## What the code needs (survey 2026-11-19)

| Component | State | Work |
|---|---|---|
| Vita3K core, audio (cubeb: AAudio/OpenSL ES), network | Android supported upstream (`ANDROID` branches in CMake, `__ANDROID__` in 35 files) | build and test |
| Upstream's Android build | Gradle (AGP 9.2.1), `compileSdk 35`, `minSdk 28`, **NDK 29.0.14206865**, CMake 3.22.1+ from Gradle's `externalNativeBuild`; `arm64-v8a` and `x86_64`; dependencies through vcpkg's Android triplets (`cmake/vcpkg_android.cmake`, needs `ANDROID_NDK_HOME` and `VCPKG_ROOT`) | builds the `vita3k` shared library only; `VITA3K_GAMES_ONLY` leaves it out |
| Single-game library (`vita3k/CMakeLists.txt`, `add_game`) | built on `WIN32`, Linux and APPLE only, as executables | an `ANDROID` branch: `add_library(<id> SHARED ...)` with `SDL_main`, linked as upstream links `vita3k` (`-Wl,-Bsymbolic`, `--exclude-libs`). `CMAKE_SYSTEM_NAME` is `Android`, so the Linux branch doesn't apply |
| The game's APK | none | a Gradle project for the game (`vita3k/games/ss-delta/android/` or in the kit, **to decide**): manifest, `SDLActivity` subclass that names `libss-delta.so`, the assets `data/`, `shaders-builtin/` (as upstream's post-build step copies them) |
| Paths (`frontend.cpp`: `SDL_GetBasePath`, `ctx.exe_dir`) | everything next to the executable | on Android `exe_dir` becomes the app's folder: `SDL_GetAndroidExternalStoragePath()` (`/sdcard/Android/data/<pkg>/files`, reachable over adb and from a file manager) for `ss-delta.ini`, the log, the shader cache and the Vita file system, and `SDL_GetAndroidInternalStoragePath()` for the modules (below) |
| Importer (`importer.cpp`, `setup/`) | runs the kit's Python setup | not on Android (PC first). The frontend reports what's missing instead |
| JIT (dynarmic, arm64 backend) | used by upstream on Android | none expected. NativeCPU is the default; the JIT stays a fallback |
| Fork's dynarmic integration (D7) | checked on the arm64 backend on the M5 (08-macos) | none expected |
| Guest memory (`mem/src/mem.cpp`) | reserved as on Linux; the arm64 fault decoding reads ESR from `uc_mcontext.__reserved` (Linux layout) | **hypothesis**: works as on the Deck. Write tracking with 4 KiB pages as on Windows |
| **Memory mapping** (renderer) | upstream offers `disabled`, `double-buffer`, `page-table`, `external-host` and, on Android only, `native-buffer` (AHardwareBuffer). Our frontend fixes `double-buffer` (D4 update 4) | Qualcomm's driver has `bufferDeviceAddress` and `uniformBufferStandardLayout` (read 2026-11-19), so `double-buffer` is offered. Check with a run |
| Renderer features we rely on: depth clamp (patch 0032), shader interlock or raster-order access (programmable blending), surface sync, high accuracy, MSAA depth reads (0006) | checked on AMD, NVIDIA, MoltenVK | Qualcomm's driver has neither interlock nor raster-order access (read 2026-11-19, above): non-coherent subpass input. **Hypothesis**: Turnip has raster-order access. Read Turnip's extension list, then sweep the maps |
| Shader cache | `vk16-*.spv` in the frontend's `cache/` | per device; the driver's own pipeline cache on top |
| AOT loader (`cpu/src/aot.cpp`) | non-Windows branch uses `dlopen(RTLD_NOW \| RTLD_LOCAL)` | none expected, as long as the `.so` is in internal storage. **Hypothesis**: `dlopen` from the app's own data folder is allowed (W^X restricts `exec()`, and adrenotools loads drivers from there) |
| Module scan (`game-frontend/frontend.cpp`) | `.so` on non-Apple POSIX | none, apart from the folder |
| Native modules (`recomp/CMakeLists.txt`, `build-recomp.py`) | MSVC, zig for Linux (`x86_64`) and macOS (`aarch64`); `-O1 -w -ffp-contract=off`, hidden visibility, `--exclude-libs,ALL` | a target for `aarch64-linux-android`: the NDK's clang on the dev PC first (its CMake toolchain file), zig for players (below) |
| Recompiler runtime (`armrecomp.h`, `neon.h`) | plain C++20 (`<cstring>`, `<cmath>`, `<atomic>`, `<bit>`); checked on an arm64 host (M5: 23,280 + 684 dynarmic tests, 0 failing) | none expected. Escapes throw from the host through module frames: the modules need unwind tables, and **hypothesis** the host's unwinder finds them through `dl_iterate_phdr` as on Linux |
| Dynarmic tests (`run-tests`) | Windows, Linux, macOS | build the test binaries for Android, `adb push`, run under `adb shell` with a memory and time limit (`ulimit`, `timeout`) |
| Frame pacing | real-time threads on macOS (fork `09587ca1`); Windows and Linux plain timed waits | **hypothesis**: Android doesn't grant `SCHED_FIFO` to apps. Measure the frame-time spread first; 60 fps on a 120 Hz screen is every second refresh |
| Test input pipe (`VITA3K_INPUT_PIPE`) | a FIFO on Linux and macOS | a FIFO in the app's external folder, written through `adb shell` (**hypothesis**: the shell user can write `/sdcard/Android/data/<pkg>/files`; otherwise `run-as` on the debuggable build) |
| Kit: `v3kdrive.py` | Windows backend; a POSIX one is open | an adb backend: `am start` with extras for the arguments, `am force-stop`/a quit command, the FIFO, `adb pull` for `frame:` PNGs, `logcat` |
| Kit: setup, `make-dist.py`, `install-game.py` | per platform, `sys.platform` | a cross target: on a PC, build the modules for Android and lay out a folder (or push with adb) for the APK |
| Ad Hoc Play | `local` (127.0.0.N) and `lan` modes | **hypothesis**: Linux routes all of 127/8 on `lo`, so `local` works on one device as on the Deck. `lan` needs the `INTERNET` permission and, on Wi-Fi, the multicast lock for broadcasts |
| `ss-delta.ini` keyboard bindings, mouse as touch | desktop | the Thor's gamepad through SDL's Android gamepad support; the touchscreen as the front touch |

### The native modules on Android

The modules are as close to freestanding as C++ gets. They use `memcpy`,
a little `<cmath>` and atomics, and they export one symbol
(`armrecomp_aot_init`). Two ways to build them for Android:

1. **The NDK's clang** (`android.toolchain.cmake`, `ANDROID_ABI=arm64-v8a`,
   `ANDROID_PLATFORM=28`). It is already on the dev PC, it matches the fork's
   own build, and libc++ and the unwinder are the NDK's. Use it for development.
2. **zig** (`-target aarch64-linux-android`), as on Linux and macOS (D20,
   D21). **Hypothesis**: zig has no bionic of its own, but the modules need
   only a few libc symbols. A `.so` built with `-nostdlib` against a
   stub `libc.so` (just for `DT_NEEDED`) loads in the app's process and
   binds to the system's bionic. That would keep the player's setup to the
   toolchain the kit already downloads, without the NDK (2 GB, under
   Google's SDK licence) on the player's PC. To try once the NDK build
   runs.

Either way the APK can't contain them (D2). The app copies them from its
external folder (where the PC put them) into internal storage and loads them
from there.

### Where the game's files live

* **External app folder** (`/sdcard/Android/data/<pkg>/files/`): no
  permission needed. `adb push` and USB file transfer can reach it, and the
  files are deleted with the app. On Android 13, file manager apps can't open
  `Android/data` without tricks, but a PC over USB can. **Hypothesis**:
  good enough for a PC-first setup.
* **A folder the player picks** (upstream's way: `MANAGE_EXTERNAL_STORAGE`,
  "all files access"): survives an uninstall, reachable from any file
  manager. Heavier on permissions.

Start with the external app folder; revisit with the on-device setup.

## GPU drivers: Qualcomm's or Turnip

On Snapdragon handhelds, emulators commonly replace the system driver with
a Mesa **Turnip** build. Turnip is newer than the vendor driver (here
from 2023), and it has extensions the vendor driver lacks. The owner
pointed at LostOdysseyRecomp's Android port (2026-11-19), which
downloads one from inside the app:

* Its catalog lists the release feeds that the Eden emulator's driver
  fetcher uses (Mr. Purple's `purple-turnip`, KIMCHI's
  `AdrenoToolsDrivers`, Weab-chan's and Whitebelyash's
  `freedreno_turnip-CI`, a GameHub build for Adreno 8xx). It recommends
  one by Adreno model with Eden's table: for 700–799, "Mr. Purple T23".
* Packages are libadrenotools zips (`meta.json` with `libraryName`, plus
  the driver `.so`). Each is unpacked into its own folder under the app's
  `files/`, and loaded through libadrenotools' linker namespaces (API 28+,
  arm64). Picking a driver only changes the folder the loader is pointed
  at. If the driver fails, the game returns to the driver page.
* The project is GPL-3; the fork is GPL-2. Take the design, not the code.

(Since 14b our APK loads them: `[debug] gpu_driver`, *The single-game
APK on the JIT* below.) Our fork already has the loading half: `util/src/android_driver.cpp`
opens a package from `files/driver/<name>/` (`meta.json`, or upstream's
`driver_name.txt`) with `adrenotools_open_libvulkan`, named by the config's
`custom-driver-name`, and falls back to the system loader when it fails.
Missing for our APK: a way to get a package there. In order of effort:
the PC setup pushes a pinned package; a file picker for a zip; a
download page like LostOdyssey's.

Downloaded for the baseline (2026-11-19, `build/android/drivers/`):
`turnip_mrpurple_T23-toasted.adpkg.zip` (Mesa 26.0.0, Vulkan 1.4.335,
Eden's pick) and `turnip_mrpurple_T30-toasted.adpkg.zip` (Mesa 26.3.0,
Vulkan 1.4.359, the newest), each `vulkan.purple.so` with `minApi` 30.
**Hypothesis**: Turnip exposes
`VK_EXT_rasterization_order_attachment_access` on the Adreno 740, which
would give coherent framebuffer fetch. Check its `vulkaninfo` in the app.

## Baseline: upstream Vita3K on the Thor (2026-11-19)

Upstream's `android-latest.apk` (continuous release of 2026-11-17,
v0.2.1 4377-685b80a6, `org.vita3k.emulator`, targetSdk 35), installed
with `adb install`. Started straight into the game with
`am start -n org.vita3k.emulator/.Emulator --es title_id PCSA00152`
(its `.Emulator` activity is exported and turns `title_id` into
`-r <id>`), so none of its UI was used. Test file system as for the
Deck and the Mac: firmware, the game, its licence and a copy of the
test saves, 3.2 GB, in `Android/data/org.vita3k.emulator/files/vita/`.
Settings as on the Deck and the Mac: Vulkan, `high-accuracy: true`,
surface sync on, 1×, `double-buffer`. Qualcomm's driver.

* The log: Vulkan device Adreno (TM) 740, **memory mapping: Double
  buffer**, RGBA4444 surfaces native. No interlock line: the subpass
  input path, as expected from the extension list.
* **Title: 29.5 fps** while pipelines compile (frames up to 83 ms).
  **ST03A from Stage Select: 29.9 fps** at the game's 30 (SurfaceFlinger
  present times, longest frame 67 ms), on the JIT. No crash, no errors
  in the log.
* The picture: the same scene as Windows, but **brighter and hazier
  snow**, as upstream on the Mac. **Hypothesis**, as there: one of the
  fork's renderer fixes, not Android.

Not run yet: Turnip in upstream's app, the 2× scale, our fork's
settings beyond these. Upstream keeps drivers in its private `files/`.
Its Settings → Graphics → Custom GPU Driver has **Download Drivers**,
which only opens K11MCH1's release page in the browser, and **Install
Driver**, which first asks for **All files access**
(`MANAGE_EXTERNAL_STORAGE`) before it will open a zip. That isn't
granted on the test device without the owner. Our own debuggable APK can
take a package through `run-as` into `files/driver/` with no extra
permission.

### Driving the Thor over adb

What it took, for the tools to come (`v3kdrive.py`'s adb backend):

* **Screenshots** need the physical display: `screencap -p -d <id>`,
  with the ids from `dumpsys SurfaceFlinger --display-id` (HWC display 0
  is the main screen, 3 the second). Without `-d` the result is black.
* **Frame rate**: `dumpsys SurfaceFlinger --latency '<layer>'` on the
  app's `SurfaceView[...](BLAST)#n` layer (the one with timestamps); 127
  frames of present times.
* **Input**: `input keyevent` reaches the app's window, but a key's down
  and up arrive within one of the game's input polls and are lost; a
  long press repeats. The shell user is in the `input` group, so
  `sendevent` on the built-in controls' device (`/dev/input/event9`,
  "Xbox Wireless Controller", the hat for the D-pad) gives timed
  presses, through the same path as the real gamepad. One press, one
  step, every time.
* **Files**: `adb push` into another app's `Android/data` fails on
  nested folders (`remote secure_mkdirs failed: Operation not
  permitted`), though `mkdir` in `adb shell` works. Push to
  `/data/local/tmp/` and `cp -R` in the shell instead (3.2 GB in 4.3
  min over Wi-Fi). Files the shell user writes there are owned by
  `shell`, group `ext_data_rw`, mode 644: **the app can't write them**
  (`time.xml` failed) until `chmod -R g+rwX`.
* **Git Bash** rewrites `/sdcard/...` arguments into Windows paths
  before adb sees them: `MSYS_NO_PATHCONV=1`, and Windows-style local
  paths.
* **AYN's burn-in protection** ("Anti-image-retention pixel refresh, tap
  to exit") covers the screen after a while without input. It isn't in
  `settings list`. Injected gamepad events count as input.
* The system's `peak_refresh_rate` was 60 when read (the owner's
  setting), so the main screen ran at 60 Hz.

## The single-game APK on the JIT (14b, 2026-11-19)

**Build host.** The native library is built in WSL 2 (the `sniper`
distribution of the Linux work, 07-linux) with the Linux NDK r29
(`/opt/android-ndk-r29`, SHA-1 checked against Google's index). The APK is
packed on Windows with Gradle (AGP 9.2.1 through Vita3K's wrapper, Gradle
9.4.1) and the Windows SDK. Linux as the build host because OpenSSL's
build is `perl Configure` and `make`, as in upstream's CI (Ubuntu). The
WSL clone gets the Windows fork's uncommitted changes as a diff, as for
Linux.

**No vcpkg.** Upstream's Android app takes Boost, OpenSSL, curl and zlib
from vcpkg's Android triplets. For the single-game libraries
(`VITA3K_GAMES_ONLY`) the fork now builds them as the Linux games build
does:

* the top-level `CMakeLists.txt` includes `cmake/vcpkg_android.cmake` only
  for Vita3K's own app;
* Boost 1.89 from the bundled source: `b2` built for the host with gcc,
  the libraries with the NDK's clang through a b2 user config
  (`toolset=clang-android target-os=android`, `-fPIC`). Both
  `find_package(Boost ... PATHS ${BOOST_INSTALLDIR})` take
  `NO_CMAKE_FIND_ROOT_PATH`, since the NDK toolchain re-roots every search
  into its sysroot;
* OpenSSL 4.0.1 from its pinned source with its own `android-arm64` target
  (`ANDROID_NDK_ROOT`, the NDK's clang on `PATH`,
  `-D__ANDROID_API__=28`), static, its files named directly to
  `FindOpenSSL` for the same reason; curl from source on it, as on Linux;
* zlib is the platform's (`libz.so`). Upstream clears `CMAKE_SYSROOT` on
  Android, so `find_package(ZLIB)` can't find it, and psvpfstools then
  fell back to a stale x86-64 `libz.a` in its source folder. Fixed by
  naming the NDK's `libz.so`, with `zlib.h`/`zconf.h` copied to a folder
  of their own: the sysroot's whole `include/` on the command line would
  come before libc++'s headers.

Configure takes 4.5 min (Boost and OpenSSL), a clean build of the
`ss-delta` target 3.5 min on 12 threads. `libss-delta.so` is 377 MB with
debug info, **68 MB stripped**. It needs only `libz`, `libm`,
`libOpenSLES`, `libdl`, `libGLESv1_CM`, `libGLESv2`, `libandroid`,
`liblog` and `libc`, and exports `SDL_main`, `JNI_OnLoad` and the
surface callback. The APK is 22 MB.

**The fork's pieces:**

* `add_game` on `ANDROID` builds `lib<id>.so` (`add_library(SHARED)`);
  SDL3 is linked in statically, as in upstream's `libVita3K.so`.
  `<SDL3/SDL_main.h>` already turns the game's `main` into `SDL_main`.
* `game-frontend/android.cpp`, in place of upstream's `android/jni` (not
  built for the games): the JNI callback that tells the renderer the
  surface exists (`renderer::vulkan::set_android_surface`, a new setter
  beside `has_android_surface`), and `ime::set_keyboard_active` and the
  other IME functions that the core's dialogs call, as SDL text input. The
  core's own Android code calls no Java class of upstream's app.
* `frontend.cpp`: the game folder is `SDL_GetAndroidExternalStoragePath()`
  (`Android/data/<package>/files`), the static assets path is empty
  (`data/` and `shaders-builtin/` are APK assets read through
  `SDL_IOFromFile`), the IME gets the window, and the window is always
  fullscreen.
* `game-frontend/android/`: one Gradle project for every game, with
  `-Pgame`, `-PapplicationId`, `-PappName`, `-PjniLibsDir`. SDL's own Java
  sources (`external/sdl/android-project`), plus two classes in
  `io.github.vitarecomps.frontend`: `GameActivity` (SDL's activity: the
  library from the manifest's `game.library`, the command line from the
  intent's `args` string array, immersive fullscreen before the surface
  exists, screen kept on) and `GameSurface` (reports the surface). Package
  `io.github.vitarecomps.ssdelta`, `minSdk` 28, `targetSdk` 35,
  arm64-v8a only, debuggable debug build (`run-as`). Permissions: network
  and Wi-Fi multicast (Ad Hoc Play), vibration, wake lock; no storage
  permission.

**On the Thor** (2026-11-19), Qualcomm's driver, defaults (`full_3d`, 1×,
60 fps), no modules, so the frontend ran everything on the JIT. The test
file system was copied from the staging folder into
`Android/data/io.github.vitarecomps.ssdelta/files/fs/` (5 s on the device)
and made group-writable.

* First start without a game: the frontend's own dialog ("not installed
  in .../files/fs. Set [paths] vita_fs in ss-delta.ini"), with
  `ss-delta.ini`, `fs/` and `ss-delta/vita3k.log` created.
* With the game: Vulkan device Adreno (TM) 740, `double-buffer` mapping,
  the title at **45–49 fps**, and **ST03A from Stage Select at 58.5–59
  fps** (longest frame 33 ms), no errors in the log. The picture is
  Windows', without upstream's extra haze, so that haze was the fork's
  renderer fixes, as on the Mac. The Thor's B button (circle) started the
  quest: SDL takes the built-in controls as a gamepad.
* Found on the way: the first build made the window fullscreen only
  after the surface existed, and the swapchain kept the old 1920×970 size
  (the picture cropped to that band). Fixed by hiding the system bars in
  the activity before the surface is created. **A running swapchain
  doesn't follow a resized surface yet.**
* **Turnip in our APK** (2026-11-19). `[debug] gpu_driver` (Android
  only, a new setting) names a folder in the app's internal
  `files/driver/`. The frontend passes it as Vita3K's `custom-driver-name`,
  and the fork's loader opens it with libadrenotools. The package goes
  there with `run-as` on the debug build (the zip pushed to
  `/data/local/tmp`, unzipped into `files/driver/turnip-T23/`). The first
  attempt fell back to the system driver ("Could not open handle"):
  libadrenotools loads its own hook libraries (`libhook_impl.so`,
  `libmain_hook.so`, `libfile_redirect_hook.so`, `libgsl_alloc_hook.so`)
  from the app's native library folder. Upstream's Gradle build packs every
  shared library its CMake builds; ours takes prebuilt ones, so `add_game`
  now builds the hooks into `bin/` beside the game's library.
* A new log line tells which way shaders read the framebuffer. ST03A from
  Stage Select, the three drivers, the same steps (save, settings, 1×,
  60 fps target, JIT):

  | Driver | Vulkan device | Raster-order access | Interlock | ST03A fps |
  |---|---|---|---|---|
  | Qualcomm (2023-12) | Adreno (TM) 740 | no | no | 57.2–57.7 |
  | Turnip T23 (Mesa 26.0.0) | PurpleVK-public Adreno (TM) 740 | **yes** | no | 57.2 |
  | Turnip T30 (Mesa 26.3.0) | PurpleVK-public Adreno (TM) 740 (git-62ac221a33) | **yes** | no | 54.7–57.2 |

  No errors in any log, and the three pictures show the same scene,
  rendered as on Windows. Turnip reads the framebuffer coherently
  (raster-order access, Vita3K's preferred way); Qualcomm's driver goes
  through non-coherent subpass input. Which one is closer to the Vita in
  the game's programmable-blending effects waits for the map sweep
  (14c).
* Test steps: `BootSequence` in the app's copy of `config.ini` is set by
  `sed` over adb. The file has **CRLF** line ends and the game needs them:
  a replacement that dropped the `\r` made the game ignore the line and
  boot to the title.
* The version string from the WSL build reads
  `4304-8b815f2f-;mnt;c;ss-delta;third_party/HEAD` (the branch name taken
  from the clone's `/mnt/c` origin). Cosmetic.

## Thor-specific work

* **Second screen**: the 3.92″ touchscreen below. Candidates: the Vita's
  **rear touchpad** (the game uses it little; check where), the settings
  menu, or nothing (black, to save power). SDL3 sees it as a second
  display (**hypothesis**: AYN's launcher may hand it to the app only in
  some modes).
* **Main screen**: 1920×1080 at 120 Hz. 960×544 scales 2× to 1920×1088,
  which is 8 lines too tall: scale 2 with a small crop, or fit to 1080 with
  a resample. 60 fps is every second refresh at 120 Hz; 30 every fourth.
* **Controls**: the built-in gamepad reports as an "Xbox Wireless
  Controller" (in the controller style AYN's quick settings had; the
  tile `controllerStyle` switches it): A/B/X/Y, bumpers, a D-pad hat,
  sticks at ±32767, and **analog triggers** (`ABS_GAS`, `ABS_BRAKE`).
  Upstream's app takes it as a gamepad. The Black Rite binding (left
  trigger) needs a threshold.
* **Performance modes and fan**: AYN's quick settings (Standard,
  Performance, Max, and fan curves). Measure 60 fps at 1× and 2× in each,
  with power read from `/sys/class/power_supply` over adb.
* **Lifecycle**: Android pauses an app when it loses focus and may kill it
  in the background. The Vita's own suspend has no counterpart in the
  emulator. At minimum, pause emulation and audio on `onPause` and keep
  the Vulkan surface valid when it comes back.

## Developing for Android

* **Access**: wireless debugging (Android 13: Developer options →
  Wireless debugging → *Pair device with pairing code*), then
  `adb connect <ip>:<port>`. The SDK, NDK r29 and adb are installed
  on the test PC (owner's machine notes).
* **Build**: on the test PC, Gradle with the NDK. No WSL, no device-side
  compiler. The modules are cross-compiled there too.
* **Game data**: the firmware and the installed game copied from the test
  PC's junction file system (as for the Deck and the Mac), with a test
  user's saves. The owner's own saves stay on the PC.
* **Logs and pictures**: `adb logcat` (SDL logs through it), the
  frontend's log file in the external folder, `frame:` PNGs pulled with
  `adb pull`.
* **Debugging**: the `reldebug` build type (debuggable, `RelWithDebInfo`),
  `lldb-server` from the NDK. Tombstones (`adb bugreport` or
  `/data/tombstones` through `dumpsys`) for native crashes.

## Next steps

Phase 14 in [03-plan](03-plan.md): access and baseline first (upstream's
APK on the Thor with the test file system), then our renderer on the
Adreno, the single-game APK on the JIT, native modules, the PC-side
setup, and Thor polish.
