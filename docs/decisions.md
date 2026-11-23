# Decisions

Irreversible or expensive choices, newest last.

## D1 — Hybrid: AOT-recompiled code inside a Vita3K fork, dynarmic fallback (accepted, 2026-10-10)

**Context:** [01-research](01-research.md#approach-options).

* No mature Vita recompiler exists, but Vita3K already runs the game.
* GXM and the USSE shader translator are the hardest parts of Vita emulation,
  and Vita3K has both.
* The first frame is reachable only through indirect calls, so there is no
  "recompile a small static subset" milestone.

**Decision:**

* Write our own Thumb-2/ARM → C++ recompiler.
* Run its output inside a Vita3K fork that dispatches to native code by guest
  address.
* Use dynarmic as the fallback and as the differential oracle.
* Shrink to a standalone runtime once coverage is complete
  ([plan](03-plan.md) Phases 3–6).

**Consequences:**

* The runtime is GPL-2.0-or-later (Vita3K).
* Thread, callback and HLE integration follow Vita3K's model until Phase 6.

**Status:** accepted by the owner on 2026-10-10, after Phase 2. The
inventory ([04-inventory](04-inventory.md)) supports the choice: the
function list is complete, game code has no exception landing pads, and the
dynamic indirect calls (26 k) and the few unexplained data pointers are
exactly what the dynarmic fallback is for.

## D2 — Nothing derived from the dump or firmware is committed (accepted, 2026-10-09)

**Decision:** none of the following go into git:

* extracted or decrypted files;
* ELFs;
* generated C++;
* Ghidra databases;
* screenshots or logs of the game;
* licences (RIF/work.bin);
* firmware.

Hashes, addresses, names and notes are fine. Amended by D23: a few
screenshots for the README, in `docs/assets/screenshots/`.

**Consequences:**

* Every build regenerates from the user's own dump and firmware.
* The project stays private and non-distributed, which also keeps the GPL
  question moot. Update (2026-10-13): the repos are being prepared for
  publishing ([D17](#d17--the-toolchain-is-shared-with-shinobido-2-through-git-submodules-accepted-2026-10-13)):
  MIT for this repo, the fork GPL as Vita3K. This rule (no game data, ever)
  is unchanged.

## D3 — Target the merged US 1.30 build (accepted, 2026-10-09)

**Decision:** all analysis and the port target PCSA00152 at 1.30: the base
app plus the merged patch, eboot module NID `0xD66AEBF4`.

**Why:**

* It is the final version.
* It contains the post-launch content (Odin, Bahamut, collaboration
  costumes), and reportedly the DLC data.
* The VitaGrafix and XLink Kai patches exist for it.
* loktar00's numbers are for 1.10, so their addresses don't apply.

## D4 — OpenGL is the Vita3K reference backend on the dev machine for now (accepted, 2026-10-09)

**Context:** [02-baseline](02-baseline.md). Vulkan crashed at boot on the
Radeon 760M in all three runs; OpenGL reaches gameplay at 30 fps, with
rendering bugs.

**Decision:** baseline runs and early behavioural comparisons use OpenGL.
Rendering comparisons wait until Phase 1 fixes Vulkan, or until they can be
run on the RTX 4090 PC.

**Revisit:** when the Vulkan crash is understood.

**Update (2026-10-09):** Vita3K-Plus v1.2 boots on Vulkan on this machine and
renders the maps correctly, apart from a speckled player cloak. It becomes
the **rendering reference**. Upstream OpenGL stays the reference for
behaviour and timing until our own build exists. The RTX 4090 results
(`dist/ss-delta-vita3k-test`) will show which artifacts are AMD-specific.

**Update 2 (2026-10-09, RTX 4090 results):** every artifact depends on the
GPU vendor. No combination is correct on both GPUs.

* **Vulkan is the renderer to build on.** It is the only backend without
  gross errors on both vendors.
* Comparisons use two references:
  * Plus Vulkan on the Radeon 760M test PC;
  * upstream or Plus Vulkan on the RTX 4090.
* A difference between the two references is itself a bug signal, and
  points at undefined behaviour in shader translation (see
  [02-baseline](02-baseline.md#rtx-4090-results-2026-10-09)).
* OpenGL is no longer used for rendering judgements.

**Update 3 (2026-10-09):** our fork (patches 0002 and 0003) runs Vulkan on
the Radeon 760M. It renders the field correctly and the Walhalla floor
textured. **Our fork on Vulkan is now the reference on this machine.** Plus
stays as a cross-check. The NVIDIA reference needs a retest with our fork.

**Update 4 (2026-10-10):** the reference settings for our fork are now
`disable-surface-sync: false` (surface sync on) and `high-accuracy: true`,
with `memory-mapping: double-buffer` and `async-pipeline-compilation: true`
kept. Compared with a Vita hardware screenshot of the title:

* surface sync brings back the haze and smoke that the game renders
  offscreen and reads back from memory;
* high accuracy removes the flicker and blocks in the green smoke;
* Plus's `external-host` mapping hides the skulls, butterfly and candle in
  our fork, so it stays off.

The cost is small: 29.5 fps in the field, and 29.2 fps at the title with
one 46 ms frame. See [02-baseline](02-baseline.md#fog-and-smoke-differ-from-hardware-2026-10-10).
The config lives in `build/` and isn't committed, so these values are
recorded here and in `CLAUDE.md`.

## D5 — Fork upstream Vita3K, not Vita3K-Plus; cherry-pick from Plus (accepted, 2026-10-09)

**Context:** Phase 1 needs a Vita3K source tree we build and patch. Plus v1.2
(tag `v1.2` = branch `all-enhancements`, `e2331f80`) is the build that runs
on Vulkan on the Radeon 760M. Measured against upstream:

* Merge base `5b040dc4` (2026-06-12, "app: Implement linux portable").
  This is also the hash in the Plus binary's build string `2-5b040dc4`.
* Plus adds 167 commits: 250 files, +17,964/−2,417 lines. Most target other
  games (Killzone, Uncharted, Resistance, Gundam, MGS3 …), Android/Mali/
  Turnip drivers, a thread-scheduling rework ("emulate the 3 cores"), and
  deadlock/hang watchdogs.
* Two commits name this game:
  * `98a65bff` "Fixes for depth in SSDelta": whole-mip-chain texture hashing,
    tiled depth-surface row rounding, full-width colour-surface reads,
    depth-bias slope × resolution multiplier;
  * `d248beee` "Refix Sacrifice Soul Delta outlines": MSAA depth surfaces
    read back as textures at the right samples-per-texel.
* Upstream has 98 commits since the merge base, which Plus lacks.

**Decision:**

* Our fork starts from upstream `master`. It lives in `third_party/vita3k` as
  a nested git clone (it is ~1 GB with submodules, too big to vendor), on branch `ss-delta`.
* Plus is a second remote (`plus`) in that clone. Its fixes come over as
  cherry-picks, one at a time, each tested against this game.
* Our patch series is exported with `git format-patch` into
  `patches/vita3k/`, and that directory is committed here. The pinned
  upstream commit is recorded below.

**Why not Plus:**

* Its game-specific hacks and global scheduling/watchdog changes would be
  noise in the Phase 4 differential work.
* Fixes made on upstream can be sent upstream.
* Plus is behind upstream by 98 commits, and rebasing it is not our job.

**Consequences:** the AMD Vulkan crash has to be found by debugging upstream
directly, with the Plus diff as a hint rather than a ready-made fix.

**Pinned:** upstream `b75d5e62` (2026-10-09, "appimage: Correctly copy data
folder (#4216)").

**Update (2026-10-13, [D17](#d17--the-toolchain-is-shared-with-shinobido-2-through-git-submodules-accepted-2026-10-13)):**
the clone is now a git submodule on branch `games`, which continues
`ss-delta` (patch 0042). The patch series in `patches/vita3k/` is kept as a
record up to 0042; the submodule commit is the reference from now on.

## D6 — The recompiler is a Python generator; runtime and tests are C++ (accepted, 2026-10-10)

**Context:** Phase 3. PSP recompilers use a C++ framework (Yakumo's
psprecomp) because one exists for the PSP. Nothing comparable exists for ARMv7.
`tools/inventory.py` already decodes every function in Python (Capstone,
recursive descent, jump tables, IT blocks).

**Decision:**

* `recomp/` holds our recompiler:
  * `recomp/armrecomp/` is a Python package that turns the inventory's
    per-function decode into C++ in `generated/<module>/`;
  * `recomp/runtime/` holds the C++ headers the generated code includes
    (guest context, memory access, flag helpers, dispatch hooks);
  * `recomp/tests/` holds a C++ harness that runs each instruction, and a
    sample of whole leaf functions, through the generated code and through
    dynarmic (from the fork's `external/dynarmic`) and compares the results.
* The interface of the generated code is `void f_<addr>(GuestContext *)`
  plus four hooks (`call_indirect`, `call_import`, `escape`,
  `unsupported`).
  * A function returns by setting `r15` to its return address.
  * Every call site checks `r15` and escapes to the fallback CPU when the
    callee returned somewhere else.
  * See [05-recompiler](05-recompiler.md).
* Speed of the generator doesn't matter. It runs once per build and reads
  only `extracted/elf/`.

**Consequences:**

* The generator and inventory share one decoder. A decode fix applies to
  both.
* Generated code depends only on `recomp/runtime/`. Phase 4 plugs it into
  Vita3K through that interface.

**Update (2026-10-13, [D17](#d17--the-toolchain-is-shared-with-shinobido-2-through-git-submodules-accepted-2026-10-13)):**
`recomp/` and the decoding tools moved, with their history, into the
shared `vita-recomp` repo, checked out as `third_party/recomp`.

## D7 — Native code runs at JIT block boundaries, from a DLL the fork loads (accepted, 2026-10-10)

**Context:** Phase 4. Generated code needs a host CPU loop to run in,
access to Vita3K's HLE imports, and a way back to dynarmic for code that
isn't recompiled (NEON, ARM mode, the LLE libraries, indirect jumps).

**Decision:**

* Each recompiled module is built as a DLL (`ssd_aot_<module>.dll`). It is
  built from `generated/` and never committed. The fork loads every DLL
  named in the `SSD_AOT` environment variable (`;`-separated). The ABI is
  `recomp/runtime/aot_abi.h`, which the fork copies as
  `cpu/include/cpu/aot_abi.h`: the guest context, the host hooks, and the
  module's function table and code hash.
* Before a module's code runs natively, the fork checks its code hash
  against guest memory. A mismatch, for example from a different game
  version or a code patch, leaves the module on the JIT.
  * The hash skips the instruction words the loader patches for variable
    imports. Generated code reads their immediates at run time.
* **JIT → native:** dynarmic's `PreCodeReadHook` ends every block that
  reaches a recompiled function's entry, and halts the JIT there with
  `UserDefined7`. `DynarmicCPU::run` then copies the registers into the
  guest context, calls the function, copies them back and continues the
  JIT at the returned `r15`.
* **Native → JIT** (`call_indirect` without a native target, LLE import
  stubs): the call runs a nested JIT loop with `lr` set to a sentinel
  block. The hook stops the loop there. The nested loop handles SVCs and
  native entries itself.
* **Native → HLE:** `call_import` reads the patched stub. For
  `svc #0; mov pc, lr; .word nid`, it calls the kernel's import handler
  directly. Anything else, such as a stub bound to an LLE module, runs on
  the JIT.
* **Escapes** throw a C++ exception. It is caught at the innermost
  boundary, and the JIT continues from the escape address with the native
  frames above that boundary abandoned. A thread that exits while native
  code is on its stack unwinds the same way (`CPUState::aot_unwind`).
* Guest threads get 64 MiB host stacks while AOT is enabled, because guest
  calls become host calls.
* `strex` is a host compare-and-swap against the value `ldrex` read, as
  Vita3K's dynarmic does it, so native and JIT threads share one exclusive
  protocol. *Update 2026-11-20:* it also fails once another exclusive
  store to its granule has succeeded since the `ldrex` (a version table,
  as dynarmic's monitor breaks other reservations): the value check alone
  allowed an ABA in libult's queue on Android (09-android). JIT threads
  don't take part in the versions.

**Consequences:**

* Without `SSD_AOT` the fork behaves as before.
* Verification tools ship with the runtime:
  * `SSD_AOT_DIFF`, a differential mode against a shadow JIT;
  * `SSD_AOT_COUNT`/`SSD_AOT_STATS` counters;
  * `SSD_AOT_RANGE`, plus `RECOMP_BISECT` DLLs, for bisecting.
  * See [05-recompiler](05-recompiler.md#runtime-in-the-fork-phase-4).
* Every transition copies about 350 bytes of registers. A hot native
  caller of a JIT-only function (most often NEON) pays a nested `Run()`
  per call. Phase 5 removes most of these calls.
* Generated code is never linked into Vita3K. The fork stays free of
  game-derived code (D2), and a regenerated DLL needs no Vita3K rebuild
  unless the ABI version changes.

## D8 — Relocatable modules are generated for Vita3K's load addresses (accepted, 2026-10-10)

**Context:** libc, libfios2 and libult are relocatable. Vita3K loads their
code at addresses other than the ELF's (libc at `0x8031e000`). Generated
code bakes code addresses in: return addresses, branch and escape targets,
and PC-relative loads.

**Decision:**

* Generate each module for the address Vita3K loads it at
  (`recompile.py --load-base`), decoding its code at runtime addresses.
* Data references the loader relocates (Thumb `movw`/`movt`) are decoded
  from guest memory at run time.
* The code hash, with every relocated word skipped, guards the choice: a
  module loaded elsewhere fails verification and runs on the JIT.

**Consequences:**

* The addresses are a property of the boot sequence, not of the modules.
  They were the same in every run so far (title and field boots).
* If the order Vita3K loads modules in ever changes, the libraries quietly
  fall back to the JIT. The log says so ("does not match").
* A position-independent alternative (adding a module base at run time) is
  still possible if the addresses turn out to vary.


## D9 — Fiber switches stay context swaps; native code re-enters at resume points (accepted, 2026-10-10)

**Context:** libult (the game's user-level threads) switches fibers through
SceFiber. Native code reaches a switch as a host call. Swapping the CPU
context under it abandons the native frames, and the rest of each frame
ran on the JIT. Worker loops never return, so they stayed there.

**Decision:**

* With `SSD_AOT` the fork uses its SceFiber HLE and does not load
  libfiber. A switch is a context swap in an import. `call_import` sees a
  different pc, sp or lr and escapes to where the other fiber was
  suspended.
* Generated functions have **resume points**: every call's return address
  is also an entry (`GuestContext::resume`, ABI v2). When the JIT reaches
  one, because a frame whose callee escaped returns to it, the function
  continues natively from there. A switched-back fiber therefore runs
  natively again after one boundary per frame.
* Branches to another recompiled function's entry are tail calls, not
  escapes.

**Rejected:** a host fiber per guest fiber (native frames survive the
switch). ULT moves fibers between worker threads, and a host fiber's
frames point at the CPU of the thread that created it. The experiment is
kept on the fork branch `host-fibers-experiment`.

**Consequences:**

* All four modules run natively with no JIT instructions inside them in
  title, field, arena and quest runs. The JIT is left with firmware LLE
  code ([05-recompiler](05-recompiler.md#coverage-130)).
* Each fiber switch costs an escape (a C++ exception) and one boundary
  per resumed frame, about 12,000 a minute in the field at 29.6 fps.
* libult's load address depends on libfiber not being loaded
  (`80451000`, [D8](#d8--relocatable-modules-are-generated-for-vita3ks-load-addresses-accepted-2026-10-10)).
* Phase 6 does not need host fibers for libult. A standalone runtime can
  keep the same scheme without dynarmic only if every escape target is a
  resume point or a function entry.

## D10 — `ss-delta.exe` is a target in the Vita3K fork (accepted, 2026-10-10)

**Context:** Phase 6 needs a single-game executable without Vita3K's Qt
interface. Upstream's SDL front end (`--frontend sdl -r`) already runs the
game in a plain window, natively at 99.9%.

**Decision** (the user's choice): build `ss-delta.exe` as a second
executable in the fork, `vita3k/ss-delta/`, beside `Vita3K.exe`, reusing
its libraries and leaving out `gui-qt`.

* Settings the game needs are fixed in code: Vulkan, `high-accuracy`,
  surface sync on, `memory-mapping: double-buffer` (D4 update 4).
* The player's choices are in `ss-delta.ini` next to the exe. It is written with comments on first start.
* Recompiled modules (`ssd_aot_*.dll`) are loaded from a configured folder
  unless `SSD_AOT` is set. The DLLs are generated locally and never
  shipped (D2).
* Config and log go in `ss-delta/` next to the exe. The shader cache is
  shared with `Vita3K.exe`.

**Rejected:** a separate runtime that copies only the pieces it needs. It
would fork the HLE, renderer and loader away from the code the
differential checks and Vita3K comparisons run against.

**Consequences:**

* `ss-delta.exe` is built from Vita3K's code, so it is under Vita3K's
  GPLv2.
* It stays in step with the fork: every fix applies to both executables.
* Vita3K's other subsystems (app list, users, config types) come along.
  The exe hides them instead of removing them.

**Update (2026-10-13, [D17](#d17--the-toolchain-is-shared-with-shinobido-2-through-git-submodules-accepted-2026-10-13)):**
`vita3k/ss-delta/` was split into the shared single-game frontend
(`vita3k/game-frontend/`) and `vita3k/games/ss-delta/`, which holds
everything particular to this game (saves, add-ons, Ad Hoc Play,
`boot_config.ini`, the 60 fps timer). `ss-delta.exe` behaves as before; its
default `ss-delta.ini` is byte-identical. It gained `--install <pkg>
--license <work.bin>` and `--write-ini <file>`.

## D11 — Threads run on native code alone (NativeCPU); firmware modules are recompiled too (accepted, 2026-10-11)

**Context:** Phase 6's exit is no dynarmic. After Phase 5 the JIT ran only
firmware modules (the module loader, the video player) and Vita3K's halt
instruction. Its main job was driving threads into native code.

**Decision:**

* The firmware modules the game loads as guest code are recompiled like
  libc. The input is ELFs that `ss-delta.exe` writes as it loads them
  (`SSD_DUMP_ELFS=1`), decrypted and already relocated to their load
  addresses. They are generated locally from the player's firmware and
  never committed (D2). The modules are `sysmodule.skprx`, `libSceFt2`,
  `libpvf`, `libscemp4` and `libsceavplayer`.
* `NativeCPU`, a second CPU backend in the fork:
  * registers in the native context;
  * `run()` calls the native function at pc until the guest returns to
    the halt instruction;
  * escapes continue at resume points (D9), imports go straight to the
    HLE function or the native export;
  * guest code without native code is a logged error.
* The AOT hooks dispatch through an interface (`AotOwner`) both backends
  implement.
* `ss-delta.exe` uses `NativeCPU` by default. `[recompiled] jit = true` in
  `ss-delta.ini` brings the JIT back as a fallback.

**Consequences:**

* Title, dialogs, hub, book menu, field and a quest run with **zero JIT
  instructions** at the same frame rate.
* Native code can't be preempted. A suspend request takes effect only when
  the guest returns to the run loop. Single-stepping isn't available.
* Seventeen font functions (`libSceFt2`, `libpvf`) still use NEON forms
  the translator lacks. None of them has run in any session so far. If one
  ever does, `NativeCPU` names the address in the log.
* `VITA3K_DYNARMIC=OFF` builds without dynarmic (fork patch 0026). The
  normal build keeps it as the `jit = true` fallback and for the
  differential checks.
* The ELF dumps also replace an external SELF decryptor. The install flow
  (`tools/install-game.ps1`) gets every module from them.

## D12 — Shaders and pipelines compile in the background on first use; nothing is translated at install time (accepted, 2026-10-11)

**Context:** Phase 7 planned to translate every GXP the game ships at
install time, so that no shader compiles in game. The game's shaders are in
487 `resource/data/shader/psp2/*.csp` containers (`KPKy`, several GXPs
each).

**Findings:**

* Vita3K's SPIR-V translation depends on draw-time hints as well as the
  GXP: the texture formats bound to each sampler (component type and
  count), the colour surface format and the vertex attribute formats
  (`shader::Hints`). Translating a GXP without them can give a different,
  wrong shader. The cache key is the GXP hash alone, so a wrong
  install-time translation would stick.
* The expensive part on Vulkan is the pipeline, keyed by the GXP pair plus
  the render state (blending, attribute layout, primitive type, render
  pass). Those combinations exist only at draw time.
* With `async-pipeline-compilation` (on), a pipeline seen for the first
  time compiles on worker threads and its draws are skipped meanwhile. The
  SPIR-V files and the driver pipeline cache persist next to the exe.
* Measured with an empty cache (debug build, title → Stage Select →
  ST08A, 2026-10-11): 29.5 fps mean, minimum 28 in one-second samples.
  Mind's Eye, opened for the first time, compiled 6 pipelines and showed
  its outlines within the second.

**Decision:** keep Vita3K's runtime translation with background pipeline
compilation and the persistent caches. `ss-delta.exe` fixes
`async-pipeline-compilation` on and hides the "N pipelines compiled"
notice (fork patch 0028).

**Rejected:**

* Install-time translation of every GXP: wrong without draw-time hints.
* Shipping a prebuilt cache: derived from the game (D2).

**Consequences:**

* On a fresh install, an object can be missing for a frame or two the
  first time its pipeline is needed. There are no frame-time stalls.
* A cache built by one translator version stays valid only for that
  version (`CLAUDE.md`, stale shader cache).

## D13 — Higher resolution comes from the game's own 960×544 mode times Vita3K's multiplier; settings reach the game through a copy of boot_config.ini (accepted, 2026-10-11)

**Context:**

* The game draws its 3D at 720×408 and stretches it into the 960×544
  framebuffer. The plan was to patch the VitaGrafix sites.
* The render-target setup takes a mode from `boot_config.ini`'s
  `ResoDown`: 0 gives 960×544, 1 (the retail value) 720×408.
* Patching only the mode-1 immediates breaks rendering in Vita3K, since
  other code reads the mode. Code patches would also have to go through
  the recompiler, because native code checks the eboot's code against
  guest memory.
* Vita3K's resolution multiplier scales every surface consistently,
  including the depth buffer that Mind's Eye reads.

**Decision:**

* `full_3d` (default on) selects `ResoDown 0`. `scale` multiplies it.
* At scale 2 the 3D is 1920×1088, verified on all 50 map IDs at 30 fps on
  the Radeon 760M.
* `ss-delta.exe` gives the game a changed copy of `boot_config.ini`
  through an IO read override (fork patch 0029). The installed game is
  never modified. `[boot_config]` in `ss-delta.ini` passes other engine
  keys the same way, for experiments.

**Rejected:**

* Patching the immediates (VitaGrafix style): breaks rendering here, and
  needs recompiler support.
* Editing the installed `boot_config.ini`: it changes the player's game
  files, and a reinstall would lose the setting.
* Rendering the 3D above the framebuffer (supersampling into 960×544):
  Vita3K's multiplier already raises the framebuffer.

**Consequences:**

* `full_3d` changes the game's look slightly compared with a Vita, so it
  can be turned off.
* Engine keys (`FPS`, `ForceDLC`, ...) can be tried without patches, but
  `FPS` turned out not to set the frame rate (02-baseline, 60 fps study).

## D14 — The add-ons are unlocked by recording them in the save's system.bin (accepted, 2026-10-11)

**Context:**

* The add-ons' content (raiments, hoods, the additional and otherworldly
  pacts) is in the game's data since update 1.30. PSN, where they were
  sold, no longer exists. The owner asked for them to be unlocked when the
  installed game has them.
* `ForceDLC` in `boot_config.ini` is parsed but never read.
* Answering the game's PSN entitlement queries locally works (the game
  lists all 18), but it hands add-ons out only after an online download
  step on Cassus's Claim Gift page, which does not complete offline
  (tried in fork patch 0030, reverted in 0031).
* Vita owners unlock them by swapping in a `system.bin` from a save that
  had them. The file is four id lists plus a CRC-32/BZIP2 check, decoded
  in 01-research.

**Decision:** `ss-delta.exe` (`[game] dlc`, default on) adds the released
add-ons' ids to those lists in the player's own `system.bin`/`.bak` at
start, keeping anything already there, after checking that the installed
game has the add-on pacts and raiments. The previous files are copied to
`ss-delta/save-backups/` first. The ids are numbers in the fork's source;
no third-party save is shipped or needed.

**Rejected:**

* Shipping or asking for a third-party `system.bin`: it would replace the
  player's own, and the four lists are enough.
* The PSN path: needs a fake online session the game never completes.

**Consequences:**

* The change is in the save, so it carries over to a Vita (same format).
* Turning `dlc` off later does not remove them; restoring the backup does.

**Update 1 (2026-11-21, GitHub issue #11):** `system.bin` doesn't cover the
add-ons PSN handed out as gifts on the Claim Gift page: Soulbinder, the
Necky (Fox), Slave, Archsorcerer, Mad Witch, Easterner, Saint, Beast and
White Cat raiments, eight hoods and the Fox Sigil (18 rows of the
entitlement table; 01-research, "Content from the original game, and locked
raiments"). With `dlc` on, `ss-delta.exe` now also does in the loaded save
what taking those gifts does (raiment states, hood and sigil flags, the
received byte), checking twice a second, for every save loaded and for a
new game. Only items not yet owned change; the game keeps them when it
saves. Not given: the developers' box (DBG001). A second switch,
`[game] japan_raiments` (on), adds the raiments only Japan had: Sylvan
(SSC018, SSC020, marked never distributed in the other regions' tables;
all twelve rows) and Benkei (`costume_table.csv` row 168, in no box; its
colour A, as for Necky). Where Benkei was given in Japan isn't known;
its model and name are complete in the data.

## D15 — Ad hoc play uses Vita3K's ad hoc support; copies on one PC take 127.0.0.N (accepted, 2026-10-12)

**Context:**

* The owner asked for multiplayer (plan Phase 10). The game's Ad Hoc Play
  runs on SceNetCtl's ad hoc mode and the firmware's matching module,
  which Vita3K supports since late 2025: the module runs as LLE over P2P
  sockets, which Vita3K maps to UDP port 3658 + virtual port, and peers
  are found by a broadcast every second.
* A PSP port has to write its own ad hoc layer and server; here nothing
  of the kind is missing.
* Two copies on one PC collide: both bind the same ports, and loopback has
  no broadcast. They also share a save, a config and the shader cache.

**Decision:**

* Keep Vita3K's ad hoc support (LLE matching module, P2P over UDP).
* `ss-delta.exe --player N` is copy N (2-4): Vita user N-1, saves copied
  from player 1's once, its own config and log, the shader cache read
  only.
* `[multiplayer] network = local` (the default on Windows; Linux and macOS
  default to `lan` since 2026-11-18, see 08-macos) gives copy N the address
  127.0.0.N: P2P sockets bound to any address bind it, and a broadcast
  goes to each 127.0.0.1-4 but its own. `lan` is Vita3K's way, for PCs in
  one network.
* The matching module, loaded only when Ad Hoc Play opens, is recompiled
  for a fixed base (`0x80757000`, where Vita3K's allocator puts it), and
  the loader places a module with native code at its base when free (D8's
  guard, the code hash, still applies).

**Rejected:**

* An ad hoc server (PPSSPP's protocol): the Vita's ad
  hoc needs none, and Vita3K builds on IP addresses directly.
* A full copy of the Vita file system per player: gigabytes, and the users
  already separate the saves.

**Consequences:**

* Play with real Vitas (XLink Kai) is not covered; it needs Vita3K's
  traffic bridged to a Vita's ad hoc frames.
* Players on one PC are four at most, the game's room size.
* If the allocator ever puts the matching module elsewhere, the log says
  the base "is taken" and the build without the JIT stops at its first
  call; the JIT build runs it as guest code.

## D16 — 60 fps is an option that keeps loading screens at 30 (accepted, 2026-10-13)

**Context:**

* The owner asked for 60 fps, or to mark it unplanned if it needs a game
  rewrite. The game paces its main loop with a frame timer created for 30
  fps and flips every 2nd vblank; both are data in guest memory.
* Game logic steps by the measured frame time, so movement and fights keep
  their speed at 60 (02-baseline, 60 fps sections).
* The quest-start loading screen never ends at 60: something in the loader
  checks the frame time and fails below about 1/45 s. It was narrowed to
  the time step of the game update and to the `NowLoadingTask`'s
  `roading_loop` animation, which is never told to stop; the check itself
  was not found.

**Decision:**

* `[display] frame_rate = 60` sets the timer and the flip threshold every
  frame to 60, and to 30 while the `NowLoadingTask` is in state 2, 3 or 5
  (fork patch 0041). No game code is patched, so native code stays on.
* The default stays 30 until the owner has played at 60.
* Update (2026-10-13): the owner played at 60, alone and in Ad Hoc Play,
  without issues. 60 is the default (patch 0042), listed explicitly in the
  default `ss-delta.ini`; `frame_rate = 30` gives the Vita's rate.

**Rejected:**

* A fixed 1/30 s step at 60 fps: the loader works, but the game runs at
  double speed.
* Finding and patching the loader's check: not found after following it
  through the update, the loading task and its animation player; a code
  patch would also take the eboot off native code unless the recompiled
  module carried it.

**Consequences:**

* Loading screens look as on the Vita (30 fps); everything else runs at
  60, as far as the GPU allows (54–57 fps on the Radeon 760M).
* Update (2026-10-15): the frame timer is 16000 µs at 60, not 16666. Host
  waits overshoot, so frames sometimes missed their vblank, which capped
  every GPU at 57-58. Now it runs 59-60 ([02-baseline](02-baseline.md),
  "60 fps on a discrete GPU"); the flip still waits for each vblank.
* If another screen depends on the frame time the same way, it hangs at 60
  in a way the scripted checks didn't reach; switching back to 30 is the
  workaround.
* Update (2026-11-23): the cause was found, a race between the loader and
  the screen's opening (01-research, "The loading screen at 60 fps"), and
  fixed in the recompiled eboot ([D30](#d30--fixes-to-the-games-code-as-recompiler-overrides-the-blitz-offerings-at-60-fps-accepted-2026-11-23)).
  The front end now keeps loading screens at the set rate when the eboot's
  native code reports the fix (`loading_race`), and falls back to the
  30 fps switch only for an eboot without it (built before, or on the JIT).

## D17 — The toolchain is shared with shinobido-2 through git submodules (accepted, 2026-10-13)

**Context:**

* The sibling port of Shinobido 2: Revenge of Zen (now utakata)
  reuses this project's Vita3K fork and recompiler. Its D4 splits them into
  publishable repos that both games use as submodules; its D6 says they are
  written as if public, for a later GitHub release. The owner considers
  ss-delta done and approved switching it over (2026-10-13).
* Until now the fork was a nested, ignored clone (D5) recorded here as a
  patch series, and `recomp/` and the tools lived in this repo.

**Decision:**

* `third_party/vita3k` is a submodule of the fork on branch `games`: the
  `ss-delta` branch (patch 0042) plus the split of `ss-delta.exe` into a
  shared frontend and one executable per game (D10 update). Both games
  pin commits of this one integration branch, so each fix reaches both.
* `third_party/recomp` is a submodule of `vita-recomp`: `recomp/` and the
  game-agnostic tools (`velf.py`, `vitaelf.py`, `inventory.py`,
  `imix.py`, `v3kdrive.py`, `sfo.py`, `stackdump.py`), with their history,
  game values turned into parameters (`recomp/CMakeLists.txt` takes
  `GENERATED_DIR`, `VITA3K_SRC`, `VITA3K_BUILD` instead of `SSD_ROOT`).
* The PowerShell build, install and packaging scripts are replaced by
  Python scripts in `vita-recomp` (`build-vita3k.py`, `install-game.py`,
  `make-dist.py`), driven by `game.json` at this repo's root: title,
  supported eboot, modules to recompile and their load bases, the packaged
  README (`docs/dist-readme.txt`) and extra files (`run-player2.bat`). The
  ini comes from `ss-delta.exe --write-ini` instead of parsing
  `settings.cpp` (`tools/ssdelta_ini.py`).
* The fork and the recompiler are repositories of their own (`vita3k`,
  `vita-recomp-kit`), published beside this one. The submodule URLs are
  relative (`../vita3k`, `../vita-recomp-kit`), so a clone finds them next
  to wherever it came from.
* Licences: MIT for this repo (except `patches/vita3k/`, GPL) and
  vita-recomp-kit; the fork stays GPL-2.0-or-later.
* SSD's own tools stay here: `lspk.py`, `questmaps.py`, `map-sweep.ps1`,
  `package4090.ps1` with `pkg4090/`, `devshell.ps1`.

**Rejected:** keeping the nested clone and copying `recomp/` into
shinobido-2: two copies of the fork patches and of the NEON layer would
drift (shinobido-2 D4).

**Consequences:**

* A change to the fork or the recompiler is committed and pushed in its
  own repo first, then the new submodule commit is committed here.
* Docs and dated log entries written before 2026-10-13 keep the paths of
  their time (`tools/v3kdrive.py`, `recomp/...`, `tools/*.ps1`,
  `vita3k/ss-delta/`); the README and CLAUDE.md have the current ones.
* Checked on 2026-10-13: the fork builds from the submodule with
  `build-vita3k.py`, and `ss-delta.exe` from it starts a quest from Stage
  Select (ST01A) with native code, switching to 30 fps for the loading
  screen and back to 60.

## D18 — Players get a setup that compiles the port on their own machine (accepted, 2026-10-15)

**Context:** the owner wants players to get a playable port without
cloning or building. Nebula (Super Mario Galaxy) ships a setup that
compiles the game's recompiled code on the player's PC. Yakumo (Monster
Hunter Portable 3rd HD) ships releases with the recompiled game code built
in, which works on every platform, but distributes code derived from the
game's executable. The same decision is utakata's D9.

**Decision:**

* Nebula's model: nothing derived from the game or the firmware is
  distributed (D2). A release is a setup (vita-recomp-kit `make-setup.py`):
  * Python's embeddable distribution with Tk, capstone and PyYAML;
  * the kit's tools;
  * `ss-delta.exe`, built without Qt (the fork's `VITA3K_GAMES_ONLY`).
* On the player's PC the setup:
  * downloads the firmware from Sony and a pinned compiler: llvm-mingw's
    clang-cl with Microsoft's C++ runtime and Windows SDK, from Microsoft
    under Microsoft's licence, which the player accepts;
  * installs the player's dump, recompiles and compiles the modules;
  * lays out the playable folder.
* GitHub Actions builds the setup from a tag
  (`.github/workflows/release.yml`) into a draft release with its SHA-256
  and a build attestation. The release is unsigned at first.

**Rejected:** shipping recompiled game code in releases (Yakumo's way):
it makes every platform easy, but it distributes a derivative of the
game's code.


## D19 — The EU version is supported by the same executable and modules (accepted, 2026-11-17)

**Context:** a player asked for the EU release (PCSF00532, GitHub issue
#2). Its 1.30 eboot is the US build linked 31 s earlier: the same code,
the same recompiled C++ and the same addresses, with only build stamps in
the data different (01-research, "EU version").

**Decision:**

* One `ss-delta.exe` for both regions. The shared frontend's
  `Profile::other_title_ids` lists the other title IDs; the frontend runs
  whichever is installed (US first; `--title-id` picks one when both
  are), and the game's code uses that title for its files and save folder.
* `game.json` has `other_title_ids` and both eboot hashes. The kit's
  install and setup accept either region and recompile what is
  installed.
* No region-specific code: the frame-rate addresses hold for both.

**Rejected:** a second executable or `game.json` per region. It would
double the build, the release and the docs for a binary that is the same.


## D20 — Linux: a native build of the same frontend; the setup compiles with zig (accepted, 2026-11-17)

**Context:** Phase 11 (07-linux), the Steam Deck as the target. D18's
setup compiles the recompiled modules on the player's machine; SteamOS has
no compiler and a read-only root. The Windows build also runs under
Proton (07-linux), but a native build avoids Wine in both the game and
the setup's compile.

**Decision:**

* A native Linux build of the fork's single-game frontend,
  `<id>.x86_64`, built in the Steam Runtime 3 (sniper) SDK with g++ 14,
  libstdc++ and libgcc linked in, OpenSSL and curl built from their
  pinned sources and linked in. It needs glibc 2.30, zlib and Vulkan:
  it runs on SteamOS itself, without the Steam runtime container.
* Recompiled modules are `ssd_aot_<module>.so`, loaded with `dlopen`.
  The setup compiles them with **zig** (`toolchain-linux.json`, pinned by
  SHA-256), a self-contained clang with libc++ and glibc's link stubs:
  one 57 MB download, no sysroot, MIT and Apache licences (nothing for
  the player to accept). Target `x86_64-linux-gnu.2.30`, baseline CPU;
  each module exports only `armrecomp_aot_init` (a version script).
* The Linux setup is a `.tar.gz`: `setup.sh`, python-build-standalone's
  CPython 3.12 (with Tk, for the same setup window), the kit and the
  front end. The playable folder gets a desktop entry, and the setup adds
  the game to the running Steam client as a non-Steam game
  (`steam://addnonsteamgame/`, as SteamOS's "Add to Steam" does), for
  Game Mode. Not `shortcuts.vdf` edited directly: that needs Steam closed.
* The release workflow builds both setups (Linux in the sniper SDK
  container, pinned by tag) and drafts one release with both.

**Consequences:** on the Steam Deck the setup takes 20 min from the dump
to a playable folder, 14 of them compiling with 6 jobs (07-linux); the
folder plays natively at 60 fps. The setup is an 84 MB `.tar.gz`.

**Rejected:**

* A portable LLVM release plus a glibc/libstdc++ sysroot: a much larger
  download, and a sysroot to keep in step with the build.
* Distrobox or a Flatpak SDK on the player's Deck: a whole distribution,
  or a compiler meant for build time.
* Proton only: the setup's compile under Wine, and a Windows build where
  a native one works.
* Requiring the Steam runtime container at run time: SteamOS lacks only
  `libcurl-gnutls`, which a curl built in removes.

## D21 — macOS: a native arm64 build; the setup compiles with zig and isn't notarized (accepted, 2026-11-17)

**Context:** Phase 12 (08-macos), Apple Silicon only. D18's setup
compiles the recompiled modules on the player's machine. A Mac has no
compiler until the player installs Apple's Command Line Tools, and arm64
macOS runs only signed code. Without a paid Developer ID, Gatekeeper
blocks whatever a browser downloaded.

**Decision:**

* A native build of the fork's single-game frontend, `<id>.arm64`, with
  Apple's clang, OpenSSL and Boost built from source, minimum macOS 13.3
  (the fork's `CMAKE_OSX_DEPLOYMENT_TARGET`), next to MoltenVK's
  `libMoltenVK.dylib`. Memory mapping `double-buffer`, as on Windows.
* Recompiled modules are `ssd_aot_<module>.dylib`. The setup compiles them
  with **zig**, as on Linux (D20): `toolchain-macos.json` pins
  `zig-aarch64-macos-0.17.1` by SHA-256 (51 MB). Target
  `aarch64-macos.13.3`, CPU `apple_m1`, `-ffp-contract=off`. zig's Mach-O
  linker signs each module ad hoc, which is all a module needs to load.
  It takes no export list: hidden visibility leaves the entry point and
  libc++'s `operator new`/`delete` exported. With two-level namespaces
  those bind nothing outside the module.
* The macOS setup is a `.tar.gz` (Python's symbolic links and the modes
  survive): `setup.command`, python-build-standalone's CPython 3.12 for
  `aarch64-apple-darwin` (with Tk, for the same setup window), the kit and
  the front end (debug map stripped, signed again ad hoc).
* **No Developer ID, no notarization.** The player lets `setup.command`
  through once (System Settings → Privacy & Security → Open Anyway, or
  `sh setup.command` in Terminal). It clears the quarantine from its own
  folder before it starts Python. Everything else the setup makes is
  created on the player's Mac, so it is never quarantined.
* The playable folder is a plain folder, as on Windows and Linux (config,
  logs and saves beside the executable), plus a small `<name>.app` made by
  the setup: a script that starts `<id>.arm64`, with the game's icon
  (`sips` turns the PNG into `.icns`), for Finder, the Dock and Spotlight.
  `--shortcut` copies it to `~/Applications`.
* The release workflow builds the macOS setup on GitHub's `macos-15`
  (arm64) runner, beside the Windows and Linux ones.

**Consequences:** on the M5, the setup took 5.6 min from the dump to a
playable folder, firmware and zig downloads included. zig compiles the
ten modules in 2.8 min with 8 jobs, against 95 s with Apple clang. The
first run builds libc++. The modules give the same code hash as on
Windows and play ST03A natively at 60 fps. The setup is a 43 MB
`.tar.gz`.

**Rejected:**

* Apple's Command Line Tools on the player's Mac: a download of about
  1 GB through Software Update, Apple's licence to accept, and a
  different compiler from Linux's for the same generated code.
* A Developer ID and notarization for now: the owner's yearly fee, plus
  the hardened runtime, which needs `allow-jit` and
  `disable-library-validation` (modules signed on the player's Mac). It
  can be added later without changing the layout.
* The whole game inside an `.app` bundle: its config, logs, shader cache
  and modules would have to move to `~/Library/Application Support`, and
  the bundle could not be written into.

## D22 — One program per platform, a portable folder, a command line for everything (accepted, 2026-11-18)

**Context:** an open letter from the lead of RecompLauncher (a launcher
for recomp and decomp ports) asks such projects to ship one executable,
keep everything in its folder, ship a tarball, and have a command-line
flag for everything. Before this, a release was a setup (`setup.bat`,
`setup.sh`, `setup.command` and Python) that built a separate playable
folder. Linux and macOS also wrote outside it:
* the shader cache went to `~/.cache/Vita3K` or `~/Library/Application
  Support/Vita3K` (Vita3K's `init_paths`, which also made an empty
  profile folder through `SDL_GetPrefPath` on every start);
* the setup left `<out>-work` (2.3 GB on the M5) beside the folder;
* about 650 MB of downloads stayed in a per-user cache.

LostOdysseyRecomp, the letter's example, ships its recompiled code in
its executable; this project never ships game-derived code (D2), so the
compiler stays (D18).

**Decision:**

* **The release is the game's folder.** The executable is the one thing
  the player starts: `<id>.exe`, `<id>.x86_64`, or `<Name>.app` on macOS,
  whose bundle runs the executable itself (Game Mode). The rest is
  Vita3K's data, the README, and the setup in `setup/`: its Python and
  the kit. Not built yet, the executable starts the setup, now the
  game's *importer*. That is its window, or `--dump <file>` for the
  console flow. It waits, then boots the game in the same process: Play
  in the window, or exit code 0. `--install` opens the importer again.
  The archives are `ss-delta-<version>-{windows.zip, linux.tar.gz,
  macos.tar.gz}`, each unpacking to a folder `ss-delta`.
* **Everything stays in that folder.** The front end sets every path
  (assets, config, log, cache, patch) from the game's folder and never
  calls `init_paths` or `SDL_GetPrefPath`. The folder is `--game`, else
  `VITA_RECOMPS_GAME_DIR` (the `~/Applications` copy on macOS, through
  `LSEnvironment`), else the executable's. On macOS that is the one
  holding the app (`SDL_FILESYSTEM_BASE_DIR_TYPE = parent`). The
  importer downloads into `setup/downloads`, works in `setup/work`, and
  deletes both, plus the modules' dumps, after a successful build.
  `--cache DIR` keeps the downloads elsewhere for the next time. The
  setup's own files stay, so the importer can reopen. Shortcuts, the
  menu entry, Steam and the `~/Applications` copy remain opt-in.
* **Microsoft's VC++ runtime ships beside `ss-delta.exe`.** This amends
  D18, which shipped no Microsoft files: the executable has to start
  before its importer has downloaded anything. The DLLs come from the
  build machine's Visual Studio (`VC/Redist/MSVC/<version>/x64`), which
  Microsoft's licence lets a program carry. The recompiled modules still
  use the runtime the importer downloads.
* **macOS:** `make-setup.py` builds and signs the app bundle (ad hoc).
  Gatekeeper's App Translocation runs a downloaded app from a read-only
  copy that holds only the app. The executable notices
  (`SecTranslocateIsTranslocatedURL`), clears the quarantine from its
  folder, and starts again from there.
* **The command line:**
  * `--game <folder>`, `--install`, `--dump <file>` (with
    `--license`/`--zrif`) and `--add-to-steam`: LostOdysseyRecomp's
    names, which launchers know;
  * `--set section.key=value` for any setting, and `--fullscreen` /
    `--windowed`;
  * the importer's own options passed on (`--accept-microsoft-license`,
    `--shortcut`, `--steam`, `--cache`, `--jobs`);
  * `--help`, which also lists every setting. On Windows it writes to the
    caller's console, or to the pipe a launcher reads.

  The importer's internal `--install <dump>` is now `--install-content`.

**Consequences:**
* One download per platform to start; nothing outside the folder unless
  the player asks for it.
* A rebuild downloads the firmware and the compiler again, unless
  `--cache` is given.
* The folder keeps the setup's Python and kit: about 40 MB on Windows,
  180 MB on macOS, 500 MB on Linux.
* utakata shares the kit and the front end and follows when it updates
  its submodules.

**Rejected:**

* Linking the C++ runtime statically into the executable: the owner
  chose shipping Microsoft's DLLs.
* Keeping the shared per-user download cache as the default: not
  portable.
* Deleting `setup/` after a build: reopening the importer would need the
  release downloaded again.


## D23 — Screenshots of the game in the README (accepted, 2026-11-18)

**Context:** the owner asked for screenshots in the README, as utakata's
has (its D12): the title and menus, and a few from quests. D2 kept every
screenshot of the game out of git.

**Decision:**

* Eight screenshots for the README are committed, in
  `docs/assets/screenshots/`: JPEGs at 1280×725, taken from the port
  (`ss-delta.exe` at scale 2, native code). The owner's own, with F12:
  the title, Librom's menu, a journal page, the save-or-sacrifice choice.
  With `v3kdrive.py`'s `frame:`, in a test folder: quests ST09B, ST14A,
  ST03A and ST17C (the dragon Dionaea), started through Stage Select (as
  `tools/map-sweep.ps1` does).
* The pre-push leak scan blocks images as game data; this clone lets
  these through with `git config leakscan.allow 'docs/assets/screenshots/*.jpg
  docs/assets/screenshots/*.png'` (vita-recomp-kit `fb2a5cb`; a clone's
  setting, never pushed).
* Everything else D2 lists stays out, including any other screenshot
  (map sweeps, test captures: `build/`).
* The README's note says the repository holds no game data *apart from
  these screenshots*; the releases still hold none.

**Rejected:** hosting the pictures outside the repository (release assets):
the owner chose committing them, as for utakata.

**Update 1 (2026-11-22):** the owner asked for a gallery of the add-ons
from [#11](https://github.com/vita-recomps/ss-delta/issues/11) in the
docs. [GALLERY](GALLERY.md) shows 39 more JPEGs in the same folder (so
the clone's `leakscan.allow` covers them): the raiments and hoods that
ss-delta adds and the two raiments of the original game's mod (D28),
female and male, from Raiments in Portraiture. They were taken with
`frame:` in a test folder (story-complete save, the mod installed there),
cropped to the character and scaled to two thirds. The mod's two raiments
are shown in a section of their own that says they aren't in ss-delta.


## D24 — RecompLauncher support: recomplauncher.json in every release (accepted, 2026-11-18)

**Context:** [RecompLauncher](https://recomplauncher.com) installs recomps
from their GitHub releases. A `recomplauncher.json` at the top of a release
tells it how to set the game up from the player's copy, start it and show
its settings (its SDK, levels 1-3). D22 already made the release one
folder with a command line for everything.

**Decision:**

* `recomplauncher.json` (repository root) ships at the top of every
  release archive: `game.json`'s new `release_files`, which the kit's
  `make-setup.py` copies.
* Setup: one input, the player's dump (folder, `.zip`, `.vpk`, or `.pkg`
  with its licence beside it). The launcher's setup step runs the
  existing windowless build, `ss-delta.exe --dump <dump> --build-only`,
  plus a new opt-in `--progress` (front end and the kit's `setup.py`) for
  `progress <0-1> <text>` lines. Microsoft's licence for the Windows
  compiler is a tick the player must accept (`--accept-microsoft-license`).
  Without the new option nothing changes.
* The release workflow stamps the tag into `prepare.version`, so the
  launcher builds again after every update (a release's front end and kit
  need modules recompiled by it).
* Settings: the main keys of `ss-delta.ini` (display, volume, language,
  add-ons, Ad Hoc Play network), edited by the launcher line by line.
  Saves: `fs/ux0/user/<00-03>/savedata` and `ss-delta.ini`.
* No `game.dumps`: there is no Redump or No-Intro entry to check a Vita
  dump's container against; the importer checks the eboot's SHA-256.

**Rejected:** shipping the file with an unchanging `prepare.version`
(players would keep modules the updated front end may refuse); key
bindings in the launcher (its key names are not known to match the
`[keyboard]` and `[gamepad]` names).

## D25 — Android: the game's APK, its modules built on a PC with zig, Turnip on Adreno (accepted, 2026-11-19)

**Context:** Phase 14 (09-android), the AYN Thor (Snapdragon 8 Gen 2) as
the test device. The recompiled modules must be built from the player's
own dump (D2), and an Android device has no compiler, no Python and no
shell for the player. The owner chose (2026-11-19): a PC builds the
modules first; an on-device build may come later.

**Decision:**

* The game is an **APK of the fork's single-game frontend**: `lib<id>.so`
  (SDL3 inside) behind SDL's activity, with two small Java classes of our
  own (`io.github.vitarecomps.frontend`), one Gradle project for every
  game (`game-frontend/android/`). The native library is built with the
  NDK (r29) on Linux (WSL in development), with Boost, OpenSSL and curl
  from source as for Linux, not vcpkg. The APK holds no game data.
* The game's files live in the app's shared folder,
  `Android/data/<package>/files/` (no storage permission), the Vita file
  system in `fs/`. The frontend copies the modules and Vulkan driver
  packages a PC puts there into the app's internal storage (shared storage
  is `noexec`) and loads them from there.
* **The modules are built on the player's PC with zig**, the compiler the
  Linux and macOS setups already download (D20, D21), on Windows too
  (`toolchain-android-windows.json`, 96 MB): `aarch64-linux-musl` headers,
  generic ARMv8 with inline atomics, unwind tables, linked without a C
  library against `libc.so`/`libm.so` stubs, so a module binds to bionic
  when the APK loads it; `recomp/runtime/aot_android.cpp` supplies the
  thread-safe static-local guards and `__dso_handle`. A module then imports
  only `abort` and `sched_yield`. `install-game.py --android` builds them
  with the PC's own modules; `android.py push` puts the folder on the
  device over adb, keeping the saves and settings already there.
* **Turnip is the driver to play on with Adreno.** Qualcomm's driver has
  neither shader interlock nor raster-order attachment access, and draws
  ST03A's fog with black rectangles (09-android); Turnip (Mesa) reads the
  framebuffer coherently. A libadrenotools package goes into the app's
  `drivers/`, and `[debug] gpu_driver` names it (`android.py push --driver`).
  The frontend falls back to the system driver when one fails to load.

**Consequences:** from the owner's dump on the test PC to a playable test
app: 19 min (install, ELF dump, recompiling, the PC's modules with MSVC and
Android's with zig, 5.1 min of it), then 4.6 min of copying over Wi-Fi.
ST03A natively on the Thor at 60 fps on Turnip T23, 0 native-to-JIT calls.
The ten zig modules are 89 MB (the NDK's, stripped, 106 MB). The dynarmic
tests (built with the NDK) pass on the Thor: 23,280 + 684, 0 failing.

**Rejected:**

* The NDK on the player's PC: 1-2 GB, Google's SDK licence to accept, and a
  second compiler beside the one the other setups use.
* zig's `aarch64-linux-android` target: zig has no bionic headers or stubs.
* Linking zig's libc++ (or musl) into the modules: a second C library inside
  an Android process.
* The modules or a driver through `run-as`: only a debuggable APK allows it.
* Vita3K's own Android app with our patches, as the product (D10's reasons).

**Update (2026-11-20): from a release.** The PC release carries the APK
(`setup/android/<id>.apk`, built by the release workflow's `android` job
and also attached to the release by itself). `ss-delta.exe --android`
(the importer's `setup.py --android`) builds the Android modules from
the game already built in the folder, so the dump isn't needed again,
and copies everything with adb. adb is Google's platform-tools, pinned
and downloaded like the compiler; its licence (the Android SDK License
Agreement) is the player's to accept, as Microsoft's is on Windows. The
whole SDK is still not needed: adb is 8–16 MB. Release APKs are signed
with **one release key**, kept in the repository's secrets and nowhere
else: Android updates an installed app only from an APK signed with the
same key, and a lost key means every player reinstalls (and loses the
saves on the device unless copied off first). Builds without the key
(local, or a manual workflow run) are signed with a debug key and are
for testing only.

**Update (2026-11-20): D27.**
The APK will build the game on the device itself; this PC route stays
as an alternative.

## D26 — iOS: the desktop setup writes the player's IPA; no IPA is released (accepted, 2026-11-20)

**Context:** Phase 15 (10-ios), an M4 iPad Pro as the test device. The
port needs no JIT (D11), which makes a sideloaded app possible. iOS runs
only code signed inside the app's bundle, and the modules must be built
from the player's own dump (D2, D18), so a playable IPA can exist only
after the player's setup has built them. Unlike Android's APK (D25), an
IPA in the release would be useful only as an input to that setup. A
survey of other recomps with iOS versions (2026-11-19, 10-ios): the two
mature ones that keep game code private, LASRecomp and PadMint, both have
a desktop program put the player's compiled code into a published base
app with no game code. Everyone else either publishes game-derived code
or builds only on a Mac with Xcode.

**Decision:**

* No IPA for players in the release. The **desktop setup** (Windows,
  Linux, macOS; the D22 folders) gets an **iOS output** that writes an
  unsigned IPA:
  * the **base app** (the frontend, no game code) is built by CI on
    GitHub's macOS runners and published as a release asset. Its
    executable is ad hoc signed with the app's entitlements, so
    sideloaders carry them over. The setup downloads it pinned by SHA-256
    and refuses one from another release;
  * the setup builds the modules for `aarch64-ios` with a pinned toolchain
    against a `libSystem.tbd` stub, puts them at the app's root and zips
    the IPA.
* Signing and installing are the player's sideloader's job (AltStore
  Classic, SideStore, Sideloadly). The setup signs nothing and never
  handles an Apple ID.
* The game data stays out of the IPA: the player copies it into the app's
  `Documents/` (Finder, Apple Devices, Files).
* Development runs from the Mac (the owner's choice): Xcode, the
  Simulator, and the iPad through `devicectl` with a free personal team,
  no sideloader.

**Open, to settle in 15a:** the module linker (zig's own, rust-lld as
LASRecomp uses, or LLVM's `ld64.lld` as PadMint uses) and the headers
(zig's Darwin headers, or Apple's open-source headers as PadMint uses,
because Apple's SDK may only be used on Apple computers). Check the
licence of zig's Darwin headers first.

**Consequences:** an iOS player needs a computer once per game or port
update, as on Android, but not a Mac. The same IPA serves every weekly
re-sign with a free Apple ID. The entitlements a player gets depend on
their sideloader and account (10-ios); whether the 4 GiB guest
reservation needs any is answered in 15b.

**Rejected:**

* A public IPA with the recompiled code inside (most XenonRecomp-based
  iOS ports): D18's reason.
* A base IPA for players to download: on its own it can't run anything.
* Building only on a Mac with Xcode (SnapPad, HarkinianPad): shuts out
  Windows and Linux players.
* Apple's SDK extracted from an Xcode `.xip` for use off a Mac
  (DiOShonored): Apple's licence.
* Signing in the setup with the player's Apple ID (what AltServer and
  Sideloadly do): their password through our tool, for little gain.
* Building or signing on the device: no project does it, and it would
  need a compiler and Python inside the app (as Android's 14g).

## D27 — Android: the APK builds the game on the device; Python, capstone and zig ride in it (accepted, 2026-11-20)

**Context:** the owner (2026-11-20): no release until a player can build
the game on the Android device, without a PC. That is the 0.4.0
milestone (14g). D25's PC route works, but it needs a computer and adb.
The survey (09-android, "The setup on the device") found that the
recomps with Android versions (Zelda64Recomp's line, Unleashed
Recompiled's ports) publish their recompiled code, which D18 rules out.
The one project that compiles on the phone, sm64ex-coop, does it in a
modified Termux. Android 10+ lets an app execute only programs packed in
its APK (the native library folder), not files it writes, while `dlopen`
of a library it wrote still works. python.org publishes embeddable
Android builds since 3.14, and zig has an `aarch64-linux` build of the
version the desktop setups pin.

**Decision:**

* The **game's APK does the whole setup itself**, as the desktop folders
  do (D22). On first start, or when the modules no longer match the app
  after an update, a setup screen:
  * picks the dump through Android's file picker (zip, vpk or folder; a
    pkg with its licence);
  * downloads the firmware from Sony, pinned as on the desktop;
  * installs it and the game and dumps the modules' ELFs through the
    front end's own native code;
  * recompiles and compiles the modules, then starts the game.
* **The tools ride in the APK as native libraries**, the one place
  Android lets an app run programs from:
  * python.org's CPython for Android (aarch64), with a small launcher
    executable so the kit's scripts run as they do on the desktop;
  * capstone built for Android;
  * zig's `aarch64-linux` build, pinned like the desktop's.

  They go in `jniLibs` as `lib*.so`, extracted at install. Python's
  standard library, the kit's scripts and zig's `lib/` are assets,
  unpacked into the app's storage on first use.
* The long job runs in a **foreground service** (a notification and a
  wake lock). The setup screen shows progress and the log, as the
  desktop window does, and the steps can be resumed.
* **D25's PC route stays**, for devices that are too weak or too full
  to build, and for development.
* Nothing derived from the dump leaves the device, and the APK holds no
  game code (D18).

**Open, for 14g's first step:**

* The time, memory and heat of recompiling and compiling on the Thor.
  The test PC builds the ten modules in 5.1 min with 10 jobs.
* Whether zig's static binary, and the processes it starts, run from the
  native library folder inside the app, not only from adb's shell.
* Whether CPython's `subprocess` works on Android (**hypothesis**).
* The APK's size: zig alone is 53 MB as `.tar.xz`, against today's
  20 MB APK.

**Update (2026-11-20): the probe** (09-android) ran the kit unchanged on
the Thor from adb's shell:

* about 29 min (4.2 to recompile, 24.4 to compile with 8 jobs);
* peaks of 1.8 GB per process and 95.9 °C;
* 4.4 GB of build space;
* `subprocess` works, and so do zig and its child processes;
* the modules are byte-identical to the PC's.

The tools pack to 110 MB, so the APK will be about 130 MB
(**estimate**). Still open: the same from the app's native library
folder.

**Update (2026-11-20): inside the app** (09-android).

* The tools run from the APK's native library folder: the self-test
  passes, and a library zig builds loads into the app.
* Started by the app, the full build takes **14.6 min** on the Thor (it
  gets more CPU than adb's shell) and gives the same modules.
* Trimmed, the tools add 85 MB: the release APK will be about
  **105 MB**.
* Every tool is aligned for 16 KiB pages (zig to 64 KiB).

**Consequences:**

* The APK grows to roughly 100 MB (**estimate**).
* Every APK update can rebuild the modules by itself, so a new front end
  never runs stale modules.
* A build takes minutes of full CPU load. The setup asks for a charger
  and keeps the screen's progress honest.
* 0.4.0 is tagged only when a Thor with no PC gets from the release's APK
  to a quest on native code.

**Rejected:**

* The recompiled code prebuilt in the APK, as most recomps with Android
  versions do: D18's reason.
* Termux, sm64ex-coop's route:
  * a third-party app the player installs and keeps working;
  * unpinned packages outside our checks, and Android 14 already broke
    that builder once;
  * its output would have to be moved into our app by hand.
* A separate builder APK: two apps to install and keep in step, and the
  modules would have to cross between them (a signature-protected
  provider). Kept as the fallback if one APK grows too big.
* Downloading the tools on demand:
  * Android won't execute a downloaded file;
  * the `linker64` trick that Termux's Play build uses can't start a
    static program like zig, and Google treats it as a W^X violation.
* Targeting API 28 to execute from app storage, as F-Droid's Termux
  does: it ties the whole app to old behaviour, against a rising install
  floor.
* LLVM as a library loaded in-process: no `exec` at all, and it could be
  downloaded, but building and maintaining LLVM for Android would be
  ours. The fallback if the tools can't run from the native library
  folder.

## D28 — The original game's raiments: a mod the player builds from their own dump (accepted, 2026-11-22)

**Context:** GitHub issue #11 asked for the original Soul Sacrifice's
content in Delta. Delta already has nearly all of it (D14 and its update),
except two collaboration raiments of the original's 1.30: ARKS Armor
(PSO2) and Dragonslayer / Ace of Souls (Ragnarok Odyssey ACE). Delta keeps
their names and `.chr` files, but not their 4 models and 23 textures
(01-research, "The original's collaboration raiments"). The owner chose a
mod made from the original game's files, holding only what the raiments
need, outside this repository, with the tools to make it in it, installed
like the Undub (2026-11-22).

**Decision:**

* `tools/og-raiments.py` builds the mod from the player's own dump of the
  original game with update 1.30 (any region; a NoNpDrm dump is installed
  first with `ss-delta.exe --install-content`) and their installed Delta:
  a copy of the `archive_patch3` the game reads now (the Undub's, if it is
  installed) with
  * the original's `CS21`/`CS22` models and textures;
  * Delta's `costume_table.csv` with two raiments added, rows 720-731 (ARKS
    Armor, type 51, text 3954) and 732-743 (Dragonslayer, type 52, text
    3956), 12 rows each like Delta's own, colour A given;
  * `parts_upper_param.csv` and `parts_lower_param.csv` with the
    whole-body model as both the top and the bottom of each row.

  It installs into `ux0/rePatch/<title>/` (or writes a folder, `--out`),
  and `--remove` restores the archive it was built on. A manifest and the
  replaced tables ride in the archive (`ss-delta/og-raiments/`), so
  rebuilding and removing need nothing else.
* A raiment is worn as top and bottom together ("Match with Above"). Worn
  as a top with another bottom, that bottom covers the costume's legs.
  The eraser tables can't hide a bottom's main mesh (01-research, "The
  eraser tables"), so a top hiding any bottom (the owner's first choice)
  would need a code change.
* `ss-delta.exe` gives the two raiments (`[game] dlc`) when the game's
  costume table has them, i.e. with the mod installed: the save's records
  for rows past 720 are created as the game writes them.

**Rejected:**

* Loose files or another patch slot: the game reads neither for these
  tables (01-research, "Loose files override archives").
* Shipping the mod or anything from either game: the files are the
  player's (CLAUDE.md, D18).

**Consequences:**

* Installing a mod that replaces `archive_patch3` after this one (the
  Undub) replaces it; building again over it keeps both.
* Removing the mod while a save wears one of the raiments leaves the body
  undrawn until another raiment is put on; ss-delta logs a warning, and
  the raiment list works. Writing the save image to fix it raced the
  game's own check of the file and stalled the load, so it is only
  reported.

**Update 1 (2026-11-22): a packaged mod.** The owner wants to publish
the mod outside the repository (Nexus Mods), as a file players add
without touching folders. The first version was a whole `archive_patch3`:
73.3 MB, of which 71.8 MB was Delta's own patch archive. It replaced the
Undub's archive (a merged build per combination), and broke with any
other mod of that archive. Now:

* `og-raiments.py` makes a **packaged mod**, `ss-delta-og-raiments.zip`
  (1.4 MB): the 27 models and textures and the 122 table rows, with an
  `ss-delta-mod.json` (the format: BUILDING, "Packaged mods"). It installs
  it with the front end, or writes it (`--out`).
* The front end (`game-frontend/packaged_mods.cpp`, shared with utakata)
  takes such a `.zip` through every path that adds a mod (the importer,
  `--dump`, Android's Add an add-on, RecompLauncher; all reach
  `--install-content`). It merges the package into the archive the game
  reads, keeps it in `ux0/rePatch/<title>/ss-delta-mods/<id>/`, merges it
  again when another mod replaces the archive (at install and at start),
  and takes it out with `--remove-mod <id>`. Tested: the merged archive
  equals the first version's member for member; with the Undub
  installed before or after, the Undub's members stay, its voice file
  among them; removed over the Undub, the Undub's archive is left exactly;
  removed alone, rePatch's copy is deleted.
* **Rejected:** a format of our own with its own extension (players and
  Nexus know `.zip`; the manifest inside says what it is); shipping whole
  archives (Delta's data in every download, and one mod per archive).
* Removing one on Android has no button yet (Mods (rePatch) turns all
  mods off).
* What is uploaded is the owner's decision: the zip holds models from the
  original game, which are collaboration content of other companies'
  games (Nexus's guidelines on third-party content). The repository still
  holds only the tool.


## D29 — The original game's Spirits' offerings: switched on by ss-delta from Delta's own tables (accepted, 2026-11-22)

**Context:** the original Soul Sacrifice's 20 pre-order offerings
(Spirits' Flamepike ... Spirits' Gravelshield, items 600000-601900) are
the only other content of the original Delta can't give (01-research,
"What only the original has"). They are copies of Delta's own offerings
(same models, effects, motions and sounds; their own numbers), and Delta
still has every row they need, commented out with a `;` in its own
tables. The owner asked to unlock them, as they need nothing from the
original game (2026-11-22), and then for a setting of `ss-delta.exe`
rather than a mod the player makes, as for the Japan-only raiments.

**Decision:**

* `[game] spirits_offerings` (on by default; acts with `dlc`): before the
  rePatch mods are read (a new front-end hook, `before_mods`, player 1
  only), `ss-delta.exe` makes a packaged mod (D28 update 1) from the
  installed game's own archives and installs it, or removes it when the
  setting is off. It holds the commented-out rows of
  `item_param_ply.csv` (20), `skill_param_ply.csv` (49),
  `magic_eff_pack_param_ply.csv` (49), `magic_explode_param_ply.csv`
  (44), `magic_gimmick_param_ply.csv` (12), `magic_bullet_param_ply.csv`
  (5), `magic_crawl_param_ply.csv` (6), `arms_param.csv` (6) and
  `protector_param.csv` (2), appended without the `;`. Fixes on the way,
  so they match Delta's own offerings:
  * the two fang arms name a punch-effect skill Delta removed (1601001,
    1601101); Delta's own fang arms have 0 there, and so do these;
  * arms rows with 0 in Delta's falcon columns take them from Delta's arm
    with the same model, as the Spirit swords already have them;
  * Spirits' Falconfeather is "test" in Delta's western item text: the
    original's names in the seven western languages are put back
    (`item_param_text_{us,ue,fr,ge,it,sp,bp}.msgt`; the names are in the
    code, nothing is read from the original).
  A package with an older version number is made again. Like any packaged
  mod it is merged again when another mod (the Undub) replaces the
  archive, and it needs Mods (rePatch) on.
* With `dlc`, `ss-delta.exe` gives each offering once per save when the
  game's tables have them: one of rank 0, marked NEW and obtained, in the
  play block's offering stock, as an offering box's gift does
  (`0x812f6ece`). The obtained bit marks it as given: it stays when the
  offering is carried or used up, so it isn't given again.

**Rejected:**

* A script the player runs to make the mod (the first version, the same
  day): the reason the original raiments need one, files only the
  original game has, doesn't apply here.
* Shipping the rows (Delta's data); writing the offerings into the save
  image as well (the game writes the stock from the block when it saves,
  and the image holds no record for them before).

**Consequences:**

* With the setting on, every install with `dlc` has a copy of
  `archive_patch3` (72 MB) in `ux0/rePatch/<title>/`, as any packaged mod
  makes; with it off (or `dlc` off) the copy is taken out again.
* Without the rows, a save that has the offerings loads with every other
  offering as before (the game matches the records by id); the 20 aren't
  shown, and the next save drops them. Switched on again, they are given
  again.
* The packaged-mod front end now also drops, on removal, a table it had
  taken from `tables_from` (here `protector_param.csv`, which only
  `archive` holds) once no kept mod adds to it: before, the table stayed
  in rePatch's archive and its copy was never deleted.

## D30 — Fixes to the game's code as recompiler overrides; the Blitz offerings at 60 fps (accepted, 2026-11-23)

**Context:**

* GitHub issue #14: at 60 fps a Blitz offering throws the player back
  about 1.7 times as far after a hit (19.7 units against 11.6 at 30), so
  the next cast of the chain falls short. The offerings' controller
  (`0x8153f206`) moves its caster by a fixed step a frame (speed and
  distance counted a frame, the movers `0x8136e29e`/`0x8136eeca` called
  with a scale of 1.0), while the push-back lasts a time in seconds
  (01-research, "Blitz offerings at 60 fps").
* D16 kept loading screens at 30 fps from the front end, because the
  game's own code couldn't be changed without losing the native code: a
  patch to the code makes the code hash differ, so the recompiled module
  isn't loaded. Doing the same here (30 fps while the player is in the
  Blitz state) would drop the frame rate for a second at every cast.

**Decision:**

* The recompiler takes a game project's overrides (`recompile.py
  --overrides`, `game.json` `recomp_overrides`; 05-recompiler,
  "Overrides"): the C++ of single plain instructions is replaced, each
  entry checked against the instruction it expects. The game's bytes stay
  as they are, so the code hash and the JIT's view are unchanged.
  `install-game.py` and `android-setup.py` pass the file, `make-setup.py`
  ships it.
* `overrides/eboot.json` makes the Blitz controller's per-frame steps
  follow the frame time: with k = 30 × the controller's frame time (at
  most 1), the rush's speed gain and distance, the movers' scale and the
  vertical gain (k²) and a per-frame decay (0.1^k) are scaled. At 30 fps
  nothing changes; below 30 fps the steps stay as the game made them, as
  on the Vita.

**Rejected:**

* 30 fps while a Blitz runs (the front end, as D16): every cast would
  stutter, and the owner asked for the code to be fixed.
* Fixing the controller to count frames (its frame time fixed at 1/30):
  distances right, but every Blitz would play twice as fast at 60 fps.
* Patching the eboot's bytes: the native code would no longer load.

**Consequences:**

* The kit change is shared with utakata; without an overrides file the
  recompiler's output is as before (`report.txt` gains an `overrides:`
  line).
* The fix lives in the native code only: with `[recompiled] enabled =
  false` (everything on the JIT) the Blitz behaves as before.
* Players get it when the setup builds the game again from their dump
  (an update through RecompLauncher, or `--install`).
* Update (the same day): the loading-screen race of D16 is fixed the same
  way (three overrides around `0x812b50ce`, 01-research "The loading
  screen at 60 fps"). So that the front end can tell an eboot with the fix
  from one built before it (the code hash is the same), the overrides name
  `features` (`blitz_frame_time`, `loading_race`), which the module reports
  through a second, optional export (`armrecomp_aot_features`, aot_abi.h;
  no ABI version change, older modules just lack it) and the fork asks
  with `aot_module_has_feature`, for a module whose native code is
  checked. With `loading_race` the 30 fps loading screens are dropped;
  without it (an eboot built before, the JIT) they stay.
