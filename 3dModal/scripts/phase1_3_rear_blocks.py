# Zyvion Phase 1.3e — REAR BLOCKS per user markup (2026-07-18, rear-view image;
# viewer-left = east):
#   GREEN  - two stair towers at the rear outer corners (NE x 43.5..49.5 /
#            NW x -49.5..-43.5, y 43.5..49.5) connecting levels 1..8 of their
#            stacks (Recruitment_Area / Manager_Offices re-split as rings,
#            originals retired) with a GROUND EXIT door in the north facade +
#            exterior stair down to grade. Replaces the abandoned inner-corner
#            wing shafts.
#   ORANGE - EAST rear block L1 = 4 PRIVATE head-of-department offices along
#            the rear windows (full-height walls + doors), open zone south,
#            connecting doorway to the HR cubicle section (x 34..37 at y=0).
#   RED    - CENTER column L1 (Cubicle_Workspace_L0 rings) hollowed into the
#            open CUBICAL HALL around the lift core: 12 cubicles, two 4 m
#            doorways from the Grand Lobby north wall (x -20..-16 / 16..20).
#   YELLOW - WEST rear block L1 split: recruitment COMPUTER LAB north
#            (5 rows x 10 networked seats, all facing the projector screen on
#            the south partition) + the rest merged into the Cubical Hall
#            through a 21 m opening in the shared wall (y 2..23).
#   Item 4 - rear facade = SOLID wall with punched WINDOWS + CURTAINS: real
#            openings at L1 (20 windows, glass + curtain pairs), cosmetic
#            curtained window panels on levels 2..8 (14 per level).
#   Item 5 - every new area gets ducts + diffusers + color-coded tray + drops.
# Requires scene["zy_plinth"] + scene["zy_lobby"].
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# RearE_/RearW_/CHall_/RearF_ sweeps + explicit re-split kills.
# Order: ... -> phase1_3_west_wing -> phase1_3_east_wing -> THIS (last).

def zy_rear_blocks():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_rear_status.json"
    created = []
    groups = {"stacks": 0, "towers": 0, "hall": 0, "west": 0, "east": 0, "facade": 0}
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_rear", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        for key in ("zy_plinth", "zy_lobby"):
            if key not in scene.keys():
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump({"ok": False, "step": "phase1_3_rear",
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
        LT = lb["z1"]                       # 33.63 lobby wall top
        GZ = 5.41
        TSX0, TSX1 = 43.5, 49.5             # NE tower x (NW mirrored negative)
        TSY0, TSY1 = 43.5, 49.5             # tower y
        XDW0, XDW1 = 45.4, 47.6             # ground-exit door x (abs, mirrored)

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
        m_cera  = mkmat("ZY_Ceramic_White", "#E8E8E4", rough=0.3)
        m_curt  = mkmat("ZY_Curtain_Cream", "#D9CBB0", rough=0.9)    # new: curtains

        c_east = get_coll("Rear_East_Offices", root)
        c_west = get_coll("Rear_West_Recruitment", root)
        c_hall = get_coll("Central_Hall", root)
        c_twr  = get_coll("Rear_Towers", root)
        c_fac  = get_coll("Rear_Facade", root)

        # ---------- idempotency sweep + explicit re-split kills ----------
        for n in [o.name for o in bpy.data.objects if o.name.startswith(
                ("RearE_", "RearW_", "CHall_", "RearF_",
                 "Lobby_Wall_N_W", "Lobby_Wall_N_E", "EWing_Wall_N"))]:
            kill(n)
        for n in ("Cubicle_Workspace_L0_W", "Cubicle_Workspace_L0_E",
                  "Cubicle_Workspace_L0_N", "Cubicle_Workspace_L0_S",
                  "Cubicle_Workspace_L0_S_W", "Cubicle_Workspace_L0_S_E",
                  "Cubicle_Workspace_L0_S_Hdr"):
            kill(n)
        retired = []
        for base, tag in (("Recruitment_Area", "Recruitment_Area_ORIG"),
                          ("Manager_Offices", "Manager_Offices_ORIG")):
            ob = bpy.data.objects.get(base)
            if ob is not None:
                retire(ob, tag + "_L1")
                retired.append(base)
            for k in range(1, 8):
                ob = bpy.data.objects.get("%s.%03d" % (base, k))
                if ob is not None:
                    retire(ob, "%s_L%d" % (tag, k + 1))
                    retired.append("%s.%03d" % (base, k))

        # ---------- upper stack rings (levels 2..8) around the two towers ----------
        n0 = len(created)
        for k in range(2, 9):
            zb = LZ0 + (k - 1) * H
            zt = zb + H
            rbox("RearE_Stack_L%d_S" % k, 25.0, 50.0, 0.0, TSY0, zb, zt, m_slab, c_east)
            rbox("RearE_Stack_L%d_W" % k, 25.0, TSX0, TSY0, 50.0, zb, zt, m_slab, c_east)
            rbox("RearE_Stack_L%d_N" % k, TSX0, 50.0, TSY1, 50.0, zb, zt, m_slab, c_east)
            rbox("RearE_Stack_L%d_E" % k, TSX1, 50.0, TSY0, TSY1, zb, zt, m_slab, c_east)
            rbox("RearW_Stack_L%d_S" % k, -50.0, -25.0, 0.0, TSY0, zb, zt, m_slab, c_west)
            rbox("RearW_Stack_L%d_E" % k, -TSX0, -25.0, TSY0, 50.0, zb, zt, m_slab, c_west)
            rbox("RearW_Stack_L%d_N" % k, -50.0, -TSX0, TSY1, 50.0, zb, zt, m_slab, c_west)
            rbox("RearW_Stack_L%d_W" % k, -50.0, -TSX1, TSY0, TSY1, zb, zt, m_slab, c_west)
        groups["stacks"] = len(created) - n0

        # ---------- stair towers: L1 walls + dog-leg stairs L1..L8 ----------
        n0 = len(created)

        def stepsx(prefix, xa, xb, y0, y1, za, zb, coll):
            ns = 8
            for i in range(1, ns + 1):
                zt = za + i * (zb - za) / ns
                t0 = xa + (i - 1) * (xb - xa) / ns
                t1 = xa + i * (xb - xa) / ns
                lo, hi = min(t0, t1), max(t0, t1)
                rbox("%s_%02d" % (prefix, i), lo, hi, y0, y1, zt - 0.15, zt, m_slab, coll)

        for side, sgn in (("NE", 1.0), ("NW", -1.0)):
            def X(v):
                return sgn * v
            xs = sorted((X(TSX0), X(TSX1)))
            # L1 tower walls: south wall with door gap + inner side wall
            d0, d1 = sorted((X(45.6), X(47.4)))
            rbox("RearF_Twr%s_S_A" % side, xs[0], d0, TSY0, TSY0 + 0.5, LZ0, CT, m_wall, c_twr)
            rbox("RearF_Twr%s_S_B" % side, d1, xs[1], TSY0, TSY0 + 0.5, LZ0, CT, m_wall, c_twr)
            rbox("RearF_Twr%s_S_Hdr" % side, d0, d1, TSY0, TSY0 + 0.5, LZ0 + 3.0, CT, m_wall, c_twr)
            w0, w1 = sorted((X(TSX0), X(TSX0 + 0.5)))
            rbox("RearF_Twr%s_Side" % side, w0, w1, TSY0 + 0.5, TSY1, LZ0, CT, m_wall, c_twr)
            # dog-leg stairs: A south band out, landing, B north band back
            fa0, fa1 = X(44.7), X(47.9)
            l0, l1 = sorted((X(47.9), X(49.4)))
            p0, p1 = sorted((X(44.0), X(44.7)))
            for k in range(1, 9):           # 8 transitions: L1..L8 then roof
                za = LZ0 + (k - 1) * H
                zb = za + H
                stepsx("RearF_Twr%s_T%d_A" % (side, k), fa0, fa1, 44.0, 45.6, za, za + H / 2, c_twr)
                rbox("RearF_Twr%s_T%d_Land" % (side, k), l0, l1, 44.0, 49.5,
                     za + H / 2 - 0.15, za + H / 2, m_amber, c_twr)
                stepsx("RearF_Twr%s_T%d_B" % (side, k), fa1, fa0, 47.9, 49.5, za + H / 2, zb, c_twr)
            for k in range(2, 10):          # level platforms L2..L8 + roof (P9)
                zk = LZ0 + (k - 1) * H
                rbox("RearF_Twr%s_P%d" % (side, k), p0, p1, 44.0, 49.5, zk - 0.15, zk, m_amber, c_twr)
            # ground exit: door frame + exterior stair down to grade
            e0, e1 = sorted((X(XDW0), X(XDW1)))
            rbox("RearF_Exit%s_JambW" % side, e0 - 0.3, e0, 49.4, 50.1, LZ0, LZ0 + 3.2, m_metal, c_fac)
            rbox("RearF_Exit%s_JambE" % side, e1, e1 + 0.3, 49.4, 50.1, LZ0, LZ0 + 3.2, m_metal, c_fac)
            rbox("RearF_Exit%s_Head" % side, e0 - 0.3, e1 + 0.3, 49.4, 50.1, LZ0 + 3.0, LZ0 + 3.35, m_metal, c_fac)
            rbox("RearF_Exit%s_Land" % side, e0, e1, 50.0, 52.6, LZ0 - 0.3, LZ0, m_slab, c_fac)
            for i in range(1, 11):
                zt = LZ0 - i * (LZ0 - GZ) / 10
                y0 = 52.6 + (i - 1) * 0.72
                rbox("RearF_Exit%s_Step_%02d" % (side, i), e0, e1, y0, y0 + 0.72, zt - 0.15, zt, m_slab, c_fac)
            rbox("RearF_Exit%s_Pier1" % side, e0 + 0.1, e0 + 0.4, 56.5, 56.8, GZ, 7.2, m_metal, c_fac)
            rbox("RearF_Exit%s_Pier2" % side, e1 - 0.4, e1 - 0.1, 58.6, 58.9, GZ, 6.3, m_metal, c_fac)
        groups["towers"] = len(created) - n0

        # ---------- CENTER: cubical hall around the lift core ----------
        n0 = len(created)
        # shell: west wall w/ 21 m merge opening, east wall w/ door to offices
        rbox("CHall_Wall_W_S", -25.0, -24.5, 0.0, 2.0, LZ0, CT, m_wall, c_hall)
        rbox("CHall_Wall_W_Hdr", -25.0, -24.5, 2.0, 23.0, LZ0 + 3.5, CT, m_wall, c_hall)
        rbox("CHall_Wall_W_N", -25.0, -24.5, 23.0, 50.0, LZ0, CT, m_wall, c_hall)
        rbox("CHall_Wall_E_S", 24.5, 25.0, 0.0, 15.0, LZ0, CT, m_wall, c_hall)
        rbox("CHall_Wall_E_Hdr", 24.5, 25.0, 15.0, 18.0, LZ0 + 3.0, CT, m_wall, c_hall)
        rbox("CHall_Wall_E_N", 24.5, 25.0, 18.0, 50.0, LZ0, CT, m_wall, c_hall)
        # floor around the open core zone (x -4..4, y 1..9 stays void for the
        # lift + helix stairs arriving from the basement)
        rbox("CHall_Floor_S", -24.5, 24.5, 0.0, 1.0, LZ0, FT, m_floor, c_hall)
        rbox("CHall_Floor_W", -24.5, -4.0, 1.0, 9.0, LZ0, FT, m_floor, c_hall)
        rbox("CHall_Floor_E", 4.0, 24.5, 1.0, 9.0, LZ0, FT, m_floor, c_hall)
        rbox("CHall_Floor_N", -24.5, 24.5, 9.0, 49.5, LZ0, FT, m_floor, c_hall)
        # lobby north wall re-split: two flanking 4 m doorways into the hall
        rbox("Lobby_Wall_N_W_A", -25.0, -20.0, -0.5, 0.0, LZ0, LT, m_wall, c_hall)
        rbox("Lobby_Wall_N_W_H", -20.0, -16.0, -0.5, 0.0, LZ0 + 3.5, LT, m_wall, c_hall)
        rbox("Lobby_Wall_N_W_B", -16.0, -2.6, -0.5, 0.0, LZ0, LT, m_wall, c_hall)
        rbox("Lobby_Wall_N_E_A", 2.6, 16.0, -0.5, 0.0, LZ0, LT, m_wall, c_hall)
        rbox("Lobby_Wall_N_E_H", 16.0, 20.0, -0.5, 0.0, LZ0 + 3.5, LT, m_wall, c_hall)
        rbox("Lobby_Wall_N_E_B", 20.0, 25.0, -0.5, 0.0, LZ0, LT, m_wall, c_hall)
        rbox("CHall_Thresh_W", -20.0, -16.0, -0.5, 0.0, LZ0, FT, m_floor, c_hall)
        rbox("CHall_Thresh_E", 16.0, 20.0, -0.5, 0.0, LZ0, FT, m_floor, c_hall)
        # 36 cubicles (3x the previous 12 per user request) in two dense banks
        ci = 0
        for sx in (-22.8, -17.4, -12.0, 6.6, 12.0, 17.4):
            for sy in (12.0, 17.8, 23.6, 29.4, 35.2, 41.0):
                ci += 1
                pre = "CHall_Cub_%d" % ci
                rbox(pre + "_PartN", sx, sx + 5.2, sy + 5.52, sy + 5.6, LZ0, 10.9, m_grey, c_hall)
                rbox(pre + "_PartW", sx, sx + 0.08, sy, sy + 5.6, LZ0, 10.9, m_grey, c_hall)
                rbox(pre + "_Desk", sx + 0.7, sx + 3.9, sy + 4.2, sy + 5.0, LZ0, 10.05, m_wood, c_hall)
                rbox(pre + "_Mon", sx + 1.9, sx + 2.6, sy + 4.65, sy + 4.73, 10.05, 10.5, m_metal, c_hall)
                rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, sx + 2.3, sy + 3.5, m_couch, c_hall)
        # services: spine + 4 diffusers + tray with color runs + drops + panel
        rcyl_ax("CHall_Svc_Duct", 0.35, 36.0, (0.0, 30.0, 14.55), "x", m_duct, c_hall)
        for di, px in enumerate((-14.0, -5.0, 5.0, 14.0)):
            rcylz("CHall_Svc_Diff_%d_Stub" % (di + 1), 0.24, 13.75, 14.35, px, 30.0, m_duct, c_hall)
            rcylz("CHall_Svc_Diff_%d_Plate" % (di + 1), 0.5, 13.63, 13.75, px, 30.0, m_duct, c_hall)
        rbox("CHall_Svc_Tray", -18.0, 18.0, 28.55, 29.05, 13.95, 14.05, m_metal, c_hall)
        for bname, bm_, off in (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14)):
            rbox("CHall_Svc_Run_%s" % bname, -18.0, 18.0,
                 28.8 + off - 0.045, 28.8 + off + 0.045, 14.05, 14.12, bm_, c_hall)
        for dn, dx in (("W_P", -14.0), ("W_D", -13.7), ("E_P", 13.7), ("E_D", 14.0)):
            mm = m_amber if dn.endswith("_P") else m_teal
            rbox("CHall_Svc_Drop_%s" % dn, dx - 0.04, dx + 0.04, 28.76, 28.84, 10.9, 13.95, mm, c_hall)
        rbox("CHall_Svc_Panel", 24.2, 24.5, 22.0, 23.2, FT + 0.15, FT + 1.95, m_metal, c_hall)
        groups["hall"] = len(created) - n0

        # ---------- WEST rear L1: recruitment lab + merged cubicles ----------
        n0 = len(created)
        rbox("RearW_Floor", -49.5, -25.0, 0.5, 49.5, LZ0, FT, m_floor, c_west)
        rbox("RearW_Wall_W", -50.0, -49.5, 0.0, 50.0, LZ0, CT, m_wall, c_west)
        rbox("RearW_Wall_S", -50.0, -25.0, 0.0, 0.5, LZ0, CT, m_wall, c_west)
        # lab partition with screen; two door gaps
        rbox("RearW_Lab_Part_A", -49.5, -46.0, 25.0, 25.3, LZ0, CT, m_wall, c_west)
        rbox("RearW_Lab_Part_H1", -46.0, -44.0, 25.0, 25.3, LZ0 + 3.0, CT, m_wall, c_west)
        rbox("RearW_Lab_Part_B", -44.0, -30.0, 25.0, 25.3, LZ0, CT, m_wall, c_west)
        rbox("RearW_Lab_Part_H2", -30.0, -28.0, 25.0, 25.3, LZ0 + 3.0, CT, m_wall, c_west)
        rbox("RearW_Lab_Part_C", -28.0, -25.0, 25.0, 25.3, LZ0, CT, m_wall, c_west)
        rbox("RearW_Lab_ScreenFrame", -43.2, -31.8, 25.3, 25.42, 10.0, 13.7, m_metal, c_west)
        rbox("RearW_Lab_Screen", -43.0, -32.0, 25.42, 25.5, 10.2, 13.5, m_cera, c_west)
        rbox("RearW_Lab_Projector", -38.0, -37.4, 30.7, 31.3, 14.0, 14.3, m_metal, c_west)
        rbox("RearW_Lab_ProjMount", -37.73, -37.67, 30.97, 31.03, 14.3, CT, m_metal, c_west)
        # 5 rows x 10 networked seats, all facing SOUTH toward the screen
        for ri, ry in enumerate((29.5, 33.2, 36.9, 40.6, 44.3)):
            rbox("RearW_Lab_Row%d_Counter" % (ri + 1), -42.5, -27.0, ry, ry + 0.8, LZ0, 10.05, m_wood, c_west)
            for j in range(10):
                cx = -41.7 + j * 1.55
                rbox("RearW_Lab_Row%d_Mon%02d" % (ri + 1, j + 1),
                     cx - 0.27, cx + 0.27, ry + 0.06, ry + 0.14, 10.05, 10.45, m_metal, c_west)
                rcylz("RearW_Lab_Row%d_Stool%02d" % (ri + 1, j + 1),
                      0.22, FT, FT + 0.5, cx, ry + 1.35, m_couch, c_west)
        # merged-cubical section (south of the lab, open to the hall) - doubled
        ci = 0
        for sx in (-48.6, -43.2, -37.8, -32.4):
            for sy in (3.0, 9.2, 15.4):
                ci += 1
                pre = "RearW_Cub_%d" % ci
                rbox(pre + "_PartN", sx, sx + 4.4, sy + 5.92, sy + 6.0, LZ0, 10.9, m_grey, c_west)
                rbox(pre + "_PartW", sx, sx + 0.08, sy, sy + 6.0, LZ0, 10.9, m_grey, c_west)
                rbox(pre + "_Desk", sx + 0.6, sx + 3.6, sy + 4.6, sy + 5.4, LZ0, 10.05, m_wood, c_west)
                rbox(pre + "_Mon", sx + 1.7, sx + 2.3, sy + 5.0, sy + 5.08, 10.05, 10.5, m_metal, c_west)
                rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, sx + 2.1, sy + 3.9, m_couch, c_west)
        # services: spine through both sections + net drops to every lab row
        rcyl_ax("RearW_Svc_Duct", 0.35, 43.0, (-37.5, 25.5, 14.55), "y", m_duct, c_west)
        for di, py in enumerate((9.0, 20.0, 33.0, 45.0)):
            rcylz("RearW_Svc_Diff_%d_Stub" % (di + 1), 0.24, 13.75, 14.35, -37.5, py, m_duct, c_west)
            rcylz("RearW_Svc_Diff_%d_Plate" % (di + 1), 0.5, 13.63, 13.75, -37.5, py, m_duct, c_west)
        rbox("RearW_Svc_Tray", -36.45, -35.95, 4.0, 47.0, 13.95, 14.05, m_metal, c_west)
        for bname, bm_, off in (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14)):
            rbox("RearW_Svc_Run_%s" % bname, -36.2 + off - 0.045, -36.2 + off + 0.045,
                 4.0, 47.0, 14.05, 14.12, bm_, c_west)
        for ri, ry in enumerate((29.9, 33.6, 37.3, 41.0, 44.7)):
            rbox("RearW_Svc_NetDrop_%d" % (ri + 1), -36.24, -36.16, ry - 0.04, ry + 0.04,
                 10.1, 13.95, m_teal, c_west)
        for ci2, cy in enumerate((7.0, 18.0)):
            rbox("RearW_Svc_PwrDrop_%d" % (ci2 + 1), -36.24, -36.16, cy - 0.04, cy + 0.04,
                 10.95, 13.95, m_amber, c_west)
        rbox("RearW_Svc_Panel", -49.35, -49.2, 8.0, 9.2, FT + 0.15, FT + 1.95, m_metal, c_west)
        groups["west"] = len(created) - n0

        # ---------- EAST rear L1: private head-of-department offices ----------
        n0 = len(created)
        rbox("RearE_Floor", 25.0, 49.5, 0.5, 49.5, LZ0, FT, m_floor, c_east)
        rbox("RearE_Wall_E", 49.5, 50.0, 0.0, 50.0, LZ0, CT, m_wall, c_east)
        rbox("RearE_Wall_S_A", 25.0, 34.0, 0.0, 0.5, LZ0, CT, m_wall, c_east)
        rbox("RearE_Wall_S_Hdr", 34.0, 37.0, 0.0, 0.5, LZ0 + 3.0, CT, m_wall, c_east)
        rbox("RearE_Wall_S_B", 37.0, 50.0, 0.0, 0.5, LZ0, CT, m_wall, c_east)
        # HR-side wall re-split with the same connecting doorway (x 34..37)
        rbox("EWing_Wall_N_A", 25.0, 34.0, -0.5, 0.0, LZ0, CT, m_wall, c_east)
        rbox("EWing_Wall_N_Hdr", 34.0, 37.0, -0.5, 0.0, LZ0 + 3.0, CT, m_wall, c_east)
        rbox("EWing_Wall_N_B", 37.0, 50.0, -0.5, 0.0, LZ0, CT, m_wall, c_east)
        rbox("RearE_Thresh", 34.0, 37.0, -0.5, 0.5, LZ0, FT, m_floor, c_east)
        # 4 private offices along the rear windows, FULL-height walls + doors
        for pi, px in enumerate((30.0, 34.5, 39.0)):
            rbox("RearE_Off_Part_%d" % (pi + 1), px, px + 0.3, TSY0, 49.5, LZ0, CT, m_wall, c_east)
        cells = ((25.5, 30.0), (30.3, 34.5), (34.8, 39.0), (39.3, 43.5))
        for oi, (ox0, ox1) in enumerate(cells):
            pre = "RearE_Off_%d" % (oi + 1)
            cx = (ox0 + ox1) / 2
            rbox(pre + "_FrontA", ox0, cx - 0.6, TSY0, TSY0 + 0.3, LZ0, CT, m_wall, c_east)
            rbox(pre + "_FrontHdr", cx - 0.6, cx + 0.6, TSY0, TSY0 + 0.3, LZ0 + 2.6, CT, m_wall, c_east)
            rbox(pre + "_FrontB", cx + 0.6, ox1, TSY0, TSY0 + 0.3, LZ0, CT, m_wall, c_east)
            rbox(pre + "_Desk", cx - 1.0, cx + 1.0, 47.4, 48.3, LZ0, 10.05, m_wood, c_east)
            rcylz(pre + "_Chair", 0.32, FT, FT + 0.55, cx, 46.8, m_couch, c_east)
            rbox(pre + "_Cab", ox1 - 1.1, ox1 - 0.3, 44.1, 44.6, LZ0, 10.4, m_grey, c_east)
            rcylz(pre + "_Guest", 0.26, FT, FT + 0.5, cx - 1.2, 45.6, m_couch, c_east)
        rbox("RearE_Sec_Desk", 34.8, 37.2, 29.5, 30.4, LZ0, 10.05, m_wood, c_east)
        rcylz("RearE_Sec_Chair", 0.32, FT, FT + 0.55, 36.0, 28.9, m_couch, c_east)
        rbox("RearE_Bench", 29.0, 32.0, 20.0, 20.8, FT, FT + 0.45, m_wood, c_east)
        # services
        rcyl_ax("RearE_Svc_Duct", 0.35, 37.0, (37.5, 23.5, 14.55), "y", m_duct, c_east)
        for di, py in enumerate((10.0, 26.0, 40.0)):
            rcylz("RearE_Svc_Diff_%d_Stub" % (di + 1), 0.24, 13.75, 14.35, 37.5, py, m_duct, c_east)
            rcylz("RearE_Svc_Diff_%d_Plate" % (di + 1), 0.5, 13.63, 13.75, 37.5, py, m_duct, c_east)
        rbox("RearE_Svc_Tray", 35.95, 36.45, 5.0, 42.0, 13.95, 14.05, m_metal, c_east)
        for bname, bm_, off in (("Amber", m_amber, -0.14), ("Teal", m_teal, 0.0), ("Red", m_red, 0.14)):
            rbox("RearE_Svc_Run_%s" % bname, 36.2 + off - 0.045, 36.2 + off + 0.045,
                 5.0, 42.0, 14.05, 14.12, bm_, c_east)
        for dn, off in (("P", -0.2), ("D", 0.2)):
            mm = m_amber if dn == "P" else m_teal
            rbox("RearE_Svc_Drop_%s" % dn, 36.2 + off - 0.04, 36.2 + off + 0.04,
                 41.92, 42.0, 10.9, 13.95, mm, c_east)
        rbox("RearE_Svc_Panel", 30.0, 31.2, 0.5, 0.8, FT + 0.15, FT + 1.95, m_metal, c_east)
        groups["east"] = len(created) - n0

        # ---------- REAR FACADE: solid wall + punched windows with curtains ----------
        n0 = len(created)
        rbox("RearF_L1_Sill", -TSX0, TSX0, 49.5, 50.0, LZ0, 10.4, m_wall, c_fac)
        rbox("RearF_L1_Hdr", -TSX0, TSX0, 49.5, 50.0, 13.2, CT, m_wall, c_fac)
        PW, WW = 1.762, 2.5           # pier / window widths, 20 windows
        px = -TSX0
        for i in range(20):
            rbox("RearF_L1_Pier_%02d" % (i + 1), px, px + PW, 49.5, 50.0, 10.4, 13.2, m_wall, c_fac)
            wl = px + PW
            rbox("RearF_L1_Glass_%02d" % (i + 1), wl, wl + WW, 49.62, 49.87, 10.4, 13.2, m_glass, c_fac)
            rbox("RearF_L1_CurtW_%02d" % (i + 1), wl + 0.05, wl + 1.05, 49.32, 49.44, 10.2, 13.35, m_curt, c_fac)
            rbox("RearF_L1_CurtE_%02d" % (i + 1), wl + WW - 1.05, wl + WW - 0.05, 49.32, 49.44, 10.2, 13.35, m_curt, c_fac)
            px = wl + WW
        rbox("RearF_L1_Pier_21", px, TSX0, 49.5, 50.0, 10.4, 13.2, m_wall, c_fac)
        # cosmetic curtained windows on levels 2..8 (proud of the massing face)
        for k in range(2, 9):
            zb = LZ0 + (k - 1) * H
            for j in range(14):
                cx = -39.0 + j * 6.0
                rbox("RearF_Up_L%d_W%02d_C" % (k, j + 1), cx - 1.25, cx + 1.25,
                     50.0, 50.06, zb + 1.1, zb + 3.9, m_curt, c_fac)
                rbox("RearF_Up_L%d_W%02d_G" % (k, j + 1), cx - 1.25, cx + 1.25,
                     50.06, 50.14, zb + 1.1, zb + 3.9, m_glass, c_fac)
        groups["facade"] = len(created) - n0

        scene["zy_rear"] = json.dumps({
            "towers": [[TSX0, TSX1, TSY0, TSY1], [-TSX1, -TSX0, TSY0, TSY1]],
            "exit_doors_x": [[XDW0, XDW1], [-XDW1, -XDW0]],
            "hall_lobby_doors": [[-20.0, -16.0], [16.0, 20.0]],
            "merge_opening_y": [2.0, 23.0], "hall_office_door_y": [15.0, 18.0],
            "hr_offices_door_x": [34.0, 37.0], "lab_y": [25.3, 49.5]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_rear", "created": len(created),
                       "retired": retired, "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_rear", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_rear_blocks, first_interval=0.1)
