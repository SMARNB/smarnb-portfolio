# Zyvion Phase 1.3i — PROPER FENCE GATES + GUARD/ENTRANCE ROOM INTERIOR
# (user feedback 2026-07-18, images 1-3):
#   Item 1/2 - the south fence was a SOLID wall with gate props stuck on it and
#              no opening. It is retired and rebuilt as `Fence_S_*` segments with
#              REAL cutouts: two vehicle gates (IN / OUT) and one pedestrian gate
#              beside the guard room. Proper gates are built in the openings
#              (piers, capped header, barred leaves, track, lamps).
#              The free-standing booth outside the fence is not rebuilt.
#   Item 4   - `Enternace_Area` (the real guard room) is retired and rebuilt
#              HOLLOW so people walk through it: south pedestrian door (from the
#              street), north + west doors into the site, HUGE glazed windows,
#              and ALL security equipment INSIDE: walk-through human scanner,
#              bag X-ray scanner with in/out conveyors, guard desk + monitors,
#              queue barriers, benches. Air conditioning: ceiling cassettes,
#              wall split units and roof condensers.
# Idempotent via Fence_/Gate_/GRoom_/Sec_ sweeps + kill-by-name.
# Order: ... -> phase1_3_site.py -> THIS (last).

def zy_gates_guard():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_gg_status.json"
    created = []
    groups = {"fence": 0, "gates": 0, "room": 0, "security": 0, "ac": 0}
    retired = []
    try:
        import math, mathutils
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_gg", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
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

        def mkmat(name, hx, rough=0.85, alpha=1.0, metal=0.0):
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
                    bsdf.inputs["Metallic"].default_value = metal
                except Exception:
                    pass
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

        def rbox(name, ax0, ax1, ay0, ay1, az0, az1, m, coll, bev=0.0):
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
            if bev > 0.0:
                try:
                    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                                    offset=bev, segments=2, affect="EDGES", profile=0.7)
                except Exception:
                    pass
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = ((ax0 + ax1) / 2, (ay0 + ay1) / 2, (az0 + az1) / 2)
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

        def wbounds(ob):
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

        m_wall = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.35, metal=0.8)
        m_steel = mkmat("ZY_Steel_Brushed", "#9BA1A8", rough=0.3, metal=0.9)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.05, alpha=0.28)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_red = mkmat("ZY_Accent_Red", "#C04848")
        m_teal = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_slab = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_floor = mkmat("ZY_Lobby_Floor", "#CDC9C0", rough=0.5)
        m_wood = mkmat("ZY_Wood_Warm", "#8C6748")
        m_couch = mkmat("ZY_Couch_Charcoal", "#3A3F46", rough=0.9)
        m_scrn = mkmat("ZY_Screen_Teal", "#0E4350", rough=0.25)
        m_ac = mkmat("ZY_AC_White", "#EDEDE8", rough=0.4)

        c_fence = get_coll("Site_Fence", root)
        c_road = get_coll("Site_Roads", root)
        c_gr = get_coll("Guard_Room", root)

        for n in [o.name for o in bpy.data.objects
                  if o.name.startswith(("Fence_S_", "Gate_", "GRoom_", "Sec_"))]:
            kill(n)

        # ================= item 1/2: south fence with REAL cutouts =================
        n0 = len(created)
        fw = bpy.data.objects.get("Building_frontsidefencewall")
        if fw is not None:
            fb = wbounds(fw)
            FX0, FX1, FY, FZ0, FZ1 = fb[0], fb[1], (fb[2] + fb[3]) / 2.0, fb[4], fb[5]
            retire(fw, "Building_frontsidefencewall_ORIGINAL")
            retired.append("Building_frontsidefencewall")
        else:
            FX0, FX1, FY, FZ0, FZ1 = -75.0, 50.15, -116.4, 5.39, 11.49
        FY0, FY1 = FY - 0.18, FY + 0.18
        VIN = (-40.0, -32.0)
        VOUT = (32.0, 40.0)
        PED = (44.0, 48.0)
        gaps = sorted([VIN, VOUT, PED])
        segs = []
        cx = FX0
        for g0, g1 in gaps:
            if g0 > cx:
                segs.append((cx, g0))
            cx = max(cx, g1)
        if cx < FX1:
            segs.append((cx, FX1))
        for si, (sx0, sx1) in enumerate(segs):
            rbox("Fence_S_Seg_%d" % si, sx0, sx1, FY0, FY1, FZ0, FZ1, m_wall, c_fence)
            rbox("Fence_S_Cap_%d" % si, sx0, sx1, FY0 - 0.1, FY1 + 0.1, FZ1, FZ1 + 0.25, m_slab, c_fence)
        pi = 0
        for g0, g1 in gaps:
            for px in (g0, g1):
                pi += 1
                rbox("Fence_S_Pier_%d" % pi, px - 0.6, px + 0.6, FY0 - 0.3, FY1 + 0.3,
                     FZ0, FZ1 + 0.9, m_wall, c_fence, bev=0.06)
                rbox("Fence_S_PierCap_%d" % pi, px - 0.75, px + 0.75, FY0 - 0.45, FY1 + 0.45,
                     FZ1 + 0.9, FZ1 + 1.15, m_slab, c_fence)
        groups["fence"] = len(created) - n0

        # ---------- proper gates inside the openings ----------
        n0 = len(created)

        def vehicle_gate(tag, x0, x1, ped=False):
            htop = FZ0 + (3.4 if ped else 5.2)
            rbox("Gate_%s_Header" % tag, x0 - 0.6, x1 + 0.6, FY0 - 0.25, FY1 + 0.25,
                 htop, htop + 0.7, m_metal, c_road, bev=0.05)
            rbox("Gate_%s_Sign" % tag, (x0 + x1) / 2 - 2.2, (x0 + x1) / 2 + 2.2,
                 FY0 - 0.3, FY0 - 0.24, htop + 0.1, htop + 0.6, m_amber, c_road)
            rbox("Gate_%s_Track" % tag, x0 - 0.4, x1 + 0.4, FY - 0.06, FY + 0.06,
                 FZ0, FZ0 + 0.08, m_steel, c_road)
            mid = (x0 + x1) / 2
            for li, (lx0, lx1) in enumerate(((x0 + 0.05, mid - 0.06), (mid + 0.06, x1 - 0.05))):
                rbox("Gate_%s_L%d_Rail_T" % (tag, li), lx0, lx1, FY - 0.06, FY + 0.06,
                     FZ0 + 2.35, FZ0 + 2.6, m_steel, c_road)
                rbox("Gate_%s_L%d_Rail_B" % (tag, li), lx0, lx1, FY - 0.06, FY + 0.06,
                     FZ0 + 0.12, FZ0 + 0.32, m_steel, c_road)
                nb = max(4, int((lx1 - lx0) / 0.34))
                for b in range(nb):
                    bx = lx0 + 0.14 + b * ((lx1 - lx0 - 0.2) / max(1, nb - 1))
                    rbox("Gate_%s_L%d_Bar_%02d" % (tag, li, b), bx - 0.035, bx + 0.035,
                         FY - 0.035, FY + 0.035, FZ0 + 0.12, FZ0 + 2.6, m_steel, c_road)
            for lx in (x0, x1):
                rbox("Gate_%s_Lamp_%d" % (tag, int(lx)), lx - 0.16, lx + 0.16,
                     FY0 - 0.16, FY0 - 0.02, FZ1 + 1.15, FZ1 + 1.45, m_amber, c_road)

        vehicle_gate("S_In", VIN[0], VIN[1])
        vehicle_gate("S_Out", VOUT[0], VOUT[1])
        vehicle_gate("S_Ped", PED[0], PED[1], ped=True)
        groups["gates"] = len(created) - n0

        # ================= item 4: hollow guard / entrance room =================
        n0 = len(created)
        ent = bpy.data.objects.get("Enternace_Area")
        if ent is not None:
            eb = wbounds(ent)
            EX0, EX1, EY0, EY1, EZ0, EZ1 = eb
            retire(ent, "Enternace_Area_ORIGINAL")
            retired.append("Enternace_Area")
        else:
            EX0, EX1, EY0, EY1, EZ0, EZ1 = 50.3, 75.3, -116.45, -92.8, 5.3, 11.4
        W = 0.4
        FLR = EZ0 + 0.12
        ECX = (EX0 + EX1) / 2.0
        DW = 2.2
        WT = EZ1 - 0.5
        WB = FLR + 1.0
        rbox("GRoom_Floor", EX0, EX1, EY0, EY1, EZ0, FLR, m_floor, c_gr)
        rbox("GRoom_Roof", EX0 - 0.3, EX1 + 0.3, EY0 - 0.3, EY1 + 0.3, EZ1, EZ1 + 0.35, m_slab, c_gr)
        rbox("GRoom_Wall_E", EX1 - W, EX1, EY0, EY1, FLR, EZ1, m_wall, c_gr)

        def wall_with_door(tag, horiz, fixed0, fixed1, a0, a1, dc, dh=3.0):
            if horiz:
                rbox("GRoom_%s_A" % tag, a0, dc - DW, fixed0, fixed1, FLR, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_B" % tag, dc + DW, a1, fixed0, fixed1, FLR, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_H" % tag, dc - DW, dc + DW, fixed0, fixed1, FLR + dh, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_JW" % tag, dc - DW - 0.14, dc - DW, fixed0 - 0.08, fixed1 + 0.08,
                     FLR, FLR + dh + 0.18, m_metal, c_gr)
                rbox("GRoom_%s_JE" % tag, dc + DW, dc + DW + 0.14, fixed0 - 0.08, fixed1 + 0.08,
                     FLR, FLR + dh + 0.18, m_metal, c_gr)
                rbox("GRoom_%s_HD" % tag, dc - DW - 0.14, dc + DW + 0.14, fixed0 - 0.08, fixed1 + 0.08,
                     FLR + dh, FLR + dh + 0.18, m_metal, c_gr)
            else:
                rbox("GRoom_%s_A" % tag, fixed0, fixed1, a0, dc - DW, FLR, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_B" % tag, fixed0, fixed1, dc + DW, a1, FLR, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_H" % tag, fixed0, fixed1, dc - DW, dc + DW, FLR + dh, EZ1, m_wall, c_gr)
                rbox("GRoom_%s_JS" % tag, fixed0 - 0.08, fixed1 + 0.08, dc - DW - 0.14, dc - DW,
                     FLR, FLR + dh + 0.18, m_metal, c_gr)
                rbox("GRoom_%s_JN" % tag, fixed0 - 0.08, fixed1 + 0.08, dc + DW, dc + DW + 0.14,
                     FLR, FLR + dh + 0.18, m_metal, c_gr)
                rbox("GRoom_%s_HD" % tag, fixed0 - 0.08, fixed1 + 0.08, dc - DW - 0.14, dc + DW + 0.14,
                     FLR + dh, FLR + dh + 0.18, m_metal, c_gr)

        wall_with_door("Wall_S", True, EY0, EY0 + W, EX0, EX1, ECX)
        wall_with_door("Wall_N", True, EY1 - W, EY1, EX0, EX1, ECX)
        wall_with_door("Wall_W", False, EX0, EX0 + W, EY0, EY1, (EY0 + EY1) / 2.0)

        def window_band(tag, horiz, fixed0, fixed1, a0, a1, dc):
            runs = [(a0 + 1.0, dc - DW - 0.4), (dc + DW + 0.4, a1 - 1.0)]
            for ri, (r0, r1) in enumerate(runs):
                if r1 - r0 < 1.5:
                    continue
                if horiz:
                    rbox("GRoom_Win_%s_%d" % (tag, ri), r0, r1, fixed0 + 0.12, fixed1 - 0.12, WB, WT, m_glass, c_gr)
                    rbox("GRoom_WinSill_%s_%d" % (tag, ri), r0 - 0.1, r1 + 0.1, fixed0, fixed1,
                         WB - 0.16, WB, m_slab, c_gr)
                    rbox("GRoom_WinHead_%s_%d" % (tag, ri), r0 - 0.1, r1 + 0.1, fixed0, fixed1,
                         WT, WT + 0.18, m_slab, c_gr)
                    nm = max(1, int((r1 - r0) / 2.6))
                    for mm in range(1, nm):
                        mx = r0 + mm * ((r1 - r0) / nm)
                        rbox("GRoom_Mul_%s_%d_%d" % (tag, ri, mm), mx - 0.06, mx + 0.06,
                             fixed0 + 0.06, fixed1 - 0.06, WB, WT, m_metal, c_gr)
                else:
                    rbox("GRoom_Win_%s_%d" % (tag, ri), fixed0 + 0.12, fixed1 - 0.12, r0, r1, WB, WT, m_glass, c_gr)
                    rbox("GRoom_WinSill_%s_%d" % (tag, ri), fixed0, fixed1, r0 - 0.1, r1 + 0.1,
                         WB - 0.16, WB, m_slab, c_gr)
                    rbox("GRoom_WinHead_%s_%d" % (tag, ri), fixed0, fixed1, r0 - 0.1, r1 + 0.1,
                         WT, WT + 0.18, m_slab, c_gr)
                    nm = max(1, int((r1 - r0) / 2.6))
                    for mm in range(1, nm):
                        my = r0 + mm * ((r1 - r0) / nm)
                        rbox("GRoom_Mul_%s_%d_%d" % (tag, ri, mm), fixed0 + 0.06, fixed1 - 0.06,
                             my - 0.06, my + 0.06, WB, WT, m_metal, c_gr)

        window_band("S", True, EY0, EY0 + W, EX0, EX1, ECX)
        window_band("N", True, EY1 - W, EY1, EX0, EX1, ECX)
        window_band("W", False, EX0, EX0 + W, EY0, EY1, (EY0 + EY1) / 2.0)
        groups["room"] = len(created) - n0

        # ---------- ALL security equipment INSIDE the room ----------
        n0 = len(created)
        yq = EY0 + 4.0
        rbox("Sec_Bag_InFeed", ECX + 2.2, ECX + 4.6, yq - 0.6, yq + 0.6, FLR, FLR + 0.75, m_steel, c_gr, bev=0.03)
        rbox("Sec_Bag_Tunnel", ECX + 4.6, ECX + 7.4, yq - 0.9, yq + 0.9, FLR, FLR + 1.55, m_metal, c_gr, bev=0.05)
        rbox("Sec_Bag_TunnelMouth", ECX + 4.55, ECX + 4.62, yq - 0.55, yq + 0.55, FLR + 0.75, FLR + 1.25, m_red, c_gr)
        rbox("Sec_Bag_OutFeed", ECX + 7.4, ECX + 9.8, yq - 0.6, yq + 0.6, FLR, FLR + 0.75, m_steel, c_gr, bev=0.03)
        rbox("Sec_Bag_Belt", ECX + 2.3, ECX + 9.7, yq - 0.5, yq + 0.5, FLR + 0.75, FLR + 0.79, m_couch, c_gr)
        rbox("Sec_Bag_Monitor", ECX + 8.4, ECX + 9.6, yq + 0.65, yq + 0.72, FLR + 0.85, FLR + 1.5, m_scrn, c_gr)
        for bi, bx in enumerate((3.2, 8.6)):
            rbox("Sec_Bag_Tray_%d" % bi, ECX + bx, ECX + bx + 0.8, yq - 0.34, yq + 0.34,
                 FLR + 0.79, FLR + 0.9, m_amber, c_gr)
        rbox("Sec_Human_Arch_L", ECX - 5.2, ECX - 4.8, yq - 0.5, yq + 0.5, FLR, FLR + 2.3, m_wall, c_gr, bev=0.04)
        rbox("Sec_Human_Arch_R", ECX - 2.4, ECX - 2.0, yq - 0.5, yq + 0.5, FLR, FLR + 2.3, m_wall, c_gr, bev=0.04)
        rbox("Sec_Human_Arch_Top", ECX - 5.2, ECX - 2.0, yq - 0.5, yq + 0.5, FLR + 2.3, FLR + 2.7, m_wall, c_gr, bev=0.04)
        rbox("Sec_Human_Arch_LedL", ECX - 4.8, ECX - 4.72, yq - 0.42, yq + 0.42, FLR + 0.4, FLR + 2.2, m_teal, c_gr)
        rbox("Sec_Human_Arch_LedR", ECX - 2.48, ECX - 2.4, yq - 0.42, yq + 0.42, FLR + 0.4, FLR + 2.2, m_teal, c_gr)
        rbox("Sec_Human_Arch_Lamp", ECX - 4.4, ECX - 2.8, yq - 0.45, yq + 0.45, FLR + 2.72, FLR + 2.86, m_amber, c_gr)
        rbox("Sec_Desk", ECX - 2.0, ECX + 1.6, yq + 3.4, yq + 4.4, FLR, FLR + 1.1, m_wood, c_gr, bev=0.04)
        rbox("Sec_Desk_Top", ECX - 2.1, ECX + 1.7, yq + 3.3, yq + 4.5, FLR + 1.1, FLR + 1.18, m_metal, c_gr)
        for mi in range(3):
            mx = ECX - 1.5 + mi * 1.1
            rbox("Sec_Desk_Mon_%d" % mi, mx, mx + 0.8, yq + 4.3, yq + 4.38, FLR + 1.18, FLR + 1.78, m_scrn, c_gr)
        rcyl("Sec_Desk_Chair", 0.32, 0.55, (ECX - 0.2, yq + 5.1, FLR + 0.28), "z", m_couch, c_gr)
        for qi in range(4):
            qy = EY0 + 1.0 + qi * 0.9
            rbox("Sec_Queue_L_%d" % qi, ECX - 6.4, ECX - 6.28, qy, qy + 0.12, FLR, FLR + 1.0, m_steel, c_gr)
            rbox("Sec_Queue_R_%d" % qi, ECX - 1.2, ECX - 1.08, qy, qy + 0.12, FLR, FLR + 1.0, m_steel, c_gr)
        rbox("Sec_Queue_Tape_L", ECX - 6.4, ECX - 6.28, EY0 + 1.0, EY0 + 4.4, FLR + 0.95, FLR + 1.0, m_amber, c_gr)
        rbox("Sec_Queue_Tape_R", ECX - 1.2, ECX - 1.08, EY0 + 1.0, EY0 + 4.4, FLR + 0.95, FLR + 1.0, m_amber, c_gr)
        for bi2, bxo in enumerate((-9.5, 6.0)):
            rbox("Sec_Bench_%d" % bi2, ECX + bxo, ECX + bxo + 3.0, EY1 - 3.2, EY1 - 2.4,
                 FLR, FLR + 0.45, m_wood, c_gr, bev=0.03)
        rbox("Sec_Sign_Inner", ECX - 3.0, ECX + 3.0, EY1 - W - 0.06, EY1 - W, FLR + 3.4, FLR + 4.3, m_red, c_gr)
        groups["security"] = len(created) - n0

        # ---------- air conditioning ----------
        n0 = len(created)
        for ci, (cxp, cyp) in enumerate(((ECX - 7.0, EY0 + 8.0), (ECX + 6.0, EY0 + 8.0),
                                         (ECX - 7.0, EY1 - 6.0), (ECX + 6.0, EY1 - 6.0))):
            rbox("GRoom_AC_Cassette_%d" % ci, cxp - 1.1, cxp + 1.1, cyp - 1.1, cyp + 1.1,
                 EZ1 - 0.34, EZ1, m_ac, c_gr, bev=0.05)
            rbox("GRoom_AC_Grille_%d" % ci, cxp - 0.75, cxp + 0.75, cyp - 0.75, cyp + 0.75,
                 EZ1 - 0.4, EZ1 - 0.34, m_steel, c_gr)
        for si2, (sxp, syp) in enumerate(((EX0 + 3.0, EY0 + 2.2), (EX1 - 3.0, EY1 - 2.2))):
            rbox("GRoom_AC_Split_%d" % si2, sxp - 1.0, sxp + 1.0, syp - 0.28, syp + 0.28,
                 EZ1 - 1.5, EZ1 - 0.7, m_ac, c_gr, bev=0.06)
            rbox("GRoom_AC_SplitVane_%d" % si2, sxp - 0.85, sxp + 0.85, syp - 0.32, syp - 0.24,
                 EZ1 - 1.25, EZ1 - 1.1, m_steel, c_gr)
        for oi, oxp in enumerate((EX0 + 5.0, EX0 + 9.0, EX0 + 13.0)):
            rbox("GRoom_AC_Condenser_%d" % oi, oxp, oxp + 2.2, EY1 - 4.0, EY1 - 2.6,
                 EZ1 + 0.35, EZ1 + 1.35, m_ac, c_gr, bev=0.05)
            rcyl("GRoom_AC_Fan_%d" % oi, 0.55, 0.08, (oxp + 1.1, EY1 - 3.3, EZ1 + 1.4), "z", m_steel, c_gr, seg=12)
        groups["ac"] = len(created) - n0

        scene["zy_guard"] = json.dumps({
            "room": [EX0, EX1, EY0, EY1, EZ0, EZ1],
            "fence_y": FY, "vehicle_gates": [list(VIN), list(VOUT)], "ped_gate": list(PED)})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_gg", "created": len(created),
                       "retired": retired, "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_gg", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_gates_guard, first_interval=0.1)
