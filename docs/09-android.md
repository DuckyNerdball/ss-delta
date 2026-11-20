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
   Update (2026-11-20): the on-device build is the 0.4.0 milestone (D27,
   below).
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

## Native code on Android (14d, 2026-11-19)

**Building the modules.** The recompiler's CMake (`third_party/recomp/recomp`)
works unchanged with the NDK's toolchain file on the Windows test PC (NDK
r29, Ninja, `ANDROID_ABI=arm64-v8a`, `ANDROID_PLATFORM=28`, Release, 8
jobs). The generated C++ stays on Windows; nothing game-derived goes to
WSL. All ten modules (eboot, libc, libfios2, libult, and the six firmware
modules) take **6.8 min**. Each needs only `libc`, `libm` and `libdl` and
exports only `armrecomp_aot_init`. The NDK's toolchain adds `-g`, so
`ssd_aot_eboot.so` is 1.17 GB as built; with `llvm-strip --strip-debug`
all ten are **106 MB** (eboot 101 MB).

**Loading them.** On Android, the frontend's module scan
(`select_recompiled_modules`) copies `ssd_aot_*.so` from `[paths]
recompiled` (by default the app's external folder, where a PC puts them)
into the app's internal storage (`files/recompiled/`) when size or time
differ, removes copies whose module is gone, and loads them from there:
shared storage is `noexec`. The fork's `dlopen` loader is unchanged.

**On the Thor** (2026-11-19): NativeCPU, every module verified against
guest memory and placed where its code expects it (the same load
addresses as on the PC), **0 native-to-JIT calls**; 40,563 escapes in
the first minute (C++ exceptions thrown by the host through the modules'
frames: the NDK's unwinder finds the modules' unwind tables). ST03A from
Stage Select:

| Driver | 1× (960×544) | 2× (1920×1088) |
|---|---|---|
| Qualcomm's | **60.0 fps**, longest frame 16.7 ms | 59.9–60.0 fps, 16.7 ms |
| Turnip T23 | 59.9–60.0 fps, 16.7 ms | 58.1 fps, 33.4 ms |

(On the JIT the same map ran at about 57 fps.) No errors in the logs; the
pictures as on Windows.

**Dynarmic tests on arm64 Android.** `recomp_tests` built per module in
WSL with the Linux NDK against the Android games build's dynarmic
(`VITA3K_CONFIG` empty for its single-config layout), pushed to
`/data/local/tmp/recomp-tests/`, run as the shell user under a time limit
and an RSS watchdog (`guarded-test.sh`), with `run-tests.ps1`'s iterations
(256 per form, 64 per function). The filter argument `*` must be quoted
for the device's shell, or it globs the folder's file names and nothing
runs.

* eboot: **9,145 instruction tests and 325 function tests, 0 failing**
  (42 never returned within the tick budget, 4,032 of 20,800 runs
  skipped, as on the other hosts), 4 min 14 s, 63 MB peak.
* The other nine in 4.8 min, peak RSS at most 91 MB: libc 3,000 + 121,
  libfios2 2,176 + 47, libult 869 + 3, sysmodule 351 + 0, libSceFt2
  3,537 + 131, libpvf 1,468 + 23, libsceavplayer 895 + 9, libscemp4
  1,385 + 20, adhoc_matching 454 + 5.
* In all: **23,280 instruction and 684 function tests, 0 failing**, the
  same count as on the M5.

## The owner's first sessions on the Thor (2026-11-19)

**Qualcomm's driver: black rectangles in the fog.** The owner started the
APK from the launcher (native code, Qualcomm's driver, defaults) and
played the first story quest on ST03A. Now and then, black pixelated
rectangles appeared all over the screen, with the fog clouds that drift
across the map, more often in combat. The log had nothing at those times.

The cause: the fog is programmable blending (the shader reads the
framebuffer). Qualcomm's driver has neither shader interlock nor
raster-order access, so Vita3K reads the framebuffer through
non-coherent subpass input. A barrier before each such draw orders draws
against each other (`scene.cpp`), but not the overlapping sprites
**within** one draw, which a fog cloud is. On the Adreno's tiled renderer
that comes out as tile-shaped garbage. The earlier research had it from
the other side: loktar00's "blocky fog/particle artifacts" on Vulkan went
away with `high-accuracy: true`, which on the PC means interlock.

**Turnip fixes it.** The same quest with `[debug] gpu_driver =
turnip-T23` (Turnip has raster-order access, so reads within a draw are
ordered): **two quests played without the glitch** (owner). Turnip
T23 stays set on the test device.

Consequences:

* On Adreno, Turnip is the driver to play on, not just an option. The
  APK should recommend or fetch it, as LostOdysseyRecomp does, and the
  PC setup can push a pinned package meanwhile (14e, 14f).
* Qualcomm's driver stays wrong for this effect. Fixing it without
  coherent reads would mean splitting overlapping primitives into
  separate draws: slow, not planned.

**Write tracking: a false critical line.** The log of the Turnip session
had 38 "Unhandled write protected region was valid" lines, every address
exactly twice, in bursts a few milliseconds apart. That is the race the
handler already describes: several threads fault on one page, the first
handles it (unprotects the page, removes the segment), and the ones that
waited find no segment. macOS checks the page's protection there
(`page_accessible`); elsewhere it returned "unknown", so the race was
logged as critical before the "keep going" path unprotected the page
again, which was the right outcome. Now (`mem.cpp`), on hosts other than
macOS, a page that no tracked segment overlaps is treated as that race:
retried without the log line. Tracked regions cover whole host pages
since the macOS work, so on 4 KiB hosts that bookkeeping is exact. A
fault on a page that still has a segment keeps the critical line.
Checked: ST03A natively on the Thor (Turnip) and on Windows, 0 critical
lines, 60 fps. An idle quest didn't show the race before either, so the
next play session is the real check.

**The log lost its end.** That session's log stopped five minutes in:
the log is written on a thread of its own, and an app swiped away from
the recent apps is killed without notice. The frontend now flushes every
log sink when Android sends the app to the background, ends it, or runs
low on memory: an SDL event watch (`android.cpp`), because SDL blocks the
game's event loop while the app is paused. Checked: Home pressed 25 s in,
the log's last line two seconds before.

## The PC setup for Android (14e, D25, 2026-11-19)

**The compiler.** What a module needs from the C and C++ runtime, found by
linking one without libc++ (`-nostdlib++`): the thread-safe static-local
guards (`__cxa_guard_*`, libc++abi's), `__cxa_atexit`/`__cxa_finalize`,
`abort`, `strncmp`, and the NDK compiler-rt's outline-atomics probe
(`getauxval`, `__system_property_get`). No `__gxx_personality_v0`: the
generated code has no cleanups, so escapes only need unwind tables. zig
(already the Linux and macOS setups' compiler) builds such a module:

* zig's `aarch64-linux-android` target has no libc headers;
  `aarch64-linux-musl` compiles (the functions used have the same ABI in
  bionic);
* `-mcpu=generic -mno-outline-atomics` (LL/SC inline, any ARMv8, no
  compiler-rt), `-funwind-tables`, `-fno-stack-protector`;
* `recomp/runtime/aot_android.cpp`: `__cxa_guard_acquire/release/abort`
  (atomics and `sched_yield`, so no musl type crosses into bionic) and
  `__dso_handle`;
* linked `-shared -nostdlib` against stub `libc.so`/`libm.so` made by zig
  (`--no-as-needed`, so the `DT_NEEDED` entries stay), with
  `--eh-frame-hdr` (without `PT_GNU_EH_FRAME` the host's unwinder can't
  walk the module's frames: the first try lacked it),
  `-z max-page-size=16384`, the export list, `--gc-sections`.

A module then imports only `abort` and `sched_yield` and exports only
`armrecomp_aot_init`. The ten build in **5.1 min** with 10 jobs on the
test PC (zig 0.17.1 for Windows), 89 MB. On the Thor: every module
verified, NativeCPU, 0 native-to-JIT calls, over 60,000 escapes,
ST03A at 59.9 fps on Turnip.

**The kit** (`third_party/recomp`):

* `toolchain.py`: the Android branch of the zig build;
  `toolchain-android-windows.json` pins zig for Windows (96 MB, SHA-256);
  fetch unpacks zips too. Linux and macOS use their own lock file's zig.
* `build-recomp.py --android --toolchain <dir>` → `build/recomp-android-zig`.
* `install-game.py --android <dir>`: after the PC's modules, Android's, into
  `<out>/android/`.
* `android.py push <folder>`: installs the APK (`--apk`), starts the app
  once if it never ran (its folder and settings file), copies `fs/` through
  `/data/local/tmp` (adbd's `secure_mkdirs`) and makes it writable for the
  app, keeps any save files already on the device and the settings file,
  replaces the modules, and with `--driver <zip>` puts a driver package
  into `drivers/` and sets `[debug] gpu_driver`. The first version took
  an existing `ux0/user` folder for saves, but the app's first start makes
  empty user folders: it now looks for files.
* `gameproject.py`: `android_package` (default
  `io.github.vitarecomps.<id>`).

**The frontend** unpacks `drivers/<name>.adpkg.zip` from the shared
folder into internal `files/driver/<name>/` when the zip is new or
changed (size and time in a marker file), refusing unsafe paths, so a
release APK gets Turnip without `run-as`. Checked: T30 from `drivers/`
loaded; the second start reused it.

**End to end** (2026-11-19), from the owner's US dump with a separate
test package (`io.github.vitarecomps.ssdelta.kittest`, so the owner's
app and saves were untouched): `install-game.py --name scratch-android
--android build/android-toolchain` took **19 min** (both sets of
modules); `android.py push --apk ... --driver turnip_mrpurple_T23...`
took **4.6 min** (3.2 GB at about 12 MB/s over Wi-Fi). The app started
on native code with T23 from `drivers/`: ST03A at 60.0 fps, no critical
log lines.

### From a release folder (2026-11-20)

A player has a release folder, not the project. The pieces for that:

* **`setup.py --android`** (kit): from a folder whose game is built, the
  Android modules from the game installed there (`install-game.py
  --android-only`: no dump, no firmware, no PC compiler; the game is run
  once unseen for its ELFs as in the PC build, then recompiled and
  compiled with zig), then adb, then `android.py push` with the release's
  APK (`setup/android/<id>.apk`). With `--install` parts it builds both
  sets of modules in one run and then copies. `--push-only` copies what
  an earlier run left in `<folder>/android/` (the modules stay there; the
  downloads and work files go, as for the PC build). Without `--console`
  and device options a window asks (below).
* **adb from Google**: `android-tools.json` pins platform-tools r37.0.3
  for Windows, Linux and macOS (SHA-1 from Google's
  `repository2-3.xml` checked, SHA-256 pinned); `android.py fetch-adb`.
  It comes under the Android SDK License Agreement, which the player
  accepts (`--accept-android-sdk-license`, or the window's box), as
  Microsoft's on Windows. The setup stops adb's server at the end, so its
  downloads can be deleted.
* **`android.py`**: `--pair <ip:port> --code <code>` (wireless debugging's
  pairing dialog; adb then finds the device by mDNS within seconds) and
  `--connect`; one device listed twice (its address and its mDNS name,
  as the Thor is once paired) counts once (by `ro.serialno`); a clear
  message when the installed app was signed by another key. **Found in
  the test:** `push` started the app once for its folder and settings
  file, and the game never started with the screen off (it waits for its
  surface), so the push failed. The device's shell can make the app's
  folder itself, so `push` no longer starts the app, except for
  `--driver` (it then wakes the screen first).
* **The window** (`setupgui.AndroidWindow`): Wi-Fi (pairing address,
  port and code, or the connect address) or a USB cable, Google's licence,
  "build again" when modules exist, Copy, then the same progress and log
  view as the build window.
* **The front end**: `--android` opens that window and quits afterwards;
  `--serial`, `--pair`/`--code`, `--connect`, `--push-only`,
  `--accept-android-sdk-license` and `--apk` go to the importer without
  the window; with `--dump` it builds both, then copies.
* **The APK**: `make-setup.py --apk` puts it in `setup/android/`. The
  release workflow's new `android` job builds it (NDK r29 on Ubuntu,
  Vita3K's Gradle wrapper, `assembleRelease`, versionCode from the tag),
  and every PC job takes it into its archive; it is also a release asset.
  The Gradle project signs the release build with the key in the
  environment (`ANDROID_KEYSTORE`, its passwords and alias, from the
  repository's secrets), else with the debug key; a tag without the
  key fails. Checked: the job's CMake steps from a fresh build folder in
  WSL (with Python 3.12: Vita3K's language catalog generator needs it;
  the job sets it up), and a release-type APK (not debuggable) built and
  run. A manual run on GitHub (2026-11-20, `f2131e8`): the `android` job
  in 11 min, the whole run in 33; the APK (20.3 MB, versionCode from the
  run number) verifies with APK Signature Scheme v2 under the release
  key (`CN=vita-recomps`), and the Windows, Linux and macOS archives
  each carry the same file as `setup/android/ss-delta.apk`. Installing
  it over an app signed with a debug key fails until that app is removed
  (back its saves up first).

**End to end from a release folder** (2026-11-20), the US dump, a
scratch release from `make-setup.py --apk` (with a test package name in
its `game.json`, so the owner's app was untouched), the download cache
of the Phase 13 tests:

* `ss-delta.exe --dump <zip> --accept-microsoft-license --android
  --accept-android-sdk-license --build-only`: the PC build, the Android
  modules, adb, the device found by itself and the APK installed, in
  **16.7 min** for the whole run (`--cache`: the firmware and the
  Windows compiler were there; zig for Android and adb were downloaded);
  the push then failed as above (screen off).
* After the fix, `setup.py --android --console --push-only`: **6.2 min**
  (3.4 GB at about 9 MB/s over Wi-Fi), the ten modules.
* On the Thor, the app from its icon: the Turnip offer, Download (D-pad
  to it, then A: the dialog's first press only moves the focus), T23
  injected, every module verified native, Stage Select, **ST03A at 60.0
  fps** (longest frame 16.7 ms), no critical log lines.
* The window, its Copy button driven by a test harness (the licence
  ticked, Wi-Fi with empty fields: paired before), without `--cache`:
  **4.4 min**, "Done"; afterwards `setup/` held only `android/`, `kit/`
  and `python/` (adb's download deleted).

## The map sweep on Turnip (14c, 2026-11-20)

The Phase 7 sweep over adb (`build/android/thor-map-sweep.py`, not
committed): each map's first quest from Stage Select, screenshots after
loading, with Mind's Eye, after camera turns and after a walk, and the
frame rate from SurfaceFlinger (`dumpsys SurfaceFlinger --latency` on
the game's `SurfaceView` layer). The first try stepped through the quest
list wrongly: a 300 ms R+right press reaches the game's key repeat on
the Thor and moves 20 quests. With a 120 ms press, and each Stage Select
screenshot compared with the Windows sweep's (the text on the left,
thresholded: below 0.6 for the same quest, above 2 for another; a retry
above 1.2), **all 50 maps matched on the first attempt**.

On Turnip T23, natively, 1×: **48 of 50 at 59.9–60.0 fps**, longest
frame 16.7 ms (ST22C 57.2 fps once while loading). Side by side with
Windows' pictures, every map shows the same scene, effects and HUD; the
rows that differ differ in timing only (enemies, a quest that ends early
or never leaves Stage Select, which Windows' does too; ST08B's dark shots
are its boss's darkness attack).

The other two (ST06A, ST20A) **hung**: 2.0 fps, frames 517 ms apart,
which is the renderer re-presenting the last frame every 500 ms when the
game submits nothing. Both logs end the same way:
`Queue.h:797:[ult] Assertion Failed: packet != NULL`, then
`NativeCPU: no native code for the guest code at 0x8045D7BC`: libult
asserted (`bkpt`, which has no native code), and its thread,
`MDL_DRAW_ULT_KERNEL`, stopped. About 6 hangs in some 130 quest loads on
the Thor so far, none in hundreds on Windows, none in 57 on the Mac
(arm64 too, but 57 loads at that rate miss it one time in ten).

## The libult hang: the exclusive monitor (2026-11-20)

libult's `Queue` (dequeue `f_8045ac4c`, enqueue `f_8045a920`) is a
Michael–Scott queue of 64-bit links (pointer and flag in the high word),
updated with `ldrexd`/`strexd`. Dequeue moves the packet into the old
dummy node, resets that node's `next` to (0, 0) with a plain `stm`
(`8045ade8`) and returns it. Enqueue reads the tail, `ldrexd`s its
`next`, checks the tail again and `strexd`s its node there if `next` was
(0, 0) (`8045a978` … `8045aab0`).

The recompiler made `strex` a host compare-and-swap against the value
`ldrex` read (D7, as dynarmic's value check). A real `strexd` also fails
if anything else stored to the address in between, and after any
exception. So, on the host only: a producer reads tail X's `next` as
(0, 0) and stalls; another producer links Y there, the tail moves on, a
consumer pops X and resets its `next` to (0, 0); the first producer's
CAS still matches and links its node onto X, which has left the queue.
The packet is lost while the count says it is there, and the next
dequeue finds none. A long stall between the two instructions is what
makes it likely: a host thread preempted there (the Thor's eight cores,
three of them small, run more threads than cores) keeps a value-checked
reservation; the Vita's monitor wouldn't survive it.

The barriers were not the problem: `dmb` is a sequentially consistent
fence, the device's libult has all 446 of them, and the guest uses no
`isb` or dependency tricks a compiler could drop.

**The fix** (kit `recomp/runtime/armrecomp.h`, generated code calls
`excl_reserve`/`excl_store`): as in dynarmic's exclusive monitor, a
successful exclusive store also breaks every other reservation of its
granule. A table of 4096 versions, one per hashed 8-byte granule;
`ldrex` records its granule's version (in `excl_valid`, bit 0 set, so
`GuestContext` and the fork's ABI stay as they were), and `strex`
succeeds only if the version is unchanged and memory still holds the
value, then bumps it (bit 0 of an entry locks it during the store).
Plain stores still don't break reservations, as in dynarmic. One table
per module. The dynarmic comparison tests pass (libult, libc), but have
no exclusives (single-threaded); Windows' ST03A is unchanged (59 fps,
0 critical lines).

**On the Thor**, the same sweep twice over with the fixed modules, in a
copy of the app (the test package with a copy of the game and saves):
**100 of 100 quest loads without a hang**, 0 critical log lines, every
Stage Select screenshot matching Windows'. At the old rate (about 1 in
22) a hundred clean loads happen by chance less than once in a hundred.

## Thor polish (14f, 2026-11-20)

* **Turnip on first start**: the APK's launcher is `SetupActivity`. On an
  Adreno 7xx (from `GL_RENDERER`) without a driver package and without
  an answer yet, it offers Mr. Purple's T23 (3.5 MB from GitHub, size
  and SHA-256 checked, written through a `.part` file into `drivers/`);
  *Not now* asks again next time, *Don't ask again* doesn't. `[debug]
  gpu_driver = auto` (the new default) takes the package unpacked last,
  else the system's driver. Checked in the test package: the offer,
  Download with the built-in A button, the zip's hash, the game started
  with `Vulkan driver: turnip_mrpurple_T23-toasted ([debug] gpu_driver =
  auto)`.
* **Home and back**: Home, then the launcher's icon: the same process,
  the title screen goes on at 59.9 fps. Android's Back doesn't close the
  game.
* **60 Hz**: the surface asks for 60 Hz (`setFrameRate`, fixed source).
  This Thor's own setting already caps the screen at 60 Hz
  (`peak_refresh_rate`), so the request's effect is unmeasured here.
* **Settings menu**: holding Select (Back/View) for a second opens it on
  the Thor, as on PCs.
* **Touchscreen**: the front touchscreen works (a 300 ms press in the
  save dialog; `input tap` presses too briefly for the game's sampling).
  But the touch module takes only fingers on Android (SDL turns the
  touchscreen into a mouse too), and only its mouse path added the
  frontend's held points: the `[touch]` bindings (the Black Rite on the
  left trigger) never reached the game on Android. They are now added in
  both paths (`touch.cpp`). That this makes the Black Rite work is a
  **hypothesis**: the quests tried showed no Black Rite icon, so neither a
  finger nor the trigger could be checked on it.
* **No game yet**: on Android the message says to set the game up on a
  PC and copy it over (`android.py push`), not to edit the ini.
* **AYN's performance modes** (the quick-settings tile; `settings put
  system performance_mode` 0 Standard, 1 Performance, 2 High Performance,
  as the tile's label shows). Of the readable limits only the GPU's
  lowest clock changes: 401, 550 and 615 MHz. The highest stays at
  680 MHz, and the CPU's maximums at 2.02/2.80/3.19 GHz in all three. The
  CPU clocks in use rise all the same (a governor setting shell can't
  read): in the quest the middle and big cores ran at 1.65/1.84 GHz in
  Standard, 2.05/2.48 in Performance and 2.80/3.19 in High Performance.
  Changing the mode also sets `fan_mode`.
* **Power** (2026-11-20, ST03A after loading, the camera turning, 90 s
  each, brightness 164/255). Measured as USB input with the battery
  full, so it is what the whole device draws, the charger's losses
  included. The home screen draws 1.5 W.

  | Mode | Scale | USB in | fps (median, lowest 4 s) | GPU |
  |---|---|---|---|---|
  | Standard | 1× | 4.1 W | 60.0, 59.9 | 401 MHz, 48% busy |
  | Performance | 1× | 4.5 W | 60.0, 60.0 | 550 MHz, 36% |
  | High Performance | 1× | 4.8 W | 60.0, 60.0 | 615 MHz, 37% |
  | Standard | 2× | 5.3 W | 60.0, 57.2 | 550 MHz, 82% |
  | High Performance | 2× | 6.5 W | 59.9, 58.1 | 615 MHz, 74% |

  At 1× (the default) Standard holds 60 fps, and the other modes cost
  0.4–0.7 W for nothing. At 2× both modes drop a few frames. The battery
  holds 5,938 mAh (design), about 23 Wh: roughly 5½ hours of play at
  Standard 1×, 3½ at High Performance 2× (**hypothesis**: estimated from
  USB input, not measured unplugged). The battery stayed at 25–26 °C
  throughout.
* **The owner's app** (`io.github.vitarecomps.ssdelta`) has this APK and
  the modules with the exclusive monitor since 2026-11-20 (saves and
  settings untouched; it started on its T23 at 59 fps). The test
  package is removed; measurements that need quests use a temporary
  one, copied on the device from the staged test file system (6 s).

## The setup on the device: survey (14g, 2026-11-20)

The owner (2026-11-20): no release until a player can build the game on
the Android device itself, without a PC; that is the 0.4.0 milestone.
How other recomp and decomp ports with Android versions get the game's
code onto a phone:

| Project | Code on Android | Player supplies |
|---|---|---|
| Zelda64Recomp (N64Recomp) and its Android ports (Goemon64Recomp-Android, Tooie Recompiled) | **prebuilt**: the release carries the recompiled code; the ROM is needed only to build from source | the ROM, picked at first start (assets) |
| Unleashed Recompiled (XenonRecomp) and its community Android ports | **prebuilt**; the Android app's first start installs the player's files (in-app picker, zip or folder) and makes the installer's `patched` folder on the device when it's missing | the Xbox 360 files |
| Ship of Harkinian, 2Ship (decompilations) | prebuilt (the source is public); the app generates its asset archive from the ROM on first start | the ROM |
| sm64ex-coop (decompilation) | **built on the device**: a modified Termux app ("sm64ex-coop builder Termux") installs clang and friends with `pkg`, builds the APK from the player's ROM, the player installs it. Android 14 partly broke it (a Termux bug) | the ROM, in Termux |

Nobody else among the recomps compiles game code on the phone: they
publish it, which D18 rules out for us. The only working precedent for
compiling on the device is the Termux route.

**What Android allows** (sources: Android 10's behaviour change, Termux's
wiki on Android 10, termux-exec's README):

* An app targeting API 29+ **can't `exec()` a file it wrote** (W^X,
  enforced by SELinux). Files packed in the APK as `lib*.so` and
  extracted to the app's native library folder **can** be executed, even
  when they're programs rather than libraries (`useLegacyPackaging`, so
  they are extracted at install).
* Running `/system/bin/linker64 <file>` sidesteps that for dynamically
  linked programs (Termux's Play Store build does it through
  `LD_PRELOAD`). Static programs such as zig's release can't run that
  way, and Google calls it a W^X violation.
* Targeting API 28 (F-Droid's Termux) still allows `exec()` from app
  storage. The install floor rose to API 24 with Android 15 and stayed
  there through 17.
* `dlopen` of a `.so` the app wrote to its internal storage still works:
  our app already copies the modules there and loads them (14d).
* python.org publishes official Android builds since 3.14
  (`python-<version>-aarch64-linux-android.tar.gz`). They're embedded only:
  `libpython` loaded through JNI, the standard library unpacked from the
  APK's assets. C extensions come as cross-built wheels. capstone's Python
  binding loads `libcapstone.so` with `ctypes`.
* zig 0.17.1 has an `aarch64-linux` build (53 MB `.tar.xz`), statically
  linked, the same version the desktop setups pin.

**What our setup would run on the device** (install-game.py's steps):
installing the firmware and the game and dumping the modules' ELFs are
the front end's own options (`--install-firmware`, `--install-content`,
`--dump-elfs`), so the APK's native code can do them. Downloading the
firmware is an HTTPS download with pinned hashes. Only recompiling
(Python and capstone) and compiling (zig) need tools the APK doesn't
have. On the test PC that part takes 5.1 min for the ten modules with 10
jobs (D25). On the Thor's Snapdragon 8 Gen 2 it's **unmeasured**.

The choice is [D27](decisions.md): the APK carries Python, capstone and
zig as native libraries and runs the whole setup itself.

### The probe on the Thor (2026-11-20)

install-game.py's step 4 ran on the Thor from adb's shell
(`/data/local/tmp`), with the tools D27 puts in the APK:

* **The tools**:
  * python.org's Python 3.14.10 for Android (aarch64), started by a
    six-line launcher (`Py_BytesMain`) built with the NDK and linked to
    `libpython3.14.so`;
  * capstone 5.0.7 (the desktop's version, from its PyPI sdist), built
    for Android with the NDK's CMake, ARM only;
  * the desktop's capstone binding and PyYAML (pure Python);
  * zig 0.17.1 `aarch64-linux` (the pinned SHA-256).

  Packed, they are 110 MB as `.tar.gz` (zig 164 MB plus a 217 MB
  `lib/`, Python 84 MB, unpacked).
* **The kit ran unchanged**: `recompile.py` for each module through
  `subprocess` with `sys.executable`, as install-game.py runs it, then
  `toolchain.build_modules(..., android=True)`. CPython's `subprocess`
  works on Android, and zig's static binary and its own child processes
  run.
* **Time**: recompiling the ten modules took **4.2 min** (eboot 235 s;
  the test PC takes 3.0 min). Compiling the 205 files with 8 jobs took
  **24.4 min** (the test PC: 5.1 min with 10). About **29 min** in all.
  adb's shell may use only 6 of the 8 cores (affinity `0-5`; `taskset ff`
  got 7), while an app in the foreground gets all 8 (`top-app` cpuset
  `0-7`).
* **Memory**: at most 1.45 GB for recompiling eboot and 1.8 GB for one
  compiler process. At least 8.6 GB stayed available (16 GB device).
* **Heat**, on the charger, battery full: the CPU sensors peaked at
  95.9 °C (82.8 °C median). The prime core held 3.19 GHz for 157 of 162
  samples (1.84 GHz for the other five), the battery stayed at 27 °C.
  AYN's Standard mode, fan in the owner's setting.
* **Space**: 4.4 GB while building (zig's objects 3.8 GB, the generated
  C++ 592 MB), on top of the game.
* **Same output**:
  * the generated C++ matches the PC's file for file once Windows'
    CRLF line endings are removed (only `report.txt`'s elapsed time
    differs);
  * seven of the ten `.so` are byte-identical to the PC's zig build and
    to the modules the owner's app runs, eboot included;
  * libc, libfios2 and libult differ only because the probe took their
    unrelocated ELFs from `extracted/elf/` instead of the setup's
    relocated dumps.

What the probe leaves open: the tools running from the app's native
library folder instead of adb's shell; the time with all eight cores;
and devices smaller than the Thor (8 GB, slower SoCs).

## Thor-specific work

* **Second screen**: the 3.92″ touchscreen below stays unused (the
  owner, 2026-11-20): most Android players have one screen, so nothing
  in the game may depend on a second one. The app draws only on the main
  display; AYN's own dual-screen settings decide what the second shows.
* **Main screen**: 1920×1080 at 120 Hz. 960×544 scales 2× to 1920×1088,
  which is 8 lines too tall: scale 2 with a small crop, or fit to 1080 with
  a resample. 60 fps is every second refresh at 120 Hz; 30 every fourth.
* **Controls**: the built-in gamepad reports as an "Xbox Wireless
  Controller" (in the controller style AYN's quick settings had; the
  tile `controllerStyle` switches it): A/B/X/Y, bumpers, a D-pad hat,
  sticks at ±32767, and **analog triggers** (`ABS_GAS`, `ABS_BRAKE`).
  Upstream's app takes it as a gamepad. The Black Rite binding (left
  trigger) fires past half travel (input.cpp); on Android it needed the
  touch fix above (14f).
* **Performance modes and fan**: AYN's quick settings (Standard,
  Performance, High Performance, and fan curves). Measured in 14f
  (above): Standard is enough at 1×.
* **Lifecycle**: Android pauses an app when it loses focus and may kill it
  in the background. The Vita's own suspend has no counterpart in the
  emulator. At minimum, pause emulation and audio on `onPause` and keep
  the Vulkan surface valid when it comes back. Home and back again works
  (14f).

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

Phase 14 in [03-plan](03-plan.md): **14g, the setup on the device
([D27](decisions.md)), is the 0.4.0 milestone**; no release is tagged
before it. The probe over adb is done (above: 29 min on the Thor, the
same modules as the PC). Next, the tools inside the APK. Then the Black
Rite on the trigger, seen in play.
