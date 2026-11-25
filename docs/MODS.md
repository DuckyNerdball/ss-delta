# Installing mods

ss-delta takes two kinds of mods for *Soul Sacrifice Delta*:

| Kind | What it looks like | Example |
|---|---|---|
| **rePatch mod** | a folder named `rePatch` (often in a `.7z`), made for the Vita's rePatch plugin | [Undub patch](https://archive.org/details/soul_sacrifice_delta_undub_patch): Japanese voices from the start |
| **Packaged mod** | a `.zip` with an `ss-delta-mod.json` inside, made for ss-delta | [The Original Raiments: ARKS Armor and Dragonslayer](https://www.moddb.com/mods/the-original-raiments-arks-armor-dragonslayer) (ModDB) |

Both work with the US and the EU game, and with each other, in either
order. ss-delta keeps mods beside the game in `fs/ux0/rePatch/`, so the
game's own files are never changed.

## Before you start

* Build the game once: start ss-delta and finish the first setup from
  your dump ([INSTALLING](INSTALLING.md)).
* Packaged mods need release 0.4.2 or newer; rePatch mods need 0.4.0 or
  newer.

## 1. Get the mod ready

* **The download is a `.7z` or `.rar`:** unpack it first. ss-delta reads
  folders and `.zip` files only.
* **rePatch mod:** you'll give ss-delta the folder that *holds* `rePatch`
  (not `rePatch` itself), or a `.zip` of that folder.
* **Packaged mod:** you'll give ss-delta the `.zip` that holds
  `ss-delta-mod.json` as it is. Don't unpack it.

## 2. Add it

Adding a mod takes a few seconds and doesn't build the game again.

* **Windows:** close the game, then from the game's folder run
  ```
  ss-delta.exe --dump "C:\path\to\the-mod.zip"
  ```
  Or start `ss-delta.exe --install` and put the mod in the importer's
  add-on row, leaving the game's rows empty.
* **Linux / Steam Deck:** `./ss-delta.x86_64 --dump "/path/to/the-mod.zip"`
* **macOS:**
  `"Soul Sacrifice Delta.app/Contents/MacOS/ss-delta" --dump "/path/to/the-mod.zip"`
* **Android:** long-press the ss-delta icon, choose **Add an add-on**, and
  pick the mod. It has to be a `.zip`; for a rePatch mod, zip the folder
  that holds `rePatch`.
* **RecompLauncher:** use the Add-ons step of the game's setup.

ss-delta then starts the game. The log (`ss-delta/vita3k.log`) names
each mod it installed and the files the game reads from it.

## 3. Check it's on

Open the settings menu (F1, or hold Select on a gamepad). On its Game page,
**Mods (rePatch)** must be on. It's on by default.

For **The Original Raiments**, **Add-ons (DLC)** must be on as well. Then
the two raiments appear in Portraiture → Appearance → Raiments, marked
new. Wear each one as both top and bottom: press △ "Match with Above" in
the bottom list. The [gallery](GALLERY.md#from-the-original-game-mod)
shows them.

## Removing a mod

* **Packaged mod:** `ss-delta --remove-mod <id>` (for The Original
  Raiments: `--remove-mod og-raiments`). The install log names the id.
  If you remove a raiment mod, put on another raiment first: a save that
  wears a removed raiment shows no body until you choose another one.
* **rePatch mod:** delete its folder in `fs/ux0/rePatch/`.
* **All mods:** delete `fs/ux0/rePatch/`, or turn **Mods (rePatch)** off to
  keep them without using them. On Android that toggle is the only way to
  turn mods off for now.

## The Original Raiments without ModDB

The two raiments come from the first *Soul Sacrifice*, and ss-delta can't
ship them. If you own the original game (update 1.30, any region), you can
make the same mod yourself with `tools/og-raiments.py`
([INSTALLING](INSTALLING.md#what-you-need)). [ORIGINAL-CONTENT](ORIGINAL-CONTENT.md#the-collaboration-raiments)
explains why they're missing from Delta.

## Troubleshooting

* **Nothing changed in the game:** check that Mods (rePatch) is on and that
  the log lists the mod. A `.7z` is ignored; unpack it.
* **"installed for PCSF00532" (or PCSA00152) for a mod made for the other
  region:** that's expected. ss-delta puts a mod under the title you have
  installed.
* **The Undub and the raiments together:** add them in any order. A
  packaged mod is merged into the archive the game reads, so it doesn't
  replace the Undub.
