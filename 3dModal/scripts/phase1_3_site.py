# Zyvion Phase 1.3h — GROUND-LEVEL SITE (rev 2, user feedback 2026-07-18):
#   Item 1 - the FRONT (south) yard is GRASSLAND (green) + the north back lawn.
#   Item 2 - TILE the whole establishment ground (base tile layer + grout grid);
#            NO bare gray plaza remains. Grass in the yards sits on top of tile.
#   Item 3 - PARKING is one CONNECTED lot near the south fence (NOT under the
#            guard room); the front fence has TWO vehicle gates (IN + OUT); a
#            road links both gates and reaches the parking; ~2 m clearances
#            between guard room / parking / road. East-fence gate + spur kept
#            (connects 2 fence sides, prior item 5).
#   Brown  - guard / entrance checkpoint kept central on the pedestrian approach
#            (Sec_* login/guest/turnstile/scanner assets) with a tiled forecourt.
# Requires scene["zy_plinth"]. z-stack over ground top 5.41: tile 5.42..5.52,
# grout 5.52..5.54, grass 5.52..5.60, paving 5.60..5.66, path 5.54..5.58.
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent via
# Site_/Car_/Sec_/Road_/Gate_ sweeps. Order: ... -> rooftop -> THIS.

def zy_site():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_site_status.json"
    created = []
    groups = {"tile": 0, "grass": 0, "path": 0, "guard": 0, "parking": 0, "gates": 0, "road": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_site", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
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
            if ax1 - ax0 < 0.02 or ay1 - ay0 < 0.02 or az1 - az0 < 0.02:
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

        # ---------- z layers ----------
        GZ = 5.41
        TILE0, TILE1 = 5.42, 5.52
        GROUT = 5.54
        GRASS0, GRASS1 = 5.52, 5.60
        PV0, PV1 = 5.60, 5.66            # paving (roads / parking / approach)
        PATH0, PATH1 = 5.54, 5.58
        LN = 5.68                        # line top

        m_grass = mkmat("ZY_Grass_Green", "#4E8B3C", rough=0.95)
        m_hedge = mkmat("ZY_Hedge_Green", "#3B6B30", rough=0.95)
        m_path = mkmat("ZY_Path_Turq", "#5FA9A6", rough=0.7)
        m_tile = mkmat("ZY_Tile_Paver", "#C7BFB0", rough=0.55)      # new
        m_grout = mkmat("ZY_Tile_Grout", "#8E877A", rough=0.8)      # new
        m_asph = mkmat("ZY_Asphalt", "#2A2C30", rough=0.9)
        m_line = mkmat("ZY_RoadLine", "#E8E4C0", rough=0.6)
        m_wall = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_red = mkmat("ZY_Accent_Red", "#C04848")
        m_wood = mkmat("ZY_Wood_Warm", "#8C6748")

        c_site = get_coll("Site_Grounds", root)
        c_park = get_coll("Site_Parking", root)
        c_guard = get_coll("Site_Security", root)
        c_road = get_coll("Site_Roads", root)

        for n in [o.name for o in bpy.data.objects if o.name.startswith(
                ("Site_", "Car_", "Sec_", "Road_", "Gate_"))]:
            kill(n)

        # ---------- item 2: tile base over the whole establishment + grout grid ----------
        n0 = len(created)
        TX0, TX1, TY0, TY1 = -74.0, 75.0, -116.0, 76.0
        rbox("Site_Tile_Base", TX0, TX1, TY0, TY1, TILE0, TILE1, m_tile, c_site)
        gi = 0
        x = TX0 + 6.0
        while x < TX1:
            gi += 1
            rbox("Site_Grout_X_%d" % gi, x - 0.06, x + 0.06, TY0, TY1, TILE1, GROUT, m_grout, c_site)
            x += 6.0
        gj = 0
        y = TY0 + 6.0
        while y < TY1:
            gj += 1
            rbox("Site_Grout_Y_%d" % gj, TX0, TX1, y - 0.06, y + 0.06, TILE1, GROUT, m_grout, c_site)
            y += 6.0
        groups["tile"] = len(created) - n0

        # ---------- item 1 (rev 3): grassland goes NORTH only (orange marking).
        # The south/front lawn is REMOVED (crossed out in green). The northern
        # lower slab beyond the platform is measured from the scene so the grass
        # lands exactly on it instead of being hard-coded.
        n0 = len(created)
        import mathutils as _mu

        def _wb(ob):
            pts = [ob.matrix_world @ _mu.Vector(c) for c in ob.bound_box]
            return (min(p.x for p in pts), max(p.x for p in pts),
                    min(p.y for p in pts), max(p.y for p in pts),
                    min(p.z for p in pts), max(p.z for p in pts))

        skip_pref = ("Site_", "Car_", "Sec_", "Road_", "Gate_", "Solar_", "Heli_",
                     "Roof_", "Bulkhead_")
        nx0 = ny0 = 1e9
        nx1 = ny1 = -1e9
        ntop = None
        for ob in bpy.data.objects:
            if ob.type != "MESH" or ob.name.startswith(skip_pref):
                continue
            if any(c.name == "_Legacy_Backup" for c in ob.users_collection):
                continue
            b = _wb(ob)
            # flat, wide, and entirely north of the platform edge => the lawn slab
            if b[2] > 74.0 and (b[1] - b[0]) > 15.0 and (b[5] - b[4]) < 1.2:
                nx0 = min(nx0, b[0]); nx1 = max(nx1, b[1])
                ny0 = min(ny0, b[2]); ny1 = max(ny1, b[3])
                ntop = b[5] if ntop is None else max(ntop, b[5])
        if ntop is None:                      # fallback if nothing matched
            nx0, nx1, ny0, ny1, ntop = -74.0, 75.0, 77.0, 110.0, 3.95
        rbox("Site_Grass_Outer", nx0, nx1, ny0, ny1, ntop, ntop + 0.08, m_grass, c_site)
        # back lawn on the platform, running up to the north wall
        rbox("Site_Grass_North", -72.0, 72.0, 52.0, 73.2, GRASS0, GRASS1, m_grass, c_site)
        gt = ntop + 0.08
        span = max(4.0, (nx1 - nx0) / 5.0)
        for gi2 in range(4):
            tx = nx0 + span * (gi2 + 0.7)
            ty = (ny0 + ny1) / 2.0
            rcyl("Site_TreeG_Trunk_%d" % gi2, 0.4, 2.4, (tx, ty, gt + 1.2), "z", m_wood, c_site, seg=8)
            rcyl("Site_TreeG_Crown_%d" % gi2, 2.6, 3.0, (tx, ty, gt + 3.9), "z", m_hedge, c_site, seg=10)
        for tx in (-50.0, -25.0, 25.0, 50.0):
            rcyl("Site_TreeN_Trunk_%.0f" % tx, 0.4, 2.4, (tx, 62.0, GRASS1 + 1.2), "z", m_wood, c_site, seg=8)
            rcyl("Site_TreeN_Crown_%.0f" % tx, 2.6, 3.0, (tx, 62.0, GRASS1 + 3.9), "z", m_hedge, c_site, seg=10)
        groups["grass"] = len(created) - n0

        # ---------- turquoise walking-path ring on the tile plaza around the bldg ----------
        n0 = len(created)
        rbox("Site_Path_S", -55.0, 55.0, -55.0, -51.0, PATH0, PATH1, m_path, c_site)
        rbox("Site_Path_N", -55.0, 55.0, 51.0, 55.0, PATH0, PATH1, m_path, c_site)
        rbox("Site_Path_W", -55.0, -51.0, -55.0, 55.0, PATH0, PATH1, m_path, c_site)
        rbox("Site_Path_E", 51.0, 55.0, -55.0, 55.0, PATH0, PATH1, m_path, c_site)
        groups["path"] = len(created) - n0

        # ---------- item 2 (rev 3): the REAL guard / entrance room is the existing
        # `Enternace_Area` building (black outline in the markup). The free-standing
        # gatehouse previously built on the approach is crossed out -> not rebuilt.
        # Security assets are fitted to Enternace_Area's measured north face, and a
        # tiled walkway leads from it to the building's front stairs.
        n0 = len(created)
        ent = bpy.data.objects.get("Enternace_Area")
        if ent is not None:
            eb = _wb(ent)
            ex0, ex1, ey0, ey1, ez0, ez1 = eb
        else:                                  # fallback to its known as-built box
            ex0, ex1, ey0, ey1, ez0, ez1 = 50.3, 75.3, -116.45, -92.8, 5.3, 11.4
        gx0, gx1, gy0, gy1 = ex0, ex1, ey0, ey1
        ecx = (ex0 + ex1) / 2.0
        top = ez0 + 0.02                       # stand assets on the guard-room slab
        # entrance doorway + canopy on the north face (facing the site)
        rbox("Sec_Door_JambW", ecx - 2.6, ecx - 2.2, ey1 - 0.1, ey1 + 0.5, top, top + 3.2, m_metal, c_guard)
        rbox("Sec_Door_JambE", ecx + 2.2, ecx + 2.6, ey1 - 0.1, ey1 + 0.5, top, top + 3.2, m_metal, c_guard)
        rbox("Sec_Door_Head", ecx - 2.6, ecx + 2.6, ey1 - 0.1, ey1 + 0.5, top + 3.0, top + 3.4, m_metal, c_guard)
        rbox("Sec_Door_Glass", ecx - 2.2, ecx + 2.2, ey1 + 0.1, ey1 + 0.16, top, top + 3.0, m_glass, c_guard)
        rbox("Sec_Canopy", ecx - 4.5, ecx + 4.5, ey1, ey1 + 3.6, top + 3.4, top + 3.75, m_metal, c_guard)
        rbox("Sec_Sign", ecx - 3.0, ecx + 3.0, ey1 + 0.02, ey1 + 0.1, top + 3.8, top + 4.9, m_red, c_guard)
        # forecourt apron in front of the guard room
        rbox("Sec_Forecourt", ex0 - 3.0, ex1, ey1, ey1 + 9.0, PV0, PV1, m_tile, c_guard)
        # NOTE: the scanners / turnstiles / kiosks that used to stand out here on
        # the forecourt were crossed out by the user - all security equipment now
        # lives INSIDE the guard room (built by phase1_3_gates_guard.py).
        # tiled walkway: guard room -> west along the site -> north to the stairs
        rbox("Sec_Walk_A", -6.0, ex0, ey1 + 2.4, ey1 + 7.4, PV0, PV1, m_tile, c_guard)
        rbox("Sec_Walk_B", -6.0, 6.0, ey1 + 7.4, -51.0, PV0, PV1, m_tile, c_guard)
        rbox("Sec_Approach", -6.0, 6.0, -64.0, -51.0, PV0, PV1, m_tile, c_guard)
        groups["guard"] = len(created) - n0

        # ---------- item 3: two front gates + linking road + parking near fence ----------
        n0 = len(created)
        SFY = -116.0

        def gate(prefix, x0, x1, coll):
            rbox(prefix + "_Post_W", x0 - 1.0, x0, SFY - 0.5, SFY + 0.5, GZ, GZ + 6.5, m_metal, coll)
            rbox(prefix + "_Post_E", x1, x1 + 1.0, SFY - 0.5, SFY + 0.5, GZ, GZ + 6.5, m_metal, coll)
            rbox(prefix + "_Header", x0 - 1.0, x1 + 1.0, SFY - 0.4, SFY + 0.4, GZ + 6.5, GZ + 7.2, m_metal, coll)
            cx = (x0 + x1) / 2
            rbox(prefix + "_Sign", cx - 3.0, cx + 3.0, SFY - 0.05, SFY + 0.45, GZ + 6.6, GZ + 7.1, m_amber, coll)
            rbox(prefix + "_Leaf_W", x0, cx - 0.3, SFY - 0.12, SFY + 0.12, GZ, GZ + 2.6, m_metal, coll)
            rbox(prefix + "_Leaf_E", cx + 0.3, x1, SFY - 0.12, SFY + 0.12, GZ, GZ + 2.6, m_metal, coll)

        gate("Gate_S_In", -40.0, -32.0, c_road)      # IN gate (west of center)
        gate("Gate_S_Out", 32.0, 40.0, c_road)       # OUT gate (east of center)
        # (the free-standing booth that sat outside the fence here was crossed out)

        rbox("Road_Stub_In", -40.0, -32.0, SFY, -111.0, PV0, PV1, m_asph, c_road)
        rbox("Road_Stub_Out", 32.0, 40.0, SFY, -111.0, PV0, PV1, m_asph, c_road)
        rbox("Road_Fence", -44.0, 44.0, -114.0, -107.0, PV0, PV1, m_asph, c_road)
        rbox("Road_Fence_Median", -44.0, 44.0, -110.8, -110.2, PV1, PV1 + 0.16, m_path, c_road)
        for i in range(20):
            dx = -43.0 + i * 4.4
            rbox("Road_Fence_Dash_%d" % i, dx, dx + 2.0, -108.6, -108.44, PV1, LN, m_line, c_road)
            rbox("Road_Fence_Dash2_%d" % i, dx, dx + 2.0, -112.56, -112.4, PV1, LN, m_line, c_road)
        rbox("Road_ParkConn_W", -44.0, -40.0, -107.0, -105.0, PV0, PV1, m_asph, c_road)
        rbox("Road_ParkConn_E", 40.0, 44.0, -107.0, -105.0, PV0, PV1, m_asph, c_road)
        EFX = 75.0
        rbox("Gate_E_Post_S", EFX - 0.5, EFX + 0.5, -101.0, -100.0, GZ, GZ + 6.5, m_metal, c_road)
        rbox("Gate_E_Post_N", EFX - 0.5, EFX + 0.5, -92.0, -91.0, GZ, GZ + 6.5, m_metal, c_road)
        rbox("Gate_E_Header", EFX - 0.4, EFX + 0.4, -101.0, -91.0, GZ + 6.5, GZ + 7.2, m_metal, c_road)
        rbox("Gate_E_Leaf", EFX - 0.12, EFX + 0.12, -100.4, -91.6, GZ, GZ + 2.6, m_metal, c_road)
        rbox("Road_East_Spur", 44.0, 75.0, -100.0, -93.0, PV0, PV1, m_asph, c_road)
        groups["road"] = len(created) - n0

        # ---------- connected parking lot near the fence (2 m north of the road) ----------
        n0 = len(created)
        # white marking: the parking + road band runs between both gates and
        # reaches east toward the guard/entrance building
        PKX0, PKX1, PKY0, PKY1 = -44.0, 47.0, -105.0, -92.0
        rbox("Site_Parking_Lot", PKX0, PKX1, PKY0, PKY1, PV0, PV1, m_asph, c_park)
        for i in range(int((PKX1 - PKX0) / 3.6) + 1):
            mx = PKX0 + 1.0 + i * 3.6
            rbox("Site_Park_Line_%d" % i, mx, mx + 0.15, PKY0 + 0.5, PKY0 + 5.0, PV1, LN, m_line, c_park)
            rbox("Site_Park_Line_b%d" % i, mx, mx + 0.15, PKY1 - 5.0, PKY1 - 0.5, PV1, LN, m_line, c_park)

        def car(name, cx, cy, rz, kind, colhex):
            mc = mkmat("ZY_Car_" + colhex.lstrip("#"), colhex, rough=0.35)
            if kind == "SUV":
                L, Wd, bh, ct = 4.9, 2.05, 0.95, 1.9
            else:
                L, Wd, bh, ct = 4.6, 1.85, 0.62, 1.42

            def loc(lx, ly):
                return (cx + lx * math.cos(rz) - ly * math.sin(rz),
                        cy + lx * math.sin(rz) + ly * math.cos(rz))

            kill(name + "_Body")
            me = bpy.data.meshes.new(name + "_Body")
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= Wd; v.co.y *= L; v.co.z *= bh
            bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name + "_Body", me)
            ob.location = (cx, cy, PV1 + bh / 2); ob.rotation_euler = (0, 0, rz)
            c_park.objects.link(ob); me.materials.append(mc); created.append(name + "_Body")

            kill(name + "_Cabin")
            me2 = bpy.data.meshes.new(name + "_Cabin")
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= Wd - 0.3; v.co.y *= L * 0.5; v.co.z *= (ct - bh) * 0.85
            bm.to_mesh(me2); bm.free()
            ob2 = bpy.data.objects.new(name + "_Cabin", me2)
            ob2.location = (cx, cy - L * 0.05, PV1 + bh + (ct - bh) * 0.85 / 2)
            ob2.rotation_euler = (0, 0, rz)
            c_park.objects.link(ob2); me2.materials.append(mc); created.append(name + "_Cabin")

            kill(name + "_Glass")
            me3 = bpy.data.meshes.new(name + "_Glass")
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co.x *= Wd - 0.34; v.co.y *= L * 0.48; v.co.z *= (ct - bh) * 0.5
            bm.to_mesh(me3); bm.free()
            ob3 = bpy.data.objects.new(name + "_Glass", me3)
            ob3.location = (cx, cy - L * 0.05, PV1 + bh + (ct - bh) * 0.6)
            ob3.rotation_euler = (0, 0, rz)
            c_park.objects.link(ob3); me3.materials.append(m_glass); created.append(name + "_Glass")

            for wi, (wx, wy) in enumerate(((-Wd / 2, L * 0.32), (Wd / 2, L * 0.32),
                                           (-Wd / 2, -L * 0.32), (Wd / 2, -L * 0.32))):
                wl = loc(wx, wy)
                rcyl(name + "_Wheel%d" % wi, 0.36, 0.24, (wl[0], wl[1], PV1 + 0.36), "x", m_metal, c_park, seg=10)

        kinds = ["Sedan", "SUV", "Sedan", "SUV", "Sedan", "SUV", "Sedan", "SUV", "Sedan", "SUV"]
        cols = ["#B4402E", "#2E4E7E", "#D9D2C4", "#3A3F46", "#6E7B52",
                "#8A8F96", "#7A3B52", "#2F5E4A", "#C08A2E", "#4A4E86"]
        for i in range(5):
            cx = -34.0 + i * 16.0
            car("Car_%s_F%d" % (kinds[i], i), cx, PKY0 + 3.0, 0.0, kinds[i], cols[i])
            car("Car_%s_R%d" % (kinds[i + 5], i), cx + 6.0, PKY1 - 3.0, math.pi, kinds[i + 5], cols[i + 5])
        groups["parking"] = len(created) - n0
        groups["gates"] = 3

        scene["zy_site"] = json.dumps({
            "tile": [TX0, TX1, TY0, TY1], "front_grass": [-72.0, 72.0, -116.0, -64.0],
            "guard": [gx0, gx1, gy0, gy1], "parking": [PKX0, PKX1, PKY0, PKY1],
            "south_gates": {"in": [-40.0, -32.0], "out": [32.0, 40.0]},
            "east_gate": [EFX, -101.0, -91.0]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_site", "created": len(created),
                       "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_site", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_site, first_interval=0.1)
