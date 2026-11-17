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
| Kit: `build-vita3k.py` | vswhere, MSVC, Ninja Multi-Config | a Linux branch (clang, Ninja) |
| Kit: `install-game.py`, `make-dist.py`, `build-recomp.py` | Python, but `<id>.exe` and `.dll` names | names per platform |
| Kit: `make-setup.py`, `setup.py`, `setupgui.py` | Windows only (embeddable Python, `.bat`, `powershell.exe`, llvm-mingw + Microsoft's runtime and SDK) | a Linux setup (below) |
| Kit: `v3kdrive.py` | `user32` (window lookup, `WM_CLOSE`) | a Linux backend: process, `SIGTERM`, the FIFO |

The fork, the kit and the frontend are shared with utakata and the
third game (D17), so this work ports all of them.

## The setup on Linux (D18)

D18 forbids shipping recompiled game code, so the Deck has to compile the
generated C++ itself: on Windows, a clean build of the four game modules
with NEON takes 9.8 min with 4 jobs, 435 MB peak per job
([05-recompiler](05-recompiler.md#build-130-eboot)).
**Hypothesis**: 20–30 min on the Deck's Zen 2 cores, within its 16 GB.

SteamOS has no compiler and a read-only root, so the setup brings its own:

* **A pinned portable LLVM** (clang + lld; LLVM's Apache-2.0 licence
  allows redistribution, unlike the Windows setup's Microsoft runtime,
  which the player has to accept) **plus a small sysroot** (glibc and
  libstdc++ headers, the link stubs) matching the runtime the exe is built
  against. Downloaded at setup time like the Windows toolchain, or carried
  in the package. Recommended.
* Distrobox/podman on the Deck (both in SteamOS 3.9.5's `/usr/bin`):
  pulls a whole distribution, too much to ask of players.
* A Flatpak with the freedesktop SDK's LLVM extension: the compiler is
  meant for build time, not for apps; awkward.

The firmware's modules (D11) still come from a hidden run of the game with
`--dump-elfs`, which needs Vulkan; it works in desktop mode
(**hypothesis**).

## Packaging and runtime base

* Build inside the **Steam Linux Runtime** SDK container (sniper, Debian
  11-based), so the exe runs on SteamOS and on other distributions with
  an old enough glibc. Players add it as a non-Steam game; it can run with
  the "Steam Linux Runtime" compatibility tool or with its libraries
  bundled (Vita3K's AppImage does the latter). No Qt (`VITA3K_GAMES_ONLY`).
* The sniper SDK (3.0.20261021) has g++ 14.2, clang 11 (too old for
  Vita3K), CMake 3.25, glibc 2.31, Vulkan headers 1.4.309, PipeWire and
  PulseAudio. Its runtime's libstdc++ is gcc 10's, so a g++ 14 build links
  libstdc++ statically (`-static-libstdc++ -static-libgcc`). Steam Linux
  Runtime 4.0 is newer and also on the Deck; sniper is what most Steam
  games use.
* The release workflow (`.github/workflows/release.yml`, `windows-2025`)
  gains a Linux job. Nothing game-derived reaches CI (D2): the fork and the
  kit only.

## Deck-specific work

* **Screen**: 1280×800 is 16:10, the game 16:9 at 960×544. At 1× the image
  is scaled by 1.33 with bars top and bottom. Options: 2× (1920×1088)
  downscaled if the GPU has room; Vita3K's FSR 1 upscaling.
* **Controls**: Steam Input gives SDL an Xbox-style pad, which the
  frontend already maps. The touchscreen → the Vita's front touch;
  back touch → the back paddles or trackpads (to design).
* **Game Mode**: gamescope, fullscreen, its own frame limiter. The 60 fps
  option (D16) against 30 fps for battery life; 40 fps on a 40 Hz panel
  setting is worth a look.
* **Suspend and resume** in the middle of a quest: the Vulkan device and
  the audio stream must survive.
* **Shaders**: Steam's shader pre-caching doesn't cover non-Steam games;
  the background compile (D12) and the shader cache (`vk16-*.spv`) do the
  job as on Windows.
* **Ad Hoc Play**: the `lan` mode between a Deck and a PC
  (**hypothesis**: works as between two PCs). The `local` mode
  (127.0.0.N) works on Linux too: the whole 127/8 is loopback there.

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
