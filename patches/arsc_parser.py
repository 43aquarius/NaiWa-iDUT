#!/usr/bin/env python3
"""
Raw ARSC (resources.arsc) parser - dumps all resources by type.
Format reference: https://github.com/android/platform_frameworks_base/blob/main/libs/androidfw/include/androidfw/ResourceTypes.h
"""
import struct, sys, json

RES_STRING_POOL_TYPE = 0x0001
RES_TABLE_TYPE = 0x0002
RES_TABLE_PACKAGE_TYPE = 0x0200
RES_TABLE_TYPE_TYPE = 0x0201
RES_TABLE_TYPE_SPEC_TYPE = 0x0202
RES_TABLE_LIBRARY_TYPE = 0x0203

class StringPool:
    def __init__(self, data, offset):
        (self.type, self.headerSize, self.size, self.stringCount,
         self.styleCount, self.flags, self.stringsStart, self.stylesStart) = struct.unpack_from('<HHIIIIII', data, offset)
        self.isUTF8 = bool(self.flags & (1 << 8))
        self.isSorted = bool(self.flags & 1)
        self.offset = offset
        self.data = data
        # string offsets array
        offs_fmt = '<%dI' % self.stringCount
        self.strOffsets = list(struct.unpack_from(offs_fmt, data, offset + self.headerSize)) if self.stringCount else []
        # style offsets
        self.styleOffsets = []
        if self.styleCount:
            so_fmt = '<%dI' % self.styleCount
            self.styleOffsets = list(struct.unpack_from(so_fmt, data, offset + self.headerSize + self.stringCount * 4))

    def get_string(self, idx):
        if idx < 0 or idx >= self.stringCount:
            return None
        abs_off = self.offset + self.stringsStart + self.strOffsets[idx]
        data = self.data
        if self.isUTF8:
            # u16 len, u8 len, bytes
            n1 = data[abs_off]
            if n1 & 0x80:
                n1 = ((n1 & 0x7f) << 8) | data[abs_off + 1]
                pos = abs_off + 2
            else:
                pos = abs_off + 1
            n2 = data[pos]
            if n2 & 0x80:
                n2 = ((n2 & 0x7f) << 8) | data[pos + 1]
                pos += 2
            else:
                pos += 1
            return data[pos:pos + n2].decode('utf-8', errors='replace')
        else:
            n = struct.unpack_from('<H', data, abs_off)[0]
            pos = abs_off + 2
            if n & 0x8000:
                n2 = struct.unpack_from('<H', data, pos)[0]
                n = ((n & 0x7fff) << 16) | n2
                pos += 2
            return data[pos:pos + n * 2].decode('utf-16-le', errors='replace')

class ResTable:
    def __init__(self, data):
        self.data = data
        (t, hs, sz) = struct.unpack_from('<HHI', data, 0)
        assert t == RES_TABLE_TYPE, "not a resource table"
        # global string pool
        sp_off = hs
        self.globalStrings = StringPool(data, sp_off)
        self.packages = []
        pos = sp_off + self.globalStrings.size
        while pos < len(data):
            (t, hs, sz) = struct.unpack_from('<HHI', data, pos)
            if t == RES_TABLE_PACKAGE_TYPE:
                self.packages.append(ResPackage(data, pos, self))
            elif t == 0:
                break
            pos += sz

class ResPackage:
    def __init__(self, data, offset, table):
        self.table = table
        self.data = data
        self.offset = offset
        (self.type, self.headerSize, self.size, self.id) = struct.unpack_from('<HHII', data, offset)
        self.name = data[offset+12:offset+12+256].decode('utf-16-le', errors='replace').rstrip('\x00')
        (self.typeStrings, self.lastPublicType, self.keyStrings, self.lastPublicKey) = struct.unpack_from('<IIII', data, offset + 12 + 256)
        # typeStrings/keyStrings are offsets relative to package chunk start
        self.typeStringsPool = StringPool(data, offset + self.typeStrings)
        self.keyStringsPool = StringPool(data, offset + self.keyStrings)
        # walk inner chunks
        self.types = {}  # typeId -> list of ResTypeChunk (config variants)
        pos = offset + self.headerSize
        end = offset + self.size
        while pos < end:
            (t, hs, sz) = struct.unpack_from('<HHI', data, pos)
            if t == RES_TABLE_TYPE_TYPE:
                chunk = ResTypeChunk(data, pos, self)
                self.types.setdefault(chunk.typeId, []).append(chunk)
            elif t == RES_TABLE_TYPE_SPEC_TYPE:
                pass
            elif t == RES_TABLE_LIBRARY_TYPE:
                pass
            if sz == 0:
                break
            pos += sz

class ResTypeChunk:
    """A RES_TABLE_TYPE chunk = a set of entries for one config of one type"""
    def __init__(self, data, offset, package):
        self.package = package
        self.offset = offset
        (self.type, self.headerSize, self.size, self.typeId, self.res0, self.res1,
         _pad, self.entryCount, self.entriesStart) = struct.unpack_from('<HHIBBBBII', data, offset)
        # config chunk starts at offset+20 (after fixed header); entry offsets array at offset+headerSize
        self.configSize = struct.unpack_from('<I', data, offset + 20)[0]
        # entry offsets start at offset + headerSize + configSize... 
        # Actually: header(28 bytes incl config header size?) — layout:
        # header: type,headerSize,size(8) + id,res0,res1(3+1pad? no...)
        # Real layout: 2+2+4+1+1+1+1pad? NO — struct is <HHHBBHII>? Let me be careful.
        # chunk header: type(2) headerSize(2) size(4) => 8
        # then: id(1) res0(1) res1(1) + 1 pad? Actually: id u8, res0 u8, res1 u8, entryCount u32 => id,res0,res1 are 3 bytes, then entryCount starts... 
        # Per ResourceTypes.h: struct ResTable_type { ResChunk_header header (8); uint8_t id; uint8_t res0; uint8_t res1; (no pad - actually there IS implicit padding? No: it's packed so next u32 needs 4-align → the struct uses #ifdef with 3 bytes + pad)
        # The headerSize covers: 8 + 4(id/res0/res1/pad?) + 4(entryCount) + 4(entriesStart) + config(ResTable_config)
        # Simplest: entriesStart is relative to chunk start; entry offsets array begins at offset+headerSize
        self.entryOffsets = []
        if self.entryCount:
            fmt = '<%dI' % self.entryCount
            self.entryOffsets = list(struct.unpack_from(fmt, data, offset + self.headerSize))
        self.entriesAbs = offset + self.entriesStart

    def entry_at(self, idx):
        """Returns (is_complex, entry dict)"""
        if idx >= len(self.entryOffsets):
            return None
        off = self.entryOffsets[idx]
        if off == 0xFFFFFFFF or off == 0xFFFFFFFFFFFFFFFF:
            return None
        eoff = self.entriesAbs + off
        data = self.package.data
        size, flags, key = struct.unpack_from('<HHI', data, eoff)
        is_complex = bool(flags & 0x0001)
        is_public = bool(flags & 0x0002)
        entry = {'size': size, 'flags': flags, 'key_idx': key, 'complex': is_complex}
        if is_complex:
            parent, count = struct.unpack_from('<II', data, eoff + 8)
            entry['parent'] = parent
            items = []
            for i in range(count):
                # each item: ResTable_ref (u32 resId) + Res_value (8 bytes) = 12 bytes
                io = eoff + 8 + 8 + i * 12
                rid, vsize, vres0, vdtype, vdata = struct.unpack_from('<IHBBI', data, io)
                items.append({'resId': rid, 'type': vdtype, 'data': vdata})
            entry['items'] = items
        else:
            vsize, vres0, vdtype, vdata = struct.unpack_from('<HBBI', data, eoff + 8)
            entry['value'] = {'type': vdtype, 'data': vdata}
        return entry

def val_repr(entry, package):
    """Convert an entry value to human-readable"""
    s = None
    if entry is None:
        return None
    if entry.get('complex'):
        return entry  # caller handles style items
    v = entry['value']
    dtype, data = v['type'], v['data']
    if dtype == 0x01:  # reference
        return '@' + hex(data)
    if dtype == 0x03:  # string
        return package.table.globalStrings.get_string(data)
    if dtype == 0x04:  # float
        return struct.unpack('<f', struct.pack('<I', data))[0]
    if dtype == 0x05:  # dimension
        units = ['px', 'dip', 'sp', 'pt', 'in', 'mm']
        return f"{data >> 8}{units[(data & 0xff) - 1] if 1 <= (data & 0xff) <= 6 else '?'}"
    if dtype == 0x06:  # fraction
        return f"{data / 0x10000}%"
    if dtype == 0x1c:
        return hex(data)
    if dtype == 0x1d:  # ARGB8
        return '#%08X' % data
    if dtype == 0x1e:  # RGB8
        return '#%06X' % data
    if dtype == 0x1f:  # ARGB4
        return '#%04X' % data
    if dtype == 0x10:  # int dec
        return data
    if dtype == 0x11:  # int hex
        return hex(data)
    if dtype == 0x12:  # boolean
        return bool(data)
    return f"type=0x{dtype:02x} data=0x{data:08x}"

def dump(apk_path, out_json):
    import zipfile
    zf = zipfile.ZipFile(apk_path)
    data = zf.read('resources.arsc')
    t = ResTable(data)
    result = {}
    for pkg in t.packages:
        pkgname = pkg.name
        result[pkgname] = {}
        for typeId, chunks in pkg.types.items():
            # type name from typeStrings pool (index typeId-1)
            tname = pkg.typeStringsPool.get_string(typeId - 1)
            if tname in ('style', 'color', 'drawable', 'mipmap', 'string', 'anim', 'id', 'layout'):
                tdata = {}
                # use the first chunk (default config) for names; merge configs
                for chunk in chunks:
                    for idx in range(chunk.entryCount):
                        e = chunk.entry_at(idx)
                        if e is None:
                            continue
                        name = pkg.keyStringsPool.get_string(e['key_idx'])
                        if name is None:
                            continue
                        if tname == 'style':
                            # resolve style items
                            items = {}
                            if e.get('complex') and e.get('items'):
                                for it in e['items']:
                                    rid = it['resId']
                                    val = raw_val(it['type'], it['data'], pkg)
                                    items[hex(rid)] = val
                            parent = e.get('parent')
                            tdata.setdefault(name, {'parent': hex(parent) if parent else None, 'items': items})
                            tdata[name]['items'].update(items)
                        else:
                            val = val_repr(e, pkg)
                            if name in tdata and tdata[name] != val:
                                # multiple configs - keep list
                                if isinstance(tdata[name], str):
                                    tdata[name] = [tdata[name], val]
                                else:
                                    tdata[name].append(val)
                            else:
                                tdata[name] = val
                result[pkgname][tname] = tdata
                print(f"dumped type {tname}: {len(tdata)} entries")
    with open(out_json, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"saved to {out_json}")

def raw_val(dtype, data, pkg):
    if dtype == 0x01:
        return '@' + hex(data)
    if dtype == 0x03:
        return pkg.table.globalStrings.get_string(data)
    if dtype == 0x1d:
        return '#%08X' % data
    if dtype == 0x1e:
        return '#%06X' % data
    if dtype == 0x1f:
        return '#%04X' % data
    if dtype == 0x10:
        return data
    if dtype == 0x05:
        units = ['px', 'dip', 'sp', 'pt', 'in', 'mm']
        u = (data & 0xff)
        return f"{data >> 8}{units[u-1] if 1 <= u <= 6 else '?'}"
    if dtype == 0x12:
        return bool(data)
    return f"type=0x{dtype:02x} data=0x{data:08x}"

if __name__ == '__main__':
    apk = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/workspace/NaiWa-iDUT/i大工_3.3.12.75026.apk'
    out = sys.argv[2] if len(sys.argv) > 2 else '/home/z/my-project/workspace/arsc_dump.json'
    dump(apk, out)
