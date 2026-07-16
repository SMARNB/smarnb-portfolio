# Zyvion Phase 1.1 v3 — underground basement, ISOLATED wings, in-footprint stairs.
# User revisions over v2:
#  - No connection between wings: divider is one solid floor-to-ceiling wall.
#  - Stairs live INSIDE the building footprint, carved into the plinth (spacer):
#      West: centered grand staircase (6m wide, full-height portal) into Gym/Pool.
#      East: sidewise 2m staircase along the inside of the east wall into Cafeteria.
#  - Plinth is rebuilt as 5 boxes with the two entry notches; the user's original
#    object is preserved in _Legacy_Backup. Pool moves to the north half (the
#    grand stair owns the centered west approach).
# Listener contract: single wrapper function + bpy.app.timers (main thread only).
# Idempotent: kill-by-name before create; deprecated v1/v2 names removed explicitly.

def zy_build():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/599a7627-7a49-4e5e-bc4f-37f7ddc0fa2f/scratchpad/phase1_1_status.json"
    created = []
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_1v3",
                           "error": "REFUSED: the open file is an autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection

        # ---------- helpers ----------
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

        def mkmat(name, hx, rough=0.85):
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

        def cyl(name, cx, cy, cz, r, h, m, coll, seg=12, rot=None):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, cz)
            if rot is not None:
                ob.rotation_euler = rot
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        def world_bounds_of(ob):
            pts = [ob.matrix_world @ mathutils.Vector(c) for c in ob.bound_box]
            return (min(p.x for p in pts), max(p.x for p in pts),
                    min(p.y for p in pts), max(p.y for p in pts),
                    min(p.z for p in pts), max(p.z for p in pts))

        backup = get_coll("_Legacy_Backup", root, hide=True)

        def retire(ob, new_name):
            for uc in list(ob.users_collection):
                uc.objects.unlink(ob)
            backup.objects.link(ob)
            ob.name = new_name
            ob.hide_viewport = True
            ob.hide_render = True

        # ---------- plinth: measure, retire original, rebuild with 2 notches ----------
        plinth = (bpy.data.objects.get("Building_Plinth")
                  or bpy.data.objects.get("Basement_Level_OLD")
                  or bpy.data.objects.get("Basement_Level"))
        if plinth is not None:
            px0, px1, py0, py1, pz0, pz1 = world_bounds_of(plinth)
            scene["zy_plinth"] = json.dumps({"x0": px0, "x1": px1, "y0": py0, "y1": py1, "z0": pz0, "z1": pz1})
            retire(plinth, "Building_Plinth_ORIGINAL")
        p = json.loads(scene["zy_plinth"])
        SXY = 1.25  # footprint scale: stored ORIGINAL 40x40 -> 50x50 (idempotent: always from stored)
        px0, px1 = p["x0"] * SXY, p["x1"] * SXY
        py0, py1 = p["y0"] * SXY, p["y1"] * SXY
        pz0, pz1 = p["z0"], p["z1"]
        x0, x1, y0, y1 = px0, px1, py0, py1

        # ---------- deprecated v1/v2 objects ----------
        dead = ["Basement_Wall_West_S", "Basement_Wall_West_N", "Basement_Wall_West_Header",
                "Basement_Wall_East_S", "Basement_Wall_East_N", "Basement_Wall_East_Header",
                "Basement_Divider_A", "Basement_Divider_B", "Basement_Divider_C",
                "Basement_Divider_Header_1", "Basement_Divider_Header_2", "Basement_Divider_S",
                "Basement_Divider_N", "Basement_Divider_Header", "Basement_Ceiling",
                "Ground_S", "Ground_N", "Ground_Mid_W", "Ground_Mid_C", "Ground_Mid_E",
                "Basement_Step_West_1", "Basement_Step_West_2", "Basement_Step_East_1", "Basement_Step_East_2",
                "Stairwell_West_Wall_S", "Stairwell_West_Wall_N", "Stairwell_East_Wall_S", "Stairwell_East_Wall_N"]
        for i in range(1, 14):
            dead.append("Stairwell_West_Step_%02d" % i)
            dead.append("Stairwell_East_Step_%02d" % i)
        for n in dead:
            kill(n)

        # ---------- derived layout ----------
        H = 6.1
        z1 = pz0
        z0 = z1 - H
        T = 0.3
        SLAB = 0.35
        CEIL = 0.25
        ft = z0 + SLAB
        cb = z1 - CEIL
        xdiv = x0 + 0.6 * (x1 - x0)
        STREET = 5.41
        drop = STREET - ft
        rise = drop / 14.0
        # west grand stair: centered, 6m wide, portal notch 2m deep, run 7m
        SWY0, SWY1 = -3.0, 3.0
        SWX0 = x0 + 1.4
        SWX1 = SWX0 + 7.0
        WTREAD = 7.0 / 13
        # east cafe stair: portal notch at y -1..1, lane 2m wide along east wall, run 6.3m north
        PEY0, PEY1 = -1.0, 1.0
        SEX0 = x1 - 2.0
        SEY0, SEY1 = 1.0, 7.3
        ETREAD = 6.3 / 13
        # pool moved to north half (grand stair owns the centered west approach)
        PX0, PX1, PY0, PY1 = -21.0, -5.0, 8.0, 16.0
        KX0, KX1, KY0, KY1 = PX0 - 1.5, PX1 + 1.5, PY0 - 1.5, PY1 + 1.5

        # ---------- palette ----------
        m_slab   = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall   = mkmat("ZY_Wall_OffWhite", "#E8E6DF")
        m_div    = mkmat("ZY_Divider_Grey", "#C6C3BB")
        m_gym    = mkmat("ZY_Gym_Floor", "#3F4750")
        m_water  = mkmat("ZY_Pool_Water", "#2E9AD8", rough=0.15)
        m_basin  = mkmat("ZY_Pool_Basin", "#BFE3EE")
        m_deck   = mkmat("ZY_Deck_Grey", "#B9B4A6")
        m_metal  = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_cafe   = mkmat("ZY_Cafe_Floor", "#C9A26B")
        m_wood   = mkmat("ZY_Wood_Warm", "#8A5A33")
        m_red    = mkmat("ZY_Accent_Red", "#D24D3E")
        m_amber  = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_teal   = mkmat("ZY_Accent_Teal", "#2F9E8F")
        m_core   = mkmat("ZY_Core_Marker", "#6C7BD9")
        m_ground = mkmat("ZY_Ground_Grey", "#8E9089")

        # ---------- collections ----------
        base = get_coll("Basement_Level", root)
        shell = get_coll("Basement_Shell", base)
        zoneA = get_coll("Zone_A_Gym_Pool", base)
        zoneB = get_coll("Zone_B_Cafeteria", base)
        site = get_coll("Site_Ground", root)
        plc = get_coll("Building_Plinth", root)

        # ---------- plinth pieces: cutouts span the FULL stair runs so the entries
        # are real walk-in voids (W: x0..-11.6 x -3..3 | E: x1-1.6..x1 x -1..7.3);
        # the 20ft room slabs above (z 9.23) roof both halls ----------
        kill("Plinth_Band_EN")
        rbox("Plinth_S", x0, x1, y0, SWY0, pz0, pz1, m_slab, plc)
        rbox("Plinth_Band_C", SWX1, x1 - 1.6, SWY0, SWY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_Band_ES", x1 - 1.6, x1, SWY0, PEY0, pz0, pz1, m_slab, plc)
        rbox("Plinth_B2_W", x0, x1 - 1.6, SWY1, SEY1, pz0, pz1, m_slab, plc)
        rbox("Plinth_N", x0, x1, SEY1, y1, pz0, pz1, m_slab, plc)

        # ---------- basement floor (4 pieces around pool) ----------
        rbox("Basement_Floor_W", x0, PX0, y0, y1, z0, ft, m_slab, shell)
        rbox("Basement_Floor_E", PX1, x1, y0, y1, z0, ft, m_slab, shell)
        rbox("Basement_Floor_S", PX0, PX1, y0, PY0, z0, ft, m_slab, shell)
        rbox("Basement_Floor_N", PX0, PX1, PY1, y1, z0, ft, m_slab, shell)

        # ---------- ceiling: 6 pieces around the two stair openings ----------
        rbox("Basement_Ceiling_S", x0, x1, y0, SWY0, cb, z1, m_slab, shell)
        rbox("Basement_Ceiling_B1_W", x0, SWX0, SWY0, SWY1, cb, z1, m_slab, shell)
        rbox("Basement_Ceiling_B1_C", SWX1, SEX0, SWY0, SWY1, cb, z1, m_slab, shell)
        rbox("Basement_Ceiling_B1_E", SEX0, x1, SWY0, SEY0, cb, z1, m_slab, shell)
        rbox("Basement_Ceiling_B2_W", x0, SEX0, SWY1, SEY1, cb, z1, m_slab, shell)
        rbox("Basement_Ceiling_N", x0, x1, SEY1, y1, cb, z1, m_slab, shell)

        # ---------- perimeter walls (solid; no side doors anymore) + solid divider ----------
        rbox("Basement_Wall_Front", x0, x1, y0, y0 + T, ft, cb, m_wall, shell)
        rbox("Basement_Wall_Back", x0, x1, y1 - T, y1, ft, cb, m_wall, shell)
        rbox("Basement_Wall_West", x0, x0 + T, y0 + T, y1 - T, ft, cb, m_wall, shell)
        rbox("Basement_Wall_East", x1 - T, x1, y0 + T, y1 - T, ft, cb, m_wall, shell)
        rbox("Basement_Divider", xdiv - 0.125, xdiv + 0.125, y0 + T, y1 - T, ft, cb, m_div, shell)
        rbox("Core_Reserved_Lift_Shaft", -4, 4, -4, 4, ft, ft + 0.06, m_core, shell)

        # ---------- stairs ----------
        for i in range(1, 14):
            top = STREET - i * rise
            wx1 = SWX0 + i * WTREAD
            rbox("Stair_GrandWest_Step_%02d" % i, wx1 - WTREAD, wx1, SWY0, SWY1, ft, top, m_slab, shell)
            ey1 = SEY0 + i * ETREAD
            rbox("Stair_CafeEast_Step_%02d" % i, SEX0, x1, ey1 - ETREAD, ey1, ft, top, m_slab, shell)

        # ---------- ground: 8 pieces around the two stair openings ----------
        gplane = bpy.data.objects.get("Plane")
        if gplane is not None:
            gx0, gx1, gy0, gy1, _, _ = world_bounds_of(gplane)
            scene["zy_ground"] = json.dumps({"x0": gx0, "x1": gx1, "y0": gy0, "y1": gy1})
            retire(gplane, "Plane_OLD")
        g = json.loads(scene["zy_ground"])
        gx0, gx1, gy0, gy1 = g["x0"], g["x1"], g["y0"], g["y1"]
        rbox("Ground_S", gx0, gx1, gy0, SWY0, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B1_W", gx0, SWX0, SWY0, SWY1, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B1_C", SWX1, SEX0, SWY0, SWY1, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B1_E", SEX0, x1, SWY0, SEY0, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B1_EE", x1, gx1, SWY0, SWY1, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B2_W", gx0, SEX0, SWY1, SEY1, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_B2_E", x1, gx1, SWY1, SEY1, STREET - 0.02, STREET, m_ground, site)
        rbox("Ground_N", gx0, gx1, SEY1, gy1, STREET - 0.02, STREET, m_ground, site)

        # ---------- Zone A: pool (north half) ----------
        rbox("ZoneA_Pool_Basin_W", PX0, PX0 + 0.2, PY0, PY1, ft - 1.4, ft, m_basin, zoneA)
        rbox("ZoneA_Pool_Basin_E", PX1 - 0.2, PX1, PY0, PY1, ft - 1.4, ft, m_basin, zoneA)
        rbox("ZoneA_Pool_Basin_S", PX0 + 0.2, PX1 - 0.2, PY0, PY0 + 0.2, ft - 1.4, ft, m_basin, zoneA)
        rbox("ZoneA_Pool_Basin_N", PX0 + 0.2, PX1 - 0.2, PY1 - 0.2, PY1, ft - 1.4, ft, m_basin, zoneA)
        rbox("ZoneA_Pool_Floor", PX0, PX1, PY0, PY1, ft - 1.6, ft - 1.4, m_basin, zoneA)
        rbox("ZoneA_Pool_Water", PX0 + 0.25, PX1 - 0.25, PY0 + 0.25, PY1 - 0.25, ft - 0.41, ft - 0.35, m_water, zoneA)
        rbox("ZoneA_Pool_Lane_1", PX0 + 0.4, PX1 - 0.4, PY0 + 8 / 3 - 0.05, PY0 + 8 / 3 + 0.05, ft - 0.35, ft - 0.29, m_red, zoneA)
        rbox("ZoneA_Pool_Lane_2", PX0 + 0.4, PX1 - 0.4, PY1 - 8 / 3 - 0.05, PY1 - 8 / 3 + 0.05, ft - 0.35, ft - 0.29, m_red, zoneA)
        rbox("ZoneA_Pool_Deck_W", KX0, PX0, KY0, KY1, ft, ft + 0.05, m_deck, zoneA)
        rbox("ZoneA_Pool_Deck_E", PX1, KX1, KY0, KY1, ft, ft + 0.05, m_deck, zoneA)
        rbox("ZoneA_Pool_Deck_S", PX0, PX1, KY0, PY0, ft, ft + 0.05, m_deck, zoneA)
        rbox("ZoneA_Pool_Deck_N", PX0, PX1, PY1, KY1, ft, ft + 0.05, m_deck, zoneA)
        cyl("ZoneA_Pool_Ladder_Rail_1", PX1 - 0.35, PY1 - 0.6, ft + 0.15, 0.035, 1.5, m_metal, zoneA)
        cyl("ZoneA_Pool_Ladder_Rail_2", PX1 - 0.35, PY1 - 1.0, ft + 0.15, 0.035, 1.5, m_metal, zoneA)
        for i, rz in enumerate((ft - 0.3, ft + 0.05, ft + 0.4)):
            cyl("ZoneA_Pool_Ladder_Rung_%d" % (i + 1), PX1 - 0.35, PY1 - 0.8, rz, 0.03, 0.4, m_metal, zoneA, rot=(1.5708, 0, 0))

        # ---------- Zone A: gym floor + equipment (south half) ----------
        rbox("ZoneA_Gym_Floor_1", x0 + T, xdiv - 0.15, y0 + T, KY0, ft, ft + 0.04, m_gym, zoneA)
        rbox("ZoneA_Gym_Floor_2", x0 + T, xdiv - 0.15, KY1, y1 - T, ft, ft + 0.04, m_gym, zoneA)
        rbox("ZoneA_Gym_Floor_3", KX1, xdiv - 0.15, KY0, KY1, ft, ft + 0.04, m_gym, zoneA)
        rbox("ZoneA_Gym_Floor_4", x0 + T, KX0, KY0, KY1, ft, ft + 0.04, m_gym, zoneA)
        for i, tx in enumerate((-17.5, -14.5, -11.5, -8.5)):
            n = i + 1
            rbox("ZoneA_Treadmill_%d_Base" % n, tx - 0.45, tx + 0.45, -22.1, -19.9, ft, ft + 0.22, m_metal, zoneA)
            rbox("ZoneA_Treadmill_%d_Col" % n, tx - 0.06, tx + 0.06, -22.0, -21.88, ft + 0.22, ft + 1.25, m_metal, zoneA)
            rbox("ZoneA_Treadmill_%d_Console" % n, tx - 0.33, tx + 0.33, -22.08, -21.8, ft + 1.25, ft + 1.39, m_red, zoneA)
        rbox("ZoneA_Rack_Shelf_1", -24.6, -24.1, -20.2, -17.8, ft + 0.35, ft + 0.42, m_metal, zoneA)
        rbox("ZoneA_Rack_Shelf_2", -24.6, -24.1, -20.2, -17.8, ft + 0.75, ft + 0.82, m_metal, zoneA)
        rbox("ZoneA_Rack_Side_1", -24.6, -24.1, -20.2, -20.08, ft, ft + 0.9, m_metal, zoneA)
        rbox("ZoneA_Rack_Side_2", -24.6, -24.1, -17.92, -17.8, ft, ft + 0.9, m_metal, zoneA)
        for i, dy in enumerate((-19.8, -19.2, -18.6, -18.0)):
            dz = ft + 0.49 if i % 2 == 0 else ft + 0.89
            cyl("ZoneA_Dumbbell_%d" % (i + 1), -24.35, dy, dz, 0.07, 0.35, m_teal, zoneA, rot=(0, 1.5708, 0))
        rbox("ZoneA_Bench_1", -16.0, -14.5, -15.5, -15.0, ft, ft + 0.48, m_wood, zoneA)
        rbox("ZoneA_Bench_2", -12.5, -11.0, -15.5, -15.0, ft, ft + 0.48, m_wood, zoneA)
        rbox("ZoneA_Mat_1", -4.5, -3.5, -12.0, -10.0, ft + 0.04, ft + 0.075, m_teal, zoneA)
        rbox("ZoneA_Mat_2", -2.9, -1.9, -12.0, -10.0, ft + 0.04, ft + 0.075, m_amber, zoneA)
        rbox("ZoneA_PullupRig_Post_1", 0.45, 0.55, 21.45, 21.55, ft, ft + 2.2, m_metal, zoneA)
        rbox("ZoneA_PullupRig_Post_2", 2.45, 2.55, 21.45, 21.55, ft, ft + 2.2, m_metal, zoneA)
        cyl("ZoneA_PullupRig_Bar", 1.5, 21.5, ft + 2.15, 0.03, 2.0, m_metal, zoneA, rot=(0, 1.5708, 0))

        # ---------- Zone B: cafeteria ----------
        rbox("ZoneB_Cafe_Floor", xdiv + 0.15, x1 - T, y0 + T, y1 - T, ft, ft + 0.04, m_cafe, zoneB)
        accents = (m_red, m_amber, m_teal)
        for i, sx in enumerate((10.0, 14.5, 19.0)):
            n = i + 1
            acc = accents[i]
            rbox("ZoneB_Stall_%d_Counter" % n, sx - 1.7, sx + 1.7, 21.6, 22.7, ft, ft + 1.05, acc, zoneB)
            rbox("ZoneB_Stall_%d_CounterTop" % n, sx - 1.8, sx + 1.8, 21.5, 22.8, ft + 1.05, ft + 1.13, m_wood, zoneB)
            rbox("ZoneB_Stall_%d_Panel" % n, sx - 1.7, sx + 1.7, 24.4, 24.55, ft, ft + 2.4, acc, zoneB)
            rbox("ZoneB_Stall_%d_Sign" % n, sx - 1.3, sx + 1.3, 24.3, 24.4, ft + 1.7, ft + 2.2, m_wood, zoneB)
        for i, (tx, ty) in enumerate(((10, -3), (15, 2), (20, -5), (11, 7))):
            n = i + 1
            cyl("ZoneB_RoundTable_%d_Top" % n, tx, ty, ft + 0.75, 0.65, 0.06, m_wood, zoneB, seg=16)
            cyl("ZoneB_RoundTable_%d_Leg" % n, tx, ty, ft + 0.37, 0.08, 0.74, m_metal, zoneB)
            for j, ang in enumerate((0.0, 2.094, 4.189)):
                sxp = tx + 1.05 * math.cos(ang)
                syp = ty + 1.05 * math.sin(ang)
                cyl("ZoneB_Stool_%d_%d" % (n, j + 1), sxp, syp, ft + 0.225, 0.22, 0.45, m_teal, zoneB)
        for i, lx in enumerate((12, 18)):
            n = i + 1
            rbox("ZoneB_LongTable_%d_Top" % n, lx - 1.4, lx + 1.4, 15.05, 15.95, ft + 0.72, ft + 0.8, m_wood, zoneB)
            rbox("ZoneB_LongTable_%d_Leg_1" % n, lx - 1.3, lx - 1.15, 15.15, 15.85, ft, ft + 0.72, m_metal, zoneB)
            rbox("ZoneB_LongTable_%d_Leg_2" % n, lx + 1.15, lx + 1.3, 15.15, 15.85, ft, ft + 0.72, m_metal, zoneB)
            rbox("ZoneB_LongBench_%d_1" % n, lx - 1.4, lx + 1.4, 14.35, 14.7, ft, ft + 0.45, m_wood, zoneB)
            rbox("ZoneB_LongBench_%d_2" % n, lx - 1.4, lx + 1.4, 16.3, 16.65, ft, ft + 0.45, m_wood, zoneB)
        cyl("ZoneB_Bin_1", x1 - 0.9, -7.6, ft + 0.4, 0.3, 0.8, m_metal, zoneB)
        cyl("ZoneB_Bin_2", x1 - 0.9, -12.4, ft + 0.4, 0.3, 0.8, m_metal, zoneB)

        # ---------- tower re-stack (idempotent absolute transforms) ----------
        rooms = ("Waiting_Area", "HR_Department", "Cubicle_Workspace", "Manager_Offices", "Recruitment_Area")
        restacked = 0
        for k in range(8):
            suffix = "" if k == 0 else ".%03d" % k
            zc = pz1 + k * H + H / 2
            for rname in rooms:
                ob = bpy.data.objects.get(rname + suffix)
                if ob is not None:
                    d = ob.dimensions
                    nx = 12.5 if d.x < 18.0 else 25.0   # 10m rooms -> 12.5, 20m -> 25 (idempotent)
                    ob.dimensions = (nx, 25.0, H)
                    lx = ob.location.x
                    ob.location.x = 0.0 if abs(lx) < 7.5 else (18.75 if lx > 0 else -18.75)
                    ob.location.y = 12.5 if ob.location.y > 0 else -12.5
                    ob.location.z = zc
                    restacked += 1
        lobby = bpy.data.objects.get("Grand_Lobby_4_Story")
        if lobby is not None:
            lobby.dimensions = (25.0, 25.0, 4 * H)
            lobby.location.x = 0.0
            lobby.location.y = -12.5
            lobby.location.z = pz1 + 2 * H
            restacked += 1
        # entrance stairs: widths/positions are ORIGINAL values * SXY (idempotent)
        stair_spec = ((20.0, -20.48), (21.93, -20.98), (23.76, -21.48), (25.09, -21.98),
                      (26.69, -22.48), (28.63, -22.98), (31.49, -23.48), (33.4, -23.98),
                      (34.89, -24.48), (37.26, -24.98))
        for i, (w, sy) in enumerate(stair_spec):
            ob = bpy.data.objects.get("Entrance_Stairs_%d" % (i + 1))
            if ob is not None:
                d = ob.dimensions
                ob.dimensions = (w * SXY, d.y, d.z)
                ob.location.y = sy * SXY
                restacked += 1
        # guard house gets a 20 ft ceiling too (bottom stays on the ground at z 5.3)
        guard = bpy.data.objects.get("Enternace_Area")
        if guard is not None:
            d = guard.dimensions
            guard.dimensions = (d.x, d.y, H)
            guard.location.z = 5.3 + H / 2
            restacked += 1

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_1v3", "created": len(created), "restacked": restacked,
                       "basement_z": [round(z0, 2), round(z1, 2)], "floor_top": round(ft, 3),
                       "west_stair": [SWX0, SWX1, SWY0, SWY1], "east_stair": [SEX0, x1, SEY0, SEY1],
                       "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_1v3", "created": len(created),
                       "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_build, first_interval=0.1)
