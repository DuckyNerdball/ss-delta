# Playing together over the internet

Ad Hoc Play was made for players in one room. ss-delta also plays it between
homes, through a VPN that puts the players' machines into one private
network: [Tailscale](#tailscale), [ZeroTier](#zerotier) or
[Radmin VPN](#radmin-vpn) below, or any other. Every player's copy of the
game must be the same ss-delta release, 0.5.2 or newer.

At home, in one network, none of this is needed: `network = lan` alone finds
the others ([Ad Hoc Play](INSTALLING.md#ad-hoc-play)).

## How it works

The VPN gives each machine a second address, in the VPN's network. Over most
VPNs the game's way of finding rooms (broadcasts to the whole network)
doesn't arrive, so the other players tell their copy the host's VPN address,
and the game sends to it directly. The host needs no list: it answers
whoever reaches it.

## 1. Set up the VPN

Everyone installs the same VPN and joins one network with it: see its
section below. Note the host's address in that network.

## 2. In the game

Open the settings menu: **F1**, or **Select** (Back/View) held for a second on
a gamepad; on Android, the menu button at the top of the screen. Then the
**Multiplayer** page (L1/R1 change pages):

* **Network**: `lan`. Only Windows needs this (it starts with `local`, for
  several copies on one PC); restart the game after changing it.
* **Network adapter**:
  * The host picks the VPN's adapter: Left/Right go through the machine's
    adapters, each shown with its address and name; take the one with the
    VPN address.
  * The other players can leave it at `auto`: it takes the adapter that
    reaches the host's address, the VPN's.
* **Peers (host address)**, on every player's copy except the host's: press
  Cross, type the host's VPN address, press Cross or Enter. Without a
  keyboard (Steam Deck, a gamepad on Android), Up/Down change the character
  under the cursor, Left/Right move it, Square deletes one. The host leaves
  it empty.

On Windows, allow `ss-delta.exe` through the firewall when Windows asks, for
**private and public** networks (a VPN's network often counts as public).
On macOS, allow the game to "find and connect to devices on your local
network".

## 3. Play

The host opens Librom → **Network** → **Ad Hoc Play** → **Create Room**; the
others use **Search for Room** and pick it. From there it is the game's own
Ad Hoc Play.

## Tailscale

[Tailscale](https://tailscale.com): Windows, macOS, Linux and Android; free
for personal use.

* Everyone installs it from [tailscale.com/download](https://tailscale.com/download)
  and signs in.
* The host invites the others into their network: in the
  [admin console](https://login.tailscale.com/admin/users), **Users → Invite
  users**. Each player accepts the invitation and signs in with it. (Sharing
  only the host's machine instead has not been tried.)
* Check: in the Tailscale app every player sees the others' machines, shown
  as connected.
* The host's address is `100.x.y.z`: the Tailscale app shows it next to the
  machine's name (on Windows, the Tailscale icon in the taskbar, then the
  machine under **My devices**; a click copies it). With MagicDNS on
  (Tailscale's default), the machine's name works in Peers too.
* `tailscale ping <host address>` on a guest's machine tells whether the
  machines reach each other, and "via DERP" if Tailscale relays the
  connection through its servers (the game may lag then).

## ZeroTier

[ZeroTier](https://www.zerotier.com): Windows, macOS, Linux and Android; free
for a few dozen devices.

* The host creates a network: sign in at [my.zerotier.com](https://my.zerotier.com),
  **Create A Network**, and note its 16-character **Network ID**.
* Everyone installs ZeroTier One from [zerotier.com/download](https://www.zerotier.com/download/)
  and joins the network with that ID (the ZeroTier icon, **Join New
  Network**).
* The host lets them in: on the network's page at my.zerotier.com, under
  **Members**, tick **Auth** for each player's machine.
* The host's address is the one my.zerotier.com lists for the host's
  machine under **Managed IPs** (also in the ZeroTier app, under the
  network).

## Radmin VPN

[Radmin VPN](https://www.radmin-vpn.com): **Windows only**, free, made for
LAN games. Players on macOS, Linux, a Steam Deck or Android can't join a
Radmin VPN network; use Tailscale or ZeroTier then.

* Everyone installs it from [radmin-vpn.com](https://www.radmin-vpn.com).
* The host creates a network: **Network → Create network**, with a name and
  a password.
* The others join it: **Network → Join network**, with that name and
  password.
* The host's address is the `26.x.y.z` one the Radmin VPN window shows next
  to the host's machine.

## If no room shows up

* Does the VPN show both machines connected? Most VPNs' apps show it; a
  `ping <host address>` from a guest's machine answers if they reach each
  other (Windows answers pings only if its firewall allows them).
* Is the host's VPN address right on the guests' copies, and is it empty on
  the host's? Does the host's Network adapter show the VPN address? Do all
  players run the same release?
* The firewall: Windows must allow `ss-delta.exe` on public networks too.
* The log, `ss-delta/vita3k.log` in the game's folder: `Ad Hoc Play: network
  adapter ...` names the adapter in use, and on the host a guest shows up as
  `Ad Hoc Play: a packet from <the guest's VPN address>`. Attach the log of
  each player to an [issue](https://github.com/vita-recomps/ss-delta/issues);
  `net_trace` on the Debug page adds every packet to it.
