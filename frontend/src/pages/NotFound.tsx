import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <main className="dash-main">
      <div className="container" style={{ minHeight: "70vh", display: "grid", placeItems: "center", textAlign: "center" }}>
        <div>
          <h1 style={{ fontSize: "clamp(3rem,10vw,6rem)" }} className="text-grad">404</h1>
          <p className="lead" style={{ marginInline: "auto" }}>This page wandered off. Let's get you back.</p>
          <Link className="btn btn-primary mt-4" to="/">Back to home</Link>
        </div>
      </div>
    </main>
  );
}
