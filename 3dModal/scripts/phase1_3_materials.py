# Zyvion Phase 1.3m — PROCEDURAL SURFACE PASS
# ("every surface is still flat colour, no UVs or maps").
#
# Rebuilds the shared ZY_* palette as real node graphs instead of a single flat
# Base Color: noise / wave / brick textures drive colour variation, roughness
# variation and bump, so surfaces catch light unevenly like real material.
# Texture coordinates come from the GENERATED input, so this works without a UV
# unwrap and needs no external image files.
#
# It also box-projects a UV layer onto every mesh that lacks one. Those UVs are
# what a later image-bake pass needs; box projection tiles correctly but DOES
# overlap, so an AO/lightmap bake will still need a second, non-overlapping UV
# set (see the bake plan in ZYVION_HYBRID_ARCHITECTURE.md section 9).
#
# IMPORTANT for Phase 2: glTF does not carry procedural nodes. These materials
# improve the Blender renders only - the GLB export needs them baked to images.
# Idempotent: rebuilds node trees from scratch each run; UV pass skips meshes
# that already carry a "ZY_UV" layer.

def zy_materials():
    import bpy, bmesh, json, traceback
    OUT = r"C:/Users/alira/AppData/Local/Temp/claude/C--Users-alira-Documents-portfolio-3d/a6c07fe3-79fa-4033-895b-c5ebf725dc74/scratchpad/phase1_3_mat_status.json"
    stats = {"rebuilt": 0, "uv": 0}
    try:
        import math
        fp = bpy.data.filepath
        if "autosave" in fp.lower():
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "step": "phase1_3_mat", "error": "REFUSED: autosave: " + fp}, f, indent=1)
            return

        def hexrgb(h):
            h = h.lstrip("#")
            return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0, 1.0)

        def shade(c, f):
            return (max(0.0, min(1.0, c[0] * f)), max(0.0, min(1.0, c[1] * f)),
                    max(0.0, min(1.0, c[2] * f)), 1.0)

        ARCH = {
            "concrete": (14.0, 0.82, 0.20, 0.78, 0.94, "noise"),
            "wall":     (9.0, 0.90, 0.10, 0.70, 0.86, "noise"),
            "floor":    (22.0, 0.90, 0.06, 0.32, 0.52, "noise"),
            "tile":     (0.0, 0.93, 0.16, 0.30, 0.55, "brick"),
            "wood":     (26.0, 0.90, 0.06, 0.42, 0.62, "wave"),
            "fabric":   (48.0, 0.88, 0.26, 0.85, 0.98, "noise"),
            "metal":    (11.0, 0.88, 0.05, 0.22, 0.42, "noise"),
            "asphalt":  (34.0, 0.76, 0.30, 0.86, 0.98, "noise"),
            "grass":    (26.0, 0.64, 0.34, 0.90, 1.00, "noise"),
            "screen":   (0.0, 1.00, 0.00, 0.14, 0.20, "flat"),
            "glass":    (0.0, 1.00, 0.00, 0.03, 0.07, "flat"),
        }
        MAP = {
            "Concrete_Slab": ("concrete", "#9A9A94", 0.0),
            "Wall_OffWhite": ("wall", "#E8E4DC", 0.0),
            "Lobby_Floor": ("floor", "#CDC9C0", 0.0),
            "Tile_Paver": ("tile", "#C7BFB0", 0.0),
            "Tile_Grout": ("concrete", "#8E877A", 0.0),
            "Wood_Warm": ("wood", "#8C6748", 0.0),
            "Couch_Charcoal": ("fabric", "#3A3F46", 0.0),
            "Curtain_Cream": ("fabric", "#D9CBB0", 0.0),
            "Divider_Grey": ("fabric", "#6E6E68", 0.0),
            "Metal_Dark": ("metal", "#2B2B2E", 0.85),
            "Steel_Brushed": ("metal", "#9BA1A8", 0.92),
            "Duct_Silver": ("metal", "#AEB6BD", 0.80),
            "AC_White": ("wall", "#EDEDE8", 0.0),
            "Ceramic_White": ("floor", "#E8E8E4", 0.0),
            "Asphalt": ("asphalt", "#2A2C30", 0.0),
            "Grass_Green": ("grass", "#4E8B3C", 0.0),
            "Hedge_Green": ("grass", "#3B6B30", 0.0),
            "Path_Turq": ("floor", "#5FA9A6", 0.0),
            "Helipad_Dark": ("asphalt", "#33383B", 0.0),
            "Solar_Cell": ("metal", "#1B2A4A", 0.35),
            "Heli_Body": ("metal", "#37506B", 0.25),
            "Screen_Teal": ("screen", "#0E4350", 0.0),
            "NPC_Body": ("fabric", "#38414E", 0.0),
        }

        def build(m, arch, hexc, metal):
            m.use_nodes = True
            nt = m.node_tree
            nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            out.location = (620, 0)
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
            bsdf.location = (300, 0)
            nt.links.new(bsdf.outputs[0], out.inputs[0])
            base = hexrgb(hexc)
            scale, spread, bump, rlo, rhi, kind = ARCH[arch]
            try:
                bsdf.inputs["Metallic"].default_value = metal
            except Exception:
                pass
            if kind == "flat":
                bsdf.inputs["Base Color"].default_value = base
                bsdf.inputs["Roughness"].default_value = (rlo + rhi) / 2.0
                if arch == "glass":
                    try:
                        bsdf.inputs["Alpha"].default_value = 0.28
                    except Exception:
                        pass
                    for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
                        try:
                            setattr(m, attr, val)
                        except Exception:
                            pass
                m.diffuse_color = base
                return
            coord = nt.nodes.new("ShaderNodeTexCoord")
            coord.location = (-760, 0)
            mapn = nt.nodes.new("ShaderNodeMapping")
            mapn.location = (-580, 0)
            nt.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
            if kind == "brick":
                tex = nt.nodes.new("ShaderNodeTexBrick")
                tex.location = (-380, 60)
                tex.inputs["Scale"].default_value = 9.0
                tex.inputs["Mortar Size"].default_value = 0.018
                tex.inputs["Color1"].default_value = base
                tex.inputs["Color2"].default_value = shade(base, 0.94)
                tex.inputs["Mortar"].default_value = shade(base, 0.72)
                nt.links.new(mapn.outputs["Vector"], tex.inputs["Vector"])
                facout = tex.outputs["Fac"]
            elif kind == "wave":
                tex = nt.nodes.new("ShaderNodeTexWave")
                tex.location = (-380, 60)
                tex.inputs["Scale"].default_value = scale
                tex.inputs["Distortion"].default_value = 3.5
                tex.inputs["Detail"].default_value = 2.0
                nt.links.new(mapn.outputs["Vector"], tex.inputs["Vector"])
                facout = tex.outputs["Fac"]
            else:
                tex = nt.nodes.new("ShaderNodeTexNoise")
                tex.location = (-380, 60)
                tex.inputs["Scale"].default_value = scale
                tex.inputs["Detail"].default_value = 6.0
                tex.inputs["Roughness"].default_value = 0.6
                nt.links.new(mapn.outputs["Vector"], tex.inputs["Vector"])
                facout = tex.outputs["Fac"]
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.location = (-160, 140)
            ramp.color_ramp.elements[0].position = 0.32
            ramp.color_ramp.elements[0].color = shade(base, spread)
            ramp.color_ramp.elements[1].position = 0.72
            ramp.color_ramp.elements[1].color = base
            nt.links.new(facout, ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            rr = nt.nodes.new("ShaderNodeMapRange")
            rr.location = (-160, -110)
            rr.inputs["To Min"].default_value = rlo
            rr.inputs["To Max"].default_value = rhi
            nt.links.new(facout, rr.inputs["Value"])
            nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
            if bump > 0.0:
                fine = nt.nodes.new("ShaderNodeTexNoise")
                fine.location = (-380, -300)
                fine.inputs["Scale"].default_value = max(scale, 8.0) * 3.0
                fine.inputs["Detail"].default_value = 8.0
                nt.links.new(mapn.outputs["Vector"], fine.inputs["Vector"])
                bmp = nt.nodes.new("ShaderNodeBump")
                bmp.location = (60, -300)
                bmp.inputs["Strength"].default_value = bump
                nt.links.new(fine.outputs["Fac"], bmp.inputs["Height"])
                nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
            m.diffuse_color = base

        for m in bpy.data.materials:
            if not m.name.startswith("ZY_"):
                continue
            if "Glass" in m.name:
                build(m, "glass", "#7EC8E8", 0.0)
                stats["rebuilt"] += 1
                continue
            if m.name.startswith("ZY_Car_"):
                hexc = "#" + m.name.replace("ZY_Car_", "")[:6]
                try:
                    hexrgb(hexc)
                except Exception:
                    hexc = "#8A8F96"
                build(m, "metal", hexc, 0.45)
                stats["rebuilt"] += 1
                continue
            hit = None
            for frag, cfg in MAP.items():
                if frag in m.name:
                    hit = cfg
                    break
            if hit is None:
                continue
            build(m, hit[0], hit[1], hit[2])
            stats["rebuilt"] += 1

        for ob in bpy.data.objects:
            if ob.type != "MESH" or ob.data is None:
                continue
            me = ob.data
            if len(me.polygons) == 0 or "ZY_UV" in [l.name for l in me.uv_layers]:
                continue
            try:
                uv = me.uv_layers.new(name="ZY_UV")
                sx = ob.dimensions.x or 1.0
                sy = ob.dimensions.y or 1.0
                sz = ob.dimensions.z or 1.0
                TD = 0.5
                for poly in me.polygons:
                    n = poly.normal
                    ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                    for li in poly.loop_indices:
                        co = me.vertices[me.loops[li].vertex_index].co
                        if az >= ax and az >= ay:
                            u, v = co.x * sx, co.y * sy
                        elif ax >= ay:
                            u, v = co.y * sy, co.z * sz
                        else:
                            u, v = co.x * sx, co.z * sz
                        uv.data[li].uv = (u * TD, v * TD)
                stats["uv"] += 1
            except Exception:
                pass

        bpy.context.view_layer.update()
        with open(OUT, "w", encoding="utf-8") as f:
            d = {"ok": True, "step": "phase1_3_mat", "filepath": fp}
            d.update(stats)
            json.dump(d, f, indent=1)
    except Exception:
        with open(OUT, "w", encoding="utf-8") as f:
            d = {"ok": False, "step": "phase1_3_mat", "error": traceback.format_exc()}
            d.update(stats)
            json.dump(d, f, indent=1)

import bpy
bpy.app.timers.register(zy_materials, first_interval=0.1)
