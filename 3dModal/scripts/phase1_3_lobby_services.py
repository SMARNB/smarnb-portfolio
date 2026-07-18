# Zyvion Phase 1.3b — lobby services + lounge (user additions 2026-07-17):
#   1. Grand chandelier "Halo": 3 concentric 12-seg glass ring tiers (r 6.2/4.6/3.0
#      at z 26.8/25.4/24.0) on dark rods from a ceiling plate, amber core finial.
#   2. Central cooling, BOTH treatments: exposed silver loop duct (r 0.45, z 31.5)
#      with corner boxes, 11 drop diffusers + supply trunk from the tower, PLUS
#      slim slot-diffuser bars under every mezzanine soffit and 4 ceiling grilles.
#   3. Wires as design: dark cable-tray loop at z 29.8 carrying color-coded runs
#      (amber=electrical, teal=data, red=security), conduit drops + jumpers to all
#      6 About panels + hero, wall distribution panel + riser by the core doorway.
#   4. Three 3-seater couches: flank pair at (+/-13.5,-30) facing each other with
#      coffee tables, lift-nook couch at (21,-8) facing the atrium; charcoal body,
#      amber lumbar pillows.
# Requires scene["zy_lobby"] (phase1_3_grand_lobby.py must run first).
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# prefix sweeps (Lobby_Chandelier_/HVAC_/Cable_/Vent_/Elec_/Couch_/Coffee_/Side_).
# Pipeline order: phase1_1 -> phase1_2 -> phase1_3_grand_lobby -> THIS.

def zy_services():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3b_status.json"
    created = []
    groups = {"chandelier": 0, "hvac": 0, "cables": 0, "vents": 0, "couches": 0}
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_services", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        if "zy_lobby" not in scene.keys():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_services",
                           "error": "scene['zy_lobby'] missing - run phase1_3_grand_lobby.py first"}, f, indent=1)
            return
        lb = json.loads(scene["zy_lobby"])

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

        def rboxr(name, sx, sy, sz, cx, cy, cz, rz, m, coll):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= sx
                v.co.y *= sy
                v.co.z *= sz
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, cz)
            ob.rotation_euler = (0.0, 0.0, rz)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        def rcyl(name, r, length, center, axis, m, coll, seg=12):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r, radius2=r, depth=length)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = center
            if axis == "x":
                ob.rotation_euler = (0.0, math.pi / 2, 0.0)
            elif axis == "y":
                ob.rotation_euler = (math.pi / 2, 0.0, 0.0)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_teal  = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_red   = mkmat("ZY_Accent_Red", "#C04848")
        m_wood  = mkmat("ZY_Wood_Warm", "#8C6748")
        m_duct  = mkmat("ZY_Duct_Silver", "#AEB6BD", rough=0.35)     # new: HVAC metal
        m_couch = mkmat("ZY_Couch_Charcoal", "#3A3F46", rough=0.95)  # new: upholstery

        lob = get_coll("Grand_Lobby", root)
        svc = get_coll("Lobby_Services", lob)
        furn = get_coll("Lobby_Furnishings", lob)

        # ---------- idempotency sweep (new namespaces only) ----------
        for n in [o.name for o in bpy.data.objects if o.name.startswith((
                "Lobby_Chandelier_", "Lobby_HVAC_", "Lobby_Cable_", "Lobby_Vent_",
                "Lobby_Elec_", "Lobby_Couch_", "Lobby_Coffee_", "Lobby_Side_"))]:
            kill(n)

        LZ1 = lb["z1"]            # 33.63 roof underside
        FT = lb["floor_top"]      # 9.38
        MZ = lb["mezz_z"]         # [15.33, 21.43, 27.53]
        CX, CY = 0.0, -25.0       # lobby center

        # ---------- 1. grand chandelier: halo rings ----------
        n0 = len(created)
        plate_z0 = LZ1 - 0.2
        rcyl("Lobby_Chandelier_Plate", 1.2, 0.2, (CX, CY, plate_z0 + 0.1), "z", m_metal, svc)
        rcyl("Lobby_Chandelier_Stem", 0.12, plate_z0 - 23.6, (CX, CY, (plate_z0 + 23.6) / 2), "z", m_metal, svc)
        tiers = [(6.2, 26.8, 3.3, 0.0), (4.6, 25.4, 2.6, 15.0), (3.0, 24.0, 1.7, 0.0)]
        for ti, (R, rz, seglen, a0) in enumerate(tiers):
            for s in range(12):
                th = math.radians(a0 + s * 30.0)
                rboxr("Lobby_Chandelier_Ring%d_Seg%02d" % (ti + 1, s + 1),
                      seglen, 0.5, 0.35,
                      CX + R * math.cos(th), CY + R * math.sin(th), rz,
                      th + math.pi / 2, m_glass, svc)
            rod_angles = (45, 135, 225, 315) if ti == 1 else (0, 90, 180, 270)
            for ai, adeg in enumerate(rod_angles):
                th = math.radians(adeg)
                px, py = CX + R * math.cos(th), CY + R * math.sin(th)
                rbox("Lobby_Chandelier_Rod_T%d_%d" % (ti + 1, ai + 1),
                     px - 0.04, px + 0.04, py - 0.04, py + 0.04, rz, plate_z0, m_metal, svc)
        rcyl("Lobby_Chandelier_Core", 0.45, 0.8, (CX, CY, 23.6), "z", m_amber, svc)
        groups["chandelier"] = len(created) - n0

        # ---------- 2a. exposed loop duct + diffusers + trunk ----------
        n0 = len(created)
        ZD = 31.5                 # duct centerline
        DX, DYS, DYN = 21.5, -44.0, -6.0
        rcyl("Lobby_HVAC_Duct_W", 0.45, DYN - DYS, (-DX, (DYS + DYN) / 2, ZD), "y", m_duct, svc)
        rcyl("Lobby_HVAC_Duct_E", 0.45, DYN - DYS, (DX, (DYS + DYN) / 2, ZD), "y", m_duct, svc)
        rcyl("Lobby_HVAC_Duct_S", 0.45, 2 * DX, (0.0, DYS, ZD), "x", m_duct, svc)
        rcyl("Lobby_HVAC_Duct_N", 0.45, 2 * DX, (0.0, DYN, ZD), "x", m_duct, svc)
        for ci, (px, py) in enumerate(((-DX, DYS), (DX, DYS), (-DX, DYN), (DX, DYN))):
            rbox("Lobby_HVAC_Corner_%d" % (ci + 1), px - 0.6, px + 0.6,
                 py - 0.6, py + 0.6, ZD - 0.6, ZD + 0.6, m_metal, svc)
        rcyl("Lobby_HVAC_Trunk", 0.45, 5.5, (0.0, -3.25, ZD), "y", m_duct, svc)
        di = 0
        diff_pts = ([(-DX, y) for y in (-35, -25, -15)] + [(DX, y) for y in (-35, -25, -15)]
                    + [(x, DYS) for x in (-14, 0, 14)] + [(x, DYN) for x in (-10, 10)])
        for px, py in diff_pts:
            di += 1
            rcyl("Lobby_HVAC_Diff_%d_Stub" % di, 0.28, 0.95, (px, py, ZD - 0.925), "z", m_duct, svc)
            rcyl("Lobby_HVAC_Diff_%d_Plate" % di, 0.6, 0.12, (px, py, ZD - 1.46), "z", m_duct, svc)
        hi = 0
        for px, py in ((-DX, -36), (-DX, -14), (DX, -36), (DX, -14),
                       (-16, DYS), (16, DYS), (-16, DYN), (16, DYN)):
            hi += 1
            rbox("Lobby_HVAC_Hanger_%d" % hi, px - 0.06, px + 0.06,
                 py - 0.06, py + 0.06, ZD, LZ1, m_metal, svc)
        groups["hvac"] = len(created) - n0

        # ---------- 2b. slot diffusers under soffits + ceiling grilles ----------
        n0 = len(created)
        for k, lz in enumerate(MZ):
            L = k + 2
            zb = lz - 0.3         # slab bottom
            rbox("Lobby_Vent_Slot_L%d_W" % L, -19.4, -19.15, -38.0, -8.0, zb - 0.12, zb, m_duct, svc)
            rbox("Lobby_Vent_Slot_L%d_E" % L, 19.15, 19.4, -38.0, -8.0, zb - 0.12, zb, m_duct, svc)
            if k == 0:
                rbox("Lobby_Vent_Slot_L%d_N" % L, -16.0, 16.0, -5.95, -5.7, zb - 0.12, zb, m_duct, svc)
            else:
                rbox("Lobby_Vent_Slot_L%d_NW" % L, -16.0, -8.8, -5.95, -5.7, zb - 0.12, zb, m_duct, svc)
                rbox("Lobby_Vent_Slot_L%d_NE" % L, 8.8, 16.0, -5.95, -5.7, zb - 0.12, zb, m_duct, svc)
        for gi, (px, py) in enumerate(((-9, -34), (9, -34), (-9, -16), (9, -16))):
            rbox("Lobby_Vent_Grille_%d" % (gi + 1), px - 0.8, px + 0.8,
                 py - 0.8, py + 0.8, LZ1 - 0.06, LZ1, m_metal, svc)
        groups["vents"] = len(created) - n0

        # ---------- 3. cable trays: color-coded loop + drops ----------
        n0 = len(created)
        ZT = 29.8                 # tray top level
        TX, TYS, TYN = 20.5, -42.75, -7.25
        for tag, bx0, bx1, by0, by1 in (
                ("W", -TX - 0.25, -TX + 0.25, -43.0, -7.0),
                ("E", TX - 0.25, TX + 0.25, -43.0, -7.0),
                ("S", -20.75, 20.75, TYS - 0.25, TYS + 0.25),
                ("N", -20.75, 20.75, TYN - 0.25, TYN + 0.25)):
            rbox("Lobby_Cable_Tray_%s" % tag, bx0, bx1, by0, by1, ZT - 0.1, ZT, m_metal, svc)
        bundles = (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14))
        for bname, bm_, off in bundles:
            rbox("Lobby_Cable_Run_W_%s" % bname, -TX + off - 0.045, -TX + off + 0.045,
                 -43.0, -7.0, ZT, ZT + 0.07, bm_, svc)
            rbox("Lobby_Cable_Run_E_%s" % bname, TX + off - 0.045, TX + off + 0.045,
                 -43.0, -7.0, ZT, ZT + 0.07, bm_, svc)
            rbox("Lobby_Cable_Run_S_%s" % bname, -20.75, 20.75,
                 TYS + off - 0.045, TYS + off + 0.045, ZT, ZT + 0.07, bm_, svc)
            rbox("Lobby_Cable_Run_N_%s" % bname, -20.75, 20.75,
                 TYN + off - 0.045, TYN + off + 0.045, ZT, ZT + 0.07, bm_, svc)
        hi = 0
        for px, py in ((-TX, -31), (-TX, -19), (TX, -31), (TX, -19),
                       (-10, TYS), (10, TYS), (-10, TYN), (10, TYN)):
            hi += 1
            rbox("Lobby_Cable_Hanger_%d" % hi, px - 0.05, px + 0.05,
                 py - 0.05, py + 0.05, ZT, LZ1, m_metal, svc)
        # paired drops to the six About panels (amber=power, teal=data);
        # centers match the panel spans in phase1_3_grand_lobby.py
        IW, IE = lb["x0"] + 0.5, lb["x1"] - 0.5
        for i, pc in enumerate((-43.0, -35.0, -13.0)):
            for tag, mm, off in (("P", m_amber, -0.19), ("D", m_teal, 0.15)):
                y0, y1 = pc + off, pc + off + 0.08
                rbox("Lobby_Cable_Drop_D%d_%s" % (i + 1, tag),
                     IW - 0.06, IW + 0.02, y0, y1, 14.3, ZT, mm, svc)
                rbox("Lobby_Cable_Jump_D%d_%s" % (i + 1, tag),
                     -TX, IW + 0.02, y0, y1, ZT - 0.04, ZT + 0.04, mm, svc)
                rbox("Lobby_Cable_Drop_D%d_%s" % (i + 4, tag),
                     IE - 0.02, IE + 0.06, y0, y1, 14.3, ZT, mm, svc)
                rbox("Lobby_Cable_Jump_D%d_%s" % (i + 4, tag),
                     IE - 0.02, TX, y0, y1, ZT - 0.04, ZT + 0.04, mm, svc)
        # hero screen drops + riser + distribution panel on the north wall
        INY = lb["y1"] - 0.5
        for tag, mm, hx in (("P", m_amber, -5.2), ("D", m_teal, -4.8)):
            rbox("Lobby_Cable_Drop_Hero_%s" % tag, hx - 0.04, hx + 0.04,
                 INY - 0.08, INY, 23.4, ZT, mm, svc)
            rbox("Lobby_Cable_Jump_Hero_%s" % tag, hx - 0.04, hx + 0.04,
                 TYN, INY, ZT - 0.04, ZT + 0.04, mm, svc)
        rbox("Lobby_Elec_Panel", 15.4, 16.6, INY - 0.3, INY, FT + 0.15, FT + 1.95, m_metal, svc)
        for tag, mm, hx in (("P", m_amber, 15.7), ("D", m_teal, 16.3)):
            rbox("Lobby_Cable_Riser_%s" % tag, hx - 0.04, hx + 0.04,
                 INY - 0.08, INY, FT + 1.95, ZT, mm, svc)
            rbox("Lobby_Cable_RiserJump_%s" % tag, hx - 0.04, hx + 0.04,
                 TYN, INY, ZT - 0.04, ZT + 0.04, mm, svc)
        groups["cables"] = len(created) - n0

        # ---------- 4. three 3-seater couches + tables ----------
        n0 = len(created)

        def couch(idx, cx, cy, rz):
            pre = "Lobby_Couch_%d" % idx

            def part(tag, sx, sy, sz, lx, ly, lz_):
                wx = cx + lx * math.cos(rz) - ly * math.sin(rz)
                wy = cy + lx * math.sin(rz) + ly * math.cos(rz)
                mat = m_amber if tag.startswith("Pil") else m_couch
                rboxr("%s_%s" % (pre, tag), sx, sy, sz, wx, wy, lz_, rz, mat, furn)

            part("Base", 2.7, 1.05, 0.42, 0.0, 0.0, FT + 0.21)
            part("Back", 2.7, 0.28, 0.63, 0.0, -0.385, FT + 0.735)
            part("ArmL", 0.28, 1.05, 0.26, -1.21, 0.0, FT + 0.55)
            part("ArmR", 0.28, 1.05, 0.26, 1.21, 0.0, FT + 0.55)
            for ci, lx in enumerate((-0.82, 0.0, 0.82)):
                part("Cush%d" % (ci + 1), 0.74, 0.62, 0.12, lx, 0.12, FT + 0.48)
            part("Pil1", 0.55, 0.12, 0.32, -0.45, -0.19, FT + 0.70)
            part("Pil2", 0.55, 0.12, 0.32, 0.45, -0.19, FT + 0.70)

        couch(1, -13.5, -30.0, -math.pi / 2)   # west flank, faces east
        couch(2, 13.5, -30.0, math.pi / 2)     # east flank, faces west
        couch(3, 21.0, -8.0, math.pi / 2)      # lift nook, faces the atrium
        rbox("Lobby_Coffee_Table_1", -12.25, -10.95, -30.4, -29.6, FT, FT + 0.4, m_wood, furn)
        rbox("Lobby_Coffee_Table_2", 10.95, 12.25, -30.4, -29.6, FT, FT + 0.4, m_wood, furn)
        rbox("Lobby_Side_Table_3", 20.65, 21.35, -6.3, -5.6, FT, FT + 0.45, m_wood, furn)
        groups["couches"] = len(created) - n0

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_services", "created": len(created),
                       "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_services", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_services, first_interval=0.1)
