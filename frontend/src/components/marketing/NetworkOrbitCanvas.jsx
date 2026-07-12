import { useEffect, useRef } from "react";

/**
 * Cribra's hero visual: a rotating document network. Nodes (submission
 * documents / requirements) are scattered in a 3D ball, linked to their
 * nearest neighbours, and the whole structure slowly orbits — a genuine
 * 3D rotation projected to 2D, so the links move rigidly with the cloud.
 * Accent nodes carry the verdict palette, and floating tags (CAC, TAX
 * CLEARANCE, NSITF · MISSING…) annotate nodes as they drift past.
 */
const GREEN = "#1b7a43";
const RED = "#c05b2e";
const AMBER = "#b7791f";
const OLIVE = "#8a8a2e";
const INK = "#1a1714";
const TAU = Math.PI * 2;

const PALETTE = [
  { c: INK, weight: 0.58 },
  { c: GREEN, weight: 0.14 },
  { c: OLIVE, weight: 0.12 },
  { c: RED, weight: 0.08 },
  { c: AMBER, weight: 0.08 },
];

const TAGS = [
  { text: "CAC CERTIFICATE", color: GREEN },
  { text: "TAX CLEARANCE", color: GREEN },
  { text: "PENCOM", color: GREEN },
  { text: "ITF COMPLIANCE", color: OLIVE },
  { text: "NSITF · MISSING", color: RED },
  { text: "AVG TURNOVER · REVIEW", color: AMBER },
  { text: "EQUIPMENT SCHEDULE", color: OLIVE },
  { text: "KEY PERSONNEL", color: GREEN },
];

const FOCAL = 640;
const TILT = 0.42; // fixed X-tilt so the orbit reads as 3D

export default function NetworkOrbitCanvas({ className = "" }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let raf;
    let w = 0;
    let h = 0;
    let cx = 0;
    let cy = 0;
    let R = 0;
    let nodes = [];
    let links = [];
    let tags = [];
    let lastTagAt = 0;
    const mouse = { x: 0.5, y: 0.5 };

    const pickColor = () => {
      let r = Math.random();
      for (const p of PALETTE) {
        if (r < p.weight) return p.c;
        r -= p.weight;
      }
      return INK;
    };

    function layout() {
      const rect = canvas.parentElement.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      if (w < 1 || h < 1) {
        nodes = [];
        return;
      }
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const wide = w >= 900;
      cx = wide ? w * 0.73 : w * 0.5;
      cy = h * 0.5;
      R = wide ? Math.min(h * 0.4, w * 0.22, 330) : Math.min(w * 0.42, h * 0.62);

      // random points in a ball, slightly flattened vertically like theirs
      const count = wide ? 84 : 74;
      nodes = Array.from({ length: count }, () => {
        let x, y, z;
        do {
          x = (Math.random() * 2 - 1);
          y = (Math.random() * 2 - 1);
          z = (Math.random() * 2 - 1);
        } while (x * x + y * y + z * z > 1);
        return {
          x: x * R,
          y: y * R * 0.86,
          z: z * R,
          size: 1.4 + Math.pow(Math.random(), 2.4) * 6.4,
          color: pickColor(),
          sx: 0,
          sy: 0,
          depth: 1,
        };
      });

      // each node links to its 1–2 nearest neighbours in 3D — rigid structure
      const seen = new Set();
      links = [];
      nodes.forEach((n, i) => {
        const near = nodes
          .map((m, j) => ({ j, d: (m.x - n.x) ** 2 + (m.y - n.y) ** 2 + (m.z - n.z) ** 2 }))
          .filter((o) => o.j !== i)
          .sort((a, b) => a.d - b.d)
          .slice(0, 1 + (i % 2));
        for (const o of near) {
          const key = i < o.j ? `${i}-${o.j}` : `${o.j}-${i}`;
          if (!seen.has(key)) {
            seen.add(key);
            links.push([i, o.j]);
          }
        }
      });
      tags = [];
    }

    function project(theta, px, py) {
      const cosT = Math.cos(theta);
      const sinT = Math.sin(theta);
      const cosX = Math.cos(TILT);
      const sinX = Math.sin(TILT);
      for (const n of nodes) {
        const rx = n.x * cosT + n.z * sinT;
        const rz = -n.x * sinT + n.z * cosT;
        const ry = n.y * cosX - rz * sinX;
        const rz2 = n.y * sinX + rz * cosX;
        const p = FOCAL / (FOCAL + rz2);
        n.depth = p;
        n.sx = cx + px + rx * p;
        n.sy = cy + py + ry * p;
      }
    }

    function drawTag(t) {
      const n = nodes[t.node];
      const alpha = Math.min(1, t.age / 20) * Math.min(1, Math.max(0, (t.life - t.age) / 26));
      if (alpha <= 0) return;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.font = "500 10px 'JetBrains Mono', monospace";
      const tw = ctx.measureText(t.text).width;
      const pillW = tw + 26;
      let bx = n.sx + 16;
      if (bx + pillW > w - 8) bx = n.sx - pillW - 16;
      const by = n.sy - 30;
      ctx.strokeStyle = t.color;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(n.sx, n.sy);
      ctx.lineTo(bx > n.sx ? bx - 3 : bx + pillW + 3, by + 19);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.strokeStyle = "rgba(26,23,20,0.12)";
      ctx.beginPath();
      ctx.roundRect(bx, by, pillW, 20, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = t.color;
      ctx.beginPath();
      ctx.arc(bx + 10, by + 10, 3, 0, TAU);
      ctx.fill();
      ctx.fillStyle = INK;
      ctx.fillText(t.text, bx + 18, by + 13.5);
      ctx.restore();
    }

    function frame(now) {
      if (!nodes.length) {
        if (!reduced) raf = requestAnimationFrame(frame);
        return;
      }
      ctx.clearRect(0, 0, w, h);
      const px = (mouse.x - 0.5) * 10;
      const py = (mouse.y - 0.5) * 8;
      const theta = reduced ? 0.9 : now * 0.000085; // ~74s per revolution

      project(theta, px, py);

      // links — alpha follows depth so the far side recedes
      ctx.lineWidth = 0.6;
      for (const [a, b] of links) {
        const na = nodes[a];
        const nb = nodes[b];
        ctx.beginPath();
        ctx.moveTo(na.sx, na.sy);
        ctx.lineTo(nb.sx, nb.sy);
        ctx.globalAlpha = 0.07 + 0.1 * ((na.depth + nb.depth) / 2 - 0.7);
        ctx.strokeStyle = INK;
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      // nodes
      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.sx, n.sy, n.size * n.depth, 0, TAU);
        ctx.globalAlpha = Math.min(0.95, Math.max(0.22, (n.depth - 0.62) * 2.2));
        ctx.fillStyle = n.color;
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      // floating tags on foreground accent nodes
      if (!reduced && now - lastTagAt > 2800 && tags.length < 2) {
        const candidates = nodes
          .map((n, i) => ({ n, i }))
          .filter(({ n, i }) => n.color !== INK && n.depth > 0.95 && n.size > 2 && !tags.some((t) => t.node === i));
        if (candidates.length) {
          lastTagAt = now;
          const { n, i } = candidates[(Math.random() * candidates.length) | 0];
          const pool = TAGS.filter((t) => t.color === n.color);
          const tag = (pool.length ? pool : TAGS)[(Math.random() * (pool.length ? pool.length : TAGS.length)) | 0];
          tags.push({ node: i, text: tag.text, color: tag.color, age: 0, life: 380 });
        }
      }
      for (const t of tags) t.age++;
      tags = tags.filter((t) => t.age < t.life);
      for (const t of tags) drawTag(t);

      if (!reduced) raf = requestAnimationFrame(frame);
    }

    const onMove = (e) => {
      mouse.x = e.clientX / window.innerWidth;
      mouse.y = e.clientY / window.innerHeight;
    };
    const onResize = () => layout();

    layout();
    if (reduced) {
      // static pose with a couple of tags
      project(0.9, 0, 0);
      const accents = nodes.map((n, i) => ({ n, i })).filter(({ n }) => n.color !== INK && n.depth > 1);
      accents.slice(0, 2).forEach(({ n, i }, k) => {
        const pool = TAGS.filter((t) => t.color === n.color);
        const tag = (pool.length ? pool : TAGS)[k % (pool.length || TAGS.length)];
        tags.push({ node: i, text: tag.text, color: tag.color, age: 40, life: 260 });
      });
      frame(0);
    } else {
      raf = requestAnimationFrame(frame);
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <div className={`pointer-events-none absolute inset-0 ${className}`} aria-hidden="true">
      <canvas ref={canvasRef} className="block" />
    </div>
  );
}
