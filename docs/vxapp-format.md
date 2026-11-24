# The .vxapp format

A `.vxapp` is a folder, not an archive. Its name is the app's name plus `.vxapp`. It holds
the app's files as one or more disk images, a map that says where each image appears in
the virtual filesystem, and a list of the ways the app can be started.

This file describes what the loaders actually read. The loaders are
[vxlauncher](https://github.com/batteryshark/vxlauncher) (native) and
[VXTools.NET](https://github.com/batteryshark/VXTools.NET) (managed). Where the 2021
write-up and the code disagree, the code is what is written down here, and the difference
is called out under [Differences from the write-up](#differences-from-the-write-up).

## Layout

```text
App Name.vxapp/
  vxapp.config          required: launch entries (JSON)
  content/              required
    smoothie.map        the map named by an entry's "map" key
    windows_base.zip    empty Windows directory skeleton, mapped at C:\
    App Name.iso        the app's files, as .zip, .iso or .vhdx
    ...                 optional overlays and extra maps
  plugins/              optional: preload DLLs or bootstrap binaries for this app only
  vxapp.info            optional: descriptive metadata, never read by a loader
```

`packager.py` writes `vxapp.config` and `content/`. It does not create `plugins/` or
`vxapp.info`.

## App name and app ID

The loaders take the app's name from the folder name with `.vxapp` removed. They hash that
name with SHA-1 and turn the first nine bytes of the digest into a code such as
`ABC-12F-GZ9`: each byte, modulo 33, indexes the alphabet `0123456789ABCDEFGHJKLMNPQRSTUVWXY`
(no `I`, no `O`, no `Z`).

The code names the app's temporary mount folder and its save folder. Renaming a `.vxapp`
folder therefore gives it a new, empty save folder. `get_codes.py` prints the code for
every app in a directory.

## vxapp.config

A JSON array. Each element is one launch entry: a name a loader can show or select, and
everything needed to start that entry.

```json
[
    {
        "name": "Play Game",
        "map": "smoothie.map",
        "executable": "C:\\app\\Game.exe",
        "args": "",
        "cwd": "",
        "envar": [],
        "preload": [
            "pdxproc.dlldynamic",
            "pdxfs.dlldynamic"
        ]
    }
]
```

| Key | Type | Meaning |
| --- | --- | --- |
| `name` | string | Name of the entry. A loader asked for a named entry picks the one whose `name` matches; with no name given, it uses the first entry. |
| `map` | string | File name of a map under `content/`. Different entries may name different maps, for example to run two versions of the app from one package. |
| `executable` | string | Virtual path of the program to start, as it will exist once the map is mounted. The loader resolves it to a real path and reads its PE header to choose the 32-bit or 64-bit bootstrap. |
| `args` | string | Command-line arguments, passed as written. Empty string for none. |
| `cwd` | string | Virtual path of the working directory. Empty string to leave it alone. |
| `envar` | array of strings | Environment variables in `NAME=value` form, set before the program starts. |
| `preload` | array of strings | File names of the [pdx](https://github.com/batteryshark/pdx) libraries to inject, in order. |

Write all seven keys in every entry, even when the value is empty. The native launcher
converts each one without checking for it first, and a missing key ends the launch.

### How preload names are found

For each name in `preload`, the native launcher looks in:

1. `App Name.vxapp/plugins/`
2. the launcher's own binary folder (`VXPATH_BIN`, by default the folder the launcher is in)

VXTools.NET looks in the same two places and then in a `pdxplugins` folder inside its
binary folder. The native launcher skips a name it cannot find, with a warning.

A name ending in `.dlldynamic` stands for a pair of DLLs. `pdxfs.dlldynamic` means
`pdxfs32.dll` for a 32-bit process and `pdxfs64.dll` for a 64-bit one. The bootstrap makes
the substitution for each process it injects, so one entry covers an app that starts
programs of both kinds.

The native launcher looks for the bootstrap executables (`VXBootstrap32.exe`,
`VXBootstrap64.exe`) in the same order, so a package can carry its own in `plugins/`.

## content/ and the map

A map is a text file in the format of
[libsmoothie](https://github.com/batteryshark/libsmoothie): one command per line, fields
separated by semicolons, `#` for comments.

```text
MAP;windows_base.zip;C:\
MAP;Game.iso;C:\app
MAP;patch.zip;C:\app
REMOVE;C:\app\old_launcher.exe
```

- `MAP;image;virtual_root` mounts an image and places its contents at a virtual path. The
  image name is resolved relative to the folder the map is in.
- `REMOVE;virtual_path` hides a path.
- `LINK;source;virtual_path` places a single file.

Lines are applied top to bottom. A later `MAP` replaces any file an earlier one put at the
same virtual path, which is how an overlay such as `patch.zip` above changes an app without
rebuilding its main image. See libsmoothie for the full rules.

`packager.py` always writes the first two lines: the empty Windows skeleton at `C:\`, then
the app's image at `C:\app`. `diffgen.py` produces the pieces for the last two: a folder of
added and changed files to turn into an overlay image, and a `smoothie_addon.map` holding
the `REMOVE` lines. No loader reads `smoothie_addon.map` itself. Its lines are meant to be
appended to the app's map after the overlay's `MAP` line.

### Which image format

`packager.py` picks the container from what is in the source folder:

| Source folder | Container |
| --- | --- |
| any file over 4 GB, or more than 1000 files, or more than 8 GB in total | `.vhdx` (NTFS, expandable, built with DISKPART) |
| otherwise, more than 50 files or more than 128 MB in total | `.iso` (UDF, built with mkisofs) |
| otherwise | `.zip` (stored, not compressed) |

A loader does not care which one it gets. The choice only matters to the packager.

## Per-app registry and environment files

pdx reads two optional INI files. Neither has a fixed place in the package. Each is found
through an environment variable, which the entry sets in `envar`:

| Variable | File | Read by |
| --- | --- | --- |
| `PDXREG` | `pdxreg.ini`: registry keys and values the app should see | pdxreg |
| `PDXENV` | `pdxenv.ini`: user name and drive type, serial, label and filesystem | pdxenv |

For example `"envar": ["PDXREG=C:\\app\\pdxreg.ini"]`, with the pdxreg library added to
`preload`. With the variable unset, each library looks for its file in the working
directory.

A `pdxreg.ini` section is a registry key in native form, and each line under it is a value:

```ini
[\registry\machine\software\example\game]
@="1,default value"
installdir="1,C:\app"
version="4,3"
serial="3,0011223344"
```

The number before the comma is the registry type (`1` REG_SZ, `3` REG_BINARY as a hex
string, `4` REG_DWORD, `11` REG_QWORD). `@` is the key's default value.

A `pdxenv.ini` looks like this:

```ini
[global]
username=user

[drive_map_d]
type=5
serial=0
label=CD
filesystem=CDFS
```

`type` is the Windows drive type number (`3` fixed disk, `5` CD-ROM).

## vxapp.info

Descriptive metadata for a frontend: display name, description, scores and the like. No
loader reads it, and nothing about launching depends on it.
[VXApp4Playnite](https://github.com/batteryshark/VXApp4Playnite) reads and writes it, and
keeps `cover` and `background` image files beside it in the package root. See that
repository for the fields.

## Differences from the write-up

Part four of the write-up introduces the format. Three things in it do not match the code:

- It shows a `plugin_options.ini` inside `content/`. No code reads a file by that name. The
  per-app plugin settings are the `pdxreg.ini` and `pdxenv.ini` files described above.
- It does not show `plugins/`. Both loaders search that folder first for preload DLLs.
- It lists a `metadata` entry for an icon. No code reads a `metadata` folder. The Playnite
  adapter stores `cover` and `background` in the package root instead.

## Older layouts

Earlier packages kept a `metadata.json` and a `config/default/` folder with `entrypoint`,
`vxfilesystem` and `vxregistry` files. `vxupgrade.py` converts those to a middle layout
that put the launch entries inside `vxapp.info` under a `configuration` key. The current
loaders read `vxapp.config` only, so an app upgraded that way still needs its entries moved
into a `vxapp.config`.
