import struct

import zstandard
from construct import (
    Construct,
    Enum,
    this,
    Adapter,
    Struct,
    Seek,
    Int32ul,
    Array,
    CString,
    Tell,
    If,
    Bytes,
    Computed,
    Embedded,
    Switch,
    Hex,
    Int16ul,
    GreedyBytes,
    RestreamData,
    IfThenElse,
    NullTerminated,
    ByteSwapped,
    BitStruct,
    BitsInteger,
    Check,
)

from .common import zlib_stream

NOT_PACKED_ADDED_OFFSET = 0x10
NOT_PACKED_FILE_DATA_TABLE_OFFSET = 0x20
NOT_PACKED_FILENAME_TABLE_OFFSET = 0x40

NOT_PACKED = "not_packed"
ZSTD_PACKED = "zstd_packed"
ZSTD_PACKED_NOCHECK = "zstd_packed_nocheck"
ZLIB_PACKED = "zlib_packed"
MAYBE_PACKED = "maybe_packed"
TRAP = "hoo"

vromfs_type = Enum(
    BitsInteger(6), **{ZSTD_PACKED_NOCHECK: 0x10, MAYBE_PACKED: 0x20, ZSTD_PACKED: 0x30}
)


class ZstdContext(Construct):
    def __init__(self):
        super(ZstdContext, self).__init__()

    def _parse(self, stream, ctx, path):
        need_read_size = (
            ctx._._.header.packed_size
            - (16 if ctx.first_part else 0)
            - (16 if ctx.second_part else 0)
        )
        # ugly: align read size to 4 bytes
        need_read_size = need_read_size // 4 * 4
        deobfs_compressed_data = (
            (ctx.first_part if ctx.first_part else b"")
            + stream.getvalue()[
                ctx.middle_data_offset : ctx.middle_data_offset + need_read_size
            ]
            + (ctx.second_part.data if ctx.second_part.data else b"")
            + (ctx.align_tail if ctx.align_tail else b"")
        )
        dctx = zstandard.ZstdDecompressor()
        ctx.decompressed_data = dctx.decompress(
            deobfs_compressed_data, max_output_size=ctx._._.header.original_size
        )


class ZlibAdapter(Adapter):
    def _decode(self, obj, context, path):
        return vromfs_not_packed_body.parse(obj)


class Obfs16Adapter(Adapter):
    def _decode(self, obj, context, path):
        return struct.pack(
            "<4L",
            *[
                x ^ y
                for (x, y) in zip(obj, [0xAA55AA55, 0xF00FF00F, 0xAA55AA55, 0x12481248])
            ],
        )


class Obfs32Adapter(Adapter):
    def _decode(self, obj, context, path):
        return struct.pack(
            "<4L",
            *[
                x ^ y
                for (x, y) in zip(obj, [0x12481248, 0xAA55AA55, 0xF00FF00F, 0xAA55AA55])
            ],
        )


"""
struct VirtualRomFsExtHdr {
    ushort size;
    ushort flags;
    uint version;
};
"""
vromfs_ext_header = Struct(
    "size" / Int16ul,
    "flags" / Int16ul,
    # parsed as 34013242 -> 0207003A -> 2.7.0.58
    "version" / Int32ul,
)

filename = Struct(
    "filename" / NullTerminated(GreedyBytes, include=True),
    "filename"
    / IfThenElse(
        this.filename == b"\xff?nm\x00",
        RestreamData(b"nm\x00", CString(encoding="utf8")),
        RestreamData(this.filename, CString(encoding="utf8")),
    ),
)

filename_table = Struct(
    # move to start of filename table
    Seek(this._.data_start_offset + this._.filename_table_offset, 0),
    # here we can find offset table: (total_files * 8 byte) size
    # but we cheat, just read total_files * cstrings
    "first_filename_offset" / Int32ul,
    Seek(this._.data_start_offset + this.first_filename_offset),
    "filenames" / Array(this._.files_count, filename),
)

file_data_record = Struct(
    "file_data_offset" / Int32ul,
    "file_data_offset" / Computed(this.file_data_offset + this._._.data_start_offset),
    "file_data_size" / Int32ul,
    "unknown" / Hex(Bytes(8)),
    "next_file_data_record" / Tell,
    # move to file data offset
    Seek(this.file_data_offset, 0),
    # read file data
    "data" / Bytes(this.file_data_size),
    # return to next file data record in table
    Seek(this.next_file_data_record, 0),
)

file_data_table = Struct(
    # move to location of file data table offset
    Seek(this._.data_start_offset + this._.filedata_table_offset, 0),
    # main actions in file_data_record
    "file_data_list" / Array(this._.files_count, file_data_record),
)

not_packed_stream = Struct(
    "data_start_offset" / Tell,
    "filename_table_offset" / Int32ul,
    "files_count" / Int32ul,
    Seek(8, 1),
    "filedata_table_offset" / Int32ul,
    "filename_table" / filename_table,
    "file_data_table" / file_data_table,
)
vromfs_not_packed_body = Struct(
    "data" / Struct(Embedded(not_packed_stream)),
)

zstd_stream = "zstd_stream" / Struct(
    "before_obfs" / Tell,
    "first_part" / If(this._._.header.packed_size >= 16, Obfs16Adapter(Int32ul[4])),
    "middle_data_offset" / Tell,
    "second_part"
    / If(
        this._._.header.packed_size >= 32,
        Struct(
            # 32 = length of obfuscated header + footer of data
            # ugly: align seek with 4 bytes
            Seek((this._._._.header.packed_size - 32) // 4 * 4, 1),
            "data" / Obfs32Adapter(Int32ul[4]),
        ),
    ),
    "after_obfs" / Tell,
    # last part, if packed_size % 4 != 0
    "align_tail"
    / If(this._._.header.packed_size % 4, Bytes(this._._.header.packed_size % 4)),
    ZstdContext(),
)

vromfs_zstd_packed_body = Struct(
    Embedded(zstd_stream),
    "data" / RestreamData(this.decompressed_data, not_packed_stream),
)

vromfs_zlib_packed_body = Struct(
    Embedded(zlib_stream),
    "data" / RestreamData(this.decompressed_body, not_packed_stream),
)


def vromfs_packed_type(ctx):
    vromfs_type = ctx.vromfs_type
    packed_size = ctx.packed_size
    if not packed_size:
        type_ = NOT_PACKED
    elif vromfs_type in (ZSTD_PACKED, ZSTD_PACKED_NOCHECK):
        type_ = ZSTD_PACKED
    elif vromfs_type == MAYBE_PACKED:
        type_ = ZLIB_PACKED
    else:
        type_ = TRAP
    return type_


vromfs_header = Struct(
    "magic" / Enum(Bytes(4), vrfs=b"VRFs", vrfx=b"VRFx"),
    "platform" / Enum(Bytes(4), pc=b"\x00\x00PC", ios=b"\x00iOS", andr=b"\x00and"),
    "original_size" / Int32ul,
    "packed"
    / ByteSwapped(
        BitStruct(
            "type" / vromfs_type,
            "size" / BitsInteger(26),
        )
    ),
    "packed_size" / Computed(this.packed.size),
    "vromfs_type" / Computed(this.packed.type),
    "vromfs_packed_type" / Computed(vromfs_packed_type),
)

vromfs_body = Struct(
    "data"
    / Switch(
        this._.header.vromfs_packed_type,
        {
            NOT_PACKED: vromfs_not_packed_body,
            ZSTD_PACKED: vromfs_zstd_packed_body,
            ZLIB_PACKED: vromfs_zlib_packed_body,
        },
    ),
)

vromfs_file = Struct(
    "header" / vromfs_header,
    "ext_header"
    / If(
        this.header.magic == "vrfx",
        vromfs_ext_header,
    ),
    "is_new_version"
    / IfThenElse(
        # FIXME in one line
        this.ext_header,
        If(
            # version 2.7.0.58+
            this.ext_header.version >= 34013242,
            Computed(True),
        ),
        Computed(False),
    ),
    "vromfs_offset" / Tell,
    "body" / vromfs_body,
    If(
        this.header.packed_size == 0,
        Seek(this.vromfs_offset + this.header.original_size),
    ),
    "md5" / If(this.header.vromfs_type != ZSTD_PACKED_NOCHECK, Bytes(16)),
    "tail" / GreedyBytes,
    Check(lambda c: len(c.tail) in (0, 0x100)),
)
