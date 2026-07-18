# Zyvion Phase 1.3 — Grand Lobby interior (portfolio ABOUT page).
# Hollows the solid Grand_Lobby_4_Story box (x -25..25, y -50..0, z 9.23..33.63)
# into a 4-story atrium: glass curtain south facade with a 12x9 m open portal,
# U-shaped mezzanine rings at levels 2/3/4 (E/N/W walls, 6 m deep, glass rails,
# center notch at levels 3/4 framing the hero screen; mezz access via the wing
# stair shafts, doorways cut by the phase1_3 wing scripts), 6 raycastable About
# panels (Lobby_Display_About_1..6) + Lobby_Display_Hero, curved reception desk,
# and the capsule NPC_Lobby_Greeter (deterministic; npc_* custom props).
# Also carves a 5.2x3.5 m doorway through the lobby north wall + the
# Cubicle_Workspace_L0_S band so the lobby reaches the lift-core landing.
# User-confirmed design (2026-07-17): glass curtain / mezzanine rings /
# 6 panels + hero / curved desk with greeter behind (teal body, amber collar).
# Listener contract (doc s7): single wrapper + bpy.app.timers; idempotent
# (kill-by-name + prefix sweeps); absolutes from scene["zy_plinth"] x SXY=2.5.
# Pipeline order: phase1_1 -> phase1_2 -> THIS.

def zy_lobby():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_status.json"
    created = []
    try:
        import mathutils, math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_lobby", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
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

        backup = get_coll("_Legacy_Backup", root, hide=True)

        def retire(ob, new_name):
            for uc in list(ob.users_collection):
                uc.objects.unlink(ob)
            backup.objects.link(ob)
            ob.name = new_name
            ob.hide_viewport = True
            ob.hide_render = True

        # ---------- shared layout ----------
        p = json.loads(scene["zy_plinth"])
        SXY = 2.5                                   # must match phase1_1/1_2
        H = 6.1                                     # 20 ft story
        LX0, LX1 = -10.0 * SXY, 10.0 * SXY          # lobby envelope -25..25
        LY0, LY1 = -20.0 * SXY, 0.0                 # -50..0
        LZ0 = p["z1"]                               # lobby floor = plinth top (9.23)
        LZ1 = LZ0 + 4 * H                           # 33.63
        WALL = 0.5
        FT = LZ0 + 0.15                             # finished floor top
        PX = 6.0                                    # portal half-width (12 m)
        PZT = LZ0 + 9.0                             # portal head (9 m tall)
        DWX = 2.6                                   # core doorway half-width
        DWZT = LZ0 + 3.5                            # core doorway head
        MZ = [LZ0 + H, LZ0 + 2 * H, LZ0 + 3 * H]    # mezz walk levels 15.33/21.43/27.53
        MD = 6.0                                    # mezz depth
        MSL = 0.3                                   # mezz slab thickness
        RH = 1.1                                    # glass rail height
        RT = 0.08                                   # rail thickness
        NX0, NX1 = -8.0, 8.0                        # hero notch (levels 3/4 N slabs)

        m_slab  = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall  = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.4)
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.08, alpha=0.32)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_teal  = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_wood  = mkmat("ZY_Wood_Warm", "#8C6748")
        m_grey  = mkmat("ZY_Divider_Grey", "#6E6E68")
        m_floor = mkmat("ZY_Lobby_Floor", "#CDC9C0", rough=0.55)     # new: honed stone
        m_scrn  = mkmat("ZY_Screen_Teal", "#0E4350", rough=0.3)      # new: display faces
        m_plant = mkmat("ZY_Plant_Green", "#3F7B45", rough=0.9)      # new: planter shrubs

        lob = get_coll("Grand_Lobby", root)
        shell = get_coll("Lobby_Shell", lob)
        mezz = get_coll("Lobby_Mezzanines", lob)
        disp = get_coll("Lobby_Displays", lob)
        furn = get_coll("Lobby_Furnishings", lob)
        npcc = get_coll("Lobby_NPC", lob)
        core = get_coll("Vertical_Core", root)

        # ---------- idempotency sweeps + retire the solid box ----------
        for n in [o.name for o in bpy.data.objects
                  if o.name.startswith("Lobby_") or o.name.startswith("NPC_Lobby_")]:
            kill(n)
        orig = bpy.data.objects.get("Grand_Lobby_4_Story")
        retired = []
        if orig is not None:
            retire(orig, "Grand_Lobby_ORIGINAL")
            retired.append("Grand_Lobby_4_Story -> Grand_Lobby_ORIGINAL")

        # ---------- shell: floor, side/north walls, roof ----------
        rbox("Lobby_Floor", LX0 + WALL, LX1 - WALL, LY0 + WALL, LY1 - WALL, LZ0, FT, m_floor, shell)
        rbox("Lobby_Floor_Threshold", -PX, PX, LY0, LY0 + WALL, LZ0, FT, m_floor, shell)
        rbox("Lobby_Wall_W", LX0, LX0 + WALL, LY0 + WALL, LY1 - WALL, LZ0, LZ1, m_wall, shell)
        rbox("Lobby_Wall_E", LX1 - WALL, LX1, LY0 + WALL, LY1 - WALL, LZ0, LZ1, m_wall, shell)
        rbox("Lobby_Wall_N_W", LX0, -DWX, LY1 - WALL, LY1, LZ0, LZ1, m_wall, shell)
        rbox("Lobby_Wall_N_E", DWX, LX1, LY1 - WALL, LY1, LZ0, LZ1, m_wall, shell)
        rbox("Lobby_Wall_N_Header", -DWX, DWX, LY1 - WALL, LY1, DWZT, LZ1, m_wall, shell)
        rbox("Lobby_Wall_N_Thresh", -DWX, DWX, LY1 - WALL, LY1, LZ0, FT, m_floor, shell)
        rbox("Lobby_Roof", LX0, LX1, LY0, LY1, LZ1, LZ1 + 0.25, m_slab, shell)

        # ---------- south glass curtain wall + open portal ----------
        GY0, GY1 = LY0 + 0.1, LY0 + 0.35
        rbox("Lobby_Curtain_Glass_W", LX0, -PX, GY0, GY1, LZ0, LZ1, m_glass, shell)
        rbox("Lobby_Curtain_Glass_E", PX, LX1, GY0, GY1, LZ0, LZ1, m_glass, shell)
        rbox("Lobby_Curtain_Glass_C", -PX, PX, GY0, GY1, PZT, LZ1, m_glass, shell)
        for i, mx in enumerate((-24.8, -19.0, -13.0, 13.0, 19.0, 24.8)):
            rbox("Lobby_Curtain_Mullion_%d" % (i + 1), mx - 0.2, mx + 0.2,
                 LY0, LY0 + WALL, LZ0, LZ1, m_metal, shell)
        for li, lz in enumerate(MZ):
            if lz < PZT:  # transom would cross the portal: split W/E
                rbox("Lobby_Curtain_Transom_%d_W" % (li + 1), LX0, -PX - 0.2,
                     LY0, LY0 + WALL, lz - 0.175, lz + 0.175, m_metal, shell)
                rbox("Lobby_Curtain_Transom_%d_E" % (li + 1), PX + 0.2, LX1,
                     LY0, LY0 + WALL, lz - 0.175, lz + 0.175, m_metal, shell)
            else:
                rbox("Lobby_Curtain_Transom_%d_F" % (li + 1), LX0, LX1,
                     LY0, LY0 + WALL, lz - 0.175, lz + 0.175, m_metal, shell)
        rbox("Lobby_Portal_Jamb_W", -PX - 0.4, -PX, LY0 - 0.05, LY0 + 0.55, LZ0, PZT + 0.5, m_metal, shell)
        rbox("Lobby_Portal_Jamb_E", PX, PX + 0.4, LY0 - 0.05, LY0 + 0.55, LZ0, PZT + 0.5, m_metal, shell)
        rbox("Lobby_Portal_Header", -PX - 0.4, PX + 0.4, LY0 - 0.05, LY0 + 0.55, PZT, PZT + 0.5, m_metal, shell)
        rbox("Lobby_Portal_Canopy", -PX - 2.0, PX + 2.0, LY0 - 2.6, LY0 + 0.55, PZT + 0.5, PZT + 0.95, m_metal, shell)

        # ---------- doorway through Cubicle_Workspace_L0_S to the core landing ----------
        for n in ("Cubicle_Workspace_L0_S", "Cubicle_Workspace_L0_S_W",
                  "Cubicle_Workspace_L0_S_E", "Cubicle_Workspace_L0_S_Hdr"):
            kill(n)
        rbox("Cubicle_Workspace_L0_S_W", -4.0, -DWX, 0.0, 1.0, LZ0, LZ0 + H, m_slab, core)
        rbox("Cubicle_Workspace_L0_S_E", DWX, 4.0, 0.0, 1.0, LZ0, LZ0 + H, m_slab, core)
        rbox("Cubicle_Workspace_L0_S_Hdr", -DWX, DWX, 0.0, 1.0, DWZT, LZ0 + H, m_slab, core)

        # ---------- mezzanine rings (levels 2/3/4) ----------
        IW = LX0 + WALL          # -24.5 inner west face
        IE = LX1 - WALL          # 24.5
        IN = LY1 - WALL          # -0.5 inner north face
        MWX = IW + MD            # -18.5 west slab inner edge
        MEX = IE - MD            # 18.5
        MNY = IN - MD            # -6.5 north slab inner edge
        MSY = -40.0              # south end of the E/W slab arms
        for k, lz in enumerate(MZ):
            L = k + 2            # human level number 2/3/4
            notch = (k >= 1)     # levels 3/4 keep the hero-screen void
            z0, z1 = lz - MSL, lz
            rbox("Lobby_Mezz_L%d_W" % L, IW, MWX, MSY, MNY, z0, z1, m_slab, mezz)
            rbox("Lobby_Mezz_L%d_E" % L, MEX, IE, MSY, MNY, z0, z1, m_slab, mezz)
            spans_n = [(IW, NX0), (NX1, IE)] if notch else [(IW, IE)]
            for si, (sx0, sx1) in enumerate(spans_n):
                rbox("Lobby_Mezz_L%d_N%d" % (L, si), sx0, sx1, MNY, IN, z0, z1, m_slab, mezz)
            # glass rails on every open edge
            rbox("Lobby_Rail_L%d_W" % L, MWX - RT, MWX, MSY, MNY, lz, lz + RH, m_glass, mezz)
            rbox("Lobby_Rail_L%d_E" % L, MEX, MEX + RT, MSY, MNY, lz, lz + RH, m_glass, mezz)
            rbox("Lobby_Rail_L%d_WCap" % L, IW, MWX, MSY, MSY + RT, lz, lz + RH, m_glass, mezz)
            rbox("Lobby_Rail_L%d_ECap" % L, MEX, IE, MSY, MSY + RT, lz, lz + RH, m_glass, mezz)
            if notch:
                rbox("Lobby_Rail_L%d_N_W" % L, MWX, NX0, MNY - RT, MNY, lz, lz + RH, m_glass, mezz)
                rbox("Lobby_Rail_L%d_N_E" % L, NX1, MEX, MNY - RT, MNY, lz, lz + RH, m_glass, mezz)
                rbox("Lobby_Rail_L%d_NotchW" % L, NX0 - RT, NX0, MNY, IN, lz, lz + RH, m_glass, mezz)
                rbox("Lobby_Rail_L%d_NotchE" % L, NX1, NX1 + RT, MNY, IN, lz, lz + RH, m_glass, mezz)
            else:
                rbox("Lobby_Rail_L%d_N" % L, MWX, MEX, MNY - RT, MNY, lz, lz + RH, m_glass, mezz)

        # ---------- About displays: 3 per side wall + hero on the north wall ----------
        panels = []
        # keep y -30..-23 clear: the wing doorways (west y -28..-24, east
        # corridor y -29.5..-25.5) punch through the side walls there
        spans_y = [(-46.0, -40.0), (-38.0, -32.0), (-16.0, -10.0)]
        for i, (py0, py1) in enumerate(spans_y):
            n = "Lobby_Display_About_%d" % (i + 1)          # west wall, south->north
            rbox(n + "_Frame", IW, IW + 0.14, py0 - 0.4, py1 + 0.4, 10.0, 14.3, m_amber, disp)
            rbox(n, IW + 0.14, IW + 0.20, py0, py1, 10.4, 13.9, m_scrn, disp)
            panels.append(n)
        for i, (py0, py1) in enumerate(spans_y):
            n = "Lobby_Display_About_%d" % (i + 4)          # east wall, south->north
            rbox(n + "_Frame", IE - 0.14, IE, py0 - 0.4, py1 + 0.4, 10.0, 14.3, m_amber, disp)
            rbox(n, IE - 0.20, IE - 0.14, py0, py1, 10.4, 13.9, m_scrn, disp)
            panels.append(n)
        rbox("Lobby_Display_Hero_Frame", -7.4, 7.4, IN - 0.12, IN, 16.6, 23.4, m_amber, disp)
        rbox("Lobby_Display_Hero", -7.0, 7.0, IN - 0.18, IN - 0.12, 17.0, 23.0, m_scrn, disp)
        panels.append("Lobby_Display_Hero")

        # ---------- reception: curved 5-segment desk at (0, -10) facing the portal ----------
        C = mathutils.Vector((0.0, -4.0))
        R = 6.5
        for si in range(5):
            th = math.radians(-118.0 + si * 14.0)
            cx, cy = C.x + R * math.cos(th), C.y + R * math.sin(th)
            rboxr("Lobby_Reception_Desk_S%d" % (si + 1), 1.7, 0.7, 1.05,
                  cx, cy, FT + 0.525, th + math.pi / 2, m_wood, furn)
            rboxr("Lobby_Reception_Counter_S%d" % (si + 1), 1.9, 0.9, 0.08,
                  cx, cy, FT + 1.09, th + math.pi / 2, m_metal, furn)
        rbox("Lobby_Greeter_Dais", -1.2, 1.2, -9.2, -7.6, FT, FT + 0.12, m_amber, furn)

        # ---------- NPC_Lobby_Greeter: capsule (deterministic; raycast target) ----------
        kill("NPC_Lobby_Greeter")
        me = bpy.data.meshes.new("NPC_Lobby_Greeter")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12,
                              radius1=0.38, radius2=0.38, depth=1.25)
        sph = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.38)
        for v in sph["verts"]:
            v.co.z += 0.625
        bm.to_mesh(me)
        bm.free()
        npc = bpy.data.objects.new("NPC_Lobby_Greeter", me)
        npc.location = (0.0, -8.4, FT + 0.12 + 0.625)
        npcc.objects.link(npc)
        me.materials.append(m_teal)
        npc["npc_id"] = "lobby_greeter"
        npc["npc_type"] = "deterministic"
        npc["npc_role"] = "Lobby Greeter"
        created.append("NPC_Lobby_Greeter")
        gz = FT + 0.12
        rbox("NPC_Lobby_Greeter_Collar", -0.44, 0.44, -8.84, -7.96, gz + 1.02, gz + 1.09, m_amber, npcc)
        rbox("NPC_Lobby_Greeter_Visor", -0.18, 0.18, -8.86, -8.74, gz + 1.22, gz + 1.42, m_metal, npcc)

        # ---------- ambient furnishing: benches + planters flanking the walkway ----------
        for i, by in enumerate((-34.0, -22.0)):
            rbox("Lobby_Bench_%d" % (i * 2 + 1), -11.4, -10.6, by - 1.5, by + 1.5, FT, FT + 0.45, m_wood, furn)
            rbox("Lobby_Bench_%d" % (i * 2 + 2), 10.6, 11.4, by - 1.5, by + 1.5, FT, FT + 0.45, m_wood, furn)
        for i, py in enumerate((-38.3, -16.0)):
            for j, px in enumerate((-11.0, 11.0)):
                k = i * 2 + j + 1
                rbox("Lobby_Planter_%d" % k, px - 0.6, px + 0.6, py - 0.6, py + 0.6, FT, FT + 0.9, m_grey, furn)
                rbox("Lobby_Shrub_%d" % k, px - 0.45, px + 0.45, py - 0.45, py + 0.45, FT + 0.9, FT + 1.7, m_plant, furn)

        scene["zy_lobby"] = json.dumps({
            "x0": LX0, "x1": LX1, "y0": LY0, "y1": LY1, "z0": LZ0, "z1": LZ1,
            "floor_top": FT, "portal": [-PX, PX, PZT], "doorway": [-DWX, DWX, DWZT],
            "mezz_z": MZ, "notch": [NX0, NX1]})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_lobby", "created": len(created),
                       "retired": retired, "displays": panels, "npc": "NPC_Lobby_Greeter",
                       "params": json.loads(scene["zy_lobby"]), "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_lobby", "created": len(created),
                       "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_lobby, first_interval=0.1)
