# Zyvion Phase 1.3g — ROOFTOP (user markup 2026-07-18, items 6 + 7):
#   - Roof deck over the center-rear column (x -25..25, y 0..50) + parapet ring
#     around the whole footprint; lift-core overrun penthouse.
#   - Item 6: a roof-access BULKHEAD room over EACH of the 4 staircases
#     (2 front wing shafts + 2 rear towers), each with a door + pitched cap.
#   - Item 7.1: HELIPAD (marked pad, H, perimeter lights, FATO ring) + a
#     DETAILED HELICOPTER (fuselage, cockpit glass, tail boom, tail rotor,
#     main rotor hub + 4 blades, twin skids, engine deck).
#   - Item 7.2: SOLAR array on both wing roofs (tilted panels in rows) feeding a
#     Solar_Plant_Room (inverters + battery banks) with a DC bus + a riser
#     conduit down the core = "connected to the entire building".
# Requires scene["zy_plinth"].
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# Roof_/Heli_/Solar_/Bulkhead_ sweeps. Order: ... -> wing_floors -> THIS.

def zy_rooftop():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_roof_status.json"
    created = []
    groups = {"deck": 0, "bulkheads": 0, "helipad": 0, "heli": 0, "solar": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_roof", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        if "zy_plinth" not in scene.keys():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_roof", "error": "scene['zy_plinth'] missing"}, f, indent=1)
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

        def rboxr(name, sx, sy, sz, cx, cy, cz, rx, ry, rz, m, coll):
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
            ob.rotation_euler = (rx, ry, rz)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        def rcyl(name, r, length, center, axis, m, coll, seg=16):
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

        def rtaper(name, r1, r2, length, center, axis, m, coll, seg=16):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r1, radius2=r2, depth=length)
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

        p = json.loads(scene["zy_plinth"])
        H = 6.1
        LZ0 = p["z1"]
        RT = LZ0 + 8 * H                    # 58.03 roof top of slab bottom
        RD = RT + 0.25                      # 58.28 finished roof deck top

        m_slab = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_red = mkmat("ZY_Accent_Red", "#C04848")
        m_deck = mkmat("ZY_Deck_Grey", "#6B6E72", rough=0.9)
        m_duct = mkmat("ZY_Duct_Silver", "#AEB6BD", rough=0.35)
        m_pad = mkmat("ZY_Helipad_Dark", "#33383B", rough=0.95)      # new
        m_mark = mkmat("ZY_Helipad_Mark", "#E8E4D0", rough=0.6)      # new
        m_solar = mkmat("ZY_Solar_Cell", "#1B2A4A", rough=0.25)      # new
        m_body = mkmat("ZY_Heli_Body", "#37506B", rough=0.5)        # new

        c_roof = get_coll("Rooftop", root)
        c_heli = get_coll("Rooftop_Helipad", root)
        c_solar = get_coll("Rooftop_Solar", root)

        for n in [o.name for o in bpy.data.objects if o.name.startswith(
                ("Roof_", "Heli_", "Solar_", "Bulkhead_"))]:
            kill(n)

        # ---------- center-rear roof deck + full-footprint parapet ----------
        n0 = len(created)
        rbox("Roof_Deck_Center", -25.0, 25.0, 0.0, 50.0, RT, RD, m_slab, c_roof)
        PAR = 1.1
        for tag, x0, x1, y0, y1 in (("S", -50.0, 50.0, -50.0, -49.4),
                                    ("N", -50.0, 50.0, 49.4, 50.0),
                                    ("W", -50.0, -49.4, -50.0, 50.0),
                                    ("E", 49.4, 50.0, -50.0, 50.0)):
            rbox("Roof_Parapet_%s" % tag, x0, x1, y0, y1, RD, RD + PAR, m_wall, c_roof)
        # inner parapet around the lobby's lower roof void (front-center)
        rbox("Roof_Parapet_LobbyN", -25.0, 25.0, -0.6, 0.0, RD, RD + PAR, m_wall, c_roof)
        rbox("Roof_Parapet_LobbyW", -25.6, -25.0, -50.0, 0.0, RD, RD + PAR, m_wall, c_roof)
        rbox("Roof_Parapet_LobbyE", 25.0, 25.6, -50.0, 0.0, RD, RD + PAR, m_wall, c_roof)
        # lift-core overrun penthouse (glass shaft pokes up at x-4..4, y1..9)
        rbox("Roof_CoreOverrun_W", -4.4, -4.0, 0.6, 9.4, RD, RD + 3.0, m_wall, c_roof)
        rbox("Roof_CoreOverrun_E", 4.0, 4.4, 0.6, 9.4, RD, RD + 3.0, m_wall, c_roof)
        rbox("Roof_CoreOverrun_N", -4.4, 4.4, 9.0, 9.4, RD, RD + 3.0, m_wall, c_roof)
        rbox("Roof_CoreOverrun_S", -4.4, 4.4, 0.6, 1.0, RD, RD + 3.0, m_wall, c_roof)
        rbox("Roof_CoreOverrun_Cap", -4.6, 4.6, 0.4, 9.6, RD + 3.0, RD + 3.25, m_slab, c_roof)
        groups["deck"] = len(created) - n0

        # ---------- item 6: roof-access bulkhead room over each staircase ----------
        n0 = len(created)
        # (tag, cx0,cx1,cy0,cy1); door centered on the south face
        shafts = [("WF", -31.5, -25.5, -6.5, -0.5), ("EF", 25.5, 31.5, -6.5, -0.5),
                  ("NW", -49.5, -43.5, 43.5, 49.5), ("NE", 43.5, 49.5, 43.5, 49.5)]
        for tag, x0, x1, y0, y1 in shafts:
            zt = RD + 3.2
            dcx = (x0 + x1) / 2
            rbox("Bulkhead_%s_WN" % tag, x0, x1, y1 - 0.3, y1, RD, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_WW" % tag, x0, x0 + 0.3, y0, y1, RD, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_WE" % tag, x1 - 0.3, x1, y0, y1, RD, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_WS_A" % tag, x0, dcx - 0.9, y0, y0 + 0.3, RD, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_WS_B" % tag, dcx + 0.9, x1, y0, y0 + 0.3, RD, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_WS_H" % tag, dcx - 0.9, dcx + 0.9, y0, y0 + 0.3, RD + 2.4, zt, m_wall, c_roof)
            rbox("Bulkhead_%s_Door" % tag, dcx - 0.85, dcx + 0.85, y0 + 0.05, y0 + 0.12, RD, RD + 2.4, m_metal, c_roof)
            rbox("Bulkhead_%s_Cap" % tag, x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, zt, zt + 0.3, m_slab, c_roof)
        groups["bulkheads"] = len(created) - n0

        # ---------- item 7.1: helipad + detailed helicopter ----------
        n0 = len(created)
        HPC = (0.0, 30.0)
        rcyl("Roof_Helipad_Pad", 11.0, 0.15, (HPC[0], HPC[1], RD + 0.075), "z", m_pad, c_heli, seg=48)
        rcyl("Roof_Helipad_Ring", 10.2, 0.05, (HPC[0], HPC[1], RD + 0.17), "z", m_mark, c_heli, seg=48)
        rcyl("Roof_Helipad_RingInner", 9.6, 0.06, (HPC[0], HPC[1], RD + 0.16), "z", m_pad, c_heli, seg=48)
        rbox("Roof_Helipad_H_L", HPC[0] - 2.2, HPC[0] - 1.6, HPC[1] - 3.0, HPC[1] + 3.0, RD + 0.16, RD + 0.21, m_mark, c_heli)
        rbox("Roof_Helipad_H_R", HPC[0] + 1.6, HPC[0] + 2.2, HPC[1] - 3.0, HPC[1] + 3.0, RD + 0.16, RD + 0.21, m_mark, c_heli)
        rbox("Roof_Helipad_H_M", HPC[0] - 1.6, HPC[0] + 1.6, HPC[1] - 0.5, HPC[1] + 0.5, RD + 0.16, RD + 0.21, m_mark, c_heli)
        for i in range(12):
            ang = i * math.pi / 6
            rcyl("Roof_Helipad_Light_%d" % i, 0.18, 0.2, (HPC[0] + 10.6 * math.cos(ang), HPC[1] + 10.6 * math.sin(ang), RD + 0.2), "z", m_amber, c_heli, seg=8)

        # detailed helicopter, nose toward -y (south), sitting on skids
        hz = RD + 0.35
        fc = (HPC[0], HPC[1] + 1.0)
        bz = hz + 1.55
        rtaper("Heli_Fuselage", 1.35, 0.55, 8.6, (fc[0], fc[1], bz), "y", m_body, c_heli, seg=18)
        rtaper("Heli_Nose", 1.2, 0.35, 1.6, (fc[0], fc[1] - 5.0, bz - 0.15), "y", m_body, c_heli, seg=16)
        rboxr("Heli_Cockpit", 2.0, 2.2, 1.5, fc[0], fc[1] - 3.4, bz + 0.35, 0.0, 0.0, 0.0, m_glass, c_heli)
        rboxr("Heli_Windshield", 1.9, 1.6, 1.3, fc[0], fc[1] - 4.3, bz + 0.2, -0.5, 0.0, 0.0, m_glass, c_heli)
        rbox("Heli_Door_L", fc[0] - 1.42, fc[0] - 1.36, fc[1] - 2.6, fc[1] - 0.4, bz - 0.7, bz + 0.7, m_amber, c_heli)
        rbox("Heli_Door_R", fc[0] + 1.36, fc[0] + 1.42, fc[1] - 2.6, fc[1] - 0.4, bz - 0.7, bz + 0.7, m_amber, c_heli)
        rtaper("Heli_TailBoom", 0.5, 0.22, 6.4, (fc[0], fc[1] + 6.6, bz + 0.35), "y", m_body, c_heli, seg=14)
        rboxr("Heli_TailFin", 0.16, 1.4, 2.0, fc[0], fc[1] + 9.7, bz + 1.2, 0.35, 0.0, 0.0, m_body, c_heli)
        rboxr("Heli_Stabilizer", 3.0, 1.0, 0.14, fc[0], fc[1] + 9.2, bz + 0.5, 0.0, 0.0, 0.0, m_body, c_heli)
        rcyl("Heli_TailHub", 0.22, 0.4, (fc[0] + 0.5, fc[1] + 9.9, bz + 1.4), "x", m_metal, c_heli, seg=10)
        for s in (1, -1):
            rboxr("Heli_TailBlade_%d" % s, 0.12, 0.05, 1.5, fc[0] + 0.6, fc[1] + 9.9, bz + 1.4 + s * 1.3, 0.0, 0.0, 0.0, m_metal, c_heli)
        rboxr("Heli_Engine", 2.2, 2.6, 1.0, fc[0], fc[1] + 1.2, bz + 1.25, 0.0, 0.0, 0.0, m_metal, c_heli)
        rcyl("Heli_Exhaust", 0.35, 1.2, (fc[0] + 0.9, fc[1] + 2.6, bz + 1.2), "y", m_metal, c_heli, seg=10)
        rcyl("Heli_Mast", 0.18, 1.1, (fc[0], fc[1] + 0.8, bz + 2.3), "z", m_metal, c_heli, seg=10)
        rcyl("Heli_RotorHub", 0.55, 0.35, (fc[0], fc[1] + 0.8, bz + 2.85), "z", m_metal, c_heli, seg=12)
        for b in range(4):
            ang = b * math.pi / 2 + 0.35
            rboxr("Heli_Blade_%d" % b, 8.4, 0.55, 0.09, fc[0], fc[1] + 0.8, bz + 2.95, 0.0, 0.0, ang, m_metal, c_heli)
        for s, sx in ((0, -1.3), (1, 1.3)):
            rcyl("Heli_Skid_%d" % s, 0.13, 6.0, (fc[0] + sx, fc[1] - 0.5, hz), "y", m_metal, c_heli, seg=10)
            rbox("Heli_SkidStrutF_%d" % s, fc[0] + sx - 0.08, fc[0] + sx + 0.08, fc[1] - 2.3, fc[1] - 2.14, hz, bz - 1.0, m_metal, c_heli)
            rbox("Heli_SkidStrutR_%d" % s, fc[0] + sx - 0.08, fc[0] + sx + 0.08, fc[1] + 1.4, fc[1] + 1.56, hz, bz - 1.0, m_metal, c_heli)
        groups["heli"] = len(created) - n0

        # ---------- item 7.2: solar array + plant room + DC bus + riser ----------
        n0 = len(created)

        def solar_field(prefix, x0, x1, y0, y1):
            ri = 0
            y = y0 + 3.0
            while y < y1 - 3.0:
                ri += 1
                x = x0 + 2.5
                pi = 0
                while x < x1 - 6.5:
                    pi += 1
                    rboxr("%s_R%dP%d" % (prefix, ri, pi), 3.8, 2.2, 0.08,
                          x + 2.0, y, RD + 1.0, -0.44, 0.0, 0.0, m_solar, c_solar)
                    rbox("%s_R%dP%d_LegF" % (prefix, ri, pi), x + 0.3, x + 0.42, y - 1.0, y - 0.88, RD, RD + 0.55, m_metal, c_solar)
                    rbox("%s_R%dP%d_LegB" % (prefix, ri, pi), x + 3.6, x + 3.72, y + 0.88, y + 1.0, RD, RD + 1.45, m_metal, c_solar)
                    x += 4.4
                y += 4.6

        solar_field("Solar_W", -49.0, -25.6, -49.0, 49.0)
        solar_field("Solar_E", 25.6, 49.0, -49.0, 49.0)
        # plant room (inverters + battery banks) on the center-rear roof
        px0, px1, py0, py1 = 15.0, 24.0, 40.0, 48.5
        zt = RD + 3.2
        rbox("Solar_Plant_Wall_N", px0, px1, py1 - 0.3, py1, RD, zt, m_wall, c_solar)
        rbox("Solar_Plant_Wall_E", px1 - 0.3, px1, py0, py1, RD, zt, m_wall, c_solar)
        rbox("Solar_Plant_Wall_W", px0, px0 + 0.3, py0, py1, RD, zt, m_wall, c_solar)
        rbox("Solar_Plant_Wall_S_A", px0, 18.5, py0, py0 + 0.3, RD, zt, m_wall, c_solar)
        rbox("Solar_Plant_Wall_S_H", 18.5, 20.3, py0, py0 + 0.3, RD + 2.4, zt, m_wall, c_solar)
        rbox("Solar_Plant_Wall_S_B", 20.3, px1, py0, py0 + 0.3, RD, zt, m_wall, c_solar)
        rbox("Solar_Plant_Cap", px0 - 0.3, px1 + 0.3, py0 - 0.3, py1 + 0.3, zt, zt + 0.3, m_slab, c_solar)
        for i in range(4):
            rbox("Solar_Inverter_%d" % (i + 1), px0 + 0.8 + i * 1.9, px0 + 2.1 + i * 1.9, py1 - 1.3, py1 - 0.5, RD, RD + 1.8, m_metal, c_solar)
            rbox("Solar_Inverter_%d_Vent" % (i + 1), px0 + 1.0 + i * 1.9, px0 + 1.9 + i * 1.9, py1 - 1.36, py1 - 1.3, RD + 0.4, RD + 1.5, m_amber, c_solar)
        for i in range(5):
            rbox("Solar_Battery_%d" % (i + 1), px0 + 0.8 + i * 1.5, px0 + 2.0 + i * 1.5, py0 + 0.5, py0 + 2.0, RD, RD + 1.6, m_red, c_solar)
        rbox("Solar_DCBus_W", -25.4, 19.0, 44.0, 44.3, RD + 1.6, RD + 1.72, m_metal, c_solar)
        rbox("Solar_DCBus_Run", -25.4, 19.0, 44.1, 44.2, RD + 1.72, RD + 1.79, m_amber, c_solar)
        rbox("Solar_Riser", 18.4, 18.7, 43.6, 43.9, RD - 48.6, RD + 1.6, m_amber, c_solar)
        rbox("Solar_Riser_Label", 17.6, 19.4, 40.0, 40.06, RD + 0.6, RD + 1.6, m_red, c_solar)
        groups["solar"] = len(created) - n0

        scene["zy_roof"] = json.dumps({"deck_top": RD, "helipad": [HPC[0], HPC[1], 11.0],
                                       "bulkheads": [s[0] for s in shafts]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_roof", "created": len(created),
                       "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_roof", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_rooftop, first_interval=0.1)
