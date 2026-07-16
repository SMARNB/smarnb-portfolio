# Zyvion Phase 1.1 v2 — two confirmation renders: (1) underground basement interior
# (hides everything whose world z-min is above ~street level), (2) full building
# exterior showing the re-stacked 20 ft floors and 4-story lobby.
# Deferred to bpy.app.timers: render must run on Blender's main thread.

def zy_render_preview():
    import bpy

    def do_render():
        import bpy, json, traceback, mathutils
        SCRATCH = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/599a7627-7a49-4e5e-bc4f-37f7ddc0fa2f/scratchpad"
        OUT = SCRATCH + "/phase1_1_render_status.json"
        views = (
            {"png": SCRATCH + "/phase1_1_basement.png", "cam": (-34.0, -42.0, 30.0),
             "target": (0.0, 0.0, 0.0), "lens": 24, "hide_above": 5.0},
            {"png": SCRATCH + "/phase1_1_tower.png", "cam": (-78.0, -105.0, 62.0),
             "target": (0.0, 0.0, 28.0), "lens": 30, "hide_above": None},
            {"png": SCRATCH + "/phase1_1_west_portal.png", "cam": (-36.0, 0.0, 9.5),
             "target": (-12.0, 0.0, 1.5), "lens": 32, "hide_above": None},
            {"png": SCRATCH + "/phase1_1_east_portal.png", "cam": (33.0, -6.0, 10.0),
             "target": (19.0, 3.0, 1.5), "lens": 32, "hide_above": None},
        )
        done = []
        try:
            scene = bpy.data.scenes[0]
            if scene.world is None:
                scene.world = bpy.data.worlds.new("ZY_World")
            scene.world.use_nodes = True
            for n in scene.world.node_tree.nodes:
                if n.type == "BACKGROUND":
                    n.inputs[0].default_value = (0.55, 0.58, 0.63, 1.0)
                    n.inputs[1].default_value = 0.7
            if bpy.data.objects.get("ZY_Sun") is None:
                sd = bpy.data.lights.new("ZY_Sun", type="SUN")
                sd.energy = 2.0
                so = bpy.data.objects.new("ZY_Sun", sd)
                so.rotation_euler = (0.87, 0.0, 0.52)
                scene.collection.objects.link(so)
            engine = None
            for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
                try:
                    scene.render.engine = eng
                    engine = eng
                    break
                except Exception:
                    continue
            scene.render.resolution_x = 1400
            scene.render.resolution_y = 900
            scene.render.image_settings.file_format = "PNG"
            for v in views:
                hidden = []
                cam = None
                try:
                    cam_data = bpy.data.cameras.new("ZY_PreviewCam")
                    cam_data.lens = v["lens"]
                    cam = bpy.data.objects.new("ZY_PreviewCam", cam_data)
                    scene.collection.objects.link(cam)
                    cam.location = v["cam"]
                    direction = mathutils.Vector(v["target"]) - cam.location
                    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
                    scene.camera = cam
                    if v["hide_above"] is not None:
                        for ob in bpy.data.objects:
                            if ob.type != "MESH" or ob.hide_render:
                                continue
                            zmin = min((ob.matrix_world @ mathutils.Vector(c)).z for c in ob.bound_box)
                            if zmin > v["hide_above"] or ob.name == "Basement_Ceiling":
                                ob.hide_render = True
                                hidden.append(ob.name)
                    scene.render.filepath = v["png"]
                    bpy.ops.render.render(write_still=True)
                    done.append({"png": v["png"], "hidden": len(hidden)})
                finally:
                    for name in hidden:
                        ob = bpy.data.objects.get(name)
                        if ob is not None:
                            ob.hide_render = False
                    if cam is not None:
                        cd = cam.data
                        bpy.data.objects.remove(cam, do_unlink=True)
                        bpy.data.cameras.remove(cd)
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "engine": engine, "renders": done}, f, indent=1)
        except Exception:
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "error": traceback.format_exc(), "renders": done}, f, indent=1)
        return None

    bpy.app.timers.register(do_render, first_interval=0.3)

zy_render_preview()
