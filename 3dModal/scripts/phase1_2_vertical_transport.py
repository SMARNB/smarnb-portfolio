# Zyvion Phase 1.2 — vertical transport: glass panoramic lift + switchback stairs.
# Core: 8x8 at x -4..4, y 1..9 (inside the Cubicle_Workspace column on every level,
# clear of the Grand Lobby). Serves the GYM WING ONLY in the basement (wings stay
# isolated) and every tower level up to floor .007.
# Pipeline order: run phase1_1_basement_split.py first; this script re-splits the
# plinth and basement ceiling around the shaft and carves the 8 Cubicle rooms into
# ring pieces (originals retired to _Legacy_Backup).
# Listener contract: single wrapper + bpy.app.timers (main thread); idempotent.

def zy_transport():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/599a7627-7a49-4e5e-bc4f-37f7ddc0fa2f/scratchpad/phase1_2_status.json"
    created = []
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_2", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection

        def get_coll(name, parent, hide=False):
            c = bpy.data.collections.get(name)
            if c is None:
                c = bpy.data.collections.new(name)
            if all(ch.name != c.name for ch in parent.children):
                try:
                    parent.children.link(c)
                except Exception:
                    pass
            if hide:
                c.hide_viewport = True
                c.hide_render = True
            return c

        def kill(name):
            ob = bpy.data.objects.get(name)
            if ob is not None:
                me = ob.data if ob.type == "MESH" else None
                bpy.data.objects.remove(ob, do_unlink=True)
                if me is not None and me.users == 0:
                    bpy.data.meshes.remove(me)

        def hexrgba(h):
            h = h.lstrip("#")
            return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)

        def mkmat(name, hx, rough=0.85, alpha=1.0):
            m = bpy.data.materials.get(name)
            if m is None:
                m = bpy.data.materials.new(name)
            m.use_nodes = True
            bsdf = None
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    bsdf = n
                    break
            rgba = hexrgba(hx)
            if bsdf is not None:
                bsdf.inputs["Base Color"].default_value = rgba
                bsdf.inputs["Roughness"].default_value = rough
                try:
                    bsdf.inputs["Alpha"].default_value = alpha
                except Exception:
                    pass
            if alpha < 1.0:
                for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
                    try:
                        setattr(m, attr, val)
                    except Exception:
                        pass
                rgba = (rgba[0], rgba[1], rgba[2], alpha)
            m.diffuse_color = rgba
            return m

        def rbox(name, ax0, ax1, ay0, ay1, az0, az1, m, coll):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= (ax1 - ax0)
                v.co.y *= (ay1 - ay0)
                v.co.z *= (az1 - az0)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = ((ax0 + ax1) / 2, (ay0 + ay1) / 2, (az0 + az1) / 2)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        backup = get_coll("_Legacy_Backup", root, hide=True)

        def retire(ob, new_name):
            for uc in list(ob.users_collection):
                uc.objects.unlink(ob)
            backup.objects.link(ob)
            ob.name = new_name
            ob.hide_viewport = True
            ob.hide_render = True

        # ---------- shared layout (mirrors phase1_1 v4) ----------
        p = json.loads(scene["zy_plinth"])
        SXY = 2.5  # must match phase1_1
        x0, x1 = p["x0"] * SXY, p["x1"] * SXY
        y0, y1 = p["y0"] * SXY, p["y1"] * SXY
        pz0, pz1 = p["z0"], p["z1"]
        H = 6.1
        z1b = pz0
        z0b = z1b - H
        SLAB = 0.35
        CEIL = 0.25
        ft = z0b + SLAB
        cb = z1b - CEIL
        TOP = pz1 + 8 * H                     # 58.03: top of floor .007
        SWX1 = (x0 + 1.4) + 7.0               # west grand-stair hole east edge (-16.6)
        SEX0 = x1 - 2.0                       # east stair lane west edge (23)
        SEY0, SEY1 = 1.0, 7.3
        CX0, CX1, CY0, CY1 = -4.0, 4.0, 1.0, 9.0   # the vertical core

        m_slab  = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")

        core = get_coll("Vertical_Core", root)

        # ---------- re-split plinth around W notch, E notch and the core ----------
        for n in ("Plinth_S", "Plinth_N", "Plinth_Band_C", "Plinth_Band_ES", "Plinth_B2_W", "Plinth_Band_EN"):
            kill(n)
        plc = get_coll("Building_Plinth", root)
        rbox("Plinth_S", x0, x1, y0, -3.0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B1", -16.6, x1, -3.0, -1.0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B2", -16.6, 23.4, -1.0, CY0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B3a", -16.6, CX0, CY0, 3.0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B3b", CX1, 23.4, CY0, 3.0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B4a", x0, CX0, 3.0, SEY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_B4b", CX1, 23.4, 3.0, SEY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_B5a", x0, CX0, SEY1, CY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_B5b", CX1, x1, SEY1, CY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_N", x0, x1, CY1, y1, pz0, pz1, m_slab, plc)

        # ---------- re-split basement ceiling around both stairs and the core ----------
        for n in ("Basement_Ceiling_S", "Basement_Ceiling_B1_W", "Basement_Ceiling_B1_C",
                  "Basement_Ceiling_B1_E", "Basement_Ceiling_B2_W", "Basement_Ceiling_N",
                  "Core_Reserved_Lift_Shaft"):
            kill(n)
        shell = get_coll("Basement_Shell", get_coll("Basement_Level", root))
        SWX0 = x0 + 1.4
        rbox("Basement_Ceiling_S", x0, x1, y0, -3.0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B1a", x0, SWX0, -3.0, CY0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B1b", SWX1, x1, -3.0, CY0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B2a", x0, SWX0, CY0, 3.0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B2b", SWX1, CX0, CY0, 3.0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B2c", CX1, SEX0, CY0, 3.0, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B3a", x0, CX0, 3.0, SEY1, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B3b", CX1, SEX0, 3.0, SEY1, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B4a", x0, CX0, SEY1, CY1, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_B4b", CX1, x1, SEY1, CY1, cb, z1b, m_slab, shell)
        rbox("Basement_Ceiling_N", x0, x1, CY1, y1, cb, z1b, m_slab, shell)

        # ---------- carve the 8 Cubicle_Workspace levels into ring pieces ----------
        retired = 0
        for k in range(8):
            suffix = "" if k == 0 else ".%03d" % k
            ob = bpy.data.objects.get("Cubicle_Workspace" + suffix)
            zb = pz1 + k * H
            if ob is not None:
                retire(ob, "Cubicle_Workspace_ORIG_L%d" % k)
                retired += 1
            RW = 10.0 * SXY   # Cubicle room: 20*SXY wide centered on x=0, y 0..20*SXY
            RD = 20.0 * SXY
            rbox("Cubicle_Workspace_L%d_W" % k, -RW, CX0, 0.0, RD, zb, zb + H, m_slab, core)
            rbox("Cubicle_Workspace_L%d_E" % k, CX1, RW, 0.0, RD, zb, zb + H, m_slab, core)
            rbox("Cubicle_Workspace_L%d_S" % k, CX0, CX1, 0.0, CY0, zb, zb + H, m_slab, core)
            rbox("Cubicle_Workspace_L%d_N" % k, CX0, CX1, CY1, RD, zb, zb + H, m_slab, core)

        # ---------- glass shaft centered in the core (W/E/N glass; south face =
        # door frames per level, opening onto the wrap-stair landing) ----------
        SH_X0, SH_X1, SH_Y0, SH_Y1 = -1.8, 1.8, 3.2, 6.8
        rbox("Lift_Shaft_Glass_W", SH_X0, SH_X0 + 0.15, SH_Y0, SH_Y1, ft, TOP, m_glass, core)
        rbox("Lift_Shaft_Glass_E", SH_X1 - 0.15, SH_X1, SH_Y0, SH_Y1, ft, TOP, m_glass, core)
        rbox("Lift_Shaft_Glass_N", SH_X0, SH_X1, SH_Y1 - 0.15, SH_Y1, ft, TOP, m_glass, core)
        levels = [ft] + [pz1 + k * H for k in range(8)]
        for li, lz in enumerate(levels):
            rbox("Lift_Door_%d_Jamb_W" % li, -1.0, -0.8, SH_Y0, SH_Y0 + 0.15, lz, lz + 2.4, m_metal, core)
            rbox("Lift_Door_%d_Jamb_E" % li, 0.8, 1.0, SH_Y0, SH_Y0 + 0.15, lz, lz + 2.4, m_metal, core)
            rbox("Lift_Door_%d_Header" % li, -1.0, 1.0, SH_Y0, SH_Y0 + 0.15, lz + 2.4, lz + 2.6, m_metal, core)
        # panoramic cab parked in the basement (gym wing)
        rbox("Lift_Cab_Floor", -1.55, 1.55, SH_Y0 + 0.25, SH_Y1 - 0.25, ft, ft + 0.15, m_metal, core)
        rbox("Lift_Cab_Glass_W", -1.55, -1.4, SH_Y0 + 0.25, SH_Y1 - 0.25, ft + 0.15, ft + 2.4, m_glass, core)
        rbox("Lift_Cab_Glass_E", 1.4, 1.55, SH_Y0 + 0.25, SH_Y1 - 0.25, ft + 0.15, ft + 2.4, m_glass, core)
        rbox("Lift_Cab_Glass_N", -1.55, 1.55, SH_Y1 - 0.4, SH_Y1 - 0.25, ft + 0.15, ft + 2.4, m_glass, core)
        rbox("Lift_Cab_Roof", -1.55, 1.55, SH_Y0 + 0.25, SH_Y1 - 0.25, ft + 2.4, ft + 2.55, m_metal, core)

        # ---------- wrap stairs: square helix around the shaft. Flat landing at
        # the lift door (south) on every floor, then E -> N -> W flights climb
        # one level and arrive at the next floor's landing ----------
        for n in [o.name for o in bpy.data.objects if o.name.startswith("Core_Stair_")]:
            kill(n)

        def flight(prefix, axis, a0, a1, band0, band1, zf0, zf1):
            ns = max(4, int(math.ceil(abs(zf1 - zf0) / 0.34)))
            for i in range(1, ns + 1):
                zt = zf0 + i * ((zf1 - zf0) / ns)
                t0 = a0 + (i - 1) * ((a1 - a0) / ns)
                t1 = a0 + i * ((a1 - a0) / ns)
                lo, hi = min(t0, t1), max(t0, t1)
                if axis == "x":
                    rbox("%s_%02d" % (prefix, i), lo, hi, band0, band1, zt - 0.15, zt, m_slab, core)
                else:
                    rbox("%s_%02d" % (prefix, i), band0, band1, lo, hi, zt - 0.15, zt, m_slab, core)

        transitions = [(ft, pz1)] + [(pz1 + k * H, pz1 + (k + 1) * H) for k in range(7)]
        for t, (za, zb2) in enumerate(transitions):
            r3 = (zb2 - za) / 3.0
            rbox("Core_Stair_T%d_LandS" % t, -2.6, 2.6, CY0, SH_Y0, za - 0.15, za, m_amber, core)
            rbox("Core_Stair_T%d_CornSE" % t, 2.6, CX1, CY0, 2.4, za - 0.15, za, m_slab, core)
            flight("Core_Stair_T%d_E" % t, "y", 2.4, 7.6, 2.6, CX1, za, za + r3)
            rbox("Core_Stair_T%d_CornNE" % t, 2.6, CX1, 7.6, CY1, za + r3 - 0.15, za + r3, m_slab, core)
            flight("Core_Stair_T%d_N" % t, "x", 2.6, -2.6, 7.6, CY1, za + r3, za + 2 * r3)
            rbox("Core_Stair_T%d_CornNW" % t, CX0, -2.6, 7.6, CY1, za + 2 * r3 - 0.15, za + 2 * r3, m_slab, core)
            flight("Core_Stair_T%d_W" % t, "y", 7.6, 2.4, CX0, -2.6, za + 2 * r3, zb2)
        rbox("Core_Stair_Top_LandS", -2.6, 2.6, CY0, SH_Y0, pz1 + 7 * H - 0.15, pz1 + 7 * H, m_amber, core)

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_2", "created": len(created),
                       "retired_cubicles": retired, "core": [CX0, CX1, CY0, CY1],
                       "top": TOP, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_2", "created": len(created),
                       "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_transport, first_interval=0.1)
