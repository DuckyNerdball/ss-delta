ss-delta: Soul Sacrifice Delta (US PCSA00152 or EU PCSF00532, 1.30) on macOS
(13.3 or newer, Apple Silicon).

"Soul Sacrifice Delta.app" in this folder starts the game: double-click it,
or keep it in the Dock. It starts ss-delta.arm64, which runs the game
installed in a Vita file system ([paths] vita_fs in ss-delta.ini; default:
the fs folder next to this file), with the game's code recompiled to native
code (ssd_aot_*.dylib, built on this Mac from your own dump). The US and EU
games are the same build: either one runs. When both are installed, the US
one does; ./ss-delta.arm64 --title-id PCSF00532 (in Terminal, in this folder)
starts the EU one. Graphics go through MoltenVK (Vulkan over Metal,
libMoltenVK.dylib here). Keep the app, ss-delta.arm64 and the files next to
it together: moving the folder needs the setup run again (or a new app).

Settings: press F1, or hold Select (the View button) on a gamepad for a
second, to open the settings menu over the paused game (Up/Down choose,
Left/Right or Cross change, L1/R1 or Q/E switch pages, Circle, Esc or F1
close). Window size, fullscreen, vsync, filter, volume and frame rate change
at once; the rest are marked * and take effect the next time the game starts.
The menu writes ss-delta.ini, which can also be edited by hand (key bindings
and paths are there only). On a Mac keyboard the F keys need fn held, unless
they are set as standard function keys (System Settings, Keyboard).

Settings are in ss-delta.ini: resolution, window, fullscreen (F11 or
Option+Return while playing), filter, frame rate (frame_rate under
[display]: 60, or 30 as on the Vita; loading screens stay at 30), volume,
keyboard and gamepad bindings. The mouse or trackpad is the touchscreen:
click for the front, right-click (two fingers) for the rear. The Black Rite
icon (touch and hold) is also on F and the gamepad's left trigger ([touch] in
ss-delta.ini). F12 saves a screenshot to ss-delta/screenshots.

Language: the game has no language option of its own; it uses the console's
language, which ss-delta.arm64 sets from Language on the menu's Game page
([game] language in ss-delta.ini; takes effect at the next start). The US
game has English, French, Spanish and Portuguese (Brazil), the EU game
English, French, Spanish, German and Italian; a language the installed game
lacks gives English.

The add-ons (raiments, hoods, additional pacts) are unlocked: their content
is in the game since update 1.30, and ss-delta.arm64 records them in your
save once ([game] dlc in ss-delta.ini; a copy of the previous file goes to
ss-delta/save-backups).

Saves are in the Vita file system (ux0/user/00/savedata/PCSA00152, or
PCSF00532 for the EU game). To use a save from a Vita (decrypted, e.g. with
VitaShell or Apollo), or from the Windows or Linux port, run in Terminal, in
this folder:
  ./ss-delta.arm64 --import-save <folder or .zip> [--slot 2]
The game has three save slots (default 1); the save folder as it was is kept
in ss-delta/save-backups. To copy a slot out:
  ./ss-delta.arm64 --export-save <folder> [--slot 2]

Ad Hoc Play (Librom, Network, Ad Hoc Play): on a Mac, use network = lan in
ss-delta.ini ([multiplayer]): computers in one network, Windows, Linux or
macOS, each running the game (not yet tested on a Mac). Several copies on
one Mac (network = local, ./ss-delta.arm64 --player 2) don't work yet:
macOS only has the address 127.0.0.1 for them.

ss-delta is built from Vita3K (https://github.com/Vita3K/Vita3K) and is under
the GNU GPL version 2. The ssd_aot_*.dylib files and the game files are
derived from your own copy of the game: do not share them.
