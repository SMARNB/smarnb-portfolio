# Zyvion Phase 1.3k — PER-FLOOR NPCs (plan section 4 hybrid router).
# One guide NPC on every page-floor to explain that page's functionality, plus
# a supervisor on each centre cubicle floor and the Gate Auth NPC in the guard
# room. Each NPC is a named mesh the R3F frontend can raycast, carrying custom
# properties that survive glTF export:
#     npc_id    - stable key for the useStore npcData dictionary
#     npc_type  - 'deterministic' (hardcoded React decision tree) | 'generative'
#                 (POST /api/chat -> RAG backend)
#     npc_role  - human-readable role
#     npc_page  - which website page/floor this NPC narrates
# Geometry stays low-poly but is a bit more built-up than a bare capsule:
# tapered torso, sphere head, shoulder yoke, visor, base disc, and a floating
# emissive marker so the user can see it is interactive.
# Idempotent via the NPC_ prefix sweep (the lobby greeter built by
# phase1_3_grand_lobby.py is preserved - it is re-created by that script).
# Order: ... -> phase1_3_center_floors.py -> THIS.

def zy_npcs():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_npc_status.json"
    created = []
    npcs = []
    groups = {"wing": 0, "center": 0, "gate": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_npc", "error": "REFUSED: autosave copy: " + fp}, f, indent=1)
            return
        scene = bpy.data.scenes[0]
        root = scene.collection
        if "zy_plinth" not in scene.keys():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_npc", "error": "scene['zy_plinth'] missing"}, f, indent=1)
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

        def mkmat(name, hx, rough=0.85, alpha=1.0, emit=0.0):
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
                if emit > 0.0:
                    try:
                        bsdf.inputs["Emission Color"].default_value = rgba
                        bsdf.inputs["Emission Strength"].default_value = emit
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

        def rbox(name, sx, sy, sz, cx, cy, cz, m, coll):
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
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        def rcylz(name, r1, r2, depth, cx, cy, cz, m, coll, seg=14):
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                  radius1=r1, radius2=r2, depth=depth)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (cx, cy, cz)
            coll.objects.link(ob)
            me.materials.append(m)
            created.append(name)
            return ob

        m_body = mkmat("ZY_NPC_Body", "#38414E", rough=0.75)
        m_gen = mkmat("ZY_Accent_Teal", "#2E8C8C")
        m_det = mkmat("ZY_Accent_Amber", "#E8A13C")
        m_visor = mkmat("ZY_Metal_Dark", "#2B2B2E", rough=0.35)
        m_mark_g = mkmat("ZY_NPC_Mark_Gen", "#3FD2C7", rough=0.2, emit=2.5)
        m_mark_d = mkmat("ZY_NPC_Mark_Det", "#FFC061", rough=0.2, emit=2.5)

        c_npc = get_coll("NPCs", root)

        for n in [o.name for o in bpy.data.objects
                  if o.name.startswith("NPC_") and not o.name.startswith("NPC_Lobby_Greeter")]:
            kill(n)

        def make_npc(key, role, page, ntype, x, y, zfloor, facing=0.0):
            acc = m_gen if ntype == "generative" else m_det
            mark = m_mark_g if ntype == "generative" else m_mark_d
            name = "NPC_" + key
            kill(name)
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=14,
                                  radius1=0.34, radius2=0.27, depth=1.15)
            sph = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=0.25)
            for v in sph["verts"]:
                v.co.z += 0.82
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.location = (x, y, zfloor + 0.575)
            ob.rotation_euler = (0.0, 0.0, facing)
            c_npc.objects.link(ob)
            me.materials.append(m_body)
            ob["npc_id"] = key.lower()
            ob["npc_type"] = ntype
            ob["npc_role"] = role
            ob["npc_page"] = page
            created.append(name)
            npcs.append(name)
            rbox(name + "_Yoke", 0.72, 0.3, 0.1, x, y, zfloor + 1.12, acc, c_npc)
            rbox(name + "_Visor", 0.3, 0.1, 0.12, x, y - 0.24, zfloor + 1.4, m_visor, c_npc)
            rcylz(name + "_Base", 0.4, 0.4, 0.06, x, y, zfloor + 0.03, acc, c_npc)
            rcylz(name + "_Mark", 0.0, 0.19, 0.34, x, y, zfloor + 2.06, mark, c_npc, seg=12)
            return ob

        p = json.loads(scene["zy_plinth"])
        H = 6.1
        LZ0 = p["z1"]
        SLAB = 0.35

        WING = {
            ("W", 2): ("Services", "Services Guide", "generative"),
            ("W", 3): ("Store", "Store Attendant", "generative"),
            ("W", 4): ("Blog", "Blog Editor", "generative"),
            ("W", 5): ("Work", "Work Showcase Rep", "generative"),
            ("W", 6): ("Projects", "Projects Rep", "generative"),
            ("W", 7): ("HoD_Offices", "Head of Department", "deterministic"),
            ("W", 8): ("Directors_West", "Director", "deterministic"),
            ("E", 2): ("Conference_Center", "Conference Host", "deterministic"),
            ("E", 3): ("Departments_A", "Department Lead A", "deterministic"),
            ("E", 4): ("Departments_B", "Department Lead B", "deterministic"),
            ("E", 5): ("Departments_C", "Department Lead C", "deterministic"),
            ("E", 6): ("Operations", "Operations Manager", "deterministic"),
            ("E", 7): ("Directors", "Director", "deterministic"),
            ("E", 8): ("Founders_CEO", "Founder / CEO", "generative"),
        }
        n0 = len(created)
        for (wing, k), (page, role, ntype) in sorted(WING.items()):
            zb = LZ0 + (k - 1) * H
            zf = zb + SLAB
            x = -34.6 if wing == "W" else 34.6
            make_npc(page, role, page, ntype, x, -3.2, zf, facing=math.pi)
        groups["wing"] = len(created) - n0

        n0 = len(created)
        for k in range(1, 8):
            L = k + 1
            zf = LZ0 + k * H + SLAB
            make_npc("Center_L%d" % L, "Floor Supervisor L%d" % L,
                     "Workspace_L%d" % L, "deterministic", 0.0, 11.4, zf, facing=0.0)
        groups["center"] = len(created) - n0

        n0 = len(created)
        if "zy_guard" in scene.keys():
            g = json.loads(scene["zy_guard"])["room"]
            gcx = (g[0] + g[1]) / 2.0
            gz = g[4] + 0.12
            make_npc("Gate_Auth", "Gate Authentication", "Login_Signup",
                     "deterministic", gcx + 3.0, g[2] + 9.5, gz, facing=math.pi)
        groups["gate"] = len(created) - n0

        scene["zy_npcs"] = json.dumps({"count": len(npcs), "names": npcs})

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": True, "step": "phase1_3_npc", "created": len(created),
                       "npcs": npcs, "groups": groups, "filepath": fp}, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ok": False, "step": "phase1_3_npc", "created": len(created),
                       "groups": groups, "error": traceback.format_exc()}, f, indent=1)

import bpy
bpy.app.timers.register(zy_npcs, first_interval=0.1)
