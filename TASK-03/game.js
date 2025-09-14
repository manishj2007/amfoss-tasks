// --- DOM refs ---
const canvas  = document.getElementById("stage");
const ctx     = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const bestEl  = document.getElementById("best");
const msgEl   = document.getElementById("msg");
const audio   = document.getElementById("scribble");
const muteBtn = document.getElementById("mute");
const resetBtn= document.getElementById("reset");

// --- center point ---
const cx = canvas.width / 2;
const cy = canvas.height / 2;

// --- drawing state ---
let drawing = false;
let path = [];

// --- best score (sessionStorage) ---
const BEST_KEY = "bestCircleScore";
let bestScore = Number(sessionStorage.getItem(BEST_KEY) || 0);
bestEl.textContent = `Best: ${bestScore}`;
function updateBest(s) {
  if (s > bestScore) {
    bestScore = s;
    sessionStorage.setItem(BEST_KEY, String(bestScore));
    bestEl.textContent = `Best: ${bestScore}`;
  }
}

// --- sound ---
audio.volume = 0.3;
muteBtn.addEventListener("click", () => {
  audio.muted = !audio.muted;
  muteBtn.textContent = audio.muted ? "🔇" : "🔊";
});

// --- small helpers ---
function drawDot() {
  ctx.beginPath();
  ctx.arc(cx, cy, 5, 0, Math.PI * 2);
  ctx.fillStyle = "red";
  ctx.fill();
}
function clearCanvas() { ctx.clearRect(0, 0, canvas.width, canvas.height); }
function redraw() {
  clearCanvas();
  if (path.length) {
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    for (let i = 1; i < path.length; i++) ctx.lineTo(path[i].x, path[i].y);
    ctx.strokeStyle = "lime";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap  = "round";
    ctx.stroke();
  }
  drawDot();
}
function addPoint(e) {
  const r = canvas.getBoundingClientRect();
  const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
  const y = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
  path.push({ x, y });
}

// --- point-in-polygon (ray casting) ---
function pointInPolygon(pt, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i].x, yi = poly[i].y;
    const xj = poly[j].x, yj = poly[j].y;
    const intersects = ((yi > pt.y) !== (yj > pt.y)) &&
      (pt.x < (xj - xi) * (pt.y - yi) / ((yj - yi) || 1e-12) + xi);
    if (intersects) inside = !inside;
  }
  return inside;
}

// --- scoring ---
function checkCircle() {
  msgEl.textContent = "";
  if (path.length < 60) { scoreEl.textContent = "Score: too short!"; return; }

  // close the loop for tests (if last point far from first)
  const loop = path.slice();
  const first = loop[0], last = loop[loop.length - 1];
  const gap = Math.hypot(first.x - last.x, first.y - last.y);
  if (gap > 3) loop.push(first);

  // ONLY score if center is inside the loop
  const inside = pointInPolygon({ x: cx, y: cy }, loop);
  if (!inside) {
    scoreEl.textContent = "Score: —";
    msgEl.textContent = "The red dot is not inside your circle!";
    redraw();
    return;
  }

  // distances from center
  const radii = loop.map(p => Math.hypot(p.x - cx, p.y - cy));
  const mean  = radii.reduce((a,b)=>a+b,0) / radii.length;
  const variance = radii.reduce((a,b)=>a+(b-mean)**2,0) / radii.length;
  const std = Math.sqrt(variance);

  // base score: higher when std/mean is low
  let score = Math.round(100 * (1 - std / mean));
  if (score < 0) score = 0;

  // small penalties (optional)
  const idealLen = 2 * Math.PI * mean;
  const pathLen = loop.slice(1).reduce((L, p, i) =>
    L + Math.hypot(p.x - loop[i].x, p.y - loop[i].y), 0);
  const lenPenalty = Math.max(0, (pathLen / idealLen - 1) * 20); // cap ~20
  const gapPenalty = Math.min((gap / mean) * 100, 20);
  score = Math.max(0, Math.round(score - lenPenalty - gapPenalty));

  scoreEl.textContent = `Score: ${score}`;
  updateBest(score);

  // draw a faint guide circle at mean radius
  ctx.beginPath();
  ctx.setLineDash([6, 6]);
  ctx.strokeStyle = "#bbb";
  ctx.arc(cx, cy, mean, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);
}

// --- mouse events ---
canvas.addEventListener("mousedown", e => {
  drawing = true; path = []; addPoint(e); redraw();
  audio.currentTime = 0; audio.loop = true; audio.play().catch(()=>{});
});
canvas.addEventListener("mousemove", e => { if (!drawing) return; addPoint(e); redraw(); });
window.addEventListener("mouseup", () => {
  if (!drawing) return;
  drawing = false; audio.pause(); audio.currentTime = 0; checkCircle();
});

// --- touch (optional) ---
canvas.addEventListener("touchstart", e => { e.preventDefault();
  drawing = true; path = []; addPoint(e); redraw();
  audio.currentTime = 0; audio.loop = true; audio.play().catch(()=>{});
},{passive:false});
canvas.addEventListener("touchmove", e => { e.preventDefault(); if (!drawing) return; addPoint(e); redraw(); }, {passive:false});
canvas.addEventListener("touchend",  e => { e.preventDefault();
  if (!drawing) return; drawing = false; audio.pause(); audio.currentTime = 0; checkCircle();
},{passive:false});

// --- reset ---
resetBtn.addEventListener("click", () => {
  path = []; msgEl.textContent = ""; scoreEl.textContent = "Score: —"; redraw();
});

// --- first draw ---
redraw();
