/* Apply the `.dash-body` class to <body> while a dashboard route is mounted
   (removes the public header's top padding and switches to the flex layout the
   dashboards expect). Cleaned up on unmount. */
import { useEffect } from "react";

export function useDashBody(): void {
  useEffect(() => {
    document.body.classList.add("dash-body");
    return () => document.body.classList.remove("dash-body");
  }, []);
}
