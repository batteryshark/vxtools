# vxtools

Python scripts that turn a folder of Windows program files into a `.vxapp` package, plus
the written spec for that format.

**A note on the name.** The write-up uses "vxtools" for the runtime tools: the launcher,
the injector and the controller. Those live in
[vxlauncher](https://github.com/batteryshark/vxlauncher),
[VXBootStrap](https://github.com/batteryshark/VXBootStrap) and
[VXTools.NET](https://github.com/batteryshark/VXTools.NET). This repository is the other
side: the scripts that build the packages those tools run.

It goes with part four of the Masterpiece write-up,
[Putting together an App Format](https://batteryshark.github.io/2021/10/25/masterpiece-putting-together-an-app-format-part-four.html).

**Status: the packager, the diff tool and the upgrade tool work and have tests. The
registry and snapshot helpers are the original scripts, carried over nearly untouched.
Everything here needs Windows to do real work.**

## Why it exists

A `.vxapp` runs a Windows program out of read-only disk images that are layered into a
private `C:\`, with its registry and environment answered from files in place of the host
machine. That only works if the package has the right pieces in the right places: the
images, a map that says where each one goes, and a list of what can be launched.

Putting one together by hand means picking an image format, building the image, and
writing the map and the config JSON. `packager.py` does that in one command. The rest of
the scripts cover what comes after: shipping an update without rebuilding the image,
capturing what an installer wrote to the registry, and converting packages from older
layouts.

## What is inside

| Path | What it does |
| --- | --- |
| `vxtools/packager.py` | Packages a folder as a `.vxapp`. |
| `vxtools/diffgen.py` | Compares two versions of a folder and writes the files for an overlay, plus `REMOVE` lines for what was deleted. |
| `vxtools/vxupgrade.py` | Converts packages in an older layout, in place. Destructive, so it refuses to run without `--yes`. |
| `vxtools/get_codes.py` | Prints the app ID the loaders derive for each app in a folder. |
| `vxtools/vxsnapshot/` | Records every path on `C:\` and every registry key, then on a second run collects what is new. |
| `vxtools/regshot_convert.py`, `vxtools/convert_vxregistry.py` | Turn a Regshot export into a `pdxreg.ini`, in two steps. |
| `vxtools/pdxreg_tools.py` | Functions for walking the registry and writing `pdxreg.ini`. |
| `vxtools/pdxenv_tools.py` | Asks for a user name and drive details and writes `pdxenv.ini`. |
| `vxlib/packaging.py` | The packaging logic behind `packager.py`. |
| `templates/` | One zip file that holds an empty Windows folder skeleton, copied into every package. |
| `docs/vxapp-format.md` | The format spec. |
| `tests/` | pytest tests for packaging, diffing and registry key clean-up. |

## The .vxapp format

A `.vxapp` is a folder:

```text
App Name.vxapp/
  vxapp.config          launch entries (JSON)
  content/
    smoothie.map        where each image appears in the virtual filesystem
    windows_base.zip    empty Windows directory skeleton, mapped at C:\
    App Name.iso        the app's files, as .zip, .iso or .vhdx
  plugins/              optional: preload DLLs for this app only
  vxapp.info            optional: descriptive metadata, never read by a loader
```

`vxapp.config` is a JSON array of launch entries. Each entry has seven keys: `name`, `map`,
`executable`, `args`, `cwd`, `envar` and `preload`.

```json
[
    {
        "name": "Play Game",
        "map": "smoothie.map",
        "executable": "C:\\app\\Game.exe",
        "args": "",
        "cwd": "",
        "envar": [],
        "preload": ["pdxproc.dlldynamic", "pdxfs.dlldynamic"]
    }
]
```

The full spec is in [docs/vxapp-format.md](docs/vxapp-format.md): what each key means, how
preload names are found, the map syntax, the registry and environment INI files, how the
app ID is derived, and the three places where the write-up and the code differ.

## How the packager works

`packager.py` counts the files in the source folder and adds up their sizes. A small
folder becomes a `.zip`. More than 50 files or 128 MB becomes a UDF `.iso`, built by
mkisofs. A file over 4 GB, more than 1000 files, or more than 8 GB in total becomes an
NTFS `.vhdx`, built by a DISKPART script that creates the disk, mounts it to a temporary
folder, copies the files in and detaches it. The image goes into `content/` beside a copy
of `templates/windows_base.zip`, and the script writes a `smoothie.map` that puts the
skeleton at `C:\` and the image at `C:\app`. `vxapp.config` is either copied from a file
you pass or built from entry points you type in.

## Run it

There is nothing to install. The scripts need Python 3.11 or later, use only the standard
library, and run from a clone.

```powershell
git clone https://github.com/batteryshark/vxtools.git
cd vxtools
python vxtools\packager.py C:\Games\Example --config C:\Games\example.config
```

The package lands in `__staging\Example.vxapp` beside the source folder. Use
`--output-root` to put it somewhere else and `--dry-run` to see the path without writing
anything.

Without `--config`, the packager asks for entry points one at a time as
`path\inside\the\folder.exe;Title;arguments`. The title and arguments are optional, and an
empty line ends the list.

For an `.iso`, mkisofs has to be on `PATH`, or passed with `--mkisofs`. It is not included
here. For a `.vhdx`, run from an elevated prompt, because DISKPART needs it.

### Updates

```powershell
python vxtools\diffgen.py C:\Games\Example_v1 C:\Games\Example_v2 C:\app C:\Games\patch
```

This copies the added and changed files into `C:\Games\patch` and writes a
`smoothie_addon.map` there with one `REMOVE` line per deleted path. Files are compared by
MD5. Building the overlay image from that folder and adding the lines to the app's map is
left to you.

### Registry and environment

```powershell
mkdir C:\capture; cd C:\capture
python C:\path\to\vxtools\vxtools\vxsnapshot    # first run: writes baseline.json
# install or run the thing you want to capture
python C:\path\to\vxtools\vxtools\vxsnapshot    # second run: writes DATA\ and pdxreg.ini
```

The second run copies every file that was not in the baseline into `DATA\` and writes every
new registry key, with its values, to `pdxreg.ini`.

If you already have a Regshot comparison, save its key list as `registry_keys.txt` and its
value list as `registry_values.txt` in the current folder. Then:

```powershell
python vxtools\regshot_convert.py                        # writes a "vxregistry" JSON file
python vxtools\convert_vxregistry.py vxregistry pdxreg.ini
```

`python vxtools\pdxenv_tools.py` asks a few questions and writes `pdxenv.ini`.

### Older packages

```powershell
python vxtools\vxupgrade.py C:\Apps --yes
```

This walks every package folder in `C:\Apps` and converts the ones in the oldest layout
(those with a `metadata.json`); anything else is skipped. It deletes each package's `config`
folder, `metadata.json` and every `desktop.ini` as it goes, so work on a copy.

## Tests

```powershell
python -m pip install pytest
python -m pytest
```

Five tests cover format selection, zip output and diffing, and they run on any OS. The two
in `tests/test_registry_tools.py` import `winreg` and only run on Windows. Elsewhere, add
`--ignore=tests/test_registry_tools.py`.

## Windows versions and architectures

The scripts are plain Python and do not depend on the architecture of the machine. A
package can hold a 32-bit or a 64-bit program, and one `.dlldynamic` preload name covers
both.

Python 3.11 needs Windows 8.1 or later and VHDX needs Windows 8 or later, so Windows 10
and 11 are the realistic targets. Which Windows builds these scripts were last run on is
not recorded.

## Status and limits

- The five portable tests pass. In this cleaned-up tree they were run on macOS only. The
  `.iso` and `.vhdx` paths and all of the registry code were not run, because they need
  mkisofs, DISKPART and the Windows registry.
- `vxupgrade.py` stops at a middle layout that keeps the launch entries in `vxapp.info`.
  The current loaders read `vxapp.config`, so the entries still have to be moved across by
  hand. It also writes the converted registry to `content\vxregistry.ini` while the
  `PDXREG` variable it sets points at `C:\app\pdxreg.ini`. One of the two has to change
  before the app will see its registry.
- `vxsnapshot` only sees new files and new registry keys. A file that changed, or a new
  value under a key that already existed, is missed. It walks all of `C:\` and both
  registry hives, so it is slow.
- `vxsnapshot` writes per-user keys with the account's SID still in the key name.
  `pdxreg_tools.py` has a function that strips it, but the snapshot does not call it. Look
  through a captured `pdxreg.ini` before you share it.
- `regshot_convert.py` reads fixed file names from the current folder and has no options.
- `pdxenv_tools.py` lists drive type 6 (RAM disk) in its prompt and then rejects it.
- The original set had a `pdxfs_tools.py` that did not run as written. It is left out.

## Related repositories

- [vxlauncher](https://github.com/batteryshark/vxlauncher) and
  [VXTools.NET](https://github.com/batteryshark/VXTools.NET) load the packages these
  scripts build.
- [libsmoothie](https://github.com/batteryshark/libsmoothie) defines the map format and
  mounts the images.
- [pdx](https://github.com/batteryshark/pdx) reads `pdxreg.ini` and `pdxenv.ini`.
- [VXApp4Playnite](https://github.com/batteryshark/VXApp4Playnite) lists packages in
  Playnite and owns `vxapp.info`.

## Credits

`regshot_convert.py` reads text exported from [Regshot](https://sourceforge.net/projects/regshot/).
The `.iso` path calls mkisofs from cdrtools, which you supply. No third-party code is
included in this repository.
