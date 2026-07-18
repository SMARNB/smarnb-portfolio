# Zyvion Phase 1.3 — lobby confirmation renders: (1) south exterior with the
# glass curtain + portal above the grand stairs, (2) interior from the portal
# looking at reception/greeter/hero screen (tilted up for the chandelier),
# (3) interior toward the east wall About panels + NE stair + couches,
# (4) high atrium overview, (5) reception close-up, (6) services close-up:
# chandelier rings, duct loop + diffusers, cable trays, slot vents.
# Interior views hide Lobby_Roof so skylight reaches the floor (EEVEE).
# Deferred to bpy.app.timers: render must run on Blender's main thread.

def zy_lobby_render():
    import bpy

    def do_render():
        import bpy, json, traceback, mathutils
        SCRATCH = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad"
        OUT = SCRATCH + "/phase1_3_render_status.json"
        views = (
            {"png": SCRATCH + "/phase1_3_lobby_exterior.png", "cam": (-40.0, -105.0, 24.0),
             "target": (0.0, -28.0, 17.0), "lens": 30, "hide": ()},
            {"png": SCRATCH + "/phase1_3_lobby_entry.png", "cam": (0.0, -46.5, 11.3),
             "target": (0.0, -4.0, 15.5), "lens": 20, "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_lobby_displays.png", "cam": (-18.0, -42.0, 11.5),
             "target": (16.0, -14.0, 13.0), "lens": 24, "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_lobby_atrium.png", "cam": (0.0, -45.0, 29.0),
             "target": (0.0, -5.0, 14.0), "lens": 22, "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_lobby_reception.png", "cam": (5.5, -17.0, 11.0),
             "target": (0.0, -8.8, 10.4), "lens": 35, "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_lobby_services.png", "cam": (-16.0, -41.0, 14.0),
             "target": (4.0, -16.0, 27.0), "lens": 26, "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_waiting_room.png", "cam": (-27.5, -45.0, 11.6),
             "target": (-44.0, -6.0, 11.0), "lens": 21, "hide": ("WWing_Stack_L2",)},
            {"png": SCRATCH + "/phase1_3_hr_overview.png", "cam": (26.5, -46.5, 14.6),
             "target": (46.0, -6.0, 10.0), "lens": 20, "hide": ("EWing_Stack_L2",)},
            {"png": SCRATCH + "/phase1_3_hr_corridor.png", "cam": (26.0, -27.5, 11.2),
             "target": (49.5, -27.5, 10.8), "lens": 28, "hide": ("EWing_Stack_L2",)},
            {"png": SCRATCH + "/phase1_3_west_exit.png", "cam": (-62.0, -20.0, 9.5),
             "target": (-50.5, -9.5, 7.5), "lens": 32, "hide": ()},
            {"png": SCRATCH + "/phase1_3_east_exit.png", "cam": (66.0, -10.0, 11.0),
             "target": (50.0, -24.0, 7.5), "lens": 30, "hide": ()},
            {"png": SCRATCH + "/phase1_3_rear_facade.png", "cam": (0.0, 112.0, 24.0),
             "target": (0.0, 46.0, 14.0), "lens": 22, "hide": ()},
            {"png": SCRATCH + "/phase1_3_hall.png", "cam": (-10.0, 2.5, 12.0),
             "target": (8.0, 46.0, 11.0), "lens": 19,
             "hide": ("Cubicle_Workspace_L1_W", "Cubicle_Workspace_L1_E",
                      "Cubicle_Workspace_L1_S", "Cubicle_Workspace_L1_N")},
            {"png": SCRATCH + "/phase1_3_lab.png", "cam": (-26.5, 46.5, 11.6),
             "target": (-46.0, 27.0, 10.6), "lens": 22,
             "hide": ("RearW_Stack_L2_S", "RearW_Stack_L2_E")},
            {"png": SCRATCH + "/phase1_3_offices.png", "cam": (27.0, 4.0, 12.2),
             "target": (43.0, 47.0, 10.8), "lens": 20,
             "hide": ("RearE_Stack_L2_S", "RearE_Stack_L2_W")},
            {"png": SCRATCH + "/phase1_3_lobby_west_door.png", "cam": (-12.0, -26.0, 11.3),
             "target": (-28.0, -26.0, 10.6), "lens": 26,
             "hide": ("Lobby_Roof",)},
            {"png": SCRATCH + "/phase1_3_aerial.png", "cam": (-95.0, -150.0, 120.0),
             "target": (0.0, -10.0, 30.0), "lens": 26, "hide": ()},
            {"png": SCRATCH + "/phase1_3_rooftop.png", "cam": (-2.0, -34.0, 92.0),
             "target": (2.0, 30.0, 60.0), "lens": 24, "hide": ()},
            {"png": SCRATCH + "/phase1_3_helipad.png", "cam": (-22.0, 8.0, 70.0),
             "target": (0.0, 30.0, 60.0), "lens": 32, "hide": ()},
            {"png": SCRATCH + "/phase1_3_site_front.png", "cam": (0.0, -175.0, 55.0),
             "target": (0.0, -70.0, 8.0), "lens": 28, "hide": ()},
            {"png": SCRATCH + "/phase1_3_parking.png", "cam": (-44.0, -128.0, 26.0),
             "target": (-40.0, -98.0, 6.0), "lens": 30, "hide": ()},
            {"png": SCRATCH + "/phase1_3_guardroom.png", "cam": (62.8, -110.0, 7.6),
             "target": (62.8, -96.0, 7.0), "lens": 18, "hide": ("GRoom_Roof",)},
            {"png": SCRATCH + "/phase1_3_guard_ext.png", "cam": (34.0, -134.0, 18.0),
             "target": (62.0, -104.0, 8.0), "lens": 30, "hide": ()},
            {"png": SCRATCH + "/phase1_3_gate_close.png", "cam": (-36.0, -132.0, 11.0),
             "target": (-36.0, -112.0, 7.5), "lens": 28, "hide": ()},
            {"png": SCRATCH + "/phase1_3_wingfloor.png", "cam": (-49.0, -46.0, 22.5),
             "target": (-30.0, -20.0, 21.0), "lens": 20,
             "hide": ("WFloor_F3_Slab_A", "WFloor_F3_Slab_B", "WFloor_F3_Slab_Bs",
                      "WFloor_F3_Slab_C", "WFloor_F3_Wall_S")},
        )
        done = []
        try:
            scene = bpy.data.scenes[0]
            if scene.world is None:
                scene.world = bpy.data.worlds.new("ZY_World")
            scene.world.use_nodes = True
            for n in scene.world.node_tree.nodes:
                if n.type == "BACKGROUND":
                    n.inputs[0].default_value = (0.50, 0.56, 0.66, 1.0)
                    n.inputs[1].default_value = 0.55     # restrained sky bounce
            # key sun: soft-edged so shadows read as real, not flat cut-outs
            so = bpy.data.objects.get("ZY_Sun")
            if so is None:
                sd = bpy.data.lights.new("ZY_Sun", type="SUN")
                so = bpy.data.objects.new("ZY_Sun", sd)
                scene.collection.objects.link(so)
            so.data.energy = 2.1
            try:
                so.data.angle = 0.06                     # soft shadow penumbra
            except Exception:
                pass
            so.rotation_euler = (0.82, 0.0, 0.62)
            # cool fill from the opposite side to lift the shadow side
            fo = bpy.data.objects.get("ZY_Fill")
            if fo is None:
                fd = bpy.data.lights.new("ZY_Fill", type="SUN")
                fo = bpy.data.objects.new("ZY_Fill", fd)
                scene.collection.objects.link(fo)
            fo.data.energy = 0.45
            fo.data.color = (0.72, 0.80, 1.0)
            try:
                fo.data.angle = 0.5
                fo.data.use_shadow = False
            except Exception:
                pass
            fo.rotation_euler = (1.05, 0.0, -2.3)
            # quality: more samples + ambient occlusion / raytracing when available
            try:
                scene.eevee.taa_render_samples = 96
            except Exception:
                pass
            for flag, val in (("use_gtao", True), ("use_raytracing", True),
                              ("use_shadows", True), ("use_soft_shadows", True)):
                try:
                    setattr(scene.eevee, flag, val)
                except Exception:
                    pass
            try:
                scene.eevee.gtao_distance = 1.4
            except Exception:
                pass
            try:
                scene.view_settings.look = "AgX - Medium Contrast"
            except Exception:
                try:
                    scene.view_settings.look = "Medium Contrast"
                except Exception:
                    pass
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
                    for name in v["hide"]:
                        ob = bpy.data.objects.get(name)
                        if ob is not None and not ob.hide_render:
                            ob.hide_render = True
                            hidden.append(name)
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

zy_lobby_render()
