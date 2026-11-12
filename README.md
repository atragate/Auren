# Auren

**A customizable, white-label rEFInd boot manager theme.**

Auren gives an existing [rEFInd](https://www.rodsbooks.com/refind/) menu a dark, gaming-inspired appearance with custom OS icons, orange selection borders, a background image, and matching utility icons. rEFInd is the EFI boot manager that finds and launches operating systems; Auren changes how its menu looks.

Use Auren to personalize a Linux and Windows dual-boot menu or adapt a custom boot screen to your own branding. Colors, backgrounds, logos, and icons are editable. The included Gigabyte-branded artwork is one example configuration, not Auren's identity or a required hardware brand. Auren is a theme with supporting Linux tools, not a replacement boot manager or firmware.

## Visual preview

![Generated preview of the Auren rEFInd theme with example Gigabyte branding, Bazzite and Windows icons, and four orange utility icons](preview.png)

This is a **generated 1920×1080 preview**, not a photograph or screenshot captured from firmware. It uses the exported theme assets and rEFInd's menu layout formulas. Live text, available utilities, and display modes can differ. No firmware screenshot or additional branding preset is currently tracked in the repository.

[Installation](#installation) · [Customization](#customization) · [Restore the previous theme](#restore-the-previous-theme) · [Troubleshooting](#troubleshooting) · [FAQ](#faq)

## Features

- Editable SVG sources for Bazzite and Windows boot icons, selection indicators, and utility icons.
- PNG backgrounds and a full-screen background configuration.
- A configurable accent color, OS icon size, utility icon size, and label visibility.
- Reboot, Shutdown, Firmware Settings, and About icons with distinct designs.
- A local preview and a small command-line menu for customization and installation.
- Theme installation with asset-hash checks and one restore point.
- Checks that loader paths, volume selections, timeout, default selection, EFI executables, and firmware boot order are preserved during installation.

Auren uses native rEFInd settings: `banner`, `banner_scale`, `icons_dir`, `selection_big`, `selection_small`, `big_icon_size`, `small_icon_size`, `font`, `resolution`, `showtools`, `hideui`, and `use_graphics_for`. The generated configuration enables graphics handoff for all five recognized loader categories: `osx,linux,elilo,grub,windows`. The installer also sets `graphics on` in manual OS entries and their subentries, covering Shim and other loaders without depending on a distribution name. This suppresses rEFInd's normal text-mode launch information. See the upstream [configuration reference](https://www.rodsbooks.com/refind/configfile.html) and [theming guide](https://www.rodsbooks.com/refind/themes.html).

### Scope and limitations

The layout follows rEFInd's centered OS and utility rows. There are no animations, dynamic panels, arbitrary widget positions, or supported `menu_offset_y` setting in the bundled 0.14.2 source. The font is a bitmap ASCII atlas, not a system font picker.

The supplied icons cover Bazzite, Windows, and four utilities. Auren does not discover operating systems, create boot entries, repair dual-boot configurations, or provide an icon pack for every Linux distribution. Other entries may use rEFInd's fallback icons.

The reference configuration was developed around rEFInd 0.14.2. There is no published compatibility matrix or verified minimum rEFInd version. The installation helper is Linux-specific and currently assumes `/boot/efi/EFI/refind`; Windows and macOS installation helpers are not provided.

## Requirements

| Requirement | Used for |
|---|---|
| Existing, working rEFInd installation | Displaying the theme and launching your existing OS entries |
| EFI System Partition mounted at `/boot/efi`, with a FAT filesystem | The installer's expected destination |
| `/boot/efi/EFI/refind/refind.conf` | The main configuration the installer updates |
| Linux, Bash, and Python 3 | Running the launcher and helper |
| Pillow with `Image.Resampling` support, available since 9.1.0 | Resizing assets and composing the preview |
| ImageMagick providing the `magick` command and SVG rendering | Exporting SVG artwork to PNG |
| `pkexec`, an available authentication agent, and administrator privileges | Installing or restoring theme files |
| `findmnt` and `efibootmgr` | Checking the installation path and boot state |
| `xdg-open` and a graphical session | Opening the preview automatically |

Install dependencies using your Linux distribution's package manager. The current [requirements file](requirements.txt) says `Pillow>=9`, but the code uses [`Image.Resampling`, introduced in Pillow 9.1.0](https://pillow.readthedocs.io/en/stable/releasenotes/9.1.0.html). Use a version that exposes that API.

Pillow is needed by the Python interpreter running the local preview/build, which can be a virtual environment. Check that interpreter:

```bash
python3 -c 'from PIL import Image; print(Image.Resampling.LANCZOS)'
```

The authenticated file-copy step runs `/usr/bin/python3` and uses the standard library; it does not need Pillow in that interpreter. If using a virtual environment, keep it activated when running `start.sh` so the local build uses it.

SVG files are editable sources; the build exports PNG files for rEFInd. For custom wallpapers, PNG and JPEG are practical choices that Pillow can read. Transparent PNGs are used for icons and selection frames. See [rEFInd's image format limitations](https://www.rodsbooks.com/refind/themes.html) before substituting other formats.

## Installation

### 1. Get Auren and check dependencies

```bash
git clone https://github.com/atragate/Auren.git
cd Auren
bash start.sh doctor
```

`doctor` checks settings and the presence of several dependencies. It does not validate firmware compatibility, every dependency version, or the destination configuration. You can also run `bash start.sh` for the interactive menu.

### 2. Confirm the existing rEFInd location

These commands inspect the system without changing the EFI partition:

```bash
findmnt --target /boot/efi
sudo test -f /boot/efi/EFI/refind/refind.conf
sudo grep -nE '^[[:space:]]*(include|menuentry|scanfor|icons_dir|showtools)' /boot/efi/EFI/refind/refind.conf
```

Verify that this is the configuration used by the rEFInd entry you actually boot. The helper does not search for alternate rEFInd directories. If your installation uses another path, stop here and consult the [upstream configuration documentation](https://www.rodsbooks.com/refind/configfile.html); the helper has no destination-path option.

If the main config has more than one active theme include, review those includes first. The installer rejects multiple matching `include themes/...conf` lines rather than choosing between them.

### 3. Build and review the preview

```bash
bash start.sh build
```

This writes `build/` and updates `preview.png` in your checkout. It does not change the EFI partition. Open `preview.png` yourself, or use:

```bash
bash start.sh preview
```

The generated rEFInd configuration is `build/theme.conf`. Review it before installation. Its paths intentionally point to `themes/auren/` in the rEFInd installation.

### 4. Save an independent backup

The installer keeps one restore point, which is replaced on each installation. For a separate copy of the existing rEFInd directory, run:

```bash
auren_backup="$HOME/auren-refind-$(date +%Y%m%d-%H%M%S).tar"
sudo tar -C /boot/efi/EFI -cpf "$auren_backup" refind
```

This reads the EFI partition and writes an archive to your home directory. Keep that archive outside the theme checkout. It is separate from the helper's single restore point.

### 5. Install and activate the theme

**The following command writes to the EFI System Partition and updates the main `refind.conf`.** It also replaces the helper's previous restore point.

```bash
bash start.sh install
```

Authenticate through `pkexec` when prompted. The helper rebuilds the theme, checks asset hashes, and then:

1. Saves the current main config and any existing `themes/auren/` assets to `/var/lib/auren-refind/last-install`.
2. Copies the generated PNGs and theme configuration into `/boot/efi/EFI/refind/themes/auren/`.
3. Replaces the matching theme include, or adds this activation line if none exists:

   ```text
   include themes/auren/theme.conf
   ```

4. Updates explicit icon paths ending in `os_bazzite.png` or `os_win.png` to the installed Auren icons, and sets `graphics on` in manual OS entries and subentries. This overrides an existing `graphics off` display setting without changing the loader or OS selection.
5. Verifies the installed assets and checks that EFI executable hashes and firmware boot order have not changed.

Activation is part of the command; you do not need to add a second include manually. The helper preserves loader paths, volume selections, scan settings, timeout, and default selection. It does not install the developer reference executable or change Secure Boot settings.

### 6. Verify the installation

Inspect the installed files:

```bash
sudo grep -n 'themes/auren' /boot/efi/EFI/refind/refind.conf
sudo cat /boot/efi/EFI/refind/themes/auren/theme.conf
```

Restart when ready and select each existing OS entry. Check the icons, selected-item description, and utility row on your actual display. A generated preview cannot verify that firmware supports the requested resolution or that an OS loader works.

`bash start.sh status` reports the optional integrity guard's status if that guard is already installed. It does not verify that Auren is the active theme.

## Restore the previous theme

To undo the most recent installation made by this helper:

```bash
bash start.sh restore
```

Authenticate when prompted. Restore puts back the saved main config and the previous `themes/auren/` assets if they existed. It refuses to overwrite a main config changed since that installation. Only one restore point is retained; another install replaces it.

If Auren did not exist before installation, restoring the old config can leave the new theme directory on disk but inactive. Restore is a theme rollback, not an uninstaller for rEFInd. Do not remove the underlying boot manager to remove a theme.

## Customization

[theme.json](theme.json) controls the build. Edit it directly or use the command-line options, then preview and install again.

```bash
bash start.sh customize --accent '#FF7900' --os-size 144 --utility-size 64
bash start.sh customize --resolution 1920x1080 --labels on
bash start.sh preview
```

`customize` saves settings and rebuilds local files. It does not install them.

| Setting | Default | Behavior |
|---|---|---|
| `accent` | `#FF7900` | Replaces that orange color in exported selection and utility SVGs |
| `resolution` | `[1920, 1080]` | Sets the preview canvas and requested firmware display mode; no automatic resolution detection |
| `os_icon_size` | `144` | OS image size; accepted range 96–256px |
| `utility_icon_size` | `64` | Utility image size; accepted range 32–96px |
| `show_labels` | `true` | Shows the selected description and countdown; `false` hides both |
| `background` | `assets/background.png` | Wallpaper file; relative paths resolve from the project directory |
| `render_background_svg` | `false` | When `true`, renders `sources/background.svg` instead of using `background` |
| `utilities` | `reboot`, `shutdown`, `firmware`, `about` | A non-empty list of unique actions in the order displayed |
| `preview_description` | Bazzite example text | Changes the local preview label only; does not rename a boot entry |
| `name` | `Auren` | Descriptive metadata; does not change branding or boot labels |

### Background and branding

For a custom wallpaper, add a file to the project and set its path in `theme.json`, or select an existing file with:

```bash
bash start.sh customize --background "$HOME/Pictures/wallpaper.png"
```

That command records an absolute path and disables SVG background rendering. Images with a different aspect ratio are resized and center-cropped. Use a project-relative path in `theme.json` if you plan to share the customization.

To edit the supplied geometric background or replace its logo, edit [sources/background.svg](sources/background.svg) and set:

```json
{
  "render_background_svg": true
}
```

This is a setting to merge into the existing JSON object, not a replacement for the complete file. The Gigabyte wordmark is embedded in that SVG; replacing `sources/gigabyte-white-official.png` alone will not update it. Replace the embedded image or supply a new background. Changing `accent` recolors the background's orange geometry only when SVG rendering is enabled.

### OS icons, utility icons, and selection borders

Edit these sources and rebuild:

| Source | Purpose |
|---|---|
| [sources/os_bazzite.svg](sources/os_bazzite.svg) | Bazzite boot icon |
| [sources/os_win.svg](sources/os_win.svg) | Windows boot icon |
| [sources/func_reset.svg](sources/func_reset.svg) | Reboot |
| [sources/func_shutdown.svg](sources/func_shutdown.svg) | Shutdown |
| [sources/func_firmware.svg](sources/func_firmware.svg) | Firmware Settings |
| [sources/func_about.svg](sources/func_about.svg) | About rEFInd |
| [sources/selection_big.svg](sources/selection_big.svg) | OS selection border, 144×144 source canvas |
| [sources/selection_small.svg](sources/selection_small.svg) | Utility selection border, 64×64 source canvas |

Keep icon backgrounds and the centers of selection frames transparent. rEFInd scales the frames to its menu tiles when icon sizes change. Sources use consistent orange utility strokes and white OS artwork; large size changes may need source adjustments to keep strokes and spacing balanced.

The builder exports the fixed filenames above. Adding a new distro SVG alone does not add an export rule or boot entry. Editing the shipped icon PNGs in `assets/icons/` does not affect a rebuild, which reads `sources/`.

The font is copied from `assets/font.png`. `sources/font.svg` is reference artwork and is not automatically exported by the current build. For a replacement atlas, follow the upstream [font format documentation](https://www.rodsbooks.com/refind/themes.html#fonts).

### White-label usage

Auren can carry your own logo, colors, background, and OS artwork without replacing rEFInd. There is no dedicated logo selector or automatic rebranding command: branding changes are made through the background image or editable SVG.

The shipped manufacturer and OS marks are examples, not required branding or a hardware compatibility claim. Use artwork you own or have permission to use, and keep third-party license notices when sharing a customized version. Auren is not an official Gigabyte, AORUS, Microsoft, Linux distribution, or rEFInd product.

## Troubleshooting

| Problem | What to check |
|---|---|
| Theme does not load | Confirm you boot the rEFInd installation at `/boot/efi/EFI/refind`. Inspect its active include and the installed `themes/auren/theme.conf`. |
| Installer rejects the configuration path | The helper expects a FAT ESP at `/boot/efi` and the exact rEFInd path above. Alternate layouts are not discovered automatically. |
| Background edits do not appear | With `render_background_svg: false`, the build reads `background`, not the SVG. With it enabled, the SVG's embedded logo is used. |
| Background looks cropped or stretched | Set the intended canvas resolution and use an image with the same aspect ratio. Linux display modes and firmware GOP modes may differ. |
| Icons are missing or look unchanged | Edit the exported SVG filenames, rebuild, and inspect explicit `icon` paths in the OS stanza. The helper only rewrites paths ending in `os_bazzite.png` or `os_win.png`. |
| Utility row has unexpected or repeated-looking icons | Review active `showtools` settings and included configs. Auren defaults to four distinct actions. If the config is correct but default actions remain, investigate the installed rEFInd build; this project's development notes describe a calling-convention issue in an earlier custom build. Do not replace your executable just to test a theme. |
| Firmware Settings is missing | rEFInd only shows that action when the firmware supports it. |
| “Starting … / Using load options” remains visible when launching an OS | Rebuild and install the theme. Its config enables graphics handoff for the recognized loader categories, and the installer sets `graphics on` in manual entries, including Shim entries. This suppresses rEFInd's normal launch text, not real boot errors or messages from the next loader. The OS and firmware determine the subsequent logo and spinner. |
| Border alignment or spacing is wrong | Check icon sizes and transparent padding in the SVGs. rEFInd controls tile positions; the preview is not an arbitrary layout editor. |
| `PIL.Image` has no `Resampling` attribute | Use Pillow 9.1.0 or newer in the interpreter running the command. |
| `magick` is missing or SVG export fails | Install ImageMagick with the `magick` command and working SVG support. An installation providing only `convert` does not satisfy the helper. |
| Authentication fails | Run the install command from a Linux session with a working `pkexec` authentication agent and administrator access. |
| Restore reports a changed main config | Compare the saved and current configs before proceeding. The helper deliberately refuses to overwrite later edits. |
| An OS entry is absent or fails to boot | Check the underlying rEFInd discovery settings and OS loader separately. Auren does not create or repair boot entries. |

For boot configuration problems, start with [rEFInd's documentation](https://www.rodsbooks.com/refind/configfile.html). A theme change is not a reason to format an ESP, replace a working bootloader, or disable Secure Boot.

## FAQ

### Is Auren a replacement for rEFInd?

No. Auren is a rEFInd theme. You need a working rEFInd installation; Auren customizes its background, icons, selection indicators, and other visual settings.

### Can I use Auren with Windows and Linux dual boot?

Auren supplies Bazzite and Windows icon styling for an existing rEFInd menu. OS boot support comes from rEFInd and the installed loaders, not the theme. The helper runs from Linux; it does not set up dual boot or install from Windows.

### Can I change the logo, colors, and boot icons?

Yes. Change colors and sizes in `theme.json`, replace the wallpaper, or edit the SVGs in `sources/`. Manufacturer branding is optional; Auren does not require Gigabyte hardware. Third-party logo permissions still apply.

### Does Auren work with Secure Boot?

Theme installation does not replace EFI executables, enroll keys, or change Secure Boot settings. It uses your existing boot chain; that chain must already work with Secure Boot. See [rEFInd's Secure Boot guide](https://www.rodsbooks.com/refind/secureboot.html) for boot-manager setup. The signed reference executable under `developer/` is specific to the original machine's certificate and is not a generally trusted release.

### How do I remove Auren or restore my previous theme?

Run `bash start.sh restore` to undo the helper's most recent installation. It restores the saved main config and prior Auren assets when present. It does not uninstall rEFInd; an inactive Auren directory may remain.

### Is Auren free and open-source? Can I redistribute a custom version?

Auren's original tooling and artwork are MIT licensed. You may use, modify, and redistribute those parts under the [license](LICENSE), keeping its notice. Included third-party code, font glyphs, logos, and trademarks have separate terms. Replacing example branding does not transfer ownership of those marks.

## Developer notes

Normal theme customization does not require a compiler, signing key, or bootloader rebuild. Start with [auren.py](auren.py), [theme.json](theme.json), and the SVG sources.

[developer/README.md](developer/README.md) documents the local rEFInd work. The checkout includes rEFInd source, a patch, and a signed reference executable. The developer build script expects GNU-EFI static libraries and a startup object that are not tracked in this repository, so a fresh clone is not a complete bootloader build environment. That does not affect the theme preview/install workflow.

[system/](system/) contains recovery-guard reference files, not a portable feature installed by `start.sh`. The guard pins the original machine's ESP identifier and requires separately provisioned certificate and recovery files. Do not enable those files unchanged on another machine.

## Contributing

Open an [issue](https://github.com/atragate/Auren/issues) for a bug or proposed change, or submit a pull request. For visual changes, include a preview and explain which SVGs or settings changed. For installation bugs, include the command, error text, Linux environment, and rEFInd path; never share private signing keys.

There is no separate contribution guide, release process, or GitHub Actions workflow in the tracked project yet. Keep changes focused, document their limits, and preserve third-party notices.

## License

Auren's original tooling and artwork are distributed under the [MIT License](LICENSE), copyright Atragate.

That license does not relicense bundled third-party components. rEFInd contains GPLv3 and other licensed code; see its [COPYING.txt](developer/refind-source/COPYING.txt), [LICENSE.txt](developer/refind-source/LICENSE.txt), and source notices. GNU-EFI material, font glyphs, logos, and trademarks retain their respective terms.

## Credits

- [rEFInd](https://www.rodsbooks.com/refind/), by Roderick W. Smith, provides the underlying boot manager and theming interface.
- [GNU-EFI](https://sourceforge.net/projects/gnu-efi/) is used in the separate developer reference build.
- The example Gigabyte wordmark comes from the [official GIGABYTE logo package](https://download.gigabyte.com/FileList/Brand/GIGABYTE_Logo.zip).
- The Bazzite icon uses the project's white logo artwork; see [Bazzite](https://github.com/ublue-os/bazzite/tree/main/press_kit).
- The Windows icon is a geometric four-pane glyph. The supplied font atlas contains Noto Sans Mono glyphs. Utility icons and decorative geometry are editable project artwork.

Auren is independent of these projects and brands. Their inclusion does not imply endorsement.
