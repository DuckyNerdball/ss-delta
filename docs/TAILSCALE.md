# Playing together over the internet (Tailscale)

Ad Hoc Play was made for players in one room. ss-delta also plays it between
homes, over [Tailscale](https://tailscale.com): a free program that puts your
computers and phones into one private network, wherever they are. Every
player's copy of the game must be the same ss-delta release, after 0.5.2.

## 1. Join one Tailscale network

* Everyone installs Tailscale from [tailscale.com/download](https://tailscale.com/download)
  (Windows, macOS, Linux, Android) and signs in. The Steam Deck needs a
  setup made for SteamOS: its system is read-only, so Tailscale's Linux
  packages don't install there.
* The host invites the others into their network: in the
  [admin console](https://login.tailscale.com/admin/users), **Users → Invite
  users**. Each player accepts the invitation and signs in with it. (Sharing
  only the host's machine instead has not been tried.)
* Check: in the Tailscale app every player sees the others' machines, shown
  as connected.

## 2. The host's address

The host looks up their Tailscale address, `100.x.y.z`: the Tailscale app
shows it next to the machine's name (on Windows, the Tailscale icon in the
taskbar, then the machine under **My devices**; a click copies it). With
MagicDNS on (Tailscale's default), the machine's name works too.

## 3. In the game

Open the settings menu: **F1**, or **Select** (Back/View) held for a second on
a gamepad; on Android, the menu button at the top of the screen. Then the
**Multiplayer** page (L1/R1 change pages):

* **Network**: `lan`. Only Windows needs this (it starts with `local`, for
  several copies on one PC); restart the game after changing it.
* **Network adapter**: leave it at `auto`; it picks Tailscale's.
* **Peers (host address)**, on every player's copy except the host's: press
  Cross, type the host's address, press Cross or Enter. Without a keyboard
  (Steam Deck, a gamepad on Android), Up/Down change the character under the
  cursor, Left/Right move it, Square deletes one. The host leaves it empty:
  the game answers whoever reaches it.

On Windows, allow `ss-delta.exe` through the firewall when Windows asks, for
**private and public** networks (Tailscale's network often counts as public).
On macOS, allow the game to "find and connect to devices on your local
network".

## 4. Play

The host opens Librom → **Network** → **Ad Hoc Play** → **Create Room**; the
others use **Search for Room** and pick it. From there it is the game's own
Ad Hoc Play.

## If no room shows up

* Is Tailscale connected on both machines, and do they see each other? A
  `tailscale ping <host address>` on a guest's machine answers if they do.
* Is the host's address right on the guests' copies, and is it empty on the
  host's? Do all players run the same release?
* The firewall: Windows must allow `ss-delta.exe` on public networks too.
* The log, `ss-delta/vita3k.log` in the game's folder: `Ad Hoc Play: network
  adapter auto (...)` should name Tailscale's adapter, and on the host a guest
  shows up as `Ad Hoc Play: a packet from 100.x.y.z`. Attach the log of each
  player to an [issue](https://github.com/vita-recomps/ss-delta/issues);
  `net_trace` on the Debug page adds every packet to it.

If `tailscale ping` reports "via DERP", Tailscale relays the connection
through its servers instead of connecting the machines directly, and the game
may lag.

At home, in one network, none of this is needed: `lan` alone finds the others
([Ad Hoc Play](INSTALLING.md#ad-hoc-play)).
