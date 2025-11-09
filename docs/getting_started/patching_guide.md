# Patching Guide

This guide will walk you through patching a clean Pokémon Black 2 or White 2 ROM to create Redux.

## Prerequisites

!!! warning "Important File Requirements"
    - You need a **clean Black 2 or White 2 ROM** (American/European version)
    - ROM must be in `.nds` format (may be in `.zip` or `.7z` archive)
    - ROM should be **524,288 KB** in size when extracted
    - **Never use `.exe` files** - these are not legitimate ROM files

!!! info "Obtaining the Patch"
    Download the Redux patch from [Drayano's Twitter](https://twitter.com/Drayano60), which links to his Google Drive.

---

## Step 1: Obtain the Base ROM

1. Obtain a clean **Pokémon Black 2** or **White 2** ROM
   - Ideally from a dump of your personal cartridge
2. Ensure the file is `.nds` format or contained in a `.zip`/`.7z` archive
3. Extract the ROM if it's in an archive

---

## Step 2: Choose a Patching Tool

Select the appropriate patching tool for your platform:

=== "Windows"

    **xdeltaUI** (Recommended)

    - Included in the Redux download ZIP file
    - Simple graphical interface
    - Continue to Step 3 below

=== "Mac"

    **MultiPatch**

    - Search online for MultiPatch tool
    - Similar functionality to xdeltaUI
    - Follow similar steps to Windows instructions

=== "Android"

    **UniPatcher**

    - Available on Google Play Store
    - Free and easy to use

=== "Web-based (Any Device)"

    **ROM Patcher JS**

    - Visit [https://www.marcrobledo.com/RomPatcher.js/](https://www.marcrobledo.com/RomPatcher.js/)
    - Works on any device with a web browser
    - No installation required

---

## Step 3: Apply the Patch (Windows - xdeltaUI)

!!! tip "Step-by-Step Instructions"

    **3.1 - Select the Patch File**

    1. Open `xdeltaUI.exe`
    2. Go to the **Apply Patch** tab
    3. Click **Open** next to the **Patch:** field
    4. Select your Redux `.xdelta` patch file
        - Should be `.xdelta` format (not `.zip`, `.7z`, or `.exe`)

    **3.2 - Select the Source ROM**

    1. Click **Open** next to the **Source File:** field
    2. Select your clean `.nds` Black 2 or White 2 ROM
        - Must be extracted `.nds` file (524,288 KB)

    **3.3 - Choose Output Location**

    1. Click **...** next to the **Output File:** field
    2. Choose where to save the patched ROM
    3. Name it appropriately:
        - `Pokémon Blaze Black 2 Redux.nds`
        - `Pokémon Volt White 2 Redux.nds`
    4. **Important:** Include `.nds` extension in the filename
    5. Click **Save**

    **3.4 - Patch the ROM**

    1. Click **Patch** to begin the process
    2. Wait for completion
    3. You now have a playable Redux ROM!

---

## Step 4: Apply Optional Patches (Classic/EV-Less)

!!! example "Optional Patch Types"
    - **Classic Version** - Omits custom type combinations, abilities, and stat boosts
    - **EV-Less Version** - Modified difficulty scaling

To apply optional patches:

1. **Repeat Steps 3.1-3.4** with the following changes:
   - **Patch:** Select the optional patch (Classic or EV-Less `.xdelta`)
   - **Source File:** Select your **already-patched** Redux ROM from Step 3
        - Use `Pokémon Blaze Black 2 Redux.nds` or `Pokémon Volt White 2 Redux.nds`
   - **Output File:** Give it a new name (e.g., `BB2 Redux Classic.nds`)

2. These optional patches are included in the download from Drayano's Google Drive

---

## Step 5: Play the Game

Now you can play Redux using a DS emulator!

### Recommended Emulators

=== "PC"

    **DeSmuME**

    - Popular and stable
    - **Performance Tips:**
        - Turn **OFF**: Advanced Bus-Level Timing
        - Turn **ON**: Use Dynamic Recompiler
        - Found in: Emulation Settings → Emulator Options

    **MelonDS**

    - Modern alternative
    - Generally faster than DeSmuME

=== "Android"

    **DraStic** (Paid)

    - Best performance and compatibility
    - Small one-time fee

    **Free Alternatives:**

    - MelonDS for Android
    - Free DS emulator

=== "iOS"

    **iNDS**

    - Free DS emulator for iOS devices

=== "Other Options"

    **Hardware Options:**

    - Flashcards
    - 3DS with custom firmware
    - See the [Hardware Information](hardware_info.md) guide for compatibility details

---

## Troubleshooting

!!! danger "Common Issues"

    **Patch fails to apply**

    - Ensure ROM is exactly 524,288 KB
    - Verify ROM is clean (not pre-patched)
    - Check that you're not using the original BB2/VW2 ROM

    **Game won't load**

    - Verify the output file has `.nds` extension
    - Check [Hardware Information](hardware_info.md) for compatibility
    - Some flashcards/hardware may not support Fairy Type implementation

    **White screen on launch**

    - If using TWiLight Menu++, ensure you launch in **DS mode**

---

!!! success "Ready to Play!"
    Once patching is complete, you're ready to start your Redux adventure! Check out the [FAQ](faq.md) if you have any questions.
