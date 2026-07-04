/* ModelStage — the reusable 3D-model slot. A progressive enhancement:
   - always renders the poster image (works with no JS/WebGL, is what crawlers
     and reduced-motion users get, and never blocks LCP);
   - the heavy three.js viewer is code-split and only mounts once the stage
     scrolls near the viewport on a WebGL-capable, motion-ok device;
   - any load/render failure quietly falls back to the poster.
   Swap `src` for a new .glb (versioned filename — /assets/* is cached
   immutable) and `poster` for its Blender-rendered still; nothing else. */
import {
  Component,
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

const ModelViewer = lazy(() => import("./ModelViewer"));

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

/* Errors thrown while loading/rendering the model (bad file, lost GL context,
   network) surface here; we drop the canvas and leave the poster. */
class ModelBoundary extends Component<
  { onError: () => void; children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onError();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

export type ModelStageProps = {
  /** Path to the Draco-compressed .glb, e.g. /assets/models/hero-v1.glb */
  src: string;
  /** Poster/fallback image (Blender still render); always in the DOM. */
  poster: string;
  /** Accessible description of what the model shows. */
  alt?: string;
  className?: string;
  /** Idle auto-rotation speed multiplier; 0 disables the spin. */
  spinSpeed?: number;
  /** Allow drag-to-rotate (vertical touch swipes still scroll the page). */
  interactive?: boolean;
};

export function ModelStage({
  src,
  poster,
  alt = "",
  className = "",
  spinSpeed = 1,
  interactive = true,
}: ModelStageProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [can3d, setCan3d] = useState(false);
  const [near, setNear] = useState(false); // ever approached viewport → mount
  const [visible, setVisible] = useState(false); // on screen now → run frames
  const [ready, setReady] = useState(false); // first model mounted → fade poster
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setCan3d(!reduce && webglAvailable());
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el || !can3d || failed) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setNear(true);
          setVisible(e.isIntersecting);
        }
      },
      { rootMargin: "240px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [can3d, failed]);

  const show3d = can3d && near && !failed;
  return (
    <div
      ref={ref}
      className={("model-stage " + className).trim()}
      role={alt ? "img" : undefined}
      aria-label={alt || undefined}
    >
      <img
        className={"model-poster" + (ready && !failed ? " is-hidden" : "")}
        src={poster}
        alt=""
        aria-hidden="true"
        loading="lazy"
        decoding="async"
      />
      {show3d && (
        <ModelBoundary onError={() => setFailed(true)}>
          <Suspense fallback={null}>
            <ModelViewer
              src={src}
              paused={!visible}
              spinSpeed={spinSpeed}
              interactive={interactive}
              onReady={() => setReady(true)}
            />
          </Suspense>
        </ModelBoundary>
      )}
    </div>
  );
}
