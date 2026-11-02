"""Minimal NBT writer + structure-template builder (Minecraft 1.20.1, DataVersion 3465)."""
import gzip
import os
import struct

DATA_VERSION = 3465
AIR = "minecraft:air"


class Byte(int):
    pass


class Long(int):
    pass


class Float(float):
    pass


class Double(float):
    pass


def _str(s):
    b = s.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _type_of(v):
    if isinstance(v, Byte):
        return 1
    if isinstance(v, Long):
        return 4
    if isinstance(v, Float):
        return 5
    if isinstance(v, Double):
        return 6
    if isinstance(v, bool):
        return 1
    if isinstance(v, int):
        return 3
    if isinstance(v, str):
        return 8
    if isinstance(v, list):
        return 9
    if isinstance(v, dict):
        return 10
    raise TypeError(type(v))


def _payload(v):
    t = _type_of(v)
    if t == 1:
        return struct.pack(">b", int(v))
    if t == 3:
        return struct.pack(">i", v)
    if t == 4:
        return struct.pack(">q", v)
    if t == 5:
        return struct.pack(">f", v)
    if t == 6:
        return struct.pack(">d", v)
    if t == 8:
        return _str(v)
    if t == 9:
        if not v:
            return struct.pack(">bi", 0, 0)
        et = _type_of(v[0])
        return struct.pack(">bi", et, len(v)) + b"".join(_payload(x) for x in v)
    if t == 10:
        out = b""
        for k, x in v.items():
            out += struct.pack(">b", _type_of(x)) + _str(k) + _payload(x)
        return out + b"\x00"
    raise TypeError(t)


def nbt_bytes(compound):
    return struct.pack(">b", 10) + _str("") + _payload(compound)


NONSOLID = {AIR, "minecraft:ladder", "minecraft:rail", "minecraft:scaffolding", "minecraft:cobweb",
            "minecraft:wall_torch", "minecraft:torch", "minecraft:lantern", "minecraft:cave_air",
            "minecraft:chest", "minecraft:barrel", "minecraft:red_bed"}
CONNECT = {"donbass:rusty_fence", "minecraft:iron_bars"}
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


class Tpl:
    def __init__(self, sx, sy, sz):
        self.size = (sx, sy, sz)
        self.blocks = {}
        self.entities = []          # (x, y, z) doubles inside the template + entity NBT compound

    # -- primitives ---------------------------------------------------------
    def set(self, x, y, z, name, props=None, nbt=None):
        sx, sy, sz = self.size
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"({x},{y},{z}) outside {self.size} for {name}")
        self.blocks[(x, y, z)] = (name, tuple(sorted((props or {}).items())), nbt)

    def entity(self, x, y, z, nbt):
        """Add an entity (x, y, z are template-relative doubles; nbt must contain 'id')."""
        sx, sy, sz = self.size
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"entity at ({x},{y},{z}) outside {self.size}")
        self.entities.append((float(x), float(y), float(z), dict(nbt)))

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def fill(self, x0, y0, z0, x1, y1, z1, name, props=None):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, name, props)

    def air(self, x0, y0, z0, x1, y1, z1):
        self.fill(x0, y0, z0, x1, y1, z1, AIR)

    def shell(self, x0, y0, z0, x1, y1, z1, name, props=None):
        """Hollow box surface (all six faces)."""
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or y in (y0, y1) or z in (z0, z1):
                        self.set(x, y, z, name, props)

    def walls(self, x0, y0, z0, x1, y1, z1, name, props=None):
        """Four vertical walls only (no floor / roof)."""
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        self.set(x, y, z, name, props)

    def disc(self, cx, cz, r, y, name, props=None):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + r // 2:
                    self.set(x, y, z, name, props)

    def ring(self, cx, cz, r, y0, y1, name, props=None):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = (x - cx) ** 2 + (z - cz) ** 2
                if r * r - r <= d <= r * r + r:
                    for y in range(y0, y1 + 1):
                        self.set(x, y, z, name, props)

    # -- typed helpers ------------------------------------------------------
    def stairs(self, x, y, z, name, facing, half="bottom", shape="straight"):
        self.set(x, y, z, name, {"facing": facing, "half": half, "shape": shape, "waterlogged": "false"})

    def slab(self, x, y, z, name, typ="bottom"):
        self.set(x, y, z, name, {"type": typ, "waterlogged": "false"})

    def pillar(self, x, y0, y1, z, name, axis="y"):
        """Vertical column of an axis-aware block (logs, girders, sleepers): sets the 'axis' property."""
        for y in range(y0, y1 + 1):
            self.set(x, y, z, name, {"axis": axis})

    def column(self, x, y0, y1, z, name, props=None):
        """Vertical column of an ordinary block that has no 'axis' property."""
        for y in range(y0, y1 + 1):
            self.set(x, y, z, name, props)

    def door(self, x, y, z, facing, name="minecraft:spruce_door", hinge="left"):
        base = {"facing": facing, "hinge": hinge, "open": "false", "powered": "false"}
        self.set(x, y, z, name, dict(base, half="lower"))
        self.set(x, y + 1, z, name, dict(base, half="upper"))

    def chest(self, x, y, z, facing, loot):
        self.set(x, y, z, "minecraft:chest", {"facing": facing, "type": "single", "waterlogged": "false"},
                 {"id": "minecraft:chest", "LootTable": loot})

    def ladder(self, x, y0, y1, z, facing):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, "minecraft:ladder", {"facing": facing, "waterlogged": "false"})

    def rail(self, x, y, z, shape="east_west"):
        self.set(x, y, z, "minecraft:rail", {"shape": shape, "waterlogged": "false"})

    def scaffold(self, x, y0, y1, z):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, "minecraft:scaffolding", {"bottom": "false", "distance": "0", "waterlogged": "false"})

    def bed(self, x, y, z, facing, color="red"):
        dx, dz = DIRS[facing]
        self.set(x, y, z, f"minecraft:{color}_bed", {"facing": facing, "occupied": "false", "part": "foot"})
        self.set(x + dx, y, z + dz, f"minecraft:{color}_bed", {"facing": facing, "occupied": "false", "part": "head"})

    def spawner(self, x, y, z, entity):
        self.set(x, y, z, "minecraft:spawner", None, {
            "id": "minecraft:mob_spawner",
            "SpawnData": {"entity": {"id": entity}},
            "SpawnPotentials": [{"weight": 1, "data": {"entity": {"id": entity}}}]})

    def jigsaw(self, x, y, z, orientation, pool, name, target, final_state=AIR, joint="aligned"):
        self.set(x, y, z, "minecraft:jigsaw", {"orientation": orientation},
                 {"id": "minecraft:jigsaw", "pool": pool, "name": name, "target": target,
                  "final_state": final_state, "joint": joint})

    def wheel(self, cx, cy, cz, r, name, props=None):
        """Circle (ring) in the Y-Z plane at x=cx; used for hoisting-wheel faces."""
        for y in range(cy - r - 1, cy + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = (y - cy) ** 2 + (z - cz) ** 2
                if r * r - r <= d <= r * r + r:
                    self.set(cx, y, z, name, props)

    def mirrored_z(self):
        """Return a copy mirrored along Z (north<->south), fixing direction-dependent properties."""
        swap = {"north": "south", "south": "north"}
        flip = {"left": "right", "right": "left"}
        out = Tpl(*self.size)
        sz = self.size[2]
        for (x, y, z), (name, props, nbt) in self.blocks.items():
            p = dict(props)
            for k in list(p):
                v = p[k]
                if k in ("north", "south"):
                    pass  # handled below (swap the two keys)
                elif k == "facing" and v in swap:
                    p[k] = swap[v]
                elif k == "hinge":
                    p[k] = flip[v]
                elif k == "shape" and name.endswith(("_stairs",)):
                    p[k] = v.replace("left", "@").replace("right", "left").replace("@", "right")
                elif k == "shape" and v.startswith("ascending_") and v[10:] in swap:
                    p[k] = "ascending_" + swap[v[10:]]
                elif k == "orientation":
                    head, tail = v.split("_", 1)
                    p[k] = swap.get(head, head) + "_" + tail
            if "north" in p and "south" in p:
                p["north"], p["south"] = p["south"], p["north"]
            out.blocks[(x, y, sz - 1 - z)] = (name, tuple(sorted(p.items())), nbt)
        out.entities = [(ex, ey, sz - ez, dict(en)) for (ex, ey, ez, en) in self.entities]
        return out

    def paste(self, other, ox, oy, oz):
        """Copy another template into this one at an offset."""
        for (x, y, z), val in other.blocks.items():
            self.blocks[(x + ox, y + oy, z + oz)] = val
        for (ex, ey, ez, en) in other.entities:
            self.entities.append((ex + ox, ey + oy, ez + oz, dict(en)))

    # -- output -------------------------------------------------------------
    def _connect_panes(self):
        for (x, y, z), (name, props, nbt) in list(self.blocks.items()):
            if name not in CONNECT:
                continue
            p = dict(props)
            for d, (dx, dz) in DIRS.items():
                other = self.blocks.get((x + dx, y, z + dz))
                p[d] = "true" if other and (other[0] in CONNECT or other[0] not in NONSOLID) else "false"
            p["waterlogged"] = "false"
            self.blocks[(x, y, z)] = (name, tuple(sorted(p.items())), nbt)

    def to_nbt(self):
        self._connect_panes()
        palette, index, blocks = [], {}, []
        for (x, y, z), (name, props, nbt) in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
            key = (name, props)
            if key not in index:
                index[key] = len(palette)
                entry = {"Name": name}
                if props:
                    entry["Properties"] = {k: str(v) for k, v in props}
                palette.append(entry)
            b = {"pos": [x, y, z], "state": index[key]}
            if nbt:
                b["nbt"] = nbt
            blocks.append(b)
        entities = [{"pos": [Double(ex), Double(ey), Double(ez)],
                     "blockPos": [int(ex // 1), int(ey // 1), int(ez // 1)], "nbt": en}
                    for (ex, ey, ez, en) in self.entities]
        return {"size": list(self.size), "entities": entities, "blocks": blocks,
                "palette": palette, "DataVersion": DATA_VERSION}

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with gzip.GzipFile(path, "wb", mtime=0) as f:
            f.write(nbt_bytes(self.to_nbt()))
