## War Thunder resource extraction tools

A set of tools to extract resources from Gaijin's proprietary formats. 

Based on [kotiq's new-format](https://github.com/kotiq/wt-tools/tree/new-format) branch, which itself is based on Klensy's work. 
The main goal of forking it was to make some small tweaks to ensure it works with the latest War Thunder data, and to update dependencies as Python 3.7 is now end-of-life. Plus, 3.11 is faster!
## Installation

Check the [releases](https://github.com/ftsartek/wt-tools/releases) page for prebuilt binaries for Windows.

If you're more familiar with Python, you might prefer to use the Python package directly. You can either download it and run it as you would any Python scripts, or alternatively install it with pip as a module:

    git clone https://github.com/ftsartek/wt-tools
    cd wt-tools
    pip install .

## Usage

### As Python
All of the following examples still pertain to using this as a Python module, simply replace the executable launch, so:

    vromfs_unpacker.exe char.vromfs.bin

Becomes

    python -m wt_tools.vromfs_unpacker char.vromfs.bin

### As executables

#### vromfs_unpacker
Tool for unpacking game archives, this archives can contain any type of data:

    vromfs_unpacker.exe somefile.vromfs.bin
This will unpack files from `somefile.vromfs.bin` to `somefile.vromfs.bin_u` folder.

Options:
* -O, --output: path where to unpack vromfs file, if omitted is FILENAME with appended _u, like some.vromfs.bin_u; if used
then, for example `vromfs_unpacker.exe somefile.vromfs.bin --output my_folder`
* --metadata: if present, prints metadata of vromfs file: json with {filename: md5_hash}. If `--output` option used,
prints to file instead.
* --input_filelist: pass the file with list of files you want to unpack and only this files will be unpacked.
File list should be a json array, like: `["buildtstamp", "gamedata/units/tankmodels/fr_b1_ter.blk"]`

#### dxp_unpack 
> :warning: untested

Tool for unpacking texture archives:

    dxp_unpack.exe somefile.dxp.bin
This will unpack textures files from `somefile.dxp.bin` to `somefile.dxp.bin_u` folder,
but textures need to be unpacked with ddsx_unpack.

#### ddsx_unpack
> :warning: untested

Tool for unpacking textures, can be used to unpack single file or folder:

    ddsx_unpack.exe somefile.ddsx
This will unpack texture from `somefile.ddsx` to `somefile.dds`.

    ddsx_unpack.exe some_folder
This will unpack textures from folder `some_folder` to `some_folder`, unpacked textures will be inside with `*.dds` extension.
For unpacking most of textures, you need `oo2core_6_win64.dll`, as noted in installation section and will work only in Windows.

#### blk_unpack

The following files are used for the current version: `blk_unpack_ng` and `blk_unpack_ng_mp`.

Tool for unpacking blk files, that contain some text data

    blk_unpack.exe somefile.blk
This will unpack file from `somefile.blk` to `somefile.blkx`, data will be presented as json.
If you want to get ingame format, you can use this:

     blk_unpack.exe --format=strict_blk somefile.blk
This will unpack blk file to `somefile.blkx` in format, that can be used by game.
If you want unpack multiple files, pass folder name instead file name:

    blk_unpack.exe folder_name
This will unpack all blk filed in this folder into blkx files.

#### clog_unpack
Tool for 'decrypting' `*.clog` log files:

    clog_unpack.exe -i some_log.clog -k keyfile.bin -o out_log.log
This will decrypt `some_log.clog` with key `keyfile.bin` to `out_log.log` file.

#### blk_minify
> :warning: untested

Tool for minimizing blk files, good for modders, who want to create mission, but stuck at 512kb file size limit.
It will decrease size to ~ 70% from initial.
For basic usage:

    blk_minify.exe some_mission.blk some_mission_minified.blk
This will minify file from `some_mission.blk` to `some_mission_minified.blk`, without removing any structures from file.
If you want lower size file, you can try additional options:
* `--strip_empty_objects`: will remove empty objects
* `--strip_comment_objects`: will remove comment objects
* `--strip_disabled_objects`: remove disabled objects: the ones, which names start with __
* `--strip_all`: select all options

For example, for minimum size:

    blk_minify.exe --strip_all some_mission.blk some_mission_minified.blk

## Issues & Errors
As you've read above, some tools are untested. 

If you encounter any issues, please open an issue on GitHub. Include whatever info you can (most errors should include a stacktrace, this will help immensely).

## Klensy's interesting info page
Read [wiki](https://github.com/klensy/wt-tools/wiki).