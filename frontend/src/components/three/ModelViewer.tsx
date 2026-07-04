/* ModelViewer — the code-split three.js half of ModelStage (never in the main
   bundle). First-party constraints, deliberately:
   - Draco decoding uses the vendored /public/draco/ files with the pure-JS
     decoder — no gstatic CDN (drei's default), no 'wasm-unsafe-eval' CSP;
   - no drei <Environment>/<OrbitControls>: presets fetch HDRs from CDNs, and
     OrbitControls hijacks one-finger touch scrolling. Lighting is plain lights
     (real models bake lighting/AO into textures per the export spec), and
     drag-rotate is a tiny pointer handler with touch-action: pan-y. */
import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Center, useGLTF } from "@react-three/drei";
import { Box3, MathUtils, Vector3, type Group } from "three";
import { DRACOLoader, type GLTFLoader } from "three-stdlib";

let draco: DRACOLoader | null = null;
function extendLoader(loader: GLTFLoader) {
  if (!draco) {
    draco = new DRACOLoader();
    // Vendored, same-origin, version-stamped path → served immutable-cached.
    // Bump the folder when upgrading three (decoder files change with it).
    draco.setDecoderPath("/assets/draco/1.5.7/");
    draco.setDecoderConfig({ type: "js" }); // JS decoder: CSP needs no wasm-unsafe-eval
  }
  loader.setDRACOLoader(draco);
}

/* Fit any export into view: normalise the largest dimension to a fixed world
   size so a Blender file's absolute scale never matters. */
const TARGET_SIZE = 2.2;

function DragSpin({
  groupRef,
  spinSpeed,
  interactive,
}: {
  groupRef: React.RefObject<Group>;
  spinSpeed: number;
  interactive: boolean;
}) {
  const { gl } = useThree();
  const dragging = useRef(false);

  useFrame((_, dt) => {
    const g = groupRef.current;
    if (!g) return;
    if (!dragging.current && spinSpeed) {
      g.rotation.y += Math.min(dt, 0.05) * 0.4 * spinSpeed;
    }
  });

  useEffect(() => {
    if (!interactive) return;
    const el = gl.domElement;
    let lastX = 0;
    let lastY = 0;
    const down = (e: PointerEvent) => {
      dragging.current = true;
      lastX = e.clientX;
      lastY = e.clientY;
      el.setPointerCapture?.(e.pointerId);
    };
    const move = (e: PointerEvent) => {
      const g = groupRef.current;
      if (!dragging.current || !g) return;
      g.rotation.y += (e.clientX - lastX) * 0.008;
      g.rotation.x = MathUtils.clamp(
        g.rotation.x + (e.clientY - lastY) * 0.005,
        -0.6,
        0.6
      );
      lastX = e.clientX;
      lastY = e.clientY;
    };
    const up = () => {
      dragging.current = false;
    };
    el.addEventListener("pointerdown", down);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", up);
    return () => {
      el.removeEventListener("pointerdown", down);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
    };
  }, [gl, interactive, groupRef]);

  return null;
}

function Model({ src, onReady }: { src: string; onReady: () => void }) {
  const { scene } = useGLTF(src, false, false, extendLoader);

  const scale = useMemo(() => {
    const box = new Box3().setFromObject(scene);
    const size = box.getSize(new Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    return TARGET_SIZE / maxDim;
  }, [scene]);

  useEffect(() => {
    onReady();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Center>
      <primitive object={scene} scale={scale} />
    </Center>
  );
}

export type ModelViewerProps = {
  src: string;
  paused: boolean;
  spinSpeed: number;
  interactive: boolean;
  onReady: () => void;
};

export default function ModelViewer({
  src,
  paused,
  spinSpeed,
  interactive,
  onReady,
}: ModelViewerProps) {
  const group = useRef<Group>(null);
  return (
    <Canvas
      className="model-canvas"
      dpr={[1, 2]}
      frameloop={paused ? "never" : "always"}
      camera={{ position: [0, 0, 4], fov: 40 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      style={{
        position: "absolute",
        inset: 0,
        touchAction: "pan-y", // vertical swipes keep scrolling the page
        cursor: interactive ? "grab" : "default",
      }}
    >
      <ambientLight intensity={0.65} />
      <directionalLight position={[3, 4, 5]} intensity={1.5} />
      <directionalLight position={[-4, -2, -3]} intensity={0.35} />
      <pointLight position={[-3, 2, -4]} intensity={4} color="#22d3ee" />
      <group ref={group}>
        <Model src={src} onReady={onReady} />
      </group>
      <DragSpin groupRef={group} spinSpeed={spinSpeed} interactive={interactive} />
    </Canvas>
  );
}
