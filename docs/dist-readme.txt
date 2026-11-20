ss-delta: Soul Sacrifice Delta (US PCSA00152 or EU PCSF00532, 1.30) on PC.

Start ss-delta.exe. The first time, it builds the game from your own dump: a
window asks for it (a folder, .zip or .vpk of the game with its 1.30 update, or
the PSN .pkg files with their licence), downloads the PS Vita firmware from
Sony and a compiler (about 650 MB; accept Microsoft's licence for the C++
runtime and Windows SDK it uses), installs the game and compiles its code on
this PC, which takes a few minutes. Play then starts the game, and from then on
ss-delta.exe goes straight to it. Windows may warn the first time ("More info",
"Run anyway"): ss-delta.exe isn't signed.

Everything stays in this folder: the game (fs), its code compiled for this PC
(ssd_aot_*.dll), settings (ss-delta.ini), saves, logs and the shader cache.
The downloads are deleted once the game is built; delete the folder and the
game is gone. Nothing of the game leaves your PC.

Command line (ss-delta.exe --help lists it all): --install opens the importer
again (another dump, an update); --dump <file> builds without the window (add
--accept-microsoft-license); --fullscreen or --windowed; --set section.key=value
sets any setting of ss-delta.ini for one run; --game <folder> plays the game in
another folder.

Android (64-bit ARM with Vulkan; made for Snapdragon handhelds such as the AYN
Thor): once the game is built here, ss-delta.exe --android
puts it on the device over USB or Wi-Fi debugging: a window asks how the device
is connected, builds the game's code for Android, downloads adb from Google and
copies the app (setup\android\ss-delta.apk), the game's files and its code.
Saves already on the device stay. The APK also builds the game on the device
itself from your dump, with no PC: install it there and start it (Android in
https://github.com/vita-recomps/ss-delta/blob/main/docs/INSTALLING.md).

The US and EU games are the same build: either one runs. When both are
installed, the US one does; ss-delta.exe --title-id PCSF00532 starts the EU one.

Settings: press F1, or hold Select (Back/View) on a gamepad for a second, to
open the settings menu over the paused game (Up/Down choose, Left/Right or
Cross change, L1/R1 or Q/E switch pages, Circle, Esc or F1 close). Its last
page, Exit, quits the game: press Cross (X) twice on Exit the game. Window
size, fullscreen, vsync, filter, volume and frame rate change at once; the
rest are marked * and take effect the next time the game starts. The menu
writes ss-delta.ini, which can also be edited by hand (key bindings and paths
are there only).

Settings are in ss-delta.ini: resolution, window, fullscreen (F11 or
Alt+Enter while playing), filter, frame rate (frame_rate under [display]:
60, or 30 as on the Vita; loading screens stay at 30), volume, keyboard and
gamepad bindings. The mouse is the touchscreen: left button front, right
button rear. The Black Rite icon (touch and hold) is also on F and the
gamepad's left trigger ([touch] in ss-delta.ini). F12 saves a screenshot to
ss-delta\screenshots.

Intro logos: Skip intro logos on the menu's Game page ([game] skip_intro in
ss-delta.ini) skips the health warning and the company logos at start; the
game opens on its title screen.

Language: the game has no language option of its own; it uses the console's
language, which ss-delta.exe sets from Language on the menu's Game page
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
is in the game since update 1.30, and ss-delta.exe records them in your save
once ([game] dlc in ss-delta.ini; a copy of the previous file goes to
ss-delta\save-backups).

Saves are in the Vita file system (ux0\user\00\savedata\PCSA00152, or
PCSF00532 for the EU game). To use a
save from a Vita (decrypted, e.g. with VitaShell or Apollo), run
  ss-delta.exe --import-save <folder or .zip> [--slot 2]
The game has three save slots (default 1); the save folder as it was is kept
in ss-delta\save-backups. To copy a slot out:
  ss-delta.exe --export-save <folder> [--slot 2]

Ad Hoc Play (Librom, Network, Ad Hoc Play) works between copies of the game:
start ss-delta.exe for player 1 and run-player2.bat (ss-delta.exe --player 2)
for player 2, up to --player 4. One copy creates a room, the others use Search
for Room. Each player has its own saves (ux0\user\0<N-1>, copied from player
1's on its first start), log and config (ss-delta\player<N>);
ss-delta-player<N>.ini next to ss-delta.ini overrides settings for player N.
[multiplayer] in ss-delta.ini: network = local (copies on this PC) or lan
(computers in one network, Windows, Linux or macOS, each running the game;
allow ss-delta.exe through the firewall),
and gamepad = 1-4 to give each copy its own gamepad.

ss-delta is built from Vita3K (https://github.com/Vita3K/Vita3K) and is under
the GNU GPL version 2. The ssd_aot_*.dll files and the game files are derived
from your own copy of the game: do not share them.
