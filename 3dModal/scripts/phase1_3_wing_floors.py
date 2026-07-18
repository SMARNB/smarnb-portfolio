# Zyvion Phase 1.3f — WING UPPER FLOORS (user markup 2026-07-18, ORANGE):
# hollows levels 2..8 of BOTH side wings (front + rear halves, 28 half-floors)
# into office floors: slab, perimeter walls, cosmetic curtained windows on the
# outer/front faces, stair-shaft enclosure with a door at every level, a
# conference room + 3-4 private offices per half, y=0 connecting doorway per
# level, and a raycastable floor tag (Floor_Tag_*) mapping floors to website
# pages: W2 Services, W3 Store, W4 Blog, W5 Work, W6 Projects (+ the
# Room_Project_Tracking tag on the W6 rear conference room), W7 HoD_Offices,
# W8 Directors_West; E2 Conference_Center, E3-E5 Departments_A/B/C,
# E6 Operations, E7 Directors, E8 FOUNDERS_CEO (bigger boardroom).
# Level-8 halves also get roof slabs (z 58.03..58.28) with the shaft left
# open for the rooftop bulkheads (phase1_3_rooftop.py).
# Requires scene["zy_plinth"] + scene["zy_lobby"].
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent.
# Order: ... -> west_wing -> east_wing -> rear_blocks -> THIS.

def zy_wing_floors():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_floors_status.json"
    created = []
    groups = {"floors": 0, "windows": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_floors", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        for key in ("zy_plinth", "zy_lobby"):
            if key not in scene.keys():
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump({"ok": False, "step": "phase1_3_floors",
                               "error": "scene['%s'] missing" % key}, f, indent=1)
                return

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
            if ax1 - ax0 < 0.01 or ay1 - ay0 < 0.01 or az1 - az0 < 0.01:
                return None
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

        p = json.loads(scene["zy_plinth"])
        H = 6.1
        LZ0 = p["z1"]
        RT = LZ0 + 8 * H                    # 58.03 roof

        m_slab = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_wood = mkmat("ZY_Wood_Warm", "#8C6748")
        m_couch = mkmat("ZY_Couch_Charcoal", "#3A3F46", rough=0.95)
        m_scrn = mkmat("ZY_Screen_Teal", "#0E4350", rough=0.3)
        m_curt = mkmat("ZY_Curtain_Cream", "#D9CBB0", rough=0.9)
        m_floor = mkmat("ZY_Lobby_Floor", "#CDC9C0", rough=0.55)

        c_wf = get_coll("Wing_West_Floors", root)
        c_ef = get_coll("Wing_East_Floors", root)

        # sweep: own names + the solid/ring stack generations from earlier scripts
        for n in [o.name for o in bpy.data.objects if o.name.startswith(
                ("WFloor_", "EFloor_", "Floor_Tag_", "Room_Project",
                 "WWing_Stack_", "EWing_Stack_", "RearW_Stack_", "RearE_Stack_"))]:
            kill(n)

        PAGES = {("W", 2): "Services", ("W", 3): "Store", ("W", 4): "Blog",
                 ("W", 5): "Work", ("W", 6): "Projects", ("W", 7): "HoD_Offices",
                 ("W", 8): "Directors_West", ("E", 2): "Conference_Center",
                 ("E", 3): "Departments_A", ("E", 4): "Departments_B",
                 ("E", 5): "Departments_C", ("E", 6): "Operations",
                 ("E", 7): "Directors", ("E", 8): "Founders_CEO"}

        def floor_kit(wing, half, k):
            zb = LZ0 + (k - 1) * H
            zt = zb + H
            zw = zb + 0.35
            hx0, hx1 = (-50.0, -25.0) if wing == "W" else (25.0, 50.0)
            hy0, hy1 = (-50.0, 0.0) if half == "F" else (0.0, 50.0)
            pre = "%sFloor_%s%d_" % (wing, half, k)
            coll = c_wf if wing == "W" else c_ef
            if half == "F":
                sx0, sx1, sy0, sy1 = ((-31.5, -25.5, -6.5, -0.5) if wing == "W"
                                      else (25.5, 31.5, -6.5, -0.5))
                sdoor = (-29.0, -27.0) if wing == "W" else (27.0, 29.0)
            else:
                sx0, sx1, sy0, sy1 = ((-49.5, -43.5, 43.5, 49.5) if wing == "W"
                                      else (43.5, 49.5, 43.5, 49.5))
                sdoor = (-47.6, -45.6) if wing == "W" else (45.6, 47.6)
            near_x1 = (hx1 - sx1) < 1.0
            main = (hx0, sx0) if near_x1 else (sx1, hx1)
            sliv = (sx1, hx1) if near_x1 else (hx0, sx0)

            def hslab(tag, z0, z1, mat):
                rbox(pre + tag + "_A", hx0, hx1, hy0, sy0, z0, z1, mat, coll)
                rbox(pre + tag + "_B", main[0], main[1], sy0, sy1, z0, z1, mat, coll)
                rbox(pre + tag + "_Bs", sliv[0], sliv[1], sy0, sy1, z0, z1, mat, coll)
                rbox(pre + tag + "_C", hx0, hx1, sy1, hy1, z0, z1, mat, coll)

            hslab("Slab", zb, zb + 0.35, m_slab)
            if k == 8:
                hslab("Roof", RT, RT + 0.25, m_slab)
            # perimeter walls
            if wing == "W":
                rbox(pre + "Wall_Out", hx0, hx0 + 0.4, hy0, hy1, zw, zt, m_wall, coll)
                iw0, iw1 = hx1 - 0.4, hx1
            else:
                rbox(pre + "Wall_Out", hx1 - 0.4, hx1, hy0, hy1, zw, zt, m_wall, coll)
                iw0, iw1 = hx0, hx0 + 0.4
            if half == "F" and k in (2, 3, 4):
                rbox(pre + "Wall_In_A", iw0, iw1, hy0, -5.0, zw, zt, m_wall, coll)
                rbox(pre + "Wall_In_H", iw0, iw1, -5.0, -2.0, zb + 3.0, zt, m_wall, coll)
                rbox(pre + "Wall_In_B", iw0, iw1, -2.0, hy1, zw, zt, m_wall, coll)
            else:
                rbox(pre + "Wall_In", iw0, iw1, hy0, hy1, zw, zt, m_wall, coll)
            if half == "F":
                rbox(pre + "Wall_S", hx0, hx1, hy0, hy0 + 0.4, zw, zt, m_wall, coll)
                yw0, yw1 = -0.4, 0.0
            else:
                rbox(pre + "Wall_N", hx0, hx1, hy1 - 0.4, hy1, zw, zt, m_wall, coll)
                yw0, yw1 = 0.0, 0.4
            g0, g1 = (-39.0, -36.0) if wing == "W" else (36.0, 39.0)
            rbox(pre + "Wall_Y0_A", hx0 + 0.4, g0, yw0, yw1, zw, zt, m_wall, coll)
            rbox(pre + "Wall_Y0_H", g0, g1, yw0, yw1, zb + 3.35, zt, m_wall, coll)
            rbox(pre + "Wall_Y0_B", g1, hx1 - 0.4, yw0, yw1, zw, zt, m_wall, coll)
            # shaft enclosure with a door at this level
            if near_x1:
                rbox(pre + "Shaft_X", sx0, sx0 + 0.4, sy0, sy1, zw, zt, m_wall, coll)
                fx0, fx1 = sx0 + 0.4, sx1
            else:
                rbox(pre + "Shaft_X", sx1 - 0.4, sx1, sy0, sy1, zw, zt, m_wall, coll)
                fx0, fx1 = sx0, sx1 - 0.4
            rbox(pre + "Shaft_S_A", fx0, sdoor[0], sy0, sy0 + 0.4, zw, zt, m_wall, coll)
            rbox(pre + "Shaft_S_H", sdoor[0], sdoor[1], sy0, sy0 + 0.4, zb + 3.35, zt, m_wall, coll)
            rbox(pre + "Shaft_S_B", sdoor[1], fx1, sy0, sy0 + 0.4, zw, zt, m_wall, coll)
            # cosmetic curtained windows: outer face (7) + front face (6, F only)
            n_w0 = len(created)
            for j in range(7):
                cy = hy0 + 6.5 + j * 6.2
                if wing == "W":
                    rbox(pre + "WinO%d_C" % j, hx0 - 0.06, hx0, cy - 1.25, cy + 1.25, zb + 1.1, zb + 3.9, m_curt, coll)
                    rbox(pre + "WinO%d_G" % j, hx0 - 0.14, hx0 - 0.06, cy - 1.25, cy + 1.25, zb + 1.1, zb + 3.9, m_glass, coll)
                else:
                    rbox(pre + "WinO%d_C" % j, hx1, hx1 + 0.06, cy - 1.25, cy + 1.25, zb + 1.1, zb + 3.9, m_curt, coll)
                    rbox(pre + "WinO%d_G" % j, hx1 + 0.06, hx1 + 0.14, cy - 1.25, cy + 1.25, zb + 1.1, zb + 3.9, m_glass, coll)
            if half == "F":
                for j in range(6):
                    cx = hx0 + 4.0 + j * 3.6
                    rbox(pre + "WinS%d_C" % j, cx - 1.2, cx + 1.2, hy0 - 0.06, hy0, zb + 1.1, zb + 3.9, m_curt, coll)
                    rbox(pre + "WinS%d_G" % j, cx - 1.2, cx + 1.2, hy0 - 0.14, hy0 - 0.06, zb + 1.1, zb + 3.9, m_glass, coll)
            groups["windows"] += len(created) - n_w0
            # outer-side office row (fronts 10.6 m in) + partitions
            ro0, ro1 = (hx0 + 0.4, hx0 + 10.6) if wing == "W" else (hx1 - 10.6, hx1 - 0.4)
            fr0, fr1 = (ro1, ro1 + 0.3) if wing == "W" else (ro0 - 0.3, ro0)
            row_end = sy0 - 0.4 if not near_x1 else hy1 - 0.4
            parts = [hy0 + 12.5, hy0 + 25.0]
            if row_end > hy0 + 38.0:
                parts.append(hy0 + 37.5)
            for pi, py in enumerate(parts):
                rbox(pre + "Part%d" % pi, ro0, ro1, py, py + 0.3, zw, zb + 3.55, m_wall, coll)
            cells = []
            prev = hy0 + 0.4
            for py in parts:
                cells.append((prev, py))
                prev = py + 0.3
            cells.append((prev, row_end))
            for oi, (oy0, oy1) in enumerate(cells):
                if oy1 - oy0 < 4.0:
                    continue
                cy = (oy0 + oy1) / 2
                rbox(pre + "OfF%d_A" % oi, fr0, fr1, oy0, cy - 0.7, zw, zb + 3.55, m_wall, coll)
                rbox(pre + "OfF%d_B" % oi, fr0, fr1, cy + 0.7, oy1, zw, zb + 3.55, m_wall, coll)
                dx0, dx1 = (ro0 + 0.4, ro0 + 2.4) if wing == "W" else (ro1 - 2.4, ro1 - 0.4)
                rbox(pre + "OfD%d" % oi, dx0, dx1, cy + 1.0, cy + 1.9, zb + 0.35, zb + 1.17, m_wood, coll)
                rcylz(pre + "OfC%d" % oi, 0.3, zb + 0.35, zb + 0.9, (dx0 + dx1) / 2, cy + 2.6, m_couch, coll)
            # conference room on the inner side (CEO boardroom on E8)
            cw0, cw1 = (hx1 - 10.6, hx1 - 0.4) if wing == "W" else (hx0 + 0.4, hx0 + 10.6)
            cf0, cf1 = (cw0 - 0.3, cw0) if wing == "W" else (cw1, cw1 + 0.3)
            if half == "F":
                cy0, cy1_ = hy0 + 0.4, hy0 + 14.0
            else:
                cy0, cy1_ = hy1 - 14.0, hy1 - 0.4
            rbox(pre + "Conf_End", cw0, cw1, cy1_ if half == "F" else cy0 - 0.3,
                 (cy1_ + 0.3) if half == "F" else cy0, zw, zb + 3.55, m_wall, coll)
            cm = (cy0 + cy1_) / 2
            rbox(pre + "Conf_F_A", cf0, cf1, cy0, cm - 0.8, zw, zb + 3.55, m_wall, coll)
            rbox(pre + "Conf_F_B", cf0, cf1, cm + 0.8, cy1_, zw, zb + 3.55, m_wall, coll)
            big = (wing == "E" and k == 8 and half == "F")
            tl = 5.5 if big else 4.0
            tw = 2.0 if big else 1.6
            tcx = (cw0 + cw1) / 2
            rboxr(pre + "Conf_Table", tl, tw, 0.4, tcx, cm, zb + 0.75, math.pi / 2, m_wood, coll)
            for ci2 in range(6):
                ang = ci2 * math.pi / 3
                rcylz(pre + "Conf_Ch%d" % ci2, 0.28, zb + 0.35, zb + 0.85,
                      tcx + 1.6 * math.cos(ang), cm + (tl / 2 + 0.7) * math.sin(ang) * 0.55, m_couch, coll)
            # floor tag (front halves): raycastable page plate by the y=0 door
            if half == "F":
                page = PAGES[(wing, k)]
                tx0, tx1 = (-35.5, -33.7) if wing == "W" else (33.7, 35.5)
                rbox("Floor_Tag_%s" % page, tx0, tx1, -0.46, -0.4, zb + 1.5, zb + 2.4, m_scrn, coll)
            if wing == "W" and k == 6 and half == "R":
                rbox("Room_Project_Tracking", cf1, cf1 + 0.06, cm - 0.9, cm + 0.9,
                     zb + 1.5, zb + 2.4, m_scrn, coll)

        n0 = len(created)
        for wing in ("W", "E"):
            for k in range(2, 9):
                for half in ("F", "R"):
                    floor_kit(wing, half, k)
        groups["floors"] = len(created) - n0 - groups["windows"]

        scene["zy_floors"] = json.dumps({"%s%d" % (w, k): v for (w, k), v in PAGES.items()})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_floors", "created": len(created),
                       "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_floors", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_wing_floors, first_interval=0.1)
