# 07 — Linux and the Steam Deck

Research started 2026-11-17, after the Windows port was finished (Phases
0–10, the shared toolchain and the EU version). The target is the Steam
Deck: it is the only Linux machine available, and a port that runs well
there runs on most Linux PCs.

Claims not yet checked on the Deck or in the code are marked
**hypothesis**.

## The target

| | Steam Deck (LCD / OLED) | Test PC (Radeon 760M) |
|---|---|---|
| CPU | Zen 2, 4C/8T, 2.4–3.5 GHz | Zen 4 7640HS, 6C/12T, up to 5 GHz |
| GPU | RDNA 2, 8 CUs, 1.0–1.6 GHz | RDNA 3, 8 CUs, up to 2.6 GHz |
| Memory | 16 GB LPDDR5, shared; 88 GB/s (LCD) / 102 GB/s (OLED) | 2 × 16 GB DDR5-5600, 89.6 GB/s |
| Screen | 1280×800 (16:10) | any |
| Vulkan driver | Mesa RADV | AMD's Windows driver |
| OS | SteamOS 3 (Arch-based, read-only root, KDE desktop mode, gamescope in Game Mode) | Windows 11 |

The Deck figures are from Valve's published specifications, not measured
here.

The test Deck (LCD, 512 GB), read over SSH on 2026-11-17: SteamOS 3.9.5
(build 20261023.100), kernel 7.2.7-valve, glibc 2.43, Mesa 26.1.2
(`vulkan-radeon` 26.2.0-devel), gamescope 3.16.30, 8 threads, 14 GB
visible to the OS, 215 GB free on `/home`. Installed: Proton 7.0–11.0 and
Experimental, Steam Linux Runtime soldier, sniper and 4.0
(4.0.20261021), `distrobox`, `podman` and `flatpak`. No Vita3K. The memory bandwidth is about the same as the test PC's, the GPU
clock about 60% of it, so the GPU is the first thing to measure
(**hypothesis**: 1× render scale at 60 fps fits, 2× doesn't).

RADV is a different shader compiler from the one patch 0002 works around.
The AMD Windows crash does not apply there; RADV may have its own issues
(**hypothesis**: our patches 0002–0004 and 0039 are neutral on RADV, as
they are on NVIDIA).

## Two routes

1. **Proton.** The Windows release runs unchanged under Proton (Wine with
   DXVK/VKD3D; Vulkan goes straight to RADV through winevulkan). Nothing to
   port, but the setup (D18) would have to run under Wine too: embeddable
   Python with Tk, `powershell.exe` calls, llvm-mingw's
   clang-cl compiling 330 MB of generated C++. **Hypothesis**: the game
   runs; the setup is the fragile part.
2. **Native Linux build.** The fork already builds for Linux (upstream
   Vita3K ships Linux x64 and arm64 AppImages from the same CI presets,
   `ci-linux-clang-appimage`). The work is in the parts we added
   (below), the kit's Windows-only scripts, and a setup for Linux.

Proton is the baseline to measure first, as upstream Vita3K was for
Windows in Phase 0. The native build is the real target: no Wine layer in
the setup's compile, Linux-native file and thread handling, and a package
that also runs on Linux PCs.

## What the code needs (survey 2026-11-17)

The fork's changes to upstream are 132 files (+11.6k/−0.8k lines). The
frontend and the game's code were written with `#ifdef _WIN32` branches
from the start, so most of them already have a POSIX side.

| Component | State | Work |
|---|---|---|
| Vita3K core, renderer, audio (cubeb), network | Linux supported upstream | build and test |
| Memory mapping `double-buffer` | upstream's Linux path in `mem/src/mem.cpp` (`mmap` of a file descriptor) | works on the Deck (2026-11-17) |
| Guest threads, 64 MiB host stacks (D7) | `SDL_CreateThreadWithProperties` with a stack size (`kernel/src/kernel.cpp`) | none expected |
| File names | Vita3K's case-insensitive lookup (`io.case_isens_find_enabled`) covers `app0`, `addcont0`, `vs0` | check `ux0` saves and `boot_config.ini` copy |
| AOT loader, `cpu/src/aot.cpp` | was Windows only | `dlopen(RTLD_NOW \| RTLD_LOCAL)`/`dlsym` added; `SSD_AOT` stays `;`-separated everywhere |
| Frontend, `game-frontend/frontend.cpp` | portable apart from the module scan | scans `ssd_aot_*.so` on Linux (done); the ini's texts and example paths are still Windows ones |
| Test input pipe (patch 0005, `ctrl/src/ctrl.cpp`) | was a Windows named pipe | a FIFO, `/tmp/<VITA3K_INPUT_PIPE>` (done; drives Stage Select on the Deck) |
| `games/ss-delta/` (saves, add-ons, Ad Hoc Play, 60 fps) | portable (`localtime_r` branches exist) | icon: `.rc` → `.desktop` + PNG |
| Recompiler runtime (`armrecomp.h`, `neon.h`) | plain C++20 standard headers, no intrinsics | none expected |
| Recompiler CMake | was MSVC flags only | `-O1 -w`, PIC, hidden visibility, no `lib` prefix, `--exclude-libs,ALL` (a static libstdc++ exported all of itself); the tests' library names per platform (done) |
| `runtime/aot_dll.cpp` | was `__declspec(dllexport)` | `ARMRECOMP_EXPORT`, `visibility("default")` on Linux (done) |
| Escapes (D7, D9) | a C++ exception thrown by the host through generated frames | works with g++'s defaults: 37,012 escapes in a native quest run on the Deck (2026-11-17) |
| Kit: `build-vita3k.py` | was MSVC only | a Linux branch: games only, GCC (g++-14 when there), static libstdc++ (done) |
| Kit: `install-game.py`, `make-dist.py`, `build-recomp.py` | were `<id>.exe` and `.dll` names | names per platform from `gameproject.py` (done) |
| Kit: `make-setup.py`, `setup.py`, `setupgui.py` | were Windows only | the Linux setup (below; done) |
| Kit: `v3kdrive.py` | `user32` (window lookup, `WM_CLOSE`) | a Linux backend: process, `SIGTERM`, the FIFO |

The fork, the kit and the frontend are shared with utakata and the
third game (D17), so this work ports all of them.

## The setup on Linux (D18, D20)

D18 forbids shipping recompiled game code, so the Deck compiles the
generated C++ itself. SteamOS has no compiler and a read-only root; the
setup brings its own ([D20](decisions.md)):

* **zig** (`toolchain-linux.json` in the kit, 0.17.1, 57 MB, pinned by
  SHA-256): clang with libc++ and glibc's link stubs, so no sysroot, under
  MIT and LLVM's Apache licence (nothing for the player to accept). The
  modules are compiled for `x86_64-linux-gnu.2.30` and the baseline CPU
  (no FMA or AVX, as on Windows), `-O1`, and linked with a version script:
  each `.so` exports only `armrecomp_aot_init`. zig builds libc++ on first
  use; its cache, which also keeps a copy of every object (1.5 GB), is
  deleted after the build.
* Rejected: a portable LLVM release plus a sysroot (much larger, a sysroot
  to keep in step), distrobox/podman (both are in SteamOS 3.9.5's
  `/usr/bin`, but they pull a whole distribution), a Flatpak SDK extension.
* The setup itself is a `.tar.gz` (84 MB, 535 MB unpacked): `setup.sh`,
  python-build-standalone's CPython 3.12.16 (release 20261026, Tk included)
  with capstone 5.0.7 and PyYAML 6.0.3 (manylinux wheels), the kit, and
  `ss-delta.x86_64` stripped of its debug information. Downloads go to
  `~/.cache/vita-recomps`. `--shortcut` (a checkbox in the window) writes
  `ss-delta.desktop` into the applications menu and on the desktop, which
  Steam's "Add a Non-Steam Game" lists for Game Mode.
* The playable folder: `ss-delta.x86_64`, the ten `ssd_aot_*.so`, `fs/`,
  `ss-delta.ini` (Linux example paths), `ss-delta.png`, `run-player2.sh`
  and `README.txt` from `docs/dist-readme-linux.txt` (`game.json`'s
  `dist_readme_linux` and `dist_files_linux`).

**Measured on the Deck (2026-11-17)**, console mode, from the US dump zip,
6 jobs, firmware and zig already downloaded:

| Stage | Time |
|---|---|
| install firmware and game | 28 s |
| the game's run that writes the modules (`--dump-elfs`, JIT) | 46 s |
| recompile (the eboot 252 s) | 268 s |
| compile the 204 files with zig | 847 s |
| **total** | **1190 s (20 min)** |

The folder then plays a quest from Stage Select natively: every loaded
module matches guest memory, 0 native-to-JIT calls, 60.0 fps (worst frame
23 ms). The window (`setup.sh` without arguments) opens on the Deck's
desktop; the desktop entry passes `desktop-file-validate`.

Two Linux-only faults the first run found, fixed:

* the dump of `app0:eboot.bin` was named `..._app0:eboot.elf` (Linux reads
  `app0:` as part of the file name; Windows as a root name), so the setup
  didn't find it: the fork's `load_self.cpp` now cuts the device prefix;
* dynarmic printed thousands of "Unhandled SIGSEGV" lines during the dump
  run (JIT only; native runs print none): `install-game.py` leaves them
  out of the setup's output.

A second run with the setup as committed (kit `4ac02dc`, fork `b51c08d8`),
`--shortcut` into a scratch home: 1165 s; `ss-delta.desktop` in the
applications menu and on the desktop, `ss-delta.png` taken from the
`.ico`, zig's cache gone (466 MB left: zig and its download). Memory: 4.6
GB used at the peak against 2.0 GB idle, so about 2.6 GB for the setup with
6 jobs.

The release workflow's `linux` job (run by hand, 2026-11-17, run
44080546990): 25 min in all, 22 of them building the fork from scratch in
the SDK container; an 87 MB `.tar.gz`. Its `ss-delta.x86_64` needs only
glibc and zlib and plays the quest natively on the Deck at 60.0 fps with
the modules the Deck compiled.

Not changed: `install-game.py` keeps `<out>-work` (3.5 GB: the generated
C++ and the objects) after the setup, on Windows too.

## Packaging and runtime base

* Build inside the **Steam Linux Runtime** SDK container (sniper, Debian
  11-based), so the exe runs on SteamOS and on other distributions with
  an old enough glibc. Everything else is linked in (libstdc++, SDL3,
  OpenSSL, curl), so it runs on the host with no compatibility tool:
  glibc 2.30, zlib and Vulkan are all it needs. Players add it as a
  non-Steam game. No Qt (`VITA3K_GAMES_ONLY`).
* The sniper SDK (3.0.20261021) has g++ 14.2, clang 11 (too old for
  Vita3K), CMake 3.25, glibc 2.31, Vulkan headers 1.4.309, PipeWire and
  PulseAudio. Its runtime's libstdc++ is gcc 10's, so a g++ 14 build links
  libstdc++ statically (`-static-libstdc++ -static-libgcc`). Steam Linux
  Runtime 4.0 is newer and also on the Deck; sniper is what most Steam
  games use.
* The release workflow (`.github/workflows/release.yml`) has a `linux`
  job in the SDK container image
  (`registry.gitlab.steamos.cloud/steamrt/sniper/sdk:3.0.20261021.266025`,
  the tag pinned): Python 3.12 from the setup's own lock, `build-vita3k.py`,
  `make-setup.py`. A `release` job drafts one release with both setups.
  Nothing game-derived reaches CI (D2): the fork and the kit only.

## Deck-specific work (11e)

Measured over SSH on the test Deck (2026-11-17), from the setup's playable
folder on native code, with `tools/deck-quest.sh`: Stage Select, a quest,
a camera turn and a short walk, then 20 s standing; frame rate from
`VITA3K_FRAME_LOG`, power from the GPU driver's `power1_average` (the
whole APU, CPU and GPU, in watts; it reads on AC as well, unlike the
battery's `power_now`). The Deck was on AC, battery full.

| Map (Stage Select index) | Settings | fps, last 20 s | APU | GPU clock |
|---|---|---|---|---|
| ST16A (0) | 60 fps, 1× | 60.0 | 4.8 W | 620 MHz |
| ST16A (0) | 30 fps, 1× | 29.9 | 3.9 W | 391 MHz |
| ST16A (0) | 60 fps, 1.3333× (1279×725) | 60.0 | 5.7 W | 582 MHz |
| ST16A (0) | 60 fps, 2× (1920×1088) | 60.0 | 6.9 W | 964 MHz |
| ST03A (2) | 60 fps, 1× | 60.0 | 4.6 W | 480 MHz |
| ST01B (5) | 60 fps, 1× | 60.0 | 4.3 W | 544 MHz |
| ST22A (524), boss arena | 60 fps, 1× | 59.9 | 4.3 W | 505 MHz |

The player stands still for those 20 s: fights cost more and were not
measured. The CPU ran at about 2.4 GHz throughout.

* **Frame rate and battery**: 60 fps costs about 1 W more than 30 on the
  APU. **Hypothesis**: with the screen and the rest of the Deck (a few
  watts more), about 8–10 W in all, 4–5 h on the LCD Deck's 40 Wh; to be
  read from the battery's `power_now` unplugged. 40 fps: the game's own
  pacing flips every Nth emulated 60 Hz vblank, so only 30 and 60 exist
  (D16); a 40 Hz panel with Game Mode's frame limiter is the way to try
  it. A nested `gamescope -r 40` in desktop mode does not limit the game
  (the frame log stays at 60): Game Mode's limiter has to be tried there.
* **Screen**: 1280×800 is 16:10, the game's 960×544 a little wider than
  16:9; it fills 1280×725 with bars of 37 px. `scale` takes fractions:
  1.3333 renders 1279×725 (the multiplier is truncated; 1.33334 gives
  1280×725), and the ST16A frame at 1.3333 renders correctly. A
  fractional scale was never swept over every map and effect (Phase 8
  checked 1× and 2×), so the default stays 1; 2× holds 60 fps at 6.9 W.
* **Game Mode**: the game runs under a nested gamescope (1280×800) in
  desktop mode at 60 fps, 4.8 W, as without it. Steam's "Exit game"
  sends SIGTERM: the game quits in about 0.2 s, exit code 0, its log
  complete (SDL turns the signal into a quit).
* **Adding the game to Steam**: the setup's `--steam` (a checkbox in the
  window, ticked by default) hands `ss-delta.desktop` to the running
  Steam client with `steam://addnonsteamgame/<file>`, as SteamOS's "Add to
  Steam" does (Steam takes the link only while `/tmp/addnonsteamgamefile`
  exists). Projects that write `shortcuts.vdf` themselves need Steam
  closed, or it overwrites the file; this needs it running. Checked on the
  Deck (2026-11-17): the entry appears in `shortcuts.vdf` with name,
  executable, start folder and icon; started with `steam://rungameid/`
  (Game Mode's path) the game runs natively with Steam's overlay loaded.
  Library artwork (the grid images) isn't set: that would mean writing
  into Steam's `userdata/<id>/config/grid/` ourselves.
* **Audio**: PipeWire, through its PulseAudio side (a stereo 44.1 kHz
  stream named `ss-delta.x86_64`).
* **Controls**: outside Steam, SDL sees the "Steam Deck Controller"
  itself; in Game Mode, Steam Input gives an Xbox-style pad. The default
  `[gamepad]` and `[touch]` bindings need nothing else. The back buttons
  (L4/R4/L5/R5) can't be bound in `ss-delta.ini` (the parser knows no
  paddle names); Steam Input can map them to other buttons. The
  touchscreen is the front touchscreen (SDL's finger events).
* **Shaders**: Steam's shader pre-caching doesn't cover non-Steam games;
  the background compile (D12) and the shader cache (`vk16-*.spv`) do the
  job as on Windows.
* **Ad Hoc Play**: the `lan` mode between a Deck and a PC
  (**hypothesis**: works as between two PCs). The `local` mode
  (127.0.0.N) works on Linux too: the whole 127/8 is loopback there.

Left for a test on the Deck itself (someone holding it):

1. Game Mode: start "Soul Sacrifice Delta" (the test install, added to
   Steam on 2026-11-17) from Game Mode, play a quest; the picture fills
   the screen's width.
2. The touchscreen on a menu that takes touch (the Librom's pages) and
   the Black Rite icon; the left trigger for the Black Rite.
3. Suspend (power button) in a quest and resume: picture, sound, input.
4. Game Mode's performance overlay at 40 Hz (refresh rate 40, frame
   limit 40): does the game run at its normal speed, and does it judder?
5. Battery: half an hour of play unplugged, the percentage before and
   after (or `power_now` over SSH).

## Developing without a Linux PC

* **Build**: WSL2 on the test PC with the Steam Runtime SDK as a
  distribution (below), or GitHub Actions for the fork and kit. The
  recompiled modules are built locally (WSL2 or the Deck), never in CI
  (D2).
* **Run and test**: on the Deck in desktop mode over SSH (`sshd` has to be
  enabled and a password set). `v3kdrive.py` needs its Linux backend
  first; `frame:` and `record:` already read back on the render thread.
* **Debug**: gdb over SSH, core dumps from `systemd-coredump`.
* WSL2 itself can't stand in for the Deck: its Vulkan is Mesa's `dozen`
  over Direct3D 12, not RADV.

## Build environment (2026-11-17)

* WSL 2 on the test PC. The sniper SDK's sysroot tarball
  (`com.valvesoftware.SteamRuntime.Sdk-amd64,i386-sniper-sysroot.tar.gz`,
  3.0.20261021, checked against Valve's `SHA256SUMS`) imported as a
  distribution: `wsl --import sniper <dir> <tarball> --version 2`.
* The fork is cloned inside WSL, not built from `/mnt/c`: the Windows
  checkout has CRLF endings (`core.autocrlf true`), which break Boost's
  `bootstrap.sh`. Every submodule comes from the Windows clone's git dirs
  (`.git/modules/...`), never from GitHub. Uncommitted work goes across
  as a diff written by Windows git (Linux git reading the Windows tree
  sees every file as changed).
* Vita3K's language catalog generator needs Python 3.12 (an f-string with
  a backslash); sniper has 3.9. A standalone CPython 3.12
  (python-build-standalone) is passed as `Python3_EXECUTABLE`.
* Configure: `Ninja Multi-Config`, `gcc-14`/`g++-14`,
  `VITA3K_GAMES_ONLY=ON`, `USE_DISCORD_RICH_PRESENCE=OFF` (the Discord
  SDK's headers lack `<cstdint>` for GCC 14), static libstdc++ and libgcc.
* Fork changes needed (fork `18bdae40`; the recompiler's in kit `c5b23f5`):
  * the single-game executables are built on Linux too
    (`vita3k/CMakeLists.txt`), without the `.rc`/`.ico`, the manifest,
    `version.lib` and the VC runtime check, named `<id>.x86_64`: a bare
    `ss-delta` clashes with the `ss-delta/` folder the frontend keeps
    its config and log in;
  * OpenSSL 4.0.1 built from the pinned source release and linked
    statically for the games on Linux (`external/CMakeLists.txt`), as
    on macOS;
  * Boost's `b2` builds with `-fPIC` on Linux (PIE executables);
  * `__cdecl` dropped from the RenderDoc hook, which finds
    `librenderdoc.so` with `dlopen` on Linux;
  * the AOT loader, the module scan and the input FIFO (table above).
* Result: `ss-delta.x86_64`, 759 MB with debug info, 64 MB stripped. It
  needs glibc 2.30 and `libc`, `libm`, `libz`, `libdl`, `libpthread`,
  `libcurl-gnutls`. SteamOS has no `libcurl-gnutls`; inside the sniper
  runtime (`SteamLinuxRuntime_sniper/run -- ./ss-delta.x86_64`) it
  starts. A no-op rebuild takes seconds, a clean one about 10 min.
  Since 11d the games' build links curl in too (built from its pinned
  source, HTTP only, no IDN, brotli, zstd, HTTP/2 or SSH), and the exe
  needs only glibc and zlib: it runs a quest on SteamOS itself, outside
  the Steam runtime (60.0 fps natively).

## Baselines on the Deck (2026-11-17)

Same test file system for both: the owner's firmware and install, copied
to the Deck, with the saves of the `ssd-check` test copy. 960×544 (1×),
Vulkan, `double-buffer`, `high-accuracy: true`, surface sync on.

* **Upstream Vita3K** (`Vita3K-x86_64.AppImage`, v0.2.1 4360-9f3d27c2,
  continuous build of 2026-11-16) **hangs the GPU** within 15–35 s of
  boot, every run: the kernel logs `ring gfx_0.0.0 timeout ... Process
  Vita3K`, then RADV reports `ErrorDeviceLost`. The same with
  `external-host` and `disabled` mapping and with `high-accuracy: false`.
  On OpenGL it ran 75 s without a hang.
* **Our fork on the JIT** (`ss-delta.x86_64` in the sniper runtime, no
  recompiled modules) runs without a hang. Title and menus: 60 fps
  (17.1 ms mean over 90 s, with loading). From Stage Select (the
  `BootSequence Quest Select` copy of `config.ini`), quest index 0 loads,
  renders correctly (rain, textured floor, cloak, HUD) and holds
  **60.0 fps, worst frame 25 ms**, in the last 20 s.
  **Hypothesis**: one of our renderer patches avoids the upstream hang
  on RADV; the vertex stride repacks (0003, 0004) are the likeliest, a
  misaligned vertex fetch being a classic GPU hang.
* **At 2×** (1920×1088 frames, checked), the same quest also holds
  **59.9 fps** in its last 20 s (2 frames over 20 ms, worst 91 ms) on
  the JIT. One small map only; the heavy maps are still to measure.
* **Our Windows build under Proton 11.0** (the `ssd-check` folder's
  `ss-delta.exe` of 2026-10-13 with its ten `ssd_aot_*.dll`, run with
  `proton run` outside Steam, `XAUTHORITY` set for Xwayland): boots on
  NativeCPU, every module matches guest memory and runs natively, still
  running after 120 s, no GPU hang. That exe predates
  `VITA3K_FRAME_LOG`, so no frame rate yet.
* "Unhandled SIGSEGV at rip ..." lines on stderr (thousands per run, in
  both builds, with `double-buffer` only) are noise: dynarmic's POSIX
  handler prints that for any fault outside JIT code and then passes it
  to Vita3K's handler, which handles the write-tracking fault. Vita3K's
  own "Unhandled access" was never logged.
* Screenshots with `spectacle -b` over SSH come out blank (Wayland); the
  input pipe's `screenshot` command works.

## Native code on the Deck (2026-11-17)

* The ten modules (`eboot`, `libc`, `libfios2`, `libult` and the six
  firmware modules) built as `ssd_aot_<module>.so` in WSL with g++ 14,
  `-O1`, static libstdc++: **7.1 min with 4 jobs, 492 MB peak**, against
  9.8 min with MSVC on the same PC. `ssd_aot_eboot.so` is 106 MB. Each
  module exports only `armrecomp_aot_init` and needs only `libc`/`libm`.
* With `jit = false` and the `.so` files next to `ss-delta.x86_64`, the
  Deck runs NativeCPU: every module that loads matches guest memory, the
  quest from Stage Select holds **60.0 fps (worst frame 22–23 ms)** at
  1×, with 0 native→JIT calls and about 37,000 escapes over the run.
* The compile time on the Deck itself (the D18 setup) is still to be
  measured; 7 min on 6 Zen 4 cores suggests 15–20 min on the Deck's 4
  Zen 2 cores (**hypothesis**).

## Next steps

Phase 11 in [03-plan](03-plan.md).
