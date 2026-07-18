# Zyvion Phase 1.3l — ASSET POLISH PASS (user: "the assets feel cheap").
# The build scripts only ever emit hard-edged primitives with flat colours.
# This pass upgrades what already exists instead of rebuilding it:
#   1. MATERIALS - retunes the shared ZY_* palette with sane roughness /
#      metallic so surfaces stop reading as flat paint.
#   2. BEVEL - rounds the edges of every prop-class mesh in place (bmesh, so it
#      survives glTF export - no modifier stack). Sharp CG box edges are the
#      single biggest "cheap" tell.
#   3. CHAIRS - bare seat cylinders gain a gas post, 5-star base and castors.
#      Deliberately rotationally symmetric: the build scripts seat people facing
#      different ways per floor, so an oriented backrest would be wrong half the
#      time.
#   4. DESKS - gain legs and a modesty panel.  5. COUCHES - gain feet.
#   6. CARS - gain bumpers, head/tail lights and door mirrors, oriented off the
#      body's own rotation.
# Idempotent: every touched object is stamped zy_polished and skipped on re-run.
# Order: run LAST, after all build scripts.

def zy_polish():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_polish_status.json"
    stats = {"beveled": 0, "chairs": 0, "desks": 0, "cars": 0, "couches": 0, "materials": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_polish", "error": "REFUSED: autosave: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection

        def get_coll(name, parent):
            c = bpy.data.collections.get(name)
            if c is None:
                c = bpy.data.collections.new(name)
            if all(ch.name != c.name for ch in parent.children):
                try:
                    parent.children.link(c)
                except Exception:
                    pass
            return c

        c_det = get_coll("Asset_Detail", root)

        def kill(name):
            ob = bpy.data.objects.get(name)
            if ob is not None:
                me = ob.data if ob.type == "MESH" else None
                bpy.data.objects.remove(ob, do_unlink=True)
                if me is not None and me.users == 0:
                    bpy.data.meshes.remove(me)

        TUNE = {
            "Metal_Dark": (0.32, 0.85), "Steel_Brushed": (0.28, 0.92),
            "Duct_Silver": (0.30, 0.80), "Concrete_Slab": (0.88, 0.0),
            "Wall_OffWhite": (0.80, 0.0), "Lobby_Floor": (0.42, 0.0),
            "Tile_Paver": (0.45, 0.0), "Tile_Grout": (0.90, 0.0),
            "Wood_Warm": (0.55, 0.0), "Couch_Charcoal": (0.92, 0.0),
            "Divider_Grey": (0.86, 0.0), "Asphalt": (0.93, 0.0),
            "Grass_Green": (0.96, 0.0), "Hedge_Green": (0.95, 0.0),
            "Ceramic_White": (0.25, 0.0), "AC_White": (0.38, 0.0),
            "Screen_Teal": (0.18, 0.0), "Solar_Cell": (0.16, 0.35),
            "Accent_Amber": (0.50, 0.0), "Accent_Teal": (0.50, 0.0),
            "Accent_Red": (0.52, 0.0), "Helipad_Dark": (0.94, 0.0),
            "Curtain_Cream": (0.93, 0.0), "Heli_Body": (0.38, 0.25),
            "RoadLine": (0.65, 0.0), "Path_Turq": (0.62, 0.0),
        }
        for m in bpy.data.materials:
            if not m.name.startswith("ZY_") or not m.use_nodes:
                continue
            bsdf = None
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    bsdf = n
                    break
            if bsdf is None:
                continue
            for frag, (rough, metal) in TUNE.items():
                if frag in m.name:
                    try:
                        bsdf.inputs["Roughness"].default_value = rough
                        bsdf.inputs["Metallic"].default_value = metal
                    except Exception:
                        pass
                    stats["materials"] += 1
                    break
            if m.name.startswith("ZY_Car_"):
                try:
                    bsdf.inputs["Roughness"].default_value = 0.28
                    bsdf.inputs["Metallic"].default_value = 0.45
                except Exception:
                    pass
                stats["materials"] += 1
            if "Glass" in m.name:
                try:
                    bsdf.inputs["Roughness"].default_value = 0.04
                except Exception:
                    pass

        def mat(name):
            return bpy.data.materials.get(name)

        m_metal = mat("ZY_Metal_Dark")
        m_steel = mat("ZY_Steel_Brushed") or m_metal
        m_wood = mat("ZY_Wood_Warm")
        m_red = mat("ZY_Accent_Red")
        m_glass = mat("ZY_Glass_Blue")

        def addbox(name, sx, sy, sz, cx, cy, cz, rz, m):
            if sx <= 0.001 or sy <= 0.001 or sz <= 0.001:
                return None
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= sx
                v.co.y *= sy
                v.co.z *= sz
            try:
                bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                                offset=min(0.02, sx / 4, sy / 4, sz / 4), segments=1,
                                affect="EDGES", profile=0.7)
            except Exception:
                pass
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, cz)
            ob.rotation_euler = (0.0, 0.0, rz)
            c_det.objects.link(ob)
            if m is not None:
                me.materials.append(m)
            ob["zy_polished"] = True
            return ob

        def addcyl(name, r, depth, cx, cy, cz, m, seg=10):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r, radius2=r, depth=depth)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, cz)
            c_det.objects.link(ob)
            if m is not None:
                me.materials.append(m)
            ob["zy_polished"] = True
            return ob

        PROP_HINTS = ("_Desk", "_Mon", "_Chair", "_Stool", "Couch_", "_Bench",
                      "_Table", "_Cab", "Cub_", "Car_", "_Counter", "_Tray",
                      "Sec_", "_Kiosk", "_Pil", "_Shrub", "_Planter")
        targets = [o for o in bpy.data.objects
                   if o.type == "MESH" and not o.get("zy_polished")]

        for ob in targets:
            nm = ob.name
            is_prop = any(h in nm for h in PROP_HINTS)
            if is_prop and ob.data is not None and len(ob.data.vertices) <= 64:
                try:
                    bm = bmesh.new()
                    bm.from_mesh(ob.data)
                    dims = ob.dimensions
                    off = min(0.022, max(0.004, min(dims.x, dims.y, dims.z) / 5.0))
                    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                                    offset=off, segments=1, affect="EDGES", profile=0.7)
                    bm.to_mesh(ob.data)
                    bm.free()
                    stats["beveled"] += 1
                except Exception:
                    pass

            loc = ob.location
            rz = ob.rotation_euler.z
            d = ob.dimensions

            if ("_Chair" in nm or nm.endswith("Chair")) and d.z > 0.2:
                seat_bot = loc.z - d.z / 2.0
                addcyl(nm + "_Post", 0.055, max(0.18, d.z * 0.7),
                       loc.x, loc.y, seat_bot - d.z * 0.35, m_steel, seg=8)
                for si in range(5):
                    a = si * (2.0 * math.pi / 5.0)
                    addbox(nm + "_Star%d" % si, 0.30, 0.055, 0.035,
                           loc.x + 0.15 * math.cos(a), loc.y + 0.15 * math.sin(a),
                           seat_bot - d.z * 0.62 - 0.03, a, m_metal)
                    addcyl(nm + "_Cast%d" % si, 0.045, 0.05,
                           loc.x + 0.30 * math.cos(a), loc.y + 0.30 * math.sin(a),
                           seat_bot - d.z * 0.62 - 0.07, m_metal, seg=6)
                stats["chairs"] += 1

            elif ("_Desk" in nm or "_Counter" in nm) and d.x > 0.6 and d.y > 0.4 and d.z > 0.3:
                bot = loc.z - d.z / 2.0
                hx, hy = d.x / 2.0 - 0.12, d.y / 2.0 - 0.10
                for li, (lx, ly) in enumerate(((-hx, -hy), (hx, -hy), (-hx, hy), (hx, hy))):
                    wx = loc.x + lx * math.cos(rz) - ly * math.sin(rz)
                    wy = loc.y + lx * math.sin(rz) + ly * math.cos(rz)
                    addbox(nm + "_Leg%d" % li, 0.07, 0.07, d.z, wx, wy, bot + d.z / 2.0, rz, m_steel)
                mx = loc.x + (d.y / 2.0 - 0.06) * math.sin(rz)
                my = loc.y - (d.y / 2.0 - 0.06) * math.cos(rz)
                addbox(nm + "_Modesty", d.x * 0.86, 0.05, d.z * 0.55,
                       mx, my, bot + d.z * 0.34, rz, m_wood)
                stats["desks"] += 1

            elif nm.startswith("Lobby_Couch_") and nm.endswith("_Base"):
                bot = loc.z - d.z / 2.0
                hx, hy = d.x / 2.0 - 0.18, d.y / 2.0 - 0.16
                for li, (lx, ly) in enumerate(((-hx, -hy), (hx, -hy), (-hx, hy), (hx, hy))):
                    wx = loc.x + lx * math.cos(rz) - ly * math.sin(rz)
                    wy = loc.y + lx * math.sin(rz) + ly * math.cos(rz)
                    addbox(nm + "_Foot%d" % li, 0.09, 0.09, 0.14, wx, wy, bot - 0.05, rz, m_metal)
                stats["couches"] += 1

            elif nm.startswith("Car_") and nm.endswith("_Body"):
                L = d.y
                Wd = d.x
                mid = loc.z

                def place(lx, ly, lz, sx, sy, sz, tag, mm):
                    wx = loc.x + lx * math.cos(rz) - ly * math.sin(rz)
                    wy = loc.y + lx * math.sin(rz) + ly * math.cos(rz)
                    addbox(nm + tag, sx, sy, sz, wx, wy, lz, rz, mm)

                place(0.0, -L / 2.0 - 0.05, mid - d.z * 0.18, Wd * 0.98, 0.16, d.z * 0.4, "_BumperF", m_metal)
                place(0.0, L / 2.0 + 0.05, mid - d.z * 0.18, Wd * 0.98, 0.16, d.z * 0.4, "_BumperR", m_metal)
                for sgn, tag in ((-1.0, "L"), (1.0, "R")):
                    place(sgn * Wd * 0.3, -L / 2.0 - 0.02, mid + d.z * 0.10,
                          Wd * 0.26, 0.07, d.z * 0.24, "_Head" + tag, m_glass or m_metal)
                    place(sgn * Wd * 0.3, L / 2.0 + 0.02, mid + d.z * 0.10,
                          Wd * 0.26, 0.07, d.z * 0.22, "_Tail" + tag, m_red)
                    place(sgn * (Wd / 2.0 + 0.09), -L * 0.16, mid + d.z * 0.55,
                          0.16, 0.09, 0.09, "_Mirror" + tag, m_metal)
                stats["cars"] += 1

            ob["zy_polished"] = True

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            d2 = {"ok": True, "step": "phase1_3_polish", "filepath": fp}
            d2.update(stats)
            json.dump(d2, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            d2 = {"ok": False, "step": "phase1_3_polish", "error": traceback.format_exc()}
            d2.update(stats)
            json.dump(d2, f, indent=1)

import bpy
bpy.app.timers.register(zy_polish, first_interval=0.1)
