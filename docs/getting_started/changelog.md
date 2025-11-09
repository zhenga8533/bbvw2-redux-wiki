# Changelog

!!! info "About Updates"
    Redux is periodically updated to fix issues and keep the game fresh. This changelog documents all changes since the initial release.

!!! question "Found a Bug?"
    If you find any issues with Redux, report them to [@AphexCubed](https://twitter.com/AphexCubed) on Twitter.

---

## Version 1.4.1
**Released: June 24, 2023**

### Balance Changes

- **Walrein line**
    - Spheal now evolves into Sealeo at level 16
- Nerfed Normal mode Burgh's Masquerain

### Bug Fixes

- Eevee now evolves into Glaceon correctly
- Snorunt now evolves into Glalie correctly

### Other

- All Hall of Fame screens show the project's version number

---

## Version 1.4.0
**Released: May 24, 2023**

### Major Changes

!!! warning "Challenge Mode Difficulty Rework"
    Challenge mode has been significantly reworked to be easier in the early game, with a scaling difficulty progression that increases over time. Mid-to-late game difficulty remains untouched.

### Balance Changes

**Trainer Nerfs:**

- **Ranch Grunt** - Reduced spread move usage and weaker moves overall
- **Cheren** - Doduo and Deerling slightly weakened
- **Roxie** - Removed Explosion on Qwilfish, adjusted movesets
- **Brycen** - Swapped Delibird for weaker Cryogonal, reduced Smoochum's move BP
- **Sewer Grunts** - Dramatically lowered move BP
- **Burgh** - Multiple team changes (Yanmega→Mothim, Scyther→Escavalier, Durant→Heracross)
- **Virbank Grunts** - Nerfed Beedrill's coverage

**Note:** Hoenn leaders remain untouched due to their optional nature. See Trainer Changes document for complete details.

### Pokémon Buffs

??? note "Pokémon Receiving Buffs (Click to expand)"
    - **Venusaur line** - Learns Charm at level 16
    - **Eevee family** - Complete learnset overhaul with early elemental moves
    - **Victreebel line** - Clear Smog at 12, Knock Off at 30/33
    - **Aerodactyl** - Dual Wingbeat at 45
    - **Typhlosion line** - Flame Burst at 22
    - **Crobat** - Dual Wingbeat at level 1
    - **Delibird** - Drill Peck at 32
    - **Blaziken line** - U-turn at 25
    - **Breloom** - Shroomish evolves at 21, new learnset
    - **Sharpedo line** - Carvanha evolves at 26
    - **Torterra line** - Sandstorm and Sunny Day at level 1
    - **Infernape line** - Cross Chop at 37, Focus Punch at level 1
    - **Staraptor line** - Retaliate at 26, Sky Uppercut at 34
    - **Cherrim** - Cherubi evolves at 18, new learnset
    - **Serperior line** - Glare at 22, Heart Stamp at 31, Psycho Cut at 50
    - **Emboar line** - Slack Off at 34
    - **Vanilluxe line** - Hail at level 1

### Pokémon Nerfs

- **Meganium line** - Ingrain at 17 instead of screens (still available via TM)
- **Medicham** - New Complete version stats: 60/65/80/75/80/90 (450 BST), swapped Reversal and Drain Punch levels

### Bug Fixes

- Corrected Thunderbolt TM location
- Fixed Starly and Staravia learnsets
- Corrected evolution information in documentation

---

## Version 1.3.0
**Released: January 21, 2023**

### New Features

- **Moonblast** has a new animation matching official games (Thanks @GoranConstant1!)

### Balance Changes

??? note "Pokémon Changes (Click to expand)"
    **Buffs:**

    - **Wigglytuff line** - Nasty Plot at 70
    - **Dugtrio line** - Swords Dance at 62
    - **Poliwrath line** - Waterfall at 15 (Poliwhirl), level 1 (Poliwrath)
    - **Muk line** - Toxic Spikes at level 1
    - **Hypno line** - Recover instead of Drain Punch at 48/58
    - **Quagsire line** - Spikes instead of Ancient Power, Toxic Spikes at level 1
    - **Gastrodon line** - Spikes instead of Amnesia at 40/45
    - **Garchomp line** - Spikes at 72
    - **Samurott line** - Drill Run instead of Retaliate, Sucker Punch instead of Assurance
    - **Eelektross line** - Close Combat at 70
    - **Hydreigon line** - Stealth Rock at level 1

    **Trainer Changes:**

    - Replaced Burgh's Scyther with Larvesta on Normal mode

### Bug Fixes

- Juan no longer has Wingull on Challenge mode
- Tate and Liza have correct Pokémon on Challenge mode
- Eevee and Snorunt evolution fixes
- Benga uses correct team per difficulty
- Wave Crash deals correct damage
- Various trainer updates for Wave Crash changes

### Other

- Updated dark title cards

### Outstanding Issues

- Infestation doesn't display text when target is hurt between turns
- Postgame remains untouched from v1.1.1

---

## Version 1.2.1
**Released: August 24, 2022**

### Critical Bug Fixes

!!! danger "Important Fixes"
    - **Fixed catastrophic memory issue** causing crashes on real hardware and MelonDS (Fairy type related)
    - **Fixed 20+ evolution methods** that were reverted to vanilla (Riolu, Ponyta, etc.)

### Other Fixes

- Fixed Wii Cheat Menu typo
- Corrected move effects on White 2 version
- Fixed Cheren's Normal mode levels in documentation
- Swapped Medicham's Zen Headbutt and Psycho Cut levels
- Fixed Vanilluxe TM documentation
- Removed duplicate Shiftry text
- Ranch Grunt levels corrected
- Egg hatching speed fixes (Meditite, Bonsly, Mime Jr., Glameow, Stunky)
- Fixed Spheal appearing in Castelia Battle Company Egg
- Juan's item documentation corrected
- Minor AI tweaks

---

## Version 1.2.0
**Released: August 20, 2022**

### Major New Features

!!! success "Cheat Code System"
    Interact with the Wii in your house to access cheat codes:

    **Item Codes:**

    - Add Rare Candies
    - Add Money
    - Add Master Balls
    - Add Berries
    - Add Shiny Charm
    - Add Oval Charm
    - Add Max Repels
    - Add Medicine Items
    - Add Battle Items
    - Add Sacred Ash
    - Add Gems
    - Recollect Gift Pokémon

    **Skull Challenges (Sci-Fi inspired):**

    - **Foreign** - Blocks gift Pokémon
    - **Recession** - Hides all Market Clerks and Vendors
    - **Illiterate** - Hides all Move Tutors and Reminders

### Trainer Overhaul

- **Complete trainer documentation** up to Postgame
- Almost all trainers have new/adjusted movesets and AI
- Massive fundamental overhaul (too extensive to list completely)
- Special thanks to gippal#3903 for documentation framework

### Hoenn Leaders Rework

**New Battle Structure:**

- Separate Easy and Normal/Challenge teams (instead of Main Game/Postgame)
- Infinitely re-battleable until next Unova leader defeated
- New rewards per leader:

| Leader | Normal Mode | Challenge Mode |
|--------|-------------|----------------|
| Roxanne | 2x Berry Juice | 2x Berry Juice |
| Brawly | Meditite Egg | Meditite Egg |
| Wattson | 2x Tanga Berry | 2x Tanga Berry |
| Flannery | Choice Band | 12x Cheri Berry |
| Norman | Choice Specs | 5x Sitrus + 2x Micle Berry |
| Juan | Choice Scarf | Air Balloon |
| Winona | Old Amber | Rotom encounter |
| Tate & Liza | Protect TM | Protect TM |

### Quality of Life

!!! tip "HM Improvements"
    HM moves can now be forgotten on the fly without the Move Deleter! (Thanks totally_anonymous#0405!)

### Balance Changes

**New Features:**

- New Castelia Battle Company Egg gift (Bonsly, Mime Jr., Glameow, or Stunky)
- Swords of Justice all encountered at level 80
- Victini's Guardian changes (no longer challengeable after Burgh)
- Castelia Gardens split into separate met location
- Eviolite gift requirement increased (160 seen + Battle Company cleared)
- Bianca heals player before Reversal Mountain battle

**Challenge Mode Adjustments:**

- Air Balloon NPC postgame-only
- Grip Claw and Light Clay replaced with Power Herb
- Multiple TM location swaps
- Gems removed from cave Dust Clouds
- Various berry/item availability changes
- Entralink Missions blocked until Clay
- Join Avenue vendors blocked
- Player team healed before Gym fights and Pokémon League

### Move Changes

- Reverted Attack Order stats to vanilla
- Razor Shell accuracy: 95 → 100
- Leaf Tornado accuracy: 95 → 100
- Psyshield Bash now raises both Defense and Sp. Def
- Poison Tail BP: 90 → 80
- Fly BP: 100 → 80
- Poison Gas accuracy: 80 → 100
- Stun Spore accuracy: 75 → 90
- Needle Arm and Rock Smash boosted by Iron Fist
- Kinesis targets both opponents in doubles
- Psycho Cut BP: 70 → 90, PP: 15 → 10
- Improved AI move selection logic

### Extensive Pokémon Changes

??? note "Pokémon Buffs (Click to expand - extensive list)"
    The v1.2.0 update included massive changes to over 60 Pokémon evolution lines. Notable changes include:

    - **Charizard line** - Defiant ability instead of Levitate
    - **Mr. Mime line** - Mime Jr. evolves at 25, complete learnset revamp
    - **Bonsly line** - Evolves at 25, offensive-focused learnset
    - **Smeargle** - Learns all TMs and HMs without Sketch
    - **Multiple evolution level changes** for better curve fitting
    - **Extensive learnset overhauls** for early-game viability
    - **New type combinations and abilities** (Complete version)

    See full documentation for complete details.

### Wild Encounter Changes

- Aspertia/Route 19: Surskit when fishing (not Poliwag)
- Route 20: Dratini year-round (not seasonal Shellder)
- Castelia Sewers: Increased Stunfisk fishing odds
- Lostlorn Forest: Psyduck instead of Seaking line
- Route 6: Aron in Hidden Grotto (not Woobat)

### Bug Fixes

Over 20 critical bugs fixed including evolution methods, move effects, trainer AI, TM compatibility, and various crashes on hardware/MelonDS.

### Outstanding Issues

- Postgame left out of v1.2.0 for faster release
    - Duplicate TMs in postgame
    - Deoxys event doesn't work (appears after Nacrene City as workaround)
    - Some Cut trees remain
    - Wallace and Steven not updated to new Hoenn Leader standard
- Wave Crash incorrect damage (Base 60 instead of intended)
- Infestation text issue

---

## Version 1.1.1
**Released: May 22, 2022**

### Balance Changes

- Aron now found in Relic Passage, Castelia side (for @pponli)

### Bug Fixes

- Castelia grass rates finally fixed (raised, not lowered)
- Unity Tower crash fixed (hardware/MelonDS)
- Weavile no longer has Technician, regained Triple Axel
- Multiple BST corrections (Fearow, Noctowl, Farfetch'd, Vanillite line)
- Pledge moves BP corrected
- Staravia Intimidate documented
- Arceus infinite summon fixed
- Nature Preserve crash fixed
- Multiple move tutor/TM compatibility fixes
- Numerous ability and stat corrections
- Link Cable now functions correctly

### Documentation

- Xatu vanilla BST corrected
- Dual Chop and Dual Wingbeat documented
- Item Changes document updated for TM shifts
- All documents updated to v1.1.1

---

## Version 1.1.0
**Released: May 20, 2022**

### New Features

!!! success "Major Additions"
    - **New boss fight music!** (Thanks Drayano!)
    - **Hidden Grottos spawn new Pokémon every entry** with overhauled tables
    - **Increased frequency** for shaking grass/water/sand
    - **Gift Eevee** available pre-postgame (Easy/Normal)
    - **Postgame Unovan starters** as gifts with reset functionality
    - **All Shiny-locks removed**

### Balance Changes

**Clay Fight:**

- Added permanent Sandstorm on Challenge Mode (like Crasher Wake in Renegade Platinum)

**Item Changes:**

- Choice items now guard Blizzard, Fire Blast, and Thunder TMs
- All three Choice Items available in Postgame
- TM vendor removed
- Multiple TM location swaps
- Gems removed from cave Dust Clouds
- New berry vendors in various cities

**Challenge Mode:**

- Entralink Missions only after Clay
- Join Avenue vendors blocked
- Team healed before Gym fights and Pokémon League

**Trainer Updates:**

- Redid Chargestone Cave trainers
- Redid Route 7 trainers
- Redid Abundant Shrine trainers
- Shuffled Skyla's Gym (majority mandatory, two avoidable)

**Move Changes:**

- Nerfed: Blaze Kick, Brutal Swing, Dual Chop, Dual Wingbeat, Strength
- Buffed: Raging Fury

### Extensive Pokémon Changes

??? note "Pokémon Receiving Changes"
    **Buffs:** Venomoth line, Jumpluff line, Girafarig, Magcargo line, Shiftry line, Plusle, Minun, Sharpedo line, Camerupt line, Cacturne line, Tropius, Relicanth, Rampardos line, Electivire line, Magmortar line, Mamoswine line, Gallade, Probopass line, Serperior line, Emboar line, Liepard line, Unfezant line, Leavanny line, Sawk, Basculin, Vanilluxe line

    **Nerfs:** Venusaur line, Fearow line, Rapidash line, Farfetch'd, Marowak line, Jynx line, Typhlosion line, Furret line, Sceptile line, Gardevoir, Medicham line, Infernape line, Staraptor line, Lopunny line, Mismagius line, Weavile line, Archeops line, Zoroark line

    **Reworks:** Charizard line, Blastoise line, Primeape line, Poliwrath line, Cloyster line, Kabutops line, Ledian line, Ursaring line, Mightyena line, Lucario line, Samurott line, Simisage line, Simisear line, Simipour line, Zebstrika line, Gigalith line, Ferrothorn line, Eelektross line, Beartic line, Cobalion, Terrakion, Virizion

### Trainer Changes

Important trainers updated across all modes (Cheren, Roxanne, Roxie, Brycen, Elesa, Rood, Norman, Clay, Skyla, Drayden, Marlon, Colress, Weather Trainers, Grimsley, Caitlin, TM Protectors, Hoenn leaders)

### Wild Encounter Changes

Multiple routes and areas updated (Route 20, Virbank Complex, Route 4, Relic Passage, Desert Resort, Route 5, Route 16, Lostlorn Grotto, Driftveil Drawbridge, Clay Tunnel, Chargestone Cave, Mistralton Cave, Celestial Tower, Reversal Mountain, Undella Town, Abundant Shrine, Seaside Cave, Route 9, Giant Chasm, Victory Road)

### Bug Fixes

20+ bugs fixed including crashes, evolution issues, ability corrections, TM compatibility, and various text errors.

---

## Version 1.0.2
**Released: April 2, 2022**

!!! warning "Save Compatibility"
    Somewhat compatible with older saves. Patch a vanilla ROM and name it the same as your old file. You may need to redo E4 meetings on: Driftveil Drawbridge, Twist Mountain (Route 7), Undella Town, and Opelucid Gate.

    **Route 7 event incompatibility:** If you've completed Route 7 event but not others, save is incompatible - restart required.

    Old saves will see Deoxys erroneously in Giant Chasm - ignore him!

### Balance Changes

- Seismitoad now learns Waterfall (by request)
- Raised Castelia City grass encounter rates

### Bug Fixes

Over 50 bugs fixed including:

- Critical game crashes on hardware/MelonDS (multiple locations)
- Evolution level fixes (Mienfoo, Larvesta, Psyduck, Vanillite, Gligar)
- AI fixes (Lenora, Hugh, Colress)
- Move compatibility and learnset corrections
- Pokédex crash on Volt White 2
- Deoxys early appearance
- Ledian Fly compatibility
- Multiple text and dialogue fixes
- Encounter table corrections

---

## Version 1.0.1
**Released: March 27, 2022**

**Day one patch of Redux**

!!! tip "Save Compatible"
    Patch a vanilla ROM with the same name as your old file to carry over your save.

### Balance Changes

- Ranch Egg gift: Eggs don't hatch instantly (player agency on hatch location)
- Kricketune: Swapped Bug Buzz and Fury Cutter (less reset frustration)
- Butterfree/Beedrill: Early moves not locked to Move Relearner
- Jigglypuff: Huge Power pushed to Wigglytuff evolution, learnset pacing improved
- Charmeleon: Removed Dragon typing
- Blitzle: Swapped Spark and Screech levels
- Route 5: Swapped Pikachu and Pachirisu
- Litwick: Swapped Clear Smog for Haze
- Cheren's Aipom: Tail Slap→Double Hit, Technician→Skill Link (better AI, less unfair)
- Ranch shaking grass: Reduced guaranteed Happiny/Togepi odds
- Cubchoo: Shuffled moves for peer balance
- Pansage: Swapped Acrobatics for consistency
- Cubone: Removed Double Kick for peer balance

### Bug Fixes

- Ranch Egg gift: Fixed incorrect Pokémon distribution
- Roxie: No longer calls player "Testing"
- Route 20: Fixed trainer positioning
- Pokéstar Studios: Moved after Elesa to prevent Virbank grunt crash
- Wave Crash: Fixed disappearing Pokémon animation
- Multiple move fixes (Disarming Voice, Bullet Seed→Punch, Lava Plume→Flame Burst, etc.)
- Evolution and ability corrections
- Present and Psychic Fangs functionality
- Start-up screen fix (Blaze Black 2)
- Unovan starters: Removed Gender and Shiny locks

### Documentation

- Added Gift Pokémon document entries
- Added Important NPCs document entries (EV/Level trainers, Audino trainer)
- Noted Elemental Monkeys growth rate change
- Added Infestation bug to Known Bugs
- Updated Hardware Information
- Added Evolution Changes document
- Fixed Humilau City documentation
- All documents updated to v1.0.1

### Other

- Added version indicator to Hall of Fame

---

## Version 1.0.0
**Released: March 26, 2022**

!!! success "Launch Version"
    Initial release of Blaze Black 2 & Volt White 2 Redux!

Various changes and corrections to documents based on public feedback.
