# Zyvion Phase 1.3c — WEST WING: Waiting Room fit-out (level 1) + rear stair
# shaft connecting all 8 wing levels (user spec 2026-07-17):
#   - Hollows Waiting_Area L1 (x -50..-25, y -50..0, z 9.23..15.33): finish
#     floor, front/side window-band facades, west EXIT door (y -8..-4) with an
#     exterior facade stair descending south to grade near the gym-stair lane.
#   - Program: cubicle main area w/ public PC counter (computer space, split
#     around the lobby doorway), fully COVERED coffee mini-bar (own glass
#     walls + lid, aroma-tight), restroom block (M/W) at the back NW corner.
#   - Upper levels (Waiting_Area.001-.007) retired and rebuilt as solid stack
#     boxes; phase1_3_wing_floors.py (runs AFTER this) hollows them into
#     office floors around the RESTORED front stair shaft.
#   - Front wing staircase (user 2026-07-18: "bring them back"): dog-leg shaft
#     at the back inner corner (x -31.5..-25.5, y -6.5..-0.5), transitions
#     T1..T8 up to the ROOF (58.03) with amber platforms per floor.
#   - Re-splits Lobby_Wall_W: L1 lobby<->waiting doorway (y -28..-24) with an
#     amber portal frame + mezz doorways (y -5..-2) at levels 2/3/4.
#   - Wing services: duct spine + branches + diffusers, cable tray with
#     amber/teal/red runs, drops, wall panel (item 5: central cooling + wiring).
# Requires scene["zy_plinth"] + scene["zy_lobby"].
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# "WWing_" + "Lobby_Wall_W" prefix sweeps. Order: ... -> lobby -> services -> THIS.

def zy_west_wing():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_west_status.json"
    created = []
    groups = {"shell": 0, "restroom": 0, "cafe": 0, "main": 0, "shaft": 0, "services": 0, "exit": 0}
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_west_wing", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        for key in ("zy_plinth", "zy_lobby"):
            if key not in scene.keys():
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump({"ok": False, "step": "phase1_3_west_wing",
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
        LZ0 = p["z1"]                       # 9.23 level-1 floor
        FT = LZ0 + 0.15
        CT = LZ0 + H                        # 15.33 level-1 ceiling
        WX0, WX1 = -50.0, -25.0             # wing envelope
        WY0, WY1 = -50.0, 0.0
        GZ = 5.41                           # site ground top
        SX0, SX1, SY0, SY1 = -31.5, -25.5, -6.5, -0.5   # front stair shaft
        MZ = lb["mezz_z"]                   # [15.33, 21.43, 27.53]
        DY0, DY1 = -8.0, -4.0               # west exit door span
        LDY0, LDY1 = -28.0, -24.0           # L1 lobby<->waiting doorway
        MDY0, MDY1 = -5.0, -2.0             # mezz doorway span

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
        m_cera  = mkmat("ZY_Ceramic_White", "#E8E8E4", rough=0.3)    # new: sanitary

        wing = get_coll("Wing_West_Waiting", root)
        core = get_coll("Wing_West_Stairs", root)

        # ---------- idempotency sweep + retire originals ----------
        for n in [o.name for o in bpy.data.objects
                  if o.name.startswith("WWing_") or o.name.startswith("Lobby_Wall_W")]:
            kill(n)
        retired = []
        ob = bpy.data.objects.get("Waiting_Area")
        if ob is not None:
            retire(ob, "Waiting_Area_ORIGINAL")
            retired.append("Waiting_Area")
        for k in range(1, 8):
            ob = bpy.data.objects.get("Waiting_Area.%03d" % k)
            if ob is not None:
                retire(ob, "Waiting_Area_ORIG_L%d" % (k + 1))
                retired.append("Waiting_Area.%03d" % k)

        # ---------- upper stack: solid massing (stairs live in the rear blocks) ----------
        n0 = len(created)
        for k in range(2, 9):
            zb = LZ0 + (k - 1) * H
            rbox("WWing_Stack_L%d" % k, WX0, WX1, WY0, WY1, zb, zb + H, m_slab, wing)
        groups["shell"] += len(created) - n0

        # ---------- lobby west wall re-split: L1 doorway + mezz doorways ----------
        n0 = len(created)
        LWx0, LWx1 = -25.0, -24.5
        LT = lb["z1"]
        rbox("Lobby_Wall_W_A", LWx0, LWx1, -49.5, LDY0, LZ0, LT, m_wall, wing)
        rbox("Lobby_Wall_W_BH", LWx0, LWx1, LDY0, LDY1, LZ0 + 3.5, LT, m_wall, wing)
        rbox("Lobby_Wall_W_C", LWx0, LWx1, LDY1, MDY0, LZ0, LT, m_wall, wing)
        rbox("Lobby_Wall_W_D1", LWx0, LWx1, MDY0, MDY1, LZ0, MZ[0], m_wall, wing)
        rbox("Lobby_Wall_W_D2", LWx0, LWx1, MDY0, MDY1, MZ[0] + 3.0, MZ[1], m_wall, wing)
        rbox("Lobby_Wall_W_D3", LWx0, LWx1, MDY0, MDY1, MZ[1] + 3.0, MZ[2], m_wall, wing)
        rbox("Lobby_Wall_W_D4", LWx0, LWx1, MDY0, MDY1, MZ[2] + 3.0, LT, m_wall, wing)
        rbox("Lobby_Wall_W_E", LWx0, LWx1, MDY1, -0.5, LZ0, LT, m_wall, wing)
        rbox("WWing_LDoor_JambS", LWx0 - 0.12, LWx1 + 0.12, LDY0 - 0.3, LDY0, LZ0, LZ0 + 3.7, m_amber, wing)
        rbox("WWing_LDoor_JambN", LWx0 - 0.12, LWx1 + 0.12, LDY1, LDY1 + 0.3, LZ0, LZ0 + 3.7, m_amber, wing)
        rbox("WWing_LDoor_Head", LWx0 - 0.12, LWx1 + 0.12, LDY0 - 0.3, LDY1 + 0.3, LZ0 + 3.5, LZ0 + 3.85, m_amber, wing)
        groups["shell"] += len(created) - n0

        # ---------- level-1 shell: floor, facades w/ window bands, exit door ----------
        n0 = len(created)
        rbox("WWing_Floor", WX0 + 0.5, WX1, WY0 + 0.5, WY1 - 0.5, LZ0, FT, m_floor, wing)
        rbox("WWing_Wall_S_Sill", WX0, WX1, WY0, WY0 + 0.5, LZ0, 10.4, m_wall, wing)
        rbox("WWing_Wall_S_Glass", WX0, WX1, WY0 + 0.1, WY0 + 0.35, 10.4, 13.4, m_glass, wing)
        rbox("WWing_Wall_S_Hdr", WX0, WX1, WY0, WY0 + 0.5, 13.4, CT, m_wall, wing)
        for tag, y0, y1 in (("S", WY0 + 0.5, DY0), ("N", DY1, -0.5)):
            rbox("WWing_Wall_W_Sill_%s" % tag, WX0, WX0 + 0.5, y0, y1, LZ0, 10.4, m_wall, wing)
            rbox("WWing_Wall_W_Glass_%s" % tag, WX0 + 0.1, WX0 + 0.35, y0, y1, 10.4, 13.4, m_glass, wing)
            rbox("WWing_Wall_W_Hdr_%s" % tag, WX0, WX0 + 0.5, y0, y1, 13.4, CT, m_wall, wing)
        rbox("WWing_Wall_W_DoorHdr", WX0, WX0 + 0.5, DY0, DY1, LZ0 + 3.0, CT, m_wall, wing)
        rbox("WWing_Door_JambS", WX0 - 0.15, WX0 + 0.6, DY0 - 0.3, DY0, LZ0, LZ0 + 3.2, m_metal, wing)
        rbox("WWing_Door_JambN", WX0 - 0.15, WX0 + 0.6, DY1, DY1 + 0.3, LZ0, LZ0 + 3.2, m_metal, wing)
        rbox("WWing_Door_Head", WX0 - 0.15, WX0 + 0.6, DY0 - 0.3, DY1 + 0.3, LZ0 + 3.0, LZ0 + 3.35, m_metal, wing)
        rbox("WWing_Wall_N", WX0, WX1, WY1 - 0.5, WY1, LZ0, CT, m_wall, wing)
        rbox("WWing_Shaft_E1", SX1, WX1, SY0, SY1, LZ0, CT, m_wall, wing)
        groups["shell"] += len(created) - n0

        # ---------- RESTORED front stair shaft: L1 walls + dog-leg to the ROOF ----------
        n0 = len(created)
        rbox("WWing_Shaft_W1", SX0, SX0 + 0.5, SY0, SY1, LZ0, CT, m_wall, core)
        rbox("WWing_Shaft_S1a", SX0 + 0.5, -29.0, SY0, SY0 + 0.5, LZ0, CT, m_wall, core)
        rbox("WWing_Shaft_S1b", -27.0, SX1, SY0, SY0 + 0.5, LZ0, CT, m_wall, core)
        rbox("WWing_Shaft_S1Hdr", -29.0, -27.0, SY0, SY0 + 0.5, LZ0 + 3.0, CT, m_wall, core)

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
            stepsx("WWing_Stair_T%d_A" % k, -26.4, -29.5, -6.0, -4.4, za, za + H / 2)
            rbox("WWing_Stair_T%d_Land" % k, -31.0, -29.5, -6.0, -0.5,
                 za + H / 2 - 0.15, za + H / 2, m_amber, core)
            stepsx("WWing_Stair_T%d_B" % k, -29.5, -26.4, -2.1, -0.5, za + H / 2, zb)
        for k in range(2, 10):              # level platforms L2..L8 + roof (P9)
            zk = LZ0 + (k - 1) * H
            rbox("WWing_Stair_P%d" % k, -26.4, SX1, -6.0, -0.5, zk - 0.15, zk, m_amber, core)
        groups["shaft"] = len(created) - n0

        # ---------- restrooms: back NW corner, M/W rooms ----------
        n0 = len(created)
        rbox("WWing_RR_Wall_S1", -49.5, -48.0, -8.0, -7.7, LZ0, 13.0, m_wall, wing)
        rbox("WWing_RR_Wall_S2", -46.5, -43.5, -8.0, -7.7, LZ0, 13.0, m_wall, wing)
        rbox("WWing_RR_Wall_S3", -42.0, -40.5, -8.0, -7.7, LZ0, 13.0, m_wall, wing)
        rbox("WWing_RR_HdrM", -48.0, -46.5, -8.0, -7.7, LZ0 + 3.0, 13.0, m_wall, wing)
        rbox("WWing_RR_HdrW", -43.5, -42.0, -8.0, -7.7, LZ0 + 3.0, 13.0, m_wall, wing)
        rbox("WWing_RR_Wall_E", -40.8, -40.5, -7.7, -0.5, LZ0, 13.0, m_wall, wing)
        rbox("WWing_RR_Divider", -45.15, -44.85, -8.0, -0.5, LZ0, 13.0, m_wall, wing)
        for tag, xs in (("M", (-49.0, -47.6)), ("W", (-44.3, -42.9))):
            for wi, wx in enumerate(xs):
                rbox("WWing_RR_%s_WC%d" % (tag, wi + 1), wx, wx + 0.7, -1.6, -0.85, FT, FT + 0.8, m_cera, wing)
            rbox("WWing_RR_%s_Stall" % tag, xs[1] - 0.45, xs[1] - 0.37, -2.4, -0.6, FT, FT + 1.8, m_grey, wing)
        rbox("WWing_RR_M_Sink", -47.8, -45.8, -7.5, -6.9, FT, FT + 0.9, m_cera, wing)
        rbox("WWing_RR_W_Sink", -44.4, -42.4, -7.5, -6.9, FT, FT + 0.9, m_cera, wing)
        groups["restroom"] = len(created) - n0

        # ---------- coffee mini-bar: SW corner, fully covered glass box ----------
        n0 = len(created)
        rbox("WWing_Cafe_Wall_E1", -41.3, -41.0, -44.0, -41.0, LZ0, 12.8, m_glass, wing)
        rbox("WWing_Cafe_Wall_EHdr", -41.3, -41.0, -41.0, -39.0, LZ0 + 3.0, 12.8, m_glass, wing)
        rbox("WWing_Cafe_Wall_E2", -41.3, -41.0, -39.0, -36.0, LZ0, 12.8, m_glass, wing)
        rbox("WWing_Cafe_Wall_N", -49.5, -41.0, -36.3, -36.0, LZ0, 12.8, m_glass, wing)
        rbox("WWing_Cafe_Wall_S", -49.5, -41.0, -44.0, -43.7, LZ0, 12.8, m_glass, wing)
        rbox("WWing_Cafe_Roof", -49.5, -41.0, -44.0, -36.0, 12.8, 13.0, m_slab, wing)
        rbox("WWing_Cafe_Bar", -48.5, -43.5, -40.4, -39.6, LZ0, FT + 0.9, m_wood, wing)
        rbox("WWing_Cafe_BarTop", -48.6, -43.4, -40.5, -39.5, FT + 0.9, FT + 0.98, m_metal, wing)
        rbox("WWing_Cafe_Machine", -47.5, -46.7, -40.3, -39.8, FT + 0.98, FT + 1.68, m_metal, wing)
        rbox("WWing_Cafe_Shelf", -49.4, -49.1, -43.0, -37.0, 10.5, 12.3, m_wood, wing)
        for ti, (tx, ty) in enumerate(((-47.5, -42.7), (-44.5, -42.7))):
            rcylz("WWing_Cafe_Table_%d" % (ti + 1), 0.55, FT, FT + 0.75, tx, ty, m_wood, wing)
        for si, (sx, sy) in enumerate(((-48.2, -42.0), (-46.8, -43.3), (-45.2, -42.0),
                                       (-43.8, -43.3), (-47.0, -39.1), (-45.0, -39.1))):
            rcylz("WWing_Cafe_Stool_%d" % (si + 1), 0.22, FT, FT + 0.5, sx, sy, m_couch, wing)
        groups["cafe"] = len(created) - n0

        # ---------- main area: 6 cubicles + public PC counter + benches ----------
        n0 = len(created)
        slots = [(sx, sy) for sy in (-32.0, -20.0) for sx in (-45.0, -39.6, -34.2)]
        for ci, (sx, sy) in enumerate(slots):
            pre = "WWing_Cub_%d" % (ci + 1)
            rbox(pre + "_PartN", sx, sx + 4.4, sy + 5.92, sy + 6.0, LZ0, 10.9, m_grey, wing)
            rbox(pre + "_PartW", sx, sx + 0.08, sy, sy + 6.0, LZ0, 10.9, m_grey, wing)
            rbox(pre + "_Desk", sx + 0.6, sx + 3.6, sy + 4.6, sy + 5.4, LZ0, 10.05, m_wood, wing)
            rbox(pre + "_Mon", sx + 1.7, sx + 2.3, sy + 5.0, sy + 5.08, 10.05, 10.5, m_metal, wing)
            rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, sx + 2.1, sy + 3.9, m_couch, wing)
        # PC counter split into two segments so the lobby doorway (y -28..-24)
        # stays completely clear
        rbox("WWing_PC_Counter_S", -26.4, -25.6, -34.0, -29.0, LZ0, 10.13, m_wood, wing)
        rbox("WWing_PC_Counter_N", -26.4, -25.6, -23.0, -18.0, LZ0, 10.13, m_wood, wing)
        for mi, my in enumerate((-33.3, -31.6, -29.9, -22.4, -20.7)):
            rbox("WWing_PC_Mon_%d" % (mi + 1), -26.0, -25.92, my, my + 0.6, 10.13, 10.58, m_metal, wing)
            rcylz("WWing_PC_Stool_%d" % (mi + 1), 0.24, FT, FT + 0.55, -27.2, my + 0.3, m_couch, wing)
        rbox("WWing_Bench_1", -36.0, -33.0, -46.2, -45.4, FT, FT + 0.45, m_wood, wing)
        rbox("WWing_Bench_2", -31.0, -28.0, -46.2, -45.4, FT, FT + 0.45, m_wood, wing)
        groups["main"] = len(created) - n0

        # ---------- wing services: ducts + diffusers + color-coded tray ----------
        n0 = len(created)
        rcyl_ax("WWing_Svc_Duct_Main", 0.35, 23.0, (-37.5, -24.0, 14.55), "x", m_duct, wing)
        rcyl_ax("WWing_Svc_Duct_BrN", 0.35, 20.0, (-44.0, -14.0, 14.55), "y", m_duct, wing)
        rcyl_ax("WWing_Svc_Duct_BrS", 0.35, 16.0, (-46.0, -32.0, 14.55), "y", m_duct, wing)
        for di, (px, py) in enumerate(((-44.0, -8.0), (-46.0, -40.0), (-41.0, -24.0),
                                       (-33.0, -24.0), (-28.0, -24.0))):
            rcylz("WWing_Svc_Diff_%d_Stub" % (di + 1), 0.24, 13.75, 14.35, px, py, m_duct, wing)
            rcylz("WWing_Svc_Diff_%d_Plate" % (di + 1), 0.5, 13.63, 13.75, px, py, m_duct, wing)
        rbox("WWing_Svc_Tray", -49.0, -26.0, -23.05, -22.55, 13.95, 14.05, m_metal, wing)
        for bname, bm_, off in (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14)):
            rbox("WWing_Svc_Run_%s" % bname, -49.0, -26.0,
                 -22.8 + off - 0.045, -22.8 + off + 0.045, 14.05, 14.12, bm_, wing)
        for dn, dx, dz0 in (("PC_P", -26.2, 10.2), ("PC_D", -25.9, 10.2),
                            ("C1_P", -43.2, 10.9), ("C1_D", -42.9, 10.9),
                            ("C2_P", -32.2, 10.9), ("C2_D", -31.9, 10.9)):
            mm = m_amber if dn.endswith("_P") else m_teal
            rbox("WWing_Svc_Drop_%s" % dn, dx - 0.04, dx + 0.04, -22.84, -22.76, dz0, 13.95, mm, wing)
        rbox("WWing_Svc_Panel", -38.6, -37.4, -0.8, -0.5, FT + 0.15, FT + 1.95, m_metal, wing)
        groups["services"] = len(created) - n0

        # ---------- exterior west exit stair down to grade (near gym lane) ----------
        n0 = len(created)
        rbox("WWing_Exit_Land", -52.6, -50.0, DY0, DY1, LZ0 - 0.3, LZ0, m_slab, wing)
        ns = 10
        for i in range(1, ns + 1):
            zt = LZ0 - i * (LZ0 - GZ) / ns
            y0 = DY0 - i * 0.72
            rbox("WWing_Exit_Step_%02d" % i, -52.6, -50.2, y0, y0 + 0.72, zt - 0.15, zt, m_slab, wing)
        rbox("WWing_Exit_Pier_1", -52.5, -52.2, -11.0, -10.7, GZ, 7.3, m_metal, wing)
        rbox("WWing_Exit_Pier_2", -52.5, -52.2, -14.6, -14.3, GZ, 6.2, m_metal, wing)
        groups["exit"] = len(created) - n0

        scene["zy_west_wing"] = json.dumps({
            "shaft": [SX0, SX1, SY0, SY1], "exit_door": [DY0, DY1],
            "lobby_door": [LDY0, LDY1], "mezz_door": [MDY0, MDY1],
            "cafe": [-49.5, -41.0, -44.0, -36.0], "restroom": [-49.5, -40.5, -8.0, -0.5]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_west_wing", "created": len(created),
                       "retired": retired, "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_west_wing", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_west_wing, first_interval=0.1)
