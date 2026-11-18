# 08 — macOS on Apple Silicon

Research started 2026-11-17, while Phase 11 (Linux) is still open. The
target is Apple Silicon. The test machine is a MacBook Air with an M5.
Intel Macs are out of scope: macOS 27 no longer runs on them.

Claims not yet checked on the Mac or in the code are marked
**hypothesis**. This first survey was written on the Windows test PC from
the fork's and the kit's sources, without access to the Mac.

## The target

| | MacBook Air (M5) | Test PC (Radeon 760M) |
|---|---|---|
| CPU | 10 cores (4 performance, 6 efficiency), **arm64 only, no AArch32** | Zen 4 7640HS, 6C/12T |
| GPU | 8 or 10 cores (Apple GPU, tile-based) | RDNA 3, 8 CUs |
| Memory | 16/24/32 GB unified LPDDR5X-9600, 153 GB/s | 2 × 16 GB DDR5-5600, 89.6 GB/s |
| Screen | 13.6″ or 15.3″, Retina, 60 Hz, notch | any |
| Cooling | passive (no fan) | fan |
| Graphics API | **Metal only**; Vulkan through MoltenVK or KosmicKrisp | Vulkan (AMD) |
| Host page size | **16 KiB** | 4 KiB |

The M5 figures are Apple's published specifications, not measured here.

The test Mac, read over SSH on 2026-11-17: MacBook Air 15″ (`Mac17,4`),
M5 with a 10-core CPU (4 super, 6 efficiency) and a **10-core GPU**
(Metal 4), **24 GB**, 2880×1864, macOS **27.0.1** (26A434), page size
16384 confirmed. Command Line Tools installed (Apple clang 21.0.0); no
Xcode, Homebrew, CMake or Ninja. **Hypothesis**: the GPU and memory bandwidth are well above the
760M's, and the CPU is faster per core. Sustained clocks under passive
cooling are what to measure, not peak clocks.

What differs from both earlier targets:

1. **The host is arm64.** Every earlier build ran on x86-64. The guest is
   ARMv7 (Thumb-2, VFPv3, NEON). The M-series has no AArch32 mode, so
   nothing runs directly: dynarmic still translates A32 to A64, and the
   recompiled C++ is compiled for arm64.
2. **No native Vulkan.** Vita3K's renderer is Vulkan (OpenGL on macOS
   stops at 4.1, below what Vita3K needs). Vulkan runs through a layer
   over Metal.
3. **16 KiB pages**, against the Vita's and the PC's 4 KiB.
4. **Code signing and Gatekeeper** for anything downloaded.

## Routes

1. **Native arm64 build** of the fork's single-game frontend, with the
   recompiled modules compiled for arm64 (`ssd_aot_<module>.dylib`). This
   is the target.
2. **Rosetta 2** with an x86-64 macOS build. Rejected: x86 code that a JIT
   writes runs through Rosetta's slow path, and Apple keeps Rosetta 2 for
   general apps only through macOS 27 (fall 2026). From macOS 28 it covers
   only certain older apps.
3. **The Windows build under Wine** (CrossOver, or the Game Porting
   Toolkit's D3DMetal with MoltenVK for Vulkan): x86 emulation under
   Rosetta again, plus Wine. Rejected for the same reason.

Upstream Vita3K's CI already builds macOS arm64 (`ci-macos-arm64` preset,
`macos-latest` runners, `.ci/setup-macos.sh`). Upstream's macOS arm64
build on the M5 is the reference baseline, just as the AppImage was on the
Deck.

## What the code needs (survey 2026-11-17)

| Component | State | Work |
|---|---|---|
| Vita3K core, audio (cubeb), network | macOS arm64 supported upstream (CI) | build and test |
| JIT (dynarmic) | an `arm64` backend (oaknut) and `exception_handler_macos.cpp`. oaknut allocates `MAP_JIT` and toggles `pthread_jit_write_protect_np` | none expected. The dump run (`--dump-elfs`) and the fallback run on it |
| Fork's dynarmic integration (D7: `PreCodeReadHook`, nested JIT loop, sentinel `lr`) | frontend-side callbacks, written against the x64 backend | **hypothesis**: backend-neutral. Check the arm64 backend's handling of the sentinel return and of halts |
| Guest memory (`mem/src/mem.cpp`) | reserved at `1 << 34`. `host_page_size` comes from `sysconf`, so 16 KiB is handled. macOS raises **SIGBUS** for `PROT_NONE` and gets the same handler. The arm64 fault decoding reads ESR from `uc_mcontext->__es` on macOS works on the M5. Write tracking now protects whole host pages (16 KiB): see *Our fork on the M5* |
| **Memory mapping** (renderer) | `renderer.cpp` forces `support_memory_mapping = false` on `__APPLE__` ("a copy of the vertex buffer for MoltenVK"), so only `disabled` is possible. Our frontend fixes `double-buffer` (D4 update 4) **answered**: `double-buffer` works on MoltenVK and is needed; the override is gone (below) |
| Vertex streams | upstream's `restride_stream` was Metal-only. Our patches 0003/0004 repack misaligned streams on every platform confirmed: the override isn't needed (2026-11-17) |
| Renderer patches (0002–0004, 0018, 0019, 0032, 0039, surface sync, shader interlock) | written and checked on AMD and NVIDIA | test on MoltenVK. Shader interlock maps to Metal raster order groups |
| AOT loader (`cpu/src/aot.cpp`) | non-Windows branch uses `dlopen(RTLD_NOW \| RTLD_LOCAL)` | none expected |
| Module scan (`game-frontend/frontend.cpp`) | `.dll` on Windows, `.so` elsewhere | `.dylib` on macOS (done) |
| Single-game executables (`vita3k/CMakeLists.txt`) | built on `WIN32` or Linux only. Named `<id>.<arch>` on Linux | built on APPLE too, `<id>.arm64` (done). Decide between a bare executable in a folder and an `.app` bundle (below) |
| Config, logs, shader cache | next to the executable (`ctx.exe_dir / <id>`) | fine in a plain folder. **Inside a signed `.app` bundle this breaks the signature**: there, use `~/Library/Application Support/<id>` |
| Test input pipe | a FIFO on Linux (11b) | works on macOS. The reader reopened the FIFO at each end-of-file, a race that killed a shell driver now and then; fixed for both (fork `60cf6936`, *The map sweep* below) |
| Recompiler runtime (`armrecomp.h`, `neon.h`) | plain C++20, no intrinsics, no `#ifdef` per host. NaN rules, default NaN, flush-to-zero, saturation and rounding are done in software (`process_nans`, `arm_nan`, `single_to_half`) | none expected for correctness. See *floating point* below |
| Barriers | `dmb`/`dsb` → `std::atomic_thread_fence(seq_cst)` (`semantics.py`). `ldrex`/`strex` → CAS through `std::atomic_ref` | correct on a weakly ordered host. x86's TSO hid nothing here, because the fences were already real |
| Guest loads and stores | `volatile` accesses at `g_guest_base + a` | arm64 allows unaligned plain accesses, as ARMv7 does. Exclusives must be aligned on both |
| Escapes (D7, D9) | a C++ exception thrown through generated frames works: 23,420 escapes in a native ST03A run on the M5 |
| Recompiler CMake | `-O1 -w`, PIC, hidden visibility. `--exclude-libs` already skipped on APPLE `-ffp-contract=off` added (also in the zig flags). `.dylib` names come from CMake. Only `armrecomp_aot_init` is exported (hidden visibility) |
| Dynarmic tests (`run-tests`) | compare native code against dynarmic on the host 0 failing on the M5 (23,280 instruction and 684 function tests) |
| Kit (`gameproject.py`, `build-vita3k.py`, `install-game.py`, `make-dist.py`, setup) | `WINDOWS = sys.platform == 'win32'`, everything else is treated as Linux | done (D21): `MACOS`, `.arm64`/`.dylib`, zig for `aarch64-macos`, the Apple-clang fork build, MoltenVK in the folder, `setup.command` and the app, `make-setup.py resolve-macos`/`build` |
| Kit: `v3kdrive.py` | Windows backend. The Linux backend (11b) is still open | its POSIX backend covers macOS too (process, `SIGTERM`, FIFO) |
| `games/ss-delta/` | portable (Linux build) | icon: `.icns` for a bundle |
| Ad Hoc Play `local` mode (127.0.0.N) | Windows and Linux route the whole 127/8 | **macOS configures only 127.0.0.1 on `lo0`**. Players 2–4 need `ifconfig lo0 alias 127.0.0.N` (root) or another addressing scheme. The `lan` mode works: a Mac joined a Windows host with a Deck and played a quest, after macOS's Local Network prompt was allowed (*Ad Hoc Play across platforms*) |

### The memory mapping question

D4 update 4 makes `double-buffer` mapping a requirement on Windows. On
Windows, `external-host` hides objects. `disabled` crashed in the Phase 0
baseline, but that was before the Vulkan crash fix (patch 0002), so it
was never tested in a working build. On macOS upstream allows only
`disabled`. Three outcomes, in order of preference:

1. **The override is obsolete in the fork.** The vertex copy it mentions
   is what 0003/0004 now do everywhere. Mapping also needs
   `bufferDeviceAddress` and `uniformBufferStandardLayout`; MoltenVK on
   Metal 3 has both (**hypothesis**: check `vulkaninfo` on the M5).
   Test: build the fork on the Mac without the `__APPLE__` override, run
   with `double-buffer`.
2. **`disabled` renders the game correctly.** This can be checked on the
   Windows test PC before the Mac is set up. It needs a `[debug]` switch
   for the mapping in `ss-delta.ini` and a separate shader cache, because
   the cached shaders are keyed by guest shader, not by mapping mode
   (02-baseline).
3. Neither: port the double-buffer path to Metal's constraints.

### Floating point on an arm64 host

* The VFP/NEON semantics are emulated in portable code, so the host's own
  NaN and denormal rules don't leak through. On x86, each NaN fix-up
  corrected the host's "indefinite" NaN. On arm64 the host already
  produces ARM's default NaN, so the fix-ups become no-ops.
* **Contraction.** On arm64 every core has `fmadd`. Clang's default
  (`-ffp-contract=on`) fuses `a * b + c` within one expression. GCC's
  default in GNU mode (`fast`) also fuses across statements. ARMv7
  `vmla`/`vmls` are **unfused** (two roundings). The recompiler already
  emits them as `fp_add(D, fp_mul(...))`, which `on` does not fuse, but
  generated code must not depend on the compiler's default: build the
  modules with `-ffp-contract=off`. On x86 the baseline CPU has no FMA, so
  this never came up.
* `std::fmaf` (the fused `vrecps`/`vrsqrts` steps in `neon.h`) becomes one
  instruction instead of a libm call.
* The dynarmic tests check all of this. On an arm64 host the reference
  (dynarmic's A64 backend) is new too, so a mismatch has two suspects.

## The setup on macOS (D18)

D18 forbids shipping recompiled game code, so the Mac compiles the
generated C++ itself, as the Deck does. Options for the compiler:

* **zig**, as on Linux (D20): one download that also targets
  `aarch64-macos`. It brings libc++ and the macOS libc headers and links
  against `libSystem` stubs, with no Xcode.
* **Apple's Command Line Tools** (`xcode-select --install`): Apple clang
  and the SDK, a download of about 1 GB through Software Update. The
  player accepts Apple's licence, and it is the best-tested toolchain on
  the platform.

**Chosen: zig** ([D21](decisions.md)), measured on the M5 (2026-11-17):

* `zig-aarch64-macos-0.17.1` (51 MB, SHA-256 as on ziglang.org's index).
  Target `aarch64-macos.13.3`, `-mcpu=apple_m1`, the kit's flags
  (`-O1 -ffp-contract=off` for generated code).
* **zig's Mach-O linker signs ad hoc** (`flags=0x20002(adhoc,linker-signed)`),
  so the modules load as they are. `minos 13.3`. It rejects
  `-exported_symbol` and ignores `-exported_symbols_list`. With hidden
  visibility a module exports `armrecomp_aot_init` and libc++'s
  `operator new`/`delete`, harmless under two-level namespaces. A test
  module threw and caught a C++ exception inside itself when loaded by an
  Apple-clang host.
* **Ten modules in 2.8 min with 8 jobs** (the first build of libc++
  included), largest compiler process 806 MB. Apple clang: 95 s.
  `ssd_aot_eboot.dylib` is 80 MB (Apple clang: 97 MB).
* ST03A on the zig modules: every module matched guest memory, **60.0 fps**
  (p99 17.0 ms), 0 native-to-JIT calls, 24,948 escapes (C++ exceptions
  through zig-built frames), pictures as on Windows.

The setup itself: python-build-standalone 20261026's CPython 3.12.16 for
`aarch64-apple-darwin` (25 MB, Tk 9.0, OpenSSL 3.5), capstone 5.0.7's
universal2 wheel and PyYAML 6.0.3's arm64 wheel (`setup-macos.json`,
`make-setup.py resolve-macos`). The same setup window builds on macOS; the
Steam checkbox is Linux-only, and the shortcut box puts the app in
`~/Applications`.

### The setup end to end on the M5 (2026-11-17)

`make-setup.py build setup-macos.json` on the Mac, with the fork built
there: a **43 MB `.tar.gz`** (180 MB unpacked). Then, as a download:

1. The archive marked quarantined (`com.apple.quarantine`, as Safari sets
   it) and unpacked with Archive Utility: all 1,846 files quarantined.
   `spctl` rejects `setup.command` and `python3.12`.
2. `sh setup.command` (the README's Terminal route; double-clicking it
   needs Open Anyway once): it cleared the quarantine from the folder, 0
   files left, and Python started.
3. The console setup with the US dump, a new cache and a new playable
   folder: firmware from Sony (182 MB) and zig downloaded, the game
   installed, run for 45 s to write the modules, recompiled (the eboot's
   code hash `f6f20671281686e3`, as on Windows and Linux), compiled with
   6 jobs. **5.6 min in all**, largest process 3.5 GB. The playable folder
   is 3.4 GB.
4. `open "Soul Sacrifice Delta.app"` (as a double-click): the game started
   on native code and reached the title, no errors. The ini's texts name
   `ss-delta.arm64` and `.dylib`.

**The owner's run** (2026-11-18): a setup built from the committed kit
and fork (kit `60b1bf2`, fork `bc449f9a`), put in Downloads with
Safari's quarantine flag; unpacked, `setup.command` through Open Anyway,
the window with the US zip, the shortcut box on. The setup finished, the
game runs, and the window looks right. The owner's suggestion: don't ask
for parts the dump already holds. Since kit `2b39018` the setup reads
the dump's `param.sfo` files (`dumpinfo.py`; zips, vpks, folders): for
a NoNpDrm zip with `app/` (1.00, `sce_sys/package/work.bin`) and
`patch/` (1.30) the Update row reads "in the game's dump (1.30)", and
the Licence rows show only for a pkg or a dump without a licence inside.
The console flow skips the update question the same way. Not
macOS-specific.

**The Dock icon** (the owner, 2026-11-18): the game's icon shows while it
runs, but square and larger than the other apps'. macOS doesn't shape app
icons; the artwork must be Apple's grid, an 824-point rounded square
(corner radius about 185) in a 1024-point canvas. The game's `.ico` is a
256-pixel square with only an 8-pixel margin. Since kit `49a3a5b` the setup
crops the picture to its opaque part, draws it into that shape with a
slight shadow (AppKit through `osascript -l JavaScript`, so nothing beyond
macOS's own python3), and builds the `.icns` with `iconutil` from an
iconset of 16 to 1024 pixels (`sips` alone writes `.icns` only up to 512
and failed on the 1024 picture). The shaped icon then showed only at
launch: once the window opened, the game's square `icon0.png` replaced it,
because on macOS `SDL_SetWindowIcon` sets the Dock icon (there are no
window icons). Since fork `e0a324a8` the front end skips it on macOS.
Checked by the owner on the M5: the rounded icon stays in the Dock while
the game runs.

**Game Mode** (2026-11-18): in fullscreen macOS gives a game the CPU and
GPU first, keeps background work on the efficiency cores, and doubles
the Bluetooth rate for controllers. A game needs `LSSupportsGameMode`
(macOS 26) or `GCSupportsGameMode` (14 and 15) in its Info.plist, a
games category, and macOS's own fullscreen. SDL's fullscreen (F11,
Option+Return, the green button) is that: the window list showed the
window covering the display below the notch, with the hidden title bar
above. With the keys set, Game Mode still didn't start. The app's
script `exec`ed the binary in the playable folder: LaunchServices tied
the process to the bundle (`lsappinfo`: the bundle ID and path), but
`gamepolicyd` looks the bundle up from the process
(`bundleRecordForAuditToken:`), and that executable isn't in one. A test
bundle with the binary itself in `Contents/MacOS` got Game Mode at once
(the menu bar's controller icon; the owner). The setup builds the app
that way since kit `60b1bf2`:

* `Contents/MacOS` holds a copy of the game's binary and of
  `libMoltenVK.dylib` (found through the rpath `@executable_path`);
* `LSEnvironment` sets `VITA_RECOMPS_GAME_DIR` to the playable folder,
  which the front end uses as its own folder (fork `bc449f9a`), so the
  copy in `~/Applications` uses the same settings and saves.
  `SDL_FILESYSTEM_BASE_DIR_TYPE = parent` (the folder holding the app)
  covers a missing variable;
* the bundle is signed ad hoc as a whole (`codesign -s -`), so the
  signature includes its Info.plist.

Checked on the M5: the `~/Applications` copy started from Spotlight
logged to the playable folder, loaded its native modules and saves, and
showed Game Mode in fullscreen (the owner). The app holds about 70 MB
more than the old script; each copy does.

## Packaging, signing and Gatekeeper

* Everything must be signed on arm64 macOS. An ad-hoc signature
  (`codesign -s -`, which Apple's linker applies by default) is enough to
  run locally built code. Modules the setup compiles on the player's Mac
  are never quarantined.
* **What the player downloads is quarantined** (the setup archive, and the
  frontend executable inside it). Without a Developer ID signature and
  notarization, Gatekeeper blocks it. Since macOS 15, Control-click → Open
  no longer bypasses this. The player has to use System Settings →
  Privacy & Security → "Open Anyway", or run
  `xattr -dr com.apple.quarantine` on the folder.
* A Developer ID costs Apple's yearly developer fee. Notarization also
  requires the hardened runtime, which then needs entitlements:
  `com.apple.security.cs.allow-jit` (dynarmic) and
  `com.apple.security.cs.disable-library-validation`, because the
  setup's ad-hoc signed `.dylib` files come from another signer. The owner
  decides whether to pay for one. Without it, the README documents the
  quarantine step. **Done that way** (D21): only `setup.command` goes
  through Open Anyway, and it clears the quarantine from the rest of its
  folder (tested above).
* **Folder or bundle.** A plain folder (`ss-delta.arm64`, the
  `.dylib`s, `fs/`, `ss-delta.ini`) matches Windows and Linux and keeps
  config next to the executable. An `.app` bundle is what Mac users expect
  (Dock icon, double-click), but it must not be written into. Its config,
  log, shader cache and modules then go to
  `~/Library/Application Support/<id>/`. **Chosen** (D21): the folder,
  plus a small `<name>.app` the setup makes there. The app is a script that
  starts the executable, with the game's icon. **Since D22** (2026-11-18)
  the release *is* that folder, with the app already in it: the bundle runs
  the executable itself (`Contents/MacOS/ss-delta`, MoltenVK beside it),
  and the folder holding it is the game's (`SDL_FILESYSTEM_BASE_DIR_TYPE =
  parent`). The player lets the app through Open Anyway instead of
  `setup.command`. A quarantined app is then run from a read-only,
  translocated copy that holds only the app (App Translocation). The
  front end asks Security.framework (`SecTranslocateIsTranslocatedURL`,
  `SecTranslocateCreateOriginalPathForURL`, by `dlsym`) for the original
  path. It clears `com.apple.quarantine` from the folder (also before it
  starts the importer's Python), and starts itself again from there with
  `open -n`.
* MoltenVK: upstream links it (`MoltenVK/mvk_vulkan.h`) and bundles
  `libMoltenVK.dylib`. KosmicKrisp (LunarG, Mesa) is a Vulkan 1.4
  conformant driver over Metal, shipped in the Vulkan SDK, with reported
  MoltenVK feature parity and better performance. **Hypothesis**: worth
  trying behind the same loader if MoltenVK has rendering faults.

## Mac-specific work

* **Screen**: Retina (2560×1664 on the 13″). SDL3's pixel density gives
  the backbuffer size. 2× (1920×1088) fills most of it. The notch: in
  fullscreen, macOS letterboxes below it by default
  (**hypothesis**: fine for a 16:9 image on a 16:10 screen).
* **Controls**: SDL3 uses Apple's Game Controller framework (DualSense,
  Xbox pads). Keyboard as on Windows. The trackpad as the front touch: the
  mouse already is, and two-finger gestures could serve as the back touch
  (to design).
* **Thermals and battery**: passive cooling. Measure 60 fps against 30 fps
  over a long quest, and the CPU/GPU clocks when warm.
* **Shader cache**: Metal compiles again under MoltenVK. First-use stalls
  as on other platforms, and the pipeline cache files are MoltenVK's.

## Baseline: upstream Vita3K on the M5 (2026-11-17)

Upstream's `macos-arm64-latest.dmg` (v0.2.1 4369-1a21f9cb, continuous
build of 2026-11-17): `Vita3K.app`, arm64 only, **ad-hoc signed, no
hardened runtime, no entitlements**, `LSMinimumSystemVersion` 13.3, with
`libMoltenVK.dylib` (1.4.1) and Qt in the bundle. Downloaded with `curl`
over SSH, so it was not quarantined. Run in portable mode (a `portable/`
folder next to the bundle) on the test file system: the `ssd-check` copy
(firmware, game, test saves), 3.3 GB. Settings as on the Deck: Vulkan,
`high-accuracy: true`, surface sync on, 1×.

* Vulkan device "Apple M5" through MoltenVK. **Memory mapping: Disabled**
  (the `__APPLE__` override). Shader interlock is in use (RGBA4444
  surfaces fall back to RGBA8).
* Boots to the title, the main menu, the hub and a quest (the snow map,
  ST03A) without a crash or hang. **26–29 fps** at the game's 30 fps
  (the window title: 35–39 ms a frame), on the JIT.
* What the owner saw, and the screenshots confirm: **too bright and hazy**,
  most clearly in the snow. And **ST03A's black water patches** in the
  opening fly-through. The water is upstream's per-vertex depth clamp,
  which the fork fixed (patch 0032). **Hypothesis**: the brightness is one
  of the fork's other fixes, the colour-output clamp (`a32f1c4c`) or the
  synced exposure meter (02-baseline). Neither says anything about macOS.
  The same check with our fork is what counts.
* Screens can't be captured over SSH (`screencapture`: "could not create
  image from display": the SSH session has no Screen Recording permission).
  The owner's Cmd+Shift+3 screenshots, fetched from the Desktop, or our
  fork's `frame:`/`record:` steps (read back on the render thread) work.

## Our fork on the M5 (2026-11-17)

Built on the Mac itself: the fork at `b51c08d8` (cloned from GitHub,
the newest commit from a bundle), CMake 4.5.0, Ninja 1.13.2, Apple clang
21, `Ninja Multi-Config`, `VITA3K_GAMES_ONLY=ON`,
`USE_DISCORD_RICH_PRESENCE=OFF`, `FORCE_BUILD_OPENSSL_MAC=ON`,
`VITA3K_FORCE_CUSTOM_BOOST=ON`, `Python3_EXECUTABLE` = python-build-standalone
3.12.16. **Configure 82 s** (Boost, OpenSSL 4.0.1 and MoltenVK 1.4.1
fetched and built), **build 1 min 40 s**: `ss-delta.arm64` (63 MB), next to
`libMoltenVK.dylib`. Fork changes:

* the single-game executables on APPLE too (`<id>.arm64`, rpath
  `@executable_path`, `libMoltenVK.dylib` copied by `games-runtime-files`);
* the module scan looks for `ssd_aot_*.dylib`;
* upstream's `__APPLE__` override that disabled memory mapping is gone
  (below);
* write tracking in whole host pages (below);
* `VITA3K_FRAME_LOG` also written without memory mapping;
* the ini's texts name `<id>.arm64`, `.dylib` and a macOS example path
  (they had Linux's);
* the frontend logs why a session ends ("Quit requested (quit event)" or
  "(window closed)", "The emulation stopped"). SDL turns `SIGTERM` into a
  quit event.

The input FIFO (`/tmp/<VITA3K_INPUT_PIPE>`) and its `screenshot`/`record`
commands work unchanged. A small shell driver with `v3kdrive.py`'s steps
and timings (`build/macos/drive.sh`, not committed) ran the map sweep's
ST03A route: Stage Select index 2, `record 600` from the quest's start,
the sweep's shots after 40 s.

| ST03A, 1× | JIT, mapping `disabled` | JIT, `double-buffer` | JIT, `double-buffer`, host-page tracking | **native**, the same |
|---|---|---|---|---|
| last 20 s | 58.1 fps, worst 423 ms | 59.4 fps, worst 257 ms | 57.8 fps, p50/p90/p99 17.3/22.3/28.8 ms, worst 39 | 54.8 fps, p50/p90/p99 18.1/21.6/23.0 ms, worst 25 |
| snow | **blown out** (as upstream, and as the 4090 with surface sync off) | as on Windows | as on Windows | as on Windows |
| water patch (0032) | — | none | — | none |
| unhandled write faults | 4 | 21 | **0** | 0 |

Each picture was compared with the Windows sweep (`build/maps-60/ST03A-*`).
The water check looked at every third recorded frame for dark pixels in
the lower half of the picture: none.

* **Memory mapping works on MoltenVK** and is needed: without it the
  exposure meter's surface (02-baseline, "60 fps on a discrete GPU")
  isn't synced and the snow is blown out. That is the brightness the
  owner saw in upstream. Upstream disabled mapping on Apple because
  MoltenVK needed a copy of every vertex stream. The fork repacks the
  streams that can't be fetched in place on every platform (patches
  0003/0004), so the override is gone.
* **16 KiB pages and write tracking.** `add_protect` aligned tracked
  regions to the Vita's 4 KiB (`align_to_page`, `STANDARD_PAGE_SIZE`),
  `mprotect` to the host page (16 KiB). A write to a neighbouring 4 KiB
  in the same host page found no region in `protect_tree`. The handler
  then logged "Unhandled write protected region was valid" and
  unprotected the whole host page ("HACK: keep going"). The regions in
  that page stayed in the tree but were no longer watched, so their next
  writes went unseen. Fix: tracked regions now cover whole host pages,
  and one fault fires every callback in its page. A second bug was in
  the same function: the merge loop compared against the caller's
  unaligned end, so a segment further on in the same pages was not
  merged. That one could also hit 4 KiB hosts. Windows, with the fix:
  ST03A natively, 0 unhandled faults, 0 native-to-JIT calls, 60 fps,
  pictures as before.
* **Native code on arm64.** The generated C++ from the PC (626 MB, never
  committed) compiled with Apple clang, `-O1 -ffp-contract=off`:
  **95 s for all ten modules with 8 jobs**, largest compiler process
  437 MB (Deck: 847 s; WSL: 7.1 min; MSVC: 9.8 min). `ssd_aot_eboot.dylib`
  is 97 MB. In the game every module that loaded matched guest memory.
  0 native-to-JIT calls, 6.7 G native guest instructions, 23,420 escapes
  (C++ exceptions through generated frames, as on Windows).
* **The dynarmic tests on arm64** (dynarmic's A64 backend as the
  reference, `recomp_tests 256 * 64`, under a time and memory guard):
  **23,280 instruction tests and 684 function tests over the ten
  modules, 0 failing.** The tests' CMake now links Zydis only where
  dynarmic built it (x86-64 hosts).
* Native was slower than the JIT at first (54.8 against 57.8 fps): see
  *Frame pacing* below, fixed.
* MoltenVK warns "Metal does not support disabling primitive restart"
  (`[mvk-warn]`, stdout) for some pipelines. **Hypothesis**: harmless,
  since the game's index buffers don't contain 0xFFFF by accident. To
  check on a map with odd geometry.
* One run ended early: the game shut down normally, half a second after
  a screenshot and 7 s before the script's `SIGTERM`. The owner did not
  close the window. **Hypothesis**, likely: the input pipe race found in
  the map sweep (below) killed the driver at its next command, and the
  script went straight on to its `SIGTERM`. The sweep's early ends looked
  the same ("Quit requested (quit event)", shots missing).
* dynarmic prints "Unhandled EXC_BAD_ACCESS at pc ..." (stdout, 5 with
  `disabled`, 1,007 with `double-buffer`): noise, the macOS form of the
  Linux "Unhandled SIGSEGV" lines (07-linux).

## Frame pacing: timed waits on macOS (2026-11-17)

Natively, ST03A first ran at 52–54 fps, the JIT at 54–56. Windows holds
59.9 fps in the same measurement. The measurement: Stage Select into
ST03A, 30 s standing still, the last 9 s of `VITA3K_FRAME_LOG`, three
interleaved runs per configuration (`build/macos/perf.sh`).

* **Not the code.** `ps -M` and `sample` showed every thread waiting
  nearly all the time; the busiest thread used about 33% of a core. The
  frame times spread from 15 to 22 ms (p50 18.2) instead of snapping to
  vblanks.
* **Not the cores.** QoS `USER_INTERACTIVE` on the frame-critical threads
  (the first **hypothesis**: guest threads on the efficiency cores)
  changed nothing over repeated runs (53.8 against 54.2 fps). Neither did
  `taskpolicy -l 0 -t 0`, nor vsync off.
* **Timed waits wake late.** A benchmark (`build/macos/overshoot*.cpp`,
  not committed): `nanosleep`, `pthread_cond_timedwait` and even
  `mach_wait_until` all wake **25% of the wait late, up to 5 ms, while the
  user is active** (`caffeinate -u`), and **50%, up to 10 ms, when the
  user is idle**. A 16 ms wait wakes 4 or 8 ms late. QoS `USER_INTERACTIVE`,
  `NSProcessInfo` `NSActivityLatencyCritical` and `taskpolicy -l 0`
  don't change it; started from Terminal in the GUI session, it is the
  same. Low Power Mode is off.
* The game waits out its 16,000 µs frame timer and then flips on the next
  vblank ([D16](decisions.md), fork `7f8a001c`): 0.67 ms to spare. The
  emulated vblank is a timed sleep too.
* **Real-time threads wake on time.** `THREAD_TIME_CONSTRAINT_POLICY`
  (computation 5 ms, constraint 10 ms, preemptible): about 10 µs late at
  every length. In the game (fork `09587ca1`, `util::raise_thread_qos()`
  at the start of guest threads, the vblank, render, GXM display and GPU
  wait threads, and the session loop): **60.0 fps natively, p50/p90/p99
  16.7/16.7/16.8 ms** standing still, **60.0 fps, p99 17.0 ms** on the
  moving route (0 native-to-JIT calls). The JIT reaches 60.0 too, with a
  worse tail (p99 28.7 ms). The vblank thread alone isn't enough
  (52 fps): the game's frame timer runs on a guest thread.
* macOS demotes a real-time thread that computes past its budget without
  blocking, so a busy guest thread (loading) can't starve the system.
  `VITA3K_QOS=0` turns it off. **Hypothesis**: Core Audio's own real-time
  thread is unaffected (it has a higher priority); to listen for
  crackles in play.
* Every measurement over SSH so far ran with the user idle (50% slack),
  a state a player never plays in. The fix makes that irrelevant.

## The map sweep on the M5 (2026-11-17)

`tools/map-sweep.ps1`'s 50 maps, driven the same way by a shell copy
(`build/macos/sweep.sh` with `drive.sh`, not committed): Stage Select
index per map, the quest started, six shots over 40 s with camera moves
and the Mind's Eye view, and `VITA3K_FRAME_LOG`. Native code,
`double-buffer`, real-time threads, fork `9b380165` (then `60cf6936` for
the seven maps run again). User idle (SSH), `caffeinate -i -s`.

* **Every map loads and plays at 60 fps.** Over each map's last 10 s:
  60.0 fps on 47 maps, p99 at or under 17.2 ms on all 50. ST22A, ST22C and
  ST23A show 59.8–59.9 fps with one 44–51 ms frame; in those three runs
  the player died during the shots (**hypothesis**: the death transition).
  On the Radeon 760M the sweep had dropped to 56 fps on ST16A
  (GPU-bound); the M5 doesn't drop.
* **0 native-to-JIT calls, 0 unhandled write faults, 0 critical log lines
  on every map.**
* **The pictures match Windows.** Each map's shots were laid out on
  contact sheets against the Windows sweep (`build/maps-60`): same
  lighting, fog, water, particles and effects on all 50. The differences
  are gameplay timing (enemy positions, camera, the player dying in three
  boss maps). The first in-quest shot, whose camera is the same in both,
  has the same mean brightness within a few levels on most maps.
* **ST16A's unhandled faults** (38–46 per run after the host-page fix
  above) were a race, likelier with 16 KiB pages: two threads fault on
  the same page, the first one's segment is unprotected and erased, and
  the second, once it gets the lock, finds no segment. On macOS the handler
  now checks the page's protection (`mach_vm_region`) and retries when
  the access is allowed: 0. Two related fixes in the same commit
  (`9b380165`): an allocation's `mprotect` of its whole host page no
  longer unprotects tracked segments that share it, and unmapping an
  external mapping now notifies and unprotects every segment it erases,
  not just the mapping's own pages.
* **The input pipe race.** Seven maps ended early, with 0–5 of their 7
  shots: "Quit requested (quit event)" in the middle of the route. The
  fork's FIFO reader closed and reopened the FIFO at each end-of-file. A
  driver that opened it in that window got `SIGPIPE` at its write, and the
  sweep then went straight to its `SIGTERM`. The reader now keeps the FIFO
  open read-write (fork `60cf6936`, also Linux's code). The seven maps
  run again: 7 shots each, driver exit 0, 60.0 fps, the same pictures as
  Windows.
* MoltenVK's "Metal does not support disabling primitive restart"
  appears on every map. No geometry glitch in any of the 350 shots.

## Ad Hoc Play across platforms (2026-11-17)

`network = lan` on the PC (Windows, Wi-Fi; `adapter = 1`, as Hyper-V's
adapter comes first), the Mac (`adapter = 0`, en0) and the Deck
(`adapter = 0`, wlan0), each through a `ss-delta-player<N>.ini` override,
with copies of the same story-complete save. **The PC hosted, the Mac and
the Deck joined; all three showed the same lobby. The owner readied them,
started the quest and played it to the results page (same clear time
on all three, the return-to-lobby countdown on each), without issues.**

* **macOS asks for Local Network access** ("find and connect to devices
  on your local network") when the game starts. Until it is allowed,
  broadcasts still go out and come in (the Mac listed every room), but
  every unicast send fails with `EHOSTUNREACH` (`0x80410141`), so each
  join ended in "Failed to join room". A copy started over SSH counts as
  part of SSH: the owner's Allow did not cover it, even after a restart.
  Started through an app (`open`, as a player starts the setup's app),
  macOS asked at the start, and after Allow the Mac joined at once. The
  player's README says so.
* Found with a P2P trace: `VITA3K_NET_TRACE=1` logs every datagram the ad
  hoc sockets send or receive, with address, port and result (no packet
  capture needs root then). Ports seen: the Vita3K peer records, 80
  bytes, are broadcast to 3658 + 33333; the game's room announcements,
  516 bytes, go to 3659 and 3660; a join is a 105-byte unicast to the
  host's 3659.
* **A Deck or a Mac as host could not be joined** (the joiner showed
  "Failed to join room", the host "Connecting..."). Both traces showed the
  join handshake, then nothing: on a PC host the game sent its first
  packet 4 ms after the joiner's acknowledgement. The cause is latency,
  not the platform. The game creates its matching contexts
  (`sceNetAdhocMatchingCreate`, eboot `0x818a2e48` and `0x818a3150`) with
  an 8 ms retransmit interval and 3 retries, so a joiner gives up after
  about 25 ms. Pinged from the PC, the Deck answered in 3 to 314 ms and
  the Mac in 3 to 87 ms (Wi-Fi power saving); the PC answers in 2 ms. With
  the Deck's power saving off (SteamOS's
  `steamos-disable-wireless-power-management`), the PC and the Mac joined
  it. **Fix (fork `c5654710`)**: when native code calls the firmware
  module's `sceNetAdhocMatchingCreate`, the retransmit interval is raised
  to at least 250 ms (log: "retransmit interval 8000 us raised to 250000
  us"). Tested: the Mac hosting with power saving on, the PC and the Deck
  joining. Dropping duplicate join requests on the host, tried first,
  didn't help: the joiner had already given up.
* **The Mac stopped responding after leaving a room** (menus ignored
  input, rendering went on). `sample` showed the game's MainThread in
  `sceKernelWaitThreadEnd` for its network thread, which sat in
  `recvfrom()`. On POSIX hosts closing a socket doesn't wake a blocked
  receive, and `shutdown()` of a UDP socket fails on macOS. Fix (fork
  `e41caf0d`): an aborted or closed datagram socket sends itself an empty
  datagram. Seen to work once (leaving a hosted room on the Mac).
* **"A network error has occurred" after leaving a hosted room** (Deck and
  Mac, searching right after leaving). Leaving makes the matching module
  abort, shut down and close its two sockets and open new ones. On POSIX,
  `sceNetSocketAbort` called `shutdown()`, which fails with ENOTCONN on an
  unconnected UDP socket; the module took the error as fatal, the ad hoc
  connection dropped ("Adhoc thread: stopping network loop" when the room
  was left) and the next search failed. Fixed by `e41caf0d` too: the abort
  now wakes the receive itself and returns 0. Checked on the Deck: leave
  as host (both a migrated and a freshly created room), search, no error,
  the ad hoc loop keeps running. `sceNetShutdown` of the receive side
  still returns ENOTCONN (`0x80410139`), as Winsock does; the module
  ignores it.
* **A Deck started from Game Mode hosted a room nobody saw** (2026-11-18,
  the owner). Game Mode starts player 1, which reads `ss-delta.ini`, and
  that still had the default `network = local`: every ad hoc socket was
  bound to 127.0.0.1 (`ss -uanp`). The tests above had used
  `ss-delta-player<N>.ini` overrides. Fix (fork `6cdbf678`,
  `games/ss-delta/main.cpp`): `lan` is the default on Linux and macOS,
  `local` stays the default on Windows (no firewall prompt at the first
  start). Checked: the Mac build's `--write-ini` writes `network = lan`.
  Existing installs keep the `network = local` their setup wrote. With
  `lan` set, the owner hosted from the Deck in Game Mode, with power
  saving on, and the PC found and joined the room. Then the Mac hosted,
  started from the setup's app (with the fixed binary and `network =
  lan`): no problems either (the owner).
* **Colours, Deck against PC** (the owner saw a slight blue tint on the
  Deck): a gamescope capture (`gamescopectl screenshot`) against a capture
  of the PC's window, both standing at the same spot in a quest. The
  compass (fixed HUD) matches within 1 of 255 per channel, and blue
  against red differs from region to region in both directions (camera
  angle). The game renders the same picture; the tint comes from the
  Deck's panel (**hypothesis**: its colder white point and smaller gamut,
  not checked against a colorimeter).
* Still open: the Deck ignored input once at the save's "Loading
  complete" prompt. When a host quits, a guest becomes the host ("You are now the
  host").
* The save dialog (Vita3K's overlay) is not in `frame:` captures, and its
  load prompt defaults to No: a script needs right, then confirm.

## Developing on the Mac

* **Access**: SSH to the Mac (System Settings → General → Sharing →
  Remote Login), with a key, as for the Deck. Builds and runs over SSH.
  GUI runs need the logged-in session: a process started over SSH can
  open windows when started in the user's GUI session
  (**hypothesis**: `launchctl asuser`, or `open` on a bundle).
* **Build**: on the Mac itself (Xcode CLT or Homebrew's LLVM for the
  fork, Ninja, CMake), or in GitHub Actions on `macos-latest` (arm64) for
  the fork and the kit only. Nothing game-derived goes to CI (D2).
  Cross-compiling from Windows would need Apple's SDK, which its licence
  restricts to Apple hardware: not pursued.
* **The game data**: the firmware and the installed game copied from the
  test PC (as for the Deck), with a test user's saves. The owner's own
  saves stay on the PC.
* **Screenshots**: `frame:` and `record:` read back on the render thread
  and work as on Windows. The input pipe's `screenshot` command too.

## Next steps

Phase 12 in [03-plan](03-plan.md). Done: access and baseline, memory
mapping, the fork and native code on the M5, frame pacing, the 50-map
sweep, the setup (D21). Open: the release workflow's `macos` job on
GitHub, a long play session with audio, `v3kdrive.py`'s POSIX backend,
and the Mac polish of 12f.
