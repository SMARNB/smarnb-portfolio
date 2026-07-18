# Zyvion Phase 1.3j — CENTRE COLUMN CUBICLE FLOORS, levels 2..8
# (user markup 2026-07-18: the red-outlined rear centre column was still the
# solid Phase-1.2 ring massing - only level 1 had been hollowed into the
# Cubical Hall by phase1_3_rear_blocks.py).
#
# For each of floors 2..8 (Cubicle_Workspace_L1..L7, retired here) this builds a
# real open-plan cubicle floor in the centre column (x -25..25, y 0..50):
#   - floor slab split around the vertical-core void (x -4..4, y 1..9) so the
#     glass lift + helix stairs keep running through,
#   - perimeter walls with glazed bands north (rear facade) and south,
#   - CONNECTED TO THE ELEVATOR: core enclosure with a doorway on its south face
#     opening onto the existing per-level Lift_Door_* jambs and the wrap stairs,
#   - CONNECTED TO THE OTHER ROOMS: doorways west and east (y 20..23) aligning
#     with the rear-half wing-floor inner-wall openings cut by
#     phase1_3_wing_floors.py,
#   - 18 cubicles per floor (3x3 each side of the core) + circulation,
#   - per-floor services: duct spine, diffusers, colour-coded cable tray.
# Idempotent via the CFloor_ prefix sweep + kill-by-name.
# Order: ... -> phase1_3_wing_floors.py -> THIS -> rooftop/site/gates_guard.

def zy_center_floors():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_center_status.json"
    created = []
    groups = {"shell": 0, "core": 0, "cubicles": 0, "services": 0}
    retired = []
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_center", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        if "zy_plinth" not in scene.keys():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_center", "error": "scene['zy_plinth'] missing"}, f, indent=1)
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

        p = json.loads(scene["zy_plinth"])
        H = 6.1
        LZ0 = p["z1"]                       # 9.23 level-1 floor
        X0, X1, Y0, Y1 = -25.0, 25.0, 0.0, 50.0
        VX0, VX1, VY0, VY1 = -4.0, 4.0, 1.0, 9.0     # vertical-core void
        WALL = 0.4
        SLAB = 0.35
        DY0, DY1 = 20.0, 23.0               # wing doorways (match wing_floors)

        m_slab = mkmat("ZY_Concrete_Slab", "#9A9A94")
        m_wall = mkmat("ZY_Wall_OffWhite", "#E8E4DC")
        m_glass = mkmat("ZY_Glass_Blue", "#7EC8E8", rough=0.05, alpha=0.28)
        m_metal = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.35, metal=0.8)
        m_grey = mkmat("ZY_Divider_Grey", "#6E6E68")
        m_wood = mkmat("ZY_Wood_Warm", "#8C6748")
        m_couch = mkmat("ZY_Couch_Charcoal", "#3A3F46", rough=0.9)
        m_floor = mkmat("ZY_Lobby_Floor", "#CDC9C0", rough=0.5)
        m_duct = mkmat("ZY_Duct_Silver", "#AEB6BD", rough=0.35)
        m_amber = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_teal = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_red = mkmat("ZY_Accent_Red", "#C04848")

        cf = get_coll("Center_Floors", root)

        for n in [o.name for o in bpy.data.objects if o.name.startswith("CFloor_")]:
            kill(n)
        for k in range(1, 8):
            for side in ("W", "E", "S", "N"):
                ob = bpy.data.objects.get("Cubicle_Workspace_L%d_%s" % (k, side))
                if ob is not None:
                    retire(ob, "Cubicle_Workspace_L%d_%s_ORIG" % (k, side))
                    retired.append("Cubicle_Workspace_L%d_%s" % (k, side))

        for k in range(1, 8):               # k=1..7  ->  floors 2..8
            L = k + 1
            zb = LZ0 + k * H
            zt = zb + H
            zw = zb + SLAB
            pre = "CFloor_L%d_" % L

            # ---- slab, split around the core void ----
            n0 = len(created)
            rbox(pre + "Slab_S", X0, X1, Y0, VY0, zb, zw, m_floor, cf)
            rbox(pre + "Slab_W", X0, VX0, VY0, VY1, zb, zw, m_floor, cf)
            rbox(pre + "Slab_E", VX1, X1, VY0, VY1, zb, zw, m_floor, cf)
            rbox(pre + "Slab_N", X0, X1, VY1, Y1, zb, zw, m_floor, cf)

            # ---- perimeter walls; west/east carry the doorways to the wings ----
            for tag, wx0, wx1 in (("W", X0, X0 + WALL), ("E", X1 - WALL, X1)):
                rbox(pre + "Wall_%s_A" % tag, wx0, wx1, Y0, DY0, zw, zt, m_wall, cf)
                rbox(pre + "Wall_%s_H" % tag, wx0, wx1, DY0, DY1, zb + 3.35, zt, m_wall, cf)
                rbox(pre + "Wall_%s_B" % tag, wx0, wx1, DY1, Y1, zw, zt, m_wall, cf)
                rbox(pre + "Door_%s_JS" % tag, wx0 - 0.08, wx1 + 0.08, DY0 - 0.14, DY0,
                     zw, zb + 3.5, m_metal, cf)
                rbox(pre + "Door_%s_JN" % tag, wx0 - 0.08, wx1 + 0.08, DY1, DY1 + 0.14,
                     zw, zb + 3.5, m_metal, cf)
                rbox(pre + "Door_%s_HD" % tag, wx0 - 0.08, wx1 + 0.08, DY0 - 0.14, DY1 + 0.14,
                     zb + 3.35, zb + 3.5, m_metal, cf)
            for tag, wy0, wy1 in (("S", Y0, Y0 + WALL), ("N", Y1 - WALL, Y1)):
                rbox(pre + "Wall_%s_Sill" % tag, X0, X1, wy0, wy1, zw, zb + 1.1, m_wall, cf)
                rbox(pre + "Wall_%s_Hdr" % tag, X0, X1, wy0, wy1, zb + 3.9, zt, m_wall, cf)
                for j in range(7):
                    cxw = X0 + 4.0 + j * 6.0
                    rbox(pre + "Win_%s_%d" % (tag, j), cxw - 2.1, cxw + 2.1,
                         wy0 + 0.12, wy1 - 0.12, zb + 1.1, zb + 3.9, m_glass, cf)
                    rbox(pre + "Mul_%s_%d" % (tag, j), cxw + 2.1, cxw + 3.9,
                         wy0, wy1, zb + 1.1, zb + 3.9, m_wall, cf)
            groups["shell"] += len(created) - n0

            # ---- core enclosure: doorway on the south face onto the lift lobby ----
            n0 = len(created)
            # NOTE: the doorway sits on the EAST face, not the south one. South of
            # the core there is only ~0.6 m between the core wall and the floor's
            # south perimeter - a dead end. The east door opens onto the stair
            # SE corner platform (x 2.6..4, y 1..2.4) which leads straight to the
            # lift landing at x -2.6..2.6, y 1..3.2.
            DA, DB = VY0 + 0.3, VY0 + 1.3
            rbox(pre + "Core_W", VX0, VX0 + 0.3, VY0, VY1, zw, zt, m_wall, cf)
            rbox(pre + "Core_N", VX0, VX1, VY1 - 0.3, VY1, zw, zt, m_wall, cf)
            rbox(pre + "Core_S", VX0, VX1, VY0, VY0 + 0.3, zw, zt, m_wall, cf)
            rbox(pre + "Core_E_A", VX1 - 0.3, VX1, VY0, DA, zw, zt, m_wall, cf)
            rbox(pre + "Core_E_B", VX1 - 0.3, VX1, DB, VY1, zw, zt, m_wall, cf)
            rbox(pre + "Core_E_H", VX1 - 0.3, VX1, DA, DB, zb + 3.35, zt, m_wall, cf)
            rbox(pre + "Core_Door_JS", VX1 - 0.38, VX1 + 0.08, DA - 0.14, DA, zw, zb + 3.5, m_metal, cf)
            rbox(pre + "Core_Door_JN", VX1 - 0.38, VX1 + 0.08, DB, DB + 0.14, zw, zb + 3.5, m_metal, cf)
            rbox(pre + "Core_Door_HD", VX1 - 0.38, VX1 + 0.08, DA - 0.14, DB + 0.14, zb + 3.35, zb + 3.5, m_metal, cf)
            rbox(pre + "Core_Sign", VX1 + 0.08, VX1 + 0.14, DA, DB, zb + 3.6, zb + 4.2, m_amber, cf)
            groups["core"] += len(created) - n0

            # ---- cubicles: 3x3 each side of the core ----
            n0 = len(created)
            ci = 0
            for sx in (-23.0, -16.6, -10.2, 5.0, 11.4, 17.8):
                for sy in (13.0, 25.0, 37.0):
                    ci += 1
                    cpre = pre + "Cub_%d_" % ci
                    rbox(cpre + "PartN", sx, sx + 5.4, sy + 5.5, sy + 5.6, zw, zb + 1.75, m_grey, cf)
                    rbox(cpre + "PartW", sx, sx + 0.1, sy, sy + 5.6, zw, zb + 1.75, m_grey, cf)
                    rbox(cpre + "Desk", sx + 0.7, sx + 4.3, sy + 4.2, sy + 5.0, zw, zb + 0.82, m_wood, cf, bev=0.03)
                    rbox(cpre + "Mon", sx + 2.1, sx + 2.9, sy + 4.62, sy + 4.7, zb + 0.82, zb + 1.32, m_metal, cf)
                    rcylz(cpre + "Chair", 0.32, zw, zb + 0.55, sx + 2.5, sy + 3.4, m_couch, cf)
            groups["cubicles"] += len(created) - n0

            # ---- services: duct spine + diffusers + colour-coded tray ----
            n0 = len(created)
            zc = zt - 0.55
            rcyl_ax(pre + "Svc_Duct", 0.34, 46.0, (0.0, 26.0, zc), "y", m_duct, cf)
            for di, dy in enumerate((10.0, 20.0, 32.0, 44.0)):
                rcylz(pre + "Svc_Diff_%d" % di, 0.5, zc - 0.62, zc - 0.5, 0.0, dy, m_duct, cf)
            rbox(pre + "Svc_Tray", -22.0, 22.0, 30.4, 30.9, zc - 0.2, zc - 0.1, m_metal, cf)
            for bn, bm_, off in (("P", m_amber, -0.14), ("D", m_teal, 0.0), ("S", m_red, 0.14)):
                rbox(pre + "Svc_Run_%s" % bn, -22.0, 22.0, 30.65 + off - 0.045, 30.65 + off + 0.045,
                     zc - 0.1, zc - 0.03, bm_, cf)
            groups["services"] += len(created) - n0

        scene["zy_center"] = json.dumps({
            "levels": [2, 3, 4, 5, 6, 7, 8], "envelope": [X0, X1, Y0, Y1],
            "core_void": [VX0, VX1, VY0, VY1], "wing_doors_y": [DY0, DY1],
            "cubicles_per_floor": 18})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_center", "created": len(created),
                       "retired": len(retired), "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_center", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_center_floors, first_interval=0.1)
