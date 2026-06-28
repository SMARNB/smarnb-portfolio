/* Tiny bridge so the project modal / personal-project CTAs can seed the contact
   form's message before scrolling to it (replaces the direct DOM prefill in
   app.js openProject). The contact form drains this on mount. */
let pending: string | null = null;

export function setContactPrefill(msg: string): void {
  pending = msg;
}
export function takeContactPrefill(): string | null {
  const v = pending;
  pending = null;
  return v;
}
