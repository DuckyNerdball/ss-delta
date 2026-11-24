# Content from the original Soul Sacrifice

*Soul Sacrifice Delta* (2014) is a reworked edition of the first *Soul
Sacrifice* (2013). GitHub issue
[#11](https://github.com/vita-recomps/ss-delta/issues/11) asked whether
anything of the original is missing from Delta and could be brought over.
This page sums up what we found, and what ss-delta does about each part.

In short, almost everything the original has is already in Delta, often
under a new name. Two things were left out:

* 20 pre-order offerings, which ss-delta switches back on;
* two collaboration raiments, which a mod adds from your own copy of the
  original.

One mechanic was changed rather than removed.

* [At a glance](#at-a-glance)
* [The Spirits' offerings](#the-spirits-offerings)
* [The collaboration raiments](#the-collaboration-raiments)
* [Changed in Delta: Sanguine Shot](#changed-in-delta-sanguine-shot)
* [Already in Delta](#already-in-delta)
* [How this was checked](#how-this-was-checked)

## At a glance

| Original-only content | In ss-delta | How |
|---|---|---|
| [Spirits' offerings](#the-spirits-offerings) (20, the pre-order bonus) | ✅ built in | `[game] spirits_offerings`, on by default with Add-ons (DLC) |
| [ARKS Armor and Dragonslayer](#the-collaboration-raiments) (collaboration raiments) | ✅ as a mod | made from your own copy of the original with `tools/og-raiments.py` |
| [Sanguine Shot](#changed-in-delta-sanguine-shot) (right-arm shot) | — | replaced in Delta by Sanguine Cannon, Angelshot and Demonshot |
| Mononofu (collaboration raiment) | already in Delta | remade for Delta |
| Black Rite Angelus (DLC) | already in Delta | the Sanctuarium faction's rite |

The [gallery](GALLERY.md) has screenshots of the raiments, including
[the original's two](GALLERY.md#from-the-original-game-mod), and of the
raiments ss-delta unlocks from Delta itself: the
[PSN gifts](GALLERY.md#gifts-from-psn) and the
[Japan-only raiments](GALLERY.md#only-in-japan). Those are Delta's own
add-ons, not the original's.

## The Spirits' offerings

The original's pre-order bonus: 20 offerings "gifted from the spirits",
Spirits' Flamepike to Spirits' Gravelshield. Delta still has every one of
them, switched off: their rows are commented out in its own tables, and
some were even brought up to date for Delta before being turned off.
Their names are still in Delta's text, apart from Spirits' Falconfeather,
which reads "test" in the western languages.

**In ss-delta** they are switched on by `[game] spirits_offerings` (on by
default; it needs Add-ons (DLC) and Mods (rePatch) on). At the first
start ss-delta makes a copy of the game's patch archive with them in
`fs/ux0/rePatch/`, from your own Delta; nothing of the original game is
needed. Each offering is given once in every save, at the end of Select
Offerings, marked NEW. Turned off, they are taken out of the game again
at the next start, and the game drops them from the save the next time
it saves; your other offerings stay as they are.
[INSTALLING](INSTALLING.md#what-you-need) has the player's side,
[D29](decisions.md) the decision.

**They are not new spells.** Each one is a copy of an offering Delta
already has. It uses the same weapon or arm model, the same effects,
sounds, animations and controls, with its own numbers. The only
difference you can see or hear is Spirits' Stone Arrow's hit sound, a
generic one instead of the rock hit. Compared with the offering it copies,
most attack offerings have far fewer casts; the defensive and movement
ones (Storm Ward, Falconfeather, Gravelshield) have more casts but a
shorter duration. Power is higher on some and lower on others.

Casts, power and duration as Select Offerings shows them (a duration of
0 means none, "—" no limit):

| Spirits' offering | Casts | Power | Duration (s) | Copy of (Delta) | Casts | Power | Duration (s) |
|---|---|---|---|---|---|---|---|
| Spirits' Flamepike | 2 | 50 | 30 | Imp Pitchfork | 5 | 30 | 60 |
| Spirits' Icebrand | 2 | 50 | 30 | Swordsman Icebrand | 5 | 30 | 60 |
| Spirits' Firearm | 2 | 80 | 50 | Firegiant's Arm | 5 | 65 | 70 |
| Spirits' Stormfist | 2 | 80 | 50 | Stormgiant's Arm | 5 | 65 | 70 |
| Spirits' Flame Arrow | 5 | 30 | — | Fire Djinn's Arrow (M) | 15 | 30 | — |
| Spirits' Stone Arrow | 5 | 30 | — | Stone Arrow (M) | 15 | 30 | — |
| Spirits' Blazestone | 4 | 220 | 0 | Firedrake Egg (M) | 12 | 200 | 0 |
| Spirits' Blightstone | 4 | 220 | 0 | Leafdrake Egg (M) | 12 | 200 | 0 |
| Spirits' Greatroot | 3 | 90 | 0 | Great Tree Root (Tri) | 13 | 20 | 0 |
| Spirits' Sparktree | 3 | 90 | 0 | Sparktree Root (Tri) | 13 | 20 | 0 |
| Spirits' Dragon fang | 5 | 90 | 35 | Firedrake Fang (M) | 7 | 100 | 70 |
| Spirits' Wolf fang | 5 | 90 | 35 | Blizzard Wolf Fang (M) | 7 | 100 | 70 |
| Spirits' Heart | 2 | 330 | 30 | Stonefiend Entrails | 2 | 300 | 25 |
| Spirits' Flamebulb | 2 | 250 | 90 | Blaze Bulb (S) | 5 | 260 | 90 |
| Spirits' Frostfluff | 11 | 65 | 30 | Snowtuft (M) | 13 | 40 | 30 |
| Spirits' Storm Pinion | 4 | 70 | 0 | Stormbird Pinion (M) | 14 | 65 | 0 |
| Spirits' Storm Ward | 6 | 0 | 60 | Lightning Amulet | 5 | 0 | 50 |
| Spirits' Halebloom | 2 | 100 | 15 | Healing Bloom (M) | 5 | 150 | 13 |
| Spirits' Falconfeather | 10 | 0 | 15 | Falcon Feather (M) | 5 | 0 | 70 |
| Spirits' Gravelshield | 15 | 0 | 15 | Gravelshield Fragment | 10 | 0 | 30 |

A few smaller differences in the tables behind them:

* the fang arms' punch knocks back much harder (7 against 0.7);
* the Heart's golem has one parameter far lower (500 against 7000);
* Halebloom's healing area is a little smaller (radius 5 against 5.5);
* the swords and giant arms take the weapon model of the next level up
  (Devil Pitchfork, Sword Hero Icebrand ...).

Delta later gave some of its own offerings extra effects (Falcon Feather,
the root spells, Snowtuft, Leafdrake Egg), which the Spirits' copies
don't have.

What ss-delta changes when it switches them on, so they work like Delta's
own:

* the two fang arms named a punch effect Delta removed; it is left out,
  as on Delta's own fang arms, and their punch does the arm's damage
  (before the fix, a thrust that hit crashed the game: issue #18);
* the effect rows below each Spirits' row that Delta left uncommented
  (an arrow's four arrows, a sword's further effects) are taken along
  (before the fix, the two Spirits' arrows had no arrows: issue #19);
* the giant arms and fang arms get Delta's falcon-combo values from the
  arm with the same model, as the Spirits' swords already have them;
* Spirits' Falconfeather gets the original's names back in English,
  French, German, Italian, Spanish and Brazilian Portuguese.

Tested in the port: all 20 listed with their names and icons; Spirits'
Flamepike (the flaming pitchfork), Wolf fang (the ice arm, its thrust and
frost breath) and Heart (the stone golem) cast in a try-out; kept through
a save and reload without being given twice.

## The collaboration raiments

The original's update 1.30 had three collaboration raiments, each a
single whole-body costume:

* **Mononofu** (*Toukiden*): in Delta too, remade as a raiment with a top
  and a bottom.
* **ARKS Armor** (*Phantasy Star Online 2*, Japan only in the original)
  and **Dragonslayer**, also called Ace of Souls (*Ragnarok Odyssey
  ACE*): not in Delta. Delta keeps their names and part of their files,
  but not their models and textures.

**In ss-delta** they come as a mod you make yourself from your own copy of
the original game (update 1.30, any region) with `tools/og-raiments.py`.
The models exist only in the original, so ss-delta can't include them.
The mod adds both raiments; ss-delta gives them with Add-ons (DLC) on.
Wear each one as both top and bottom.

* Screenshots: [gallery](GALLERY.md#from-the-original-game-mod)
* How to make it: [INSTALLING](INSTALLING.md#what-you-need)
* The decision: [D28](decisions.md)

## Changed in Delta: Sanguine Shot

The original's right arm fired **Sanguine Shot**, with Godly and Diabolic
forms. Delta replaced it with Sanguine Cannon, Angelshot and Demonshot.
That is a change to how the game plays, not missing content, and ss-delta
leaves it as Delta has it.

## Already in Delta

Most of what looked missing at first is in Delta under a new name or id:

* **Renamed:** 51 offerings, 57 sigils, 8 souls and 154 characters keep
  their ids with new English names, for example Iron Pinwheel → Iron
  Mill, Fire Giant's Arm → Firegiant's Arm, Effulgent Sigil → Gleaming
  Sigil, Iron Maiden → Iron Virgin, Great Sorcerer → Great Seer.
* **Black Rites:** all 14, including the DLC rite Black Rite Angelus (the
  Sanctuarium faction's rite in Delta).
* **Quests:** every quest and DLC quest of the original. The 16 quest ids
  only the original has are empty: placeholder rows ("@No Data") and
  empty copies of two chapters Delta has under other ids. Delta lists
  them only to read saves imported from the original.
* **Appearance:** every face, hairstyle, arm and low-chaos body model of
  the original is in Delta's tables; of the whole-body models only the
  three collaboration raiments' aren't.

## How this was checked

We compared the original's EU release with update 1.30 against Delta 1.30
(US): the game's data tables (offerings, skills and their effects,
raiments and their parts, sigils, souls, characters, Black Rites, quests),
matched by name and then by id, and the raiment model files. Each Spirits'
offering was traced through every table it uses and compared, row by row,
with the closest offering Delta has. Maps, music, story text and videos
were not compared.

The details, with table names and addresses, are in
[01-research](01-research.md) ("What only the original has", "The
original's collaboration raiments", "The offering stock"). Nothing from
either game is in this repository; the comparison was made on our own
copies.
