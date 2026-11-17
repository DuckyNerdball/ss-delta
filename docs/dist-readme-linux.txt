ss-delta: Soul Sacrifice Delta (US PCSA00152 or EU PCSF00532, 1.30) on Linux
(x86-64; Steam Deck).

ss-delta.x86_64 runs the game installed in a Vita file system ([paths] vita_fs
in ss-delta.ini; default: the fs folder next to this file), with the game's
code recompiled to native code (ssd_aot_*.so, built from your own dump). The
US and EU games are the same build: either one runs. When both are installed,
the US one does; ./ss-delta.x86_64 --title-id PCSF00532 starts the EU one. It
needs Vulkan, glibc 2.30 or newer and nothing else from the system.

Steam Deck: the setup adds the game to Steam as a non-Steam game (its "Add the
game to Steam" box; Steam must be running), so it starts from Game Mode. If it
didn't, add ss-delta.desktop from this folder with "Add a Non-Steam Game"
(Steam, Games menu, in desktop mode). No compatibility tool is needed: it is a
Linux program, not a Windows one. The Deck's controls are a gamepad to the game; the touchscreen is
the Vita's front touchscreen.

Settings: press F1, or hold Select (the View button) on a gamepad for a
second, to open the settings menu over the paused game (Up/Down choose,
Left/Right or Cross change, L1/R1 or Q/E switch pages, Circle, Esc or F1
close). Window size, fullscreen, vsync, filter, volume and frame rate change
at once; the rest are marked * and take effect the next time the game starts.
The menu writes ss-delta.ini, which can also be edited by hand (key bindings
and paths are there only).

Settings are in ss-delta.ini: resolution, window, fullscreen (F11 or
Alt+Enter while playing), filter, frame rate (frame_rate under [display]:
60, or 30 as on the Vita; loading screens stay at 30), volume, keyboard and
gamepad bindings. The mouse is the touchscreen: left button front, right
button rear. The Black Rite icon (touch and hold) is also on F and the
gamepad's left trigger ([touch] in ss-delta.ini). F12 saves a screenshot to
ss-delta/screenshots.

Language: the game has no language option of its own; it uses the console's
language, which ss-delta.x86_64 sets from Language on the menu's Game page
([game] language in ss-delta.ini; takes effect at the next start). The US
game has English, French, Spanish and Portuguese (Brazil), the EU game
English, French, Spanish, German and Italian; a language the installed game
lacks gives English.

The add-ons (raiments, hoods, additional pacts) are unlocked: their content
is in the game since update 1.30, and ss-delta.x86_64 records them in your
save once ([game] dlc in ss-delta.ini; a copy of the previous file goes to
ss-delta/save-backups).

Saves are in the Vita file system (ux0/user/00/savedata/PCSA00152, or
PCSF00532 for the EU game). To use a save from a Vita (decrypted, e.g. with
VitaShell or Apollo), or from the Windows port, run
  ./ss-delta.x86_64 --import-save <folder or .zip> [--slot 2]
The game has three save slots (default 1); the save folder as it was is kept
in ss-delta/save-backups. To copy a slot out:
  ./ss-delta.x86_64 --export-save <folder> [--slot 2]

Ad Hoc Play (Librom, Network, Ad Hoc Play) works between copies of the game:
start ss-delta.x86_64 for player 1 and run-player2.sh (ss-delta.x86_64
--player 2) for player 2, up to --player 4. One copy creates a room, the
others use Search for Room. Each player has its own saves (ux0/user/0<N-1>,
copied from player 1's on its first start), log and config
(ss-delta/player<N>); ss-delta-player<N>.ini next to ss-delta.ini overrides
settings for player N. [multiplayer] in ss-delta.ini: network = local (copies
on this computer) or lan (computers in one network, Windows or Linux: each
runs the game), and gamepad = 1-4 to give each copy its own gamepad.

ss-delta is built from Vita3K (https://github.com/Vita3K/Vita3K) and is under
the GNU GPL version 2. The ssd_aot_*.so files and the game files are derived
from your own copy of the game: do not share them.
