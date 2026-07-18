# Zyvion Phase 1.3d — EAST WING: HR Department fit-out (level 1) + rear stair
# shaft connecting all 8 wing levels (user spec 2026-07-17):
#   - Hollows HR_Department L1 (x 25..50, y -50..0, z 9.23..15.33): finish
#     floor, front/side window-band facades.
#   - Central walk-in corridor (y -29.5..-25.5) divides the floor FROM THE
#     MIDDLE: HIGHER-position offices south (4 mini personal offices for HR
#     heads along the front glass + assistant zone), LOWER-position section
#     north (6 cubicles + 2 personal offices). The corridor runs Grand Lobby
#     (doorway in Lobby_Wall_E) -> east facade EXIT door with an exterior
#     stair descending NORTH to grade toward the cafeteria stair lane.
#   - Upper levels (HR_Department.001-.007) retired and rebuilt as SOLID
#     massing (the building staircases live in the REAR blocks per user
#     markup — see phase1_3_rear_blocks.py). Lobby_Wall_E carries only the
#     L1 corridor opening, framed in amber.
#   - Wing services: corridor duct spine + branches + diffusers, cable tray
#     with amber/teal/red runs, drops, wall panel (item 5).
# Requires scene["zy_plinth"] + scene["zy_lobby"].
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# "EWing_" + "Lobby_Wall_E" prefix sweeps. Order: ... -> west_wing -> THIS.

def zy_east_wing():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_east_status.json"
    created = []
    groups = {"shell": 0, "corridor": 0, "heads": 0, "lower": 0, "shaft": 0, "services": 0, "exit": 0}
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_east_wing", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        for key in ("zy_plinth", "zy_lobby"):
            if key not in scene.keys():
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump({"ok": False, "step": "phase1_3_east_wing",
                               "error": "scene['%s'] missing - run earlier pipeline scripts first" % key}, f, indent=1)
                return

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

        def rcylz(name, r, z0, z1, cx, cy, m, coll, seg=12):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r, radius2=r, depth=z1 - z0)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, (z0 + z1) / 2)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        def rcyl_ax(name, r, length, center, axis, m, coll, seg=12):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r, radius2=r, depth=length)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = center
            ob.rotation_euler = (0.0, math.pi / 2, 0.0) if axis == "x" else (math.pi / 2, 0.0, 0.0)
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

        # ---------- layout ----------
        p = json.loads(scene["zy_plinth"])
        lb = json.loads(scene["zy_lobby"])
        H = 6.1
        LZ0 = p["z1"]
        FT = LZ0 + 0.15
        CT = LZ0 + H
        EX0, EX1 = 25.0, 50.0
        WY0, WY1 = -50.0, 0.0
        GZ = 5.41
        SX0, SX1, SY0, SY1 = 25.5, 31.5, -6.5, -0.5      # front stair shaft
        MZ = lb["mezz_z"]                                # [15.33, 21.43, 27.53]
        MDY0, MDY1 = -5.0, -2.0                          # mezz doorway span
        CY0, CY1 = -29.5, -25.5                          # central corridor
        DGX0, DGX1 = 37.0, 40.0                          # corridor wall door gaps

        m_slab  = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall  = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_teal  = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_red   = mkmat("ZY_Accent_Red", "#C04848")
        m_wood  = mkmat("ZY_Wood_Warm", "#8C6748")
        m_grey  = mkmat("ZY_Divider_Grey", "#6E6E68")
        m_floor = mkmat("ZY_Lobby_Floor", "#CDC9C0", rough=0.55)
        m_duct  = mkmat("ZY_Duct_Silver", "#AEB6BD", rough=0.35)
        m_couch = mkmat("ZY_Couch_Charcoal", "#3A3F46", rough=0.95)

        wing = get_coll("Wing_East_HR", root)
        core = get_coll("Wing_East_Stairs", root)

        # ---------- idempotency sweep + retire originals ----------
        for n in [o.name for o in bpy.data.objects
                  if o.name.startswith("EWing_") or o.name.startswith("Lobby_Wall_E")]:
            kill(n)
        retired = []
        ob = bpy.data.objects.get("HR_Department")
        if ob is not None:
            retire(ob, "HR_Department_ORIGINAL")
            retired.append("HR_Department")
        for k in range(1, 8):
            ob = bpy.data.objects.get("HR_Department.%03d" % k)
            if ob is not None:
                retire(ob, "HR_Department_ORIG_L%d" % (k + 1))
                retired.append("HR_Department.%03d" % k)

        # ---------- upper stack: solid massing (stairs live in the rear blocks) ----------
        n0 = len(created)
        for k in range(2, 9):
            zb = LZ0 + (k - 1) * H
            rbox("EWing_Stack_L%d" % k, EX0, EX1, WY0, WY1, zb, zb + H, m_slab, wing)
        groups["shell"] += len(created) - n0

        # ---------- lobby east wall re-split: corridor opening + amber frame ----------
        n0 = len(created)
        LEx0, LEx1 = 24.5, 25.0
        LT = lb["z1"]
        rbox("Lobby_Wall_E_A", LEx0, LEx1, -49.5, CY0, LZ0, LT, m_wall, wing)
        rbox("Lobby_Wall_E_BH", LEx0, LEx1, CY0, CY1, LZ0 + 3.5, LT, m_wall, wing)
        rbox("Lobby_Wall_E_C", LEx0, LEx1, CY1, MDY0, LZ0, LT, m_wall, wing)
        rbox("Lobby_Wall_E_D1", LEx0, LEx1, MDY0, MDY1, LZ0, MZ[0], m_wall, wing)
        rbox("Lobby_Wall_E_D2", LEx0, LEx1, MDY0, MDY1, MZ[0] + 3.0, MZ[1], m_wall, wing)
        rbox("Lobby_Wall_E_D3", LEx0, LEx1, MDY0, MDY1, MZ[1] + 3.0, MZ[2], m_wall, wing)
        rbox("Lobby_Wall_E_D4", LEx0, LEx1, MDY0, MDY1, MZ[2] + 3.0, LT, m_wall, wing)
        rbox("Lobby_Wall_E_E", LEx0, LEx1, MDY1, -0.5, LZ0, LT, m_wall, wing)
        rbox("EWing_LDoor_JambS", LEx0 - 0.12, LEx1 + 0.12, CY0 - 0.3, CY0, LZ0, LZ0 + 3.7, m_amber, wing)
        rbox("EWing_LDoor_JambN", LEx0 - 0.12, LEx1 + 0.12, CY1, CY1 + 0.3, LZ0, LZ0 + 3.7, m_amber, wing)
        rbox("EWing_LDoor_Head", LEx0 - 0.12, LEx1 + 0.12, CY0 - 0.3, CY1 + 0.3, LZ0 + 3.5, LZ0 + 3.85, m_amber, wing)
        groups["shell"] += len(created) - n0

        # ---------- level-1 shell: floor, facades, corridor exit door ----------
        n0 = len(created)
        rbox("EWing_Floor", EX0, EX1 - 0.5, WY0 + 0.5, WY1 - 0.5, LZ0, FT, m_floor, wing)
        rbox("EWing_Wall_S_Sill", EX0, EX1, WY0, WY0 + 0.5, LZ0, 10.4, m_wall, wing)
        rbox("EWing_Wall_S_Glass", EX0, EX1, WY0 + 0.1, WY0 + 0.35, 10.4, 13.4, m_glass, wing)
        rbox("EWing_Wall_S_Hdr", EX0, EX1, WY0, WY0 + 0.5, 13.4, CT, m_wall, wing)
        for tag, y0, y1 in (("S", WY0 + 0.5, -29.0), ("N", -26.0, -0.5)):
            rbox("EWing_Wall_E_Sill_%s" % tag, EX1 - 0.5, EX1, y0, y1, LZ0, 10.4, m_wall, wing)
            rbox("EWing_Wall_E_Glass_%s" % tag, EX1 - 0.35, EX1 - 0.1, y0, y1, 10.4, 13.4, m_glass, wing)
            rbox("EWing_Wall_E_Hdr_%s" % tag, EX1 - 0.5, EX1, y0, y1, 13.4, CT, m_wall, wing)
        rbox("EWing_Wall_E_DoorHdr", EX1 - 0.5, EX1, -29.0, -26.0, LZ0 + 3.0, CT, m_wall, wing)
        rbox("EWing_Door_JambS", EX1 - 0.6, EX1 + 0.15, -29.3, -29.0, LZ0, LZ0 + 3.2, m_metal, wing)
        rbox("EWing_Door_JambN", EX1 - 0.6, EX1 + 0.15, -26.0, -25.7, LZ0, LZ0 + 3.2, m_metal, wing)
        rbox("EWing_Door_Head", EX1 - 0.6, EX1 + 0.15, -29.3, -25.7, LZ0 + 3.0, LZ0 + 3.35, m_metal, wing)
        rbox("EWing_Wall_N", EX0, EX1, WY1 - 0.5, WY1, LZ0, CT, m_wall, wing)
        rbox("EWing_Shaft_W1", EX0, SX0, SY0, SY1, LZ0, CT, m_wall, wing)
        groups["shell"] += len(created) - n0

        # ---------- RESTORED front stair shaft: L1 walls + dog-leg to the ROOF ----------
        n0 = len(created)
        rbox("EWing_Shaft_E1", SX1 - 0.5, SX1, SY0, SY1, LZ0, CT, m_wall, core)
        rbox("EWing_Shaft_S1a", SX0, 27.0, SY0, SY0 + 0.5, LZ0, CT, m_wall, core)
        rbox("EWing_Shaft_S1b", 29.0, SX1 - 0.5, SY0, SY0 + 0.5, LZ0, CT, m_wall, core)
        rbox("EWing_Shaft_S1Hdr", 27.0, 29.0, SY0, SY0 + 0.5, LZ0 + 3.0, CT, m_wall, core)

        def stepsx(prefix, xa, xb, y0, y1, za, zb):
            ns = 8
            for i in range(1, ns + 1):
                zt = za + i * (zb - za) / ns
                t0 = xa + (i - 1) * (xb - xa) / ns
                t1 = xa + i * (xb - xa) / ns
                lo, hi = min(t0, t1), max(t0, t1)
                rbox("%s_%02d" % (prefix, i), lo, hi, y0, y1, zt - 0.15, zt, m_slab, core)

        for k in range(1, 9):               # 8 transitions: L1..L8 then roof
            za = LZ0 + (k - 1) * H
            zb = za + H
            stepsx("EWing_Stair_T%d_A" % k, 26.4, 29.5, -6.0, -4.4, za, za + H / 2)
            rbox("EWing_Stair_T%d_Land" % k, 29.5, 31.0, -6.0, -0.5,
                 za + H / 2 - 0.15, za + H / 2, m_amber, core)
            stepsx("EWing_Stair_T%d_B" % k, 29.5, 26.4, -2.1, -0.5, za + H / 2, zb)
        for k in range(2, 10):              # level platforms L2..L8 + roof (P9)
            zk = LZ0 + (k - 1) * H
            rbox("EWing_Stair_P%d" % k, SX0, 26.4, -6.0, -0.5, zk - 0.15, zk, m_amber, core)
        groups["shaft"] = len(created) - n0

        # ---------- central walk-in corridor walls (division from the middle) ----------
        n0 = len(created)
        rbox("EWing_Corr_Wall_S1", EX0, DGX0, CY0 - 0.3, CY0, LZ0, CT, m_wall, wing)
        rbox("EWing_Corr_Wall_SHdr", DGX0, DGX1, CY0 - 0.3, CY0, LZ0 + 3.0, CT, m_wall, wing)
        rbox("EWing_Corr_Wall_S2", DGX1, EX1 - 0.5, CY0 - 0.3, CY0, LZ0, CT, m_wall, wing)
        rbox("EWing_Corr_Wall_N1", EX0, DGX0, CY1, CY1 + 0.3, LZ0, CT, m_wall, wing)
        rbox("EWing_Corr_Wall_NHdr", DGX0, DGX1, CY1, CY1 + 0.3, LZ0 + 3.0, CT, m_wall, wing)
        rbox("EWing_Corr_Wall_N2", DGX1, EX1 - 0.5, CY1, CY1 + 0.3, LZ0, CT, m_wall, wing)
        groups["corridor"] = len(created) - n0

        # ---------- HIGHER offices (south of corridor): 4 head offices ----------
        n0 = len(created)
        parts = ((31.4, 31.7), (37.1, 37.4), (42.8, 43.1))
        for pi, (px0, px1) in enumerate(parts):
            rbox("EWing_Off_Part_%d" % (pi + 1), px0, px1, -49.5, -43.2, LZ0, 13.2, m_wall, wing)
        cells = ((26.0, 31.4), (31.7, 37.1), (37.4, 42.8), (43.1, 48.7))
        for oi, (ox0, ox1) in enumerate(cells):
            pre = "EWing_Off_%d" % (oi + 1)
            gx1 = ox1 - 0.5
            gx0 = gx1 - 1.4
            rbox(pre + "_Front", ox0, gx0, -43.5, -43.2, LZ0, 13.2, m_wall, wing)
            rbox(pre + "_FrontHdr", gx0, gx1, -43.5, -43.2, LZ0 + 3.0, 13.2, m_wall, wing)
            rbox(pre + "_FrontCap", gx1, ox1, -43.5, -43.2, LZ0, 13.2, m_wall, wing)
            cx = (ox0 + ox1) / 2
            rbox(pre + "_Desk", cx - 1.0, cx + 1.0, -48.4, -47.5, LZ0, 10.05, m_wood, wing)
            rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, cx, -46.9, m_couch, wing)
            rbox(pre + "_Cab", ox1 - 1.2, ox1 - 0.4, -44.3, -43.8, LZ0, 10.4, m_grey, wing)
        for ai, ax in enumerate((33.0, 41.0)):
            rbox("EWing_Asst_Desk_%d" % (ai + 1), ax - 1.2, ax + 1.2, -34.0, -33.1, LZ0, 10.05, m_wood, wing)
            rcylz("EWing_Asst_Chair_%d" % (ai + 1), 0.32, FT, FT + 0.55, ax, -32.5, m_couch, wing)
        rcylz("EWing_Meet_Table", 1.3, FT, FT + 0.75, 28.5, -35.0, m_wood, wing)
        groups["heads"] = len(created) - n0

        # ---------- LOWER section (north of corridor): 6 cubicles + 2 offices ----------
        n0 = len(created)
        slots = [(sx, sy) for sy in (-22.0, -14.0) for sx in (27.0, 32.4, 37.8)]
        for ci, (sx, sy) in enumerate(slots):
            pre = "EWing_Cub_%d" % (ci + 1)
            rbox(pre + "_PartN", sx, sx + 4.4, sy + 5.92, sy + 6.0, LZ0, 10.9, m_grey, wing)
            rbox(pre + "_PartW", sx, sx + 0.08, sy, sy + 6.0, LZ0, 10.9, m_grey, wing)
            rbox(pre + "_Desk", sx + 0.6, sx + 3.6, sy + 4.6, sy + 5.4, LZ0, 10.05, m_wood, wing)
            rbox(pre + "_Mon", sx + 1.7, sx + 2.3, sy + 5.0, sy + 5.08, 10.05, 10.5, m_metal, wing)
            rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, sx + 2.1, sy + 3.9, m_couch, wing)
        for oi, (ox0, ox1) in enumerate(((33.0, 38.0), (38.3, 43.3))):
            pre = "EWing_NOff_%d" % (oi + 1)
            gx1 = ox1 - 0.5
            gx0 = gx1 - 1.2
            rbox(pre + "_Front", ox0, gx0, -6.5, -6.2, LZ0, 13.2, m_wall, wing)
            rbox(pre + "_FrontHdr", gx0, gx1, -6.5, -6.2, LZ0 + 3.0, 13.2, m_wall, wing)
            rbox(pre + "_FrontCap", gx1, ox1, -6.5, -6.2, LZ0, 13.2, m_wall, wing)
            cx = (ox0 + ox1) / 2
            rbox(pre + "_Desk", cx - 1.0, cx + 1.0, -1.6, -0.8, LZ0, 10.05, m_wood, wing)
            rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, cx, -2.3, m_couch, wing)
        rbox("EWing_NOff_Part", 38.0, 38.3, -6.5, -0.5, LZ0, 13.2, m_wall, wing)
        rbox("EWing_NOff_CapE", 43.3, 43.6, -6.5, -0.5, LZ0, 13.2, m_wall, wing)
        groups["lower"] = len(created) - n0

        # ---------- wing services: corridor spine + branches + tray ----------
        n0 = len(created)
        rcyl_ax("EWing_Svc_Duct_Main", 0.35, 23.0, (37.5, -27.5, 14.55), "x", m_duct, wing)
        rcyl_ax("EWing_Svc_Duct_BrN", 0.35, 19.5, (35.0, -17.75, 14.55), "y", m_duct, wing)
        rcyl_ax("EWing_Svc_Duct_BrS", 0.35, 18.5, (35.0, -36.75, 14.55), "y", m_duct, wing)
        for di, (px, py) in enumerate(((30.0, -27.5), (44.0, -27.5), (35.0, -12.0),
                                       (35.0, -34.0), (35.0, -45.0))):
            rcylz("EWing_Svc_Diff_%d_Stub" % (di + 1), 0.24, 13.75, 14.35, px, py, m_duct, wing)
            rcylz("EWing_Svc_Diff_%d_Plate" % (di + 1), 0.5, 13.63, 13.75, px, py, m_duct, wing)
        rbox("EWing_Svc_Tray", 26.0, 49.0, -26.85, -26.35, 13.95, 14.05, m_metal, wing)
        for bname, bm_, off in (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14)):
            rbox("EWing_Svc_Run_%s" % bname, 26.0, 49.0,
                 -26.6 + off - 0.045, -26.6 + off + 0.045, 14.05, 14.12, bm_, wing)
        for dn, dx, dz0 in (("N1_P", 30.0, 10.9), ("N1_D", 30.3, 10.9),
                            ("N2_P", 42.0, 10.9), ("N2_D", 42.3, 10.9)):
            mm = m_amber if dn.endswith("_P") else m_teal
            rbox("EWing_Svc_Drop_%s" % dn, dx - 0.04, dx + 0.04, -26.64, -26.56, dz0, 13.95, mm, wing)
        rbox("EWing_Svc_Panel", 47.6, 48.8, -25.65, -25.5, FT + 0.15, FT + 1.95, m_metal, wing)
        groups["services"] = len(created) - n0

        # ---------- exterior east exit stair, descending NORTH toward cafeteria ----------
        n0 = len(created)
        rbox("EWing_Exit_Land", EX1, EX1 + 2.6, -29.0, -26.0, LZ0 - 0.3, LZ0, m_slab, wing)
        ns = 10
        for i in range(1, ns + 1):
            zt = LZ0 - i * (LZ0 - GZ) / ns
            y0 = -26.0 + (i - 1) * 0.72
            rbox("EWing_Exit_Step_%02d" % i, EX1 + 0.2, EX1 + 2.6, y0, y0 + 0.72, zt - 0.15, zt, m_slab, wing)
        rbox("EWing_Exit_Pier_1", EX1 + 2.2, EX1 + 2.5, -23.3, -23.0, GZ, 7.3, m_metal, wing)
        rbox("EWing_Exit_Pier_2", EX1 + 2.2, EX1 + 2.5, -19.7, -19.4, GZ, 6.2, m_metal, wing)
        groups["exit"] = len(created) - n0

        scene["zy_east_wing"] = json.dumps({
            "shaft": [SX0, SX1, SY0, SY1], "corridor": [CY0, CY1],
            "exit_door": [-29.0, -26.0], "corr_gaps": [DGX0, DGX1],
            "mezz_door": [MDY0, MDY1]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_east_wing", "created": len(created),
                       "retired": retired, "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_east_wing", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_east_wing, first_interval=0.1)
