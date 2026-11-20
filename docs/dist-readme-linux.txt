ss-delta: Soul Sacrifice Delta (US PCSA00152 or EU PCSF00532, 1.30) on Linux
(x86-64; Steam Deck).

Start ss-delta.x86_64 (from a file manager, or ./ss-delta.x86_64 in a
terminal; on a Steam Deck in desktop mode the first time). The first time, it
builds the game from your own dump: a window asks for it (a folder, .zip or
.vpk of the game with its 1.30 update, or the PSN .pkg files with their
licence), downloads the PS Vita firmware from Sony and a compiler (zig, about
240 MB in all), installs the game and compiles its code on this computer,
which takes a few minutes. Play then starts the game, and from then on
ss-delta.x86_64 goes straight to it. It needs Vulkan, glibc 2.30 or newer and
nothing else from the system.

Everything stays in this folder: the game (fs), its code compiled for this
computer (ssd_aot_*.so), settings (ss-delta.ini), saves, logs and the shader
cache. The downloads are deleted once the game is built; delete the folder and
the game is gone (apart from the menu entry and Steam entry, if you let the
importer add them). Nothing of the game leaves your computer.

Command line (./ss-delta.x86_64 --help lists it all): --install opens the
importer again (another dump, an update); --dump <file> builds without the
window; --add-to-steam adds the game to Steam; --fullscreen or --windowed;
--set section.key=value sets any setting of ss-delta.ini for one run; --game
<folder> plays the game in another folder.

Android (64-bit ARM with Vulkan; made for Snapdragon handhelds such as the AYN
Thor): once the game is built here, ./ss-delta.x86_64 --android
puts it on the device over USB or Wi-Fi debugging: a window asks how the device
is connected, builds the game's code for Android, downloads adb from Google and
copies the app (setup/android/ss-delta.apk), the game's files and its code.
Saves already on the device stay. The APK also builds the game on the device
itself from your dump, with no PC: install it there and start it (Android in
https://github.com/vita-recomps/ss-delta/blob/main/docs/INSTALLING.md).

The US and EU games are the same build: either one runs. When both are
installed, the US one does; ./ss-delta.x86_64 --title-id PCSF00532 starts the
EU one.

Steam Deck: the importer adds the game to Steam as a non-Steam game (its "Add
the game to Steam" box; Steam must be running), so it starts from Game Mode. If
it didn't, run ./ss-delta.x86_64 --add-to-steam, or add ss-delta.desktop from
this folder with "Add a Non-Steam Game" (Steam, Games menu, in desktop mode).
No compatibility tool is needed: it is a Linux program, not a Windows one. The
Deck's controls are a gamepad to the game; the touchscreen is the Vita's front
touchscreen.

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

Intro logos: Skip intro logos on the menu's Game page ([game] skip_intro in
ss-delta.ini) skips the health warning and the company logos at start; the
game opens on its title screen.

Language: the game has no language option of its own; it uses the console's
language, which ss-delta.x86_64 sets from Language on the menu's Game page
([game] language in ss-delta.ini; takes effect at the next start). The US
game has English, French, Spanish and Portuguese (Brazil), the EU game
English, French, Spanish, German and Italian; a language the installed game
lacks gives English.

Button prompts: Xbox labels in place of the PlayStation symbols, from Button
prompts on the menu's Game page ([game] button_labels = xbox, or auto to
follow the connected gamepad; switches at once). Each symbol shows the
gamepad button bound to it in [gamepad]: A, B, X, Y, LB, RB, and Xbox's Menu
and View for START and SELECT, also in the tutorial pictures and the text.

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
settings for player N. [multiplayer] in ss-delta.ini: network = lan (the
default: computers in one network, Windows, Linux or macOS, each running the
game) or local (copies on this computer), and gamepad = 1-4 to give each copy
its own gamepad.

ss-delta is built from Vita3K (https://github.com/Vita3K/Vita3K) and is under
the GNU GPL version 2. The ssd_aot_*.so files and the game files are derived
from your own copy of the game: do not share them.
