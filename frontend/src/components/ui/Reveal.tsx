/* Scroll-reveal wrapper — rises + fades in with a soft spring as it enters the
   viewport (the Framer replacement for the old IntersectionObserver `.reveal`).
   Honors prefers-reduced-motion (renders statically). */
import { motion, useReducedMotion } from "framer-motion";
import type { HTMLMotionProps } from "framer-motion";
import type { ElementType, ReactNode } from "react";

interface RevealProps extends Omit<HTMLMotionProps<"div">, "children"> {
  children: ReactNode;
  as?: ElementType;
  delay?: number;
  y?: number;
  once?: boolean;
}

export function Reveal({ children, as, delay = 0, y = 26, once = true, ...rest }: RevealProps) {
  const reduce = useReducedMotion();
  const MotionTag = motion(as || "div");

  if (reduce) {
    const Tag = (as || "div") as ElementType;
    return <Tag {...(rest as object)}>{children}</Tag>;
  }

  return (
    <MotionTag
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once, amount: 0.18, margin: "0px 0px -40px 0px" }}
      transition={{ type: "spring", stiffness: 90, damping: 18, mass: 0.6, delay }}
      {...rest}
    >
      {children}
    </MotionTag>
  );
}
