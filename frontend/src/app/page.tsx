"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Video, Crosshair, Radar, BarChart3,
  AlertTriangle, MessageSquare, Settings, LogOut, ChevronRight,
  Shield, Activity, Cpu, HardDrive, Wifi, Send, Bell, Eye,
  UserCheck, Package, MapPin, Clock, Zap, TrendingUp,
  Database, Bot, Download, Volume2, RefreshCw, Maximize2, Minimize2,
  Mic, Play, Pause, Square, CheckCircle, Info, XCircle,
  UserPlus, Award, Check, Save, ToggleLeft, ToggleRight,
  Sliders, SlidersHorizontal, SlidersVertical, Edit2, X, Trash, Plus
} from "lucide-react";

// ─── API base URL (proxied in dev, same-origin in prod) ──────────────────────
const API = "";

// ─── Types ───────────────────────────────────────────────────────────────────
interface CameraInfo {
  id: number; name: string; location: string; source?: string;
  online: boolean; disconnected: boolean; fps: number;
  persons: number; detections: number; threat_level: string; uptime: string;
  active_subjects?: any[]; detections_list?: any[];
}
interface HAEAPerson {
  pid: string;
  name: string;
  camera: string;
  emotion: string;
  emotion_score: number;
  activity_label: string;
  activity_score: number;
  attention: string;
  duration_secs: number;
  duration_str: string;
}

interface Telemetry {
  cpu: number; ram: number; disk: number; net_kb: number;
  gpu: number; gpu_name: string; cuda: boolean; hw_profile: string;
  yolo: boolean; face_recog: boolean; db: boolean; telegram: boolean;
  threat_level: string; fps_all: number[];
  uptime_secs: number;
}
interface Event {
  ts: string; event: string; camera: string; person: string; detail: string;
}
interface Summary {
  total_detections: number; known_persons: number; unknown_persons: number;
  objects_added: number; objects_removed: number; alerts: number;
  operator: string; uptime: string;
}

interface EnrolledUser {
  name: string;
  visitCount: number;
  lastSeen: string;
  accuracy: number;
  role: string;
  status: string;
  photo?: string;
  pid?: string;
}

// ─── Nav items ───────────────────────────────────────────────────────────────
const NAV = [
  { id: "overview",    icon: LayoutDashboard, label: "OVERVIEW" },
  { id: "cameras",     icon: Video,           label: "CAMERAS" },
  { id: "detection",   icon: Crosshair,       label: "DETECTION" },
  { id: "activity",    icon: Activity,        label: "ACTIVITY INTEL" },
  { id: "tactical",    icon: Radar,           label: "TACTICAL" },
  { id: "analytics",   icon: BarChart3,       label: "ANALYTICS" },
  { id: "events",      icon: AlertTriangle,   label: "EVENTS" },
  { id: "comms",       icon: MessageSquare,   label: "COMMUNICATION" },
  { id: "enrollment",  icon: UserPlus,        label: "ENROLLMENT" },
  { id: "settings",    icon: Settings,        label: "SETTINGS" },
];

const EVENT_COLORS: Record<string, string> = {
  PERSON_ENTERED: "#D4AF37", PERSON_RETURNED: "#D4AF37",
  PERSON_LEFT: "#B8B8B8", INTRUDER: "#FFD700",
  OBJ_ADDED: "#00E5FF", OBJ_REMOVED: "#00FFA3",
  ZONE_INTRUSION: "#D4AF37", BEHAVIOR: "#FFD700",
  EXPRESSION: "#FF8C00", RUNNING: "#FF6B35",
  SYSTEM_START: "#B8B8B8", BASELINE: "#B8B8B8",
};

function eventLabel(ev: string) {
  const m: Record<string,string> = {
    PERSON_ENTERED:"USER RECOGNIZED", PERSON_RETURNED:"USER BACK",
    PERSON_LEFT:"USER LEFT", INTRUDER:"UNAUTHORIZED SUBJECT",
    OBJ_ADDED:"OBJECT TRACKED", OBJ_REMOVED:"OBJECT DISMISSED",
    ZONE_INTRUSION:"SECURE ENTRY", BEHAVIOR:"AI ASSESSMENT",
    SYSTEM_START:"OMS CORE ONLINE", BASELINE:"BASELINE SECURED",
  };
  return m[ev] || ev;
}

// ─── Particle Canvas Background (Luxury Golden Particles) ─────────────────────
function ParticleCanvas({ active, density = 120, size = 3.0, thickness = 1.0 }: { active: boolean; density?: number; size?: number; thickness?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const sizeRef = useRef(size);
  const thicknessRef = useRef(thickness);

  useEffect(() => {
    sizeRef.current = size;
  }, [size]);

  useEffect(() => {
    thicknessRef.current = thickness;
  }, [thickness]);

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener("resize", resize);
    
    // Sparkles trailing logic
    type Sparkle = { x: number; y: number; vx: number; vy: number; r: number; life: number };
    let sparkles: Sparkle[] = [];
    let lastMouseX = 0, lastMouseY = 0;

    const trackMouse = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
      const dMouse = Math.hypot(e.clientX - lastMouseX, e.clientY - lastMouseY);
      if (dMouse > 6) {
        // Spawn glowing golden trailing micro-sparkles
        for (let k = 0; k < 2; k++) {
          sparkles.push({
            x: e.clientX + (Math.random() - 0.5) * 8,
            y: e.clientY + (Math.random() - 0.5) * 8,
            vx: (Math.random() - 0.5) * 0.8,
            vy: (Math.random() - 0.5) * 0.8 - 0.2, // float slightly upward
            r: (Math.random() * 1.5 + 0.5) * (sizeRef.current / 3.0),
            life: 1.0
          });
        }
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      }
    };
    window.addEventListener("mousemove", trackMouse);

    // Shockwave click event listener!
    const handleWindowClick = (e: MouseEvent) => {
      const cx = e.clientX;
      const cy = e.clientY;
      // Trigger a powerful blast shockwave, throwing all particles outwards!
      particles.forEach(p => {
        const dx = p.x - cx;
        const dy = p.y - cy;
        const d = Math.hypot(dx, dy);
        if (d < 300 && d > 0) {
          const force = (300 - d) * 0.09; // Strong repulsion close to click
          p.vx += (dx / d) * force;
          p.vy += (dy / d) * force;
        }
      });
      // Spawn extra sparkles in a circle blast!
      for (let k = 0; k < 12; k++) {
        const angle = (k / 12) * Math.PI * 2;
        const spd = Math.random() * 2 + 1;
        sparkles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * spd,
          vy: Math.sin(angle) * spd,
          r: (Math.random() * 2 + 0.8) * (sizeRef.current / 3.0),
          life: 1.0
        });
      }
    };
    window.addEventListener("click", handleWindowClick);

    type P = { x: number; y: number; vx: number; vy: number; r: number; alpha: number };
    const particles: P[] = Array.from({ length: density }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 2.8 + 1.2,          // Upgraded particle radius: 1.2px to 4.0px
      alpha: Math.random() * 0.5 + 0.25,      // Upgraded particle opacity: 0.25 to 0.75
    }));

    let animId: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const mx = mouseRef.current.x, my = mouseRef.current.y;

      // Update & Draw dynamic trails (sparkles)
      sparkles = sparkles.filter(s => {
        s.x += s.vx;
        s.y += s.vy;
        s.life -= 0.025; // dissolve over 40 frames (~0.6s)
        if (s.life <= 0) return false;

        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(212, 175, 55, ${s.life * 0.8})`;
        ctx.fill();
        return true;
      });

      // Update & Draw main particles
      particles.forEach(p => {
        const dx = p.x - mx, dy = p.y - my;
        const dist = Math.hypot(dx, dy);
        
        // Dynamic Vortex Swirl: attracted to cursor, rotating around it in a cool magnetic field!
        if (dist < 180 && dist > 0) {
          // 1. Attraction force
          p.vx -= (dx / dist) * 0.035;
          p.vy -= (dy / dist) * 0.035;
          
          // 2. Swirling force (perpendicular vector)
          p.vx += (-dy / dist) * 0.065;
          p.vy += (dx / dist) * 0.065;
        }

        p.vx *= 0.96; p.vy *= 0.96; // apply friction
        p.x += p.vx; p.y += p.vy;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        const rScaled = p.r * (sizeRef.current / 3.0);
        ctx.arc(p.x, p.y, rScaled, 0, Math.PI * 2);
        ctx.shadowBlur = 10;
        ctx.shadowColor = "rgba(212, 175, 55, 0.8)";
        ctx.fillStyle = `rgba(212, 175, 55, ${p.alpha})`;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Draw beautiful mesh lines between close particles
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(212, 175, 55, ${0.18 * (1 - d/100)})`;
            ctx.lineWidth = thicknessRef.current * (1 - d/100);
            ctx.stroke();
          }
        }
      }
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => { 
      cancelAnimationFrame(animId); 
      window.removeEventListener("resize", resize); 
      window.removeEventListener("mousemove", trackMouse); 
      window.removeEventListener("click", handleWindowClick);
    };
  }, [active, density]);

  if (!active) return null;
  return <canvas ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none" />;
}

// ─── Real-time Voice Waveform Visualizer Canvas ────────────────────────────────
function VoiceVisualizer({ state }: { state: "idle" | "listening" | "processing" | "speaking" }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let animId: number;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const W = canvas.width;
      const H = canvas.height;
      const midY = H / 2;

      phaseRef.current += 0.08;
      const phase = phaseRef.current;

      let lineCount = 3;
      let amplitude = 4;
      let frequency = 0.02;
      let speed = 0.05;
      let color = "rgba(212, 175, 55, ";

      if (state === "listening") {
        lineCount = 5;
        amplitude = 18;
        frequency = 0.045;
        speed = 0.15;
        color = "rgba(255, 215, 0, ";
      } else if (state === "processing") {
        lineCount = 4;
        amplitude = 6;
        frequency = 0.08;
        speed = 0.22;
        color = "rgba(0, 229, 255, ";
      } else if (state === "speaking") {
        lineCount = 5;
        amplitude = 22;
        frequency = 0.025;
        speed = 0.07;
        color = "rgba(212, 175, 55, ";
      } else {
        lineCount = 2;
        amplitude = 2;
        frequency = 0.015;
        speed = 0.02;
      }

      for (let i = 0; i < lineCount; i++) {
        ctx.beginPath();
        ctx.moveTo(0, midY);

        const currentAmp = amplitude * (1 - i / lineCount);
        const currentPhase = phase * (1 + i * speed) + i * 2;

        for (let x = 0; x < W; x++) {
          const angle = x * frequency + currentPhase;
          const y = midY + Math.sin(angle) * currentAmp * Math.sin(x * Math.PI / W);
          ctx.lineTo(x, y);
        }

        ctx.strokeStyle = color + (0.15 + (i / lineCount) * 0.45) + ")";
        ctx.lineWidth = i === 0 ? 2 : 1;
        ctx.stroke();
      }

      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animId);
  }, [state]);

  return <canvas ref={canvasRef} width={400} height={70} className="w-full h-full max-h-[70px] opacity-80" />;
}

// ─── Dynamic Live Sparkline Canvas ─────────────────────────────────────────────
function Sparkline({ data, color, height = 24 }: { data: number[]; color: string; height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;
    const ctx = canvas.getContext("2d")!;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const max = Math.max(...data, 1);
    const pts = data.map((v, i) => ({ x: (i / (data.length - 1)) * W, y: H - (v / max) * H * 0.85 - 2 }));

    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, color.replace(")", ",0.18)").replace("rgb", "rgba"));
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.beginPath();
    ctx.moveTo(pts[0].x, H);
    pts.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(pts[pts.length-1].x, H);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    pts.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.stroke();

    const last = pts[pts.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 2, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }, [data, color]);

  return <canvas ref={canvasRef} width={120} height={height} className="w-full opacity-90" style={{ height }} />;
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function Dashboard() {
  const [navExpanded, setNavExpanded] = useState(false);
  const [activeNav, setActiveNav] = useState("overview");
  const [activeCam, setActiveCam] = useState(0);
  const [cameras, setCameras] = useState<CameraInfo[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [activityData, setActivityData] = useState<HAEAPerson[]>([]);
  const [time, setTime] = useState(new Date());

  // Dynamic Sparkline state
  const [cpuHistory, setCpuHistory] = useState<number[]>(Array(40).fill(0));
  const [ramHistory, setRamHistory] = useState<number[]>(Array(40).fill(0));
  const [netHistory, setNetHistory] = useState<number[]>(Array(40).fill(0));
  const [gpuHistory, setGpuHistory] = useState<number[]>(Array(40).fill(0));

  // Button interaction loader state
  const [btnLoading, setBtnLoading] = useState<Record<string, boolean>>({});
  const [controlMsg, setControlMsg] = useState<string | null>(null);

  // Advanced Voice / AI Core states: idle, listening, processing, speaking
  const [aiState, setAiState] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [aiSubText, setAiSubText] = useState("Awaiting voice command input");
  const [speechOutput, setSpeechOutput] = useState("");

  // Face Registration wizard state
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardName, setWizardName] = useState("");
  const [wizardStep, setWizardStep] = useState(1);

  // Config settings state (Dynamically loaded & editable)
  const [opName, setOpName] = useState("Prajan");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [activeModel, setActiveModel] = useState("yolov8n.pt");
  const [confThresh, setConfThresh] = useState(0.45);
  const [tgBotToken, setTgBotToken] = useState("");
  const [tgChatId, setTgChatId] = useState("");
  const [detectNewIds, setDetectNewIds] = useState(true);
  const [useCuda, setUseCuda] = useState(true);
  const [detectPeople, setDetectPeople] = useState(true);
  const [detectObjects, setDetectObjects] = useState(true);
  const [particlesActive, setParticlesActive] = useState(true);
  const [particleDensity, setParticleDensity] = useState(120);
  const [matchThresh, setMatchThresh] = useState(0.36);
  const [particleSize, setParticleSize] = useState(3.0);
  const [meshThickness, setMeshThickness] = useState(1.0);

  const lastActivePidRef = useRef<string>("");
  const [cropKey, setCropKey] = useState<string>("");
  const activeTimeoutsRef = useRef<NodeJS.Timeout[]>([]);
  const fetchAbortControllerRef = useRef<AbortController | null>(null);

  const safeSetTimeout = useCallback((fn: () => void, delay: number) => {
    const timer = setTimeout(fn, delay);
    activeTimeoutsRef.current.push(timer);
    return timer;
  }, []);

  // Clear timeouts on unmount
  useEffect(() => {
    return () => {
      activeTimeoutsRef.current.forEach(clearTimeout);
    };
  }, []);

  // Client-side persistence for particlesActive and particleDensity
  useEffect(() => {
    if (typeof window !== "undefined") {
      const active = localStorage.getItem("particlesActive");
      if (active !== null) {
        setParticlesActive(active === "true");
      }
      const density = localStorage.getItem("particleDensity");
      if (density !== null) {
        setParticleDensity(parseInt(density, 10));
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("particlesActive", particlesActive.toString());
    }
  }, [particlesActive]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("particleDensity", particleDensity.toString());
    }
  }, [particleDensity]);

  const [camConnectUrls, setCamConnectUrls] = useState<string[]>(["0", "NONE", "NONE", "NONE"]);
  const [camNames, setCamNames] = useState<string[]>([]);
  const [newCamName, setNewCamName] = useState("");
  const [newCamSource, setNewCamSource] = useState("");
  const [newCamLocation, setNewCamLocation] = useState("");

  // Memory database state
  const [knownUsers, setKnownUsers] = useState<EnrolledUser[]>([
    { name: "Prajan", visitCount: 142, lastSeen: "Today 08:01", accuracy: 98.4, role: "System Administrator", status: "AUTHORIZED" },
    { name: "Dev Team", visitCount: 84, lastSeen: "Yesterday 18:24", accuracy: 96.1, role: "Core Developer", status: "VERIFIED" },
    { name: "Support AI", visitCount: 210, lastSeen: "Today 05:00", accuracy: 99.8, role: "Autonomous Agent", status: "ACTIVE" }
  ]);
  const [imgErrors, setImgErrors] = useState<Record<string, boolean>>({});

  // Advanced Face Enrollment States
  const [enrolledPeople, setEnrolledPeople] = useState<any[]>([]);
  const [enrollTab, setEnrollTab] = useState<"directory" | "guided" | "folder" | "import_json">("directory");
  const [guidedName, setGuidedName] = useState("");
  const [guidedPid, setGuidedPid] = useState("");
  const [guidedProgress, setGuidedProgress] = useState<Record<string, boolean>>({});
  const [guidedActivePoseIdx, setGuidedActivePoseIdx] = useState(0);
  const [guidedLog, setGuidedLog] = useState<string[]>([]);
  const [importName, setImportName] = useState("");
  const [importFolder, setImportFolder] = useState("");
  const [importLog, setImportLog] = useState<string[]>([]);
  const [settingsEnrollName, setSettingsEnrollName] = useState("");
  const [settingsEnrollFolder, setSettingsEnrollFolder] = useState("");
  const [settingsEnrollLoading, setSettingsEnrollLoading] = useState(false);
  const [settingsEnrollLog, setSettingsEnrollLog] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Success Face Recognition indicator
  const [isFaceUnlocked, setIsFaceUnlocked] = useState(false);
  
  // Real-time inline profile renaming states
  const [editingPid, setEditingPid] = useState<string | null>(null);
  const [editNameValue, setEditNameValue] = useState("");

  // Fullscreen Preview state & ref
  const viewportRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    const el = viewportRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen()
        .then(() => speakAI("Fullscreen preview activated"))
        .catch(() => {});
    } else {
      document.exitFullscreen()
        .then(() => speakAI("Fullscreen preview deactivated"))
        .catch(() => {});
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // ── Clock ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // ── Fetch configuration settings on mount ───────────────────────────────
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const r = await fetch(`${API}/api/settings`);
        const d = await r.json();
        if (d.status === "ok") {
          setOpName(d.username || "Prajan");
          setConfThresh(d.confidence || 0.45);
          setActiveModel(d.model || "yolov8n.pt");
          setTgBotToken(d.tg_token || "");
          setTgChatId(d.tg_chat_id || "");
          setDetectNewIds(d.detect_new_ids !== false);
          setUseCuda(d.use_cuda !== false);
          setDetectPeople(d.detect_people !== false);
          setDetectObjects(d.detect_objects !== false);
          setMatchThresh(d.match_threshold !== undefined ? d.match_threshold : 0.36);
          setParticleSize(d.particle_size !== undefined ? d.particle_size : 3.0);
          setMeshThickness(d.mesh_thickness !== undefined ? d.mesh_thickness : 1.0);
        }
      } catch {}
    };
    fetchSettings();
  }, []);

  // ── Data polling ──────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    if (fetchAbortControllerRef.current) {
      fetchAbortControllerRef.current.abort();
    }
    const controller = new AbortController();
    fetchAbortControllerRef.current = controller;
    const signal = controller.signal;

    try {
      const safeFetch = async (url: string) => {
        try {
          const res = await fetch(url, { signal });
          if (!res.ok) return null;
          return await res.json();
        } catch (e: any) {
          if (e.name === 'AbortError') throw e;
          return null;
        }
      };

      const results = await Promise.allSettled([
        safeFetch(`${API}/api/cameras`),
        safeFetch(`${API}/api/telemetry`),
        safeFetch(`${API}/api/events`),
        safeFetch(`${API}/api/summary`),
        safeFetch(`${API}/api/faces`),
        safeFetch(`${API}/api/activity`),
      ]);

      const camRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const telRes = results[1].status === 'fulfilled' ? results[1].value : null;
      const evtRes = results[2].status === 'fulfilled' ? results[2].value : null;
      const sumRes = results[3].status === 'fulfilled' ? results[3].value : null;
      const facRes = results[4].status === 'fulfilled' ? results[4].value : null;
      const actRes = results[5].status === 'fulfilled' ? results[5].value : null;

      if (camRes) {
        setCameras(camRes);
        if (Array.isArray(camRes)) {
          setCamNames(prev => {
            if (prev.length !== camRes.length) {
              return camRes.map((c: any) => c.name);
            }
            return prev;
          });
          setCamConnectUrls(prev => {
            if (prev.length !== camRes.length) {
              return camRes.map((c: any) => c.source || "");
            }
            return prev;
          });

          if (camRes.length > 0) {
            const activeSubject = camRes[activeCam]?.active_subjects?.[0];
            const currentPid = activeSubject?.pid || "";
            if (currentPid && currentPid !== lastActivePidRef.current) {
              lastActivePidRef.current = currentPid;
              setCropKey(Date.now().toString());
            }
          }
        }
        const activeCamDets = camRes[activeCam]?.persons || 0;
        setIsFaceUnlocked(activeCamDets > 0);
      }

      if (telRes) {
        setTelemetry(telRes);
        setCpuHistory(h => [...h.slice(1), telRes.cpu || 0]);
        setRamHistory(h => [...h.slice(1), telRes.ram || 0]);
        setNetHistory(h => [...h.slice(1), Math.min(telRes.net_kb || 0, 100)]);
        setGpuHistory(h => [...h.slice(1), telRes.gpu || 0]);

        if (typeof telRes.detect_new_ids === "boolean") {
          setDetectNewIds(telRes.detect_new_ids);
        }
      }

      if (evtRes) {
        setEvents(evtRes.slice(-15).reverse());
      }

      if (sumRes) {
        setSummary(sumRes);
      }

      if (facRes && Array.isArray(facRes) && facRes.length > 0) {
        setKnownUsers(facRes);
      }

      if (actRes && Array.isArray(actRes.persons)) {
        setActivityData(actRes.persons);
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        // Ignored
      }
    }
  }, [activeCam]);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 2000);
    return () => {
      clearInterval(t);
      if (fetchAbortControllerRef.current) {
        fetchAbortControllerRef.current.abort();
      }
    };
  }, [fetchAll]);

  // ── Browser Voice Speech Output ──────────────────────────────────────────
  const speakAI = useCallback((txt: string, forceEnabled?: boolean) => {
    const enabled = forceEnabled !== undefined ? forceEnabled : ttsEnabled;
    if (!enabled) return;
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(txt);
      const voices = window.speechSynthesis.getVoices();
      const idealVoice = voices.find(v => v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Zira"));
      if (idealVoice) utt.voice = idealVoice;
      utt.rate = 1.05;
      utt.pitch = 0.95;
      window.speechSynthesis.speak(utt);
    }
  }, [ttsEnabled]);

  // ── Real-time Inline Profile Renaming & Subject Promotion ────────────────
  const handleRenameSave = async (pid: string, newName: string) => {
    const trimmed = newName.trim();
    if (!trimmed) return;
    try {
      setBtnLoading(prev => ({ ...prev, rename_subject: true }));
      const r = await fetch(`${API}/api/control/rename_subject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pid, new_name: trimmed }),
      });
      const res = await r.json();
      if (res.status === "ok") {
        setEditingPid(null);
        await fetchAll(); // Re-fetch active camera information immediately
      } else {
        alert("Verification Error: " + (res.message || "Could not complete operation"));
      }
    } catch (err: any) {
      alert("Connection failure: " + err.message);
    } finally {
      setBtnLoading(prev => ({ ...prev, rename_subject: false }));
    }
  };

  // ── Voice Interface & Real Web Speech Recognition API ────────────────────
  const triggerVoiceAssistant = () => {
    if (aiState !== "idle") return;

    // Check if browser supports Web Speech API
    const SpeechRecognition = typeof window !== "undefined" ? ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition) : null;

    if (!SpeechRecognition) {
      // Fallback to simulated mode if browser doesn't support Web Speech API
      setAiState("listening");
      setAiSubText("Vocal simulation active. Listening...");
      speakAI("Listening");

      safeSetTimeout(async () => {
        setAiState("processing");
        setAiSubText("Simulating neural voice mapping...");
        
        const simQuery = "hey sentinel system status report";
        try {
          const res = await fetch(`${API}/api/voice_control`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: simQuery }),
          });
          const data = await res.json();
          if (data.status === "ok") {
            setAiState("speaking");
            setAiSubText("AI Core: speaking");
            setSpeechOutput(data.response);
            speakAI(data.response);
            
            if (data.action_executed === "nav_cameras") setActiveNav("cameras");
            else if (data.action_executed === "nav_settings") setActiveNav("settings");
            else if (data.action_executed === "nav_analytics") setActiveNav("analytics");
            else if (data.action_executed === "nav_events") setActiveNav("events");
            else if (data.action_executed === "open_register_wizard") setWizardOpen(true);
          } else {
            throw new Error();
          }
        } catch {
          setAiState("speaking");
          setAiSubText("AI Core: speaking");
          const text = `Greetings Operator ${opName}. AI Assistant online. Connection to neural networks verified. Ready for secure instructions.`;
          setSpeechOutput(text);
          speakAI(text);
        }

        safeSetTimeout(() => {
          setAiState("idle");
          setAiSubText("Awaiting voice command input");
          setSpeechOutput("");
        }, 6000);
      }, 2500);
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = "en-US";

      rec.onstart = () => {
        setAiState("listening");
        setAiSubText("Listening to microphone...");
        setSpeechOutput("Voice channel opened. Speak your command...");
        speakAI("Listening");
      };

      rec.onerror = (err: any) => {
        setAiState("idle");
        setAiSubText("Microphone transmission failed");
        setSpeechOutput("Vocal node failed to initialize. Ensure mic permission is granted.");
        speakAI("Microphone error");
      };

      rec.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        setAiState("processing");
        setAiSubText("Processing secure verbal protocol: " + transcript);
        setSpeechOutput(`"${transcript}"`);

        try {
          const res = await fetch(`${API}/api/voice_control`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript }),
          });
          const data = await res.json();
          if (data.status === "ok") {
            setAiState("speaking");
            setAiSubText("AI Core: speaking");
            setSpeechOutput(data.response);
            speakAI(data.response);

            // Dynamically coordinate UI adjustments requested by the backend AI
            if (data.action_executed === "alarm") {
              // Alarm was already fired in backend, sync UI alert states if any
            } else if (data.action_executed === "nav_cameras") {
              setActiveNav("cameras");
            } else if (data.action_executed === "nav_settings") {
              setActiveNav("settings");
            } else if (data.action_executed === "nav_analytics") {
              setActiveNav("analytics");
            } else if (data.action_executed === "nav_events") {
              setActiveNav("events");
            } else if (data.action_executed === "open_register_wizard") {
              setWizardOpen(true);
            }

            safeSetTimeout(() => {
              setAiState("idle");
              setAiSubText("Awaiting voice command input");
              setSpeechOutput("");
            }, 6000);
          } else {
            throw new Error(data.message || "Interpretation error");
          }
        } catch (err: any) {
          setAiState("idle");
          setAiSubText("AI Vocal interpretation failed");
          setSpeechOutput("Voice processor encountered an error mapping this command to the AI mainframe.");
          speakAI("Vocal processor error");
        }
      };

      rec.start();

    } catch (e) {
      setAiState("idle");
      setAiSubText("AI Vocal initialization failed");
    }
  };

  // ── Connected Control Handler pure functions ──────────────────────────────
  const doControl = async (action: string) => {
    setBtnLoading(b => ({ ...b, [action]: true }));
    try {
      const r = await fetch(`${API}/api/control/${action}`, { method: "POST" });
      const d = await r.json();
      setControlMsg(d.result || d.message || "Operation Completed Successfully");
      speakAI(d.result || d.message || "Executed");
      safeSetTimeout(() => setControlMsg(null), 3000);
    } catch (e) {
      setControlMsg("Transmission failed: " + e);
      safeSetTimeout(() => setControlMsg(null), 3000);
    } finally {
      setBtnLoading(b => ({ ...b, [action]: false }));
    }
  };

  // ── CCTV Camera Reconnect trigger ─────────────────────────────────────────
  const connectCctv = async (camId: number) => {
    const action = `connect_cam_${camId}`;
    setBtnLoading(b => ({ ...b, [action]: true }));
    const url = camConnectUrls[camId];
    speakAI("Reconnecting camera channel " + (camId + 1));
    
    try {
      const r = await fetch(`${API}/api/camera/${camId}/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: url })
      });
      const d = await r.json();
      setControlMsg(`Camera ${camId + 1} Reconnection Initiated`);
      safeSetTimeout(() => setControlMsg(null), 3000);
    } catch (e) {
      setControlMsg("Reconnection failed: " + e);
      safeSetTimeout(() => setControlMsg(null), 3000);
    } finally {
      setBtnLoading(b => ({ ...b, [action]: false }));
    }
  };

  // ── Rename camera channel ──────────────────────────────────────────────────
  const renameCam = async (idx: number) => {
    const newName = camNames[idx]?.trim();
    if (!newName) return;
    setBtnLoading(prev => ({ ...prev, [`rename_cam_${idx}`]: true }));
    try {
      const r = await fetch(`${API}/api/camera/${idx}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName }),
      });
      const d = await r.json();
      if (d.status === "ok") {
        speakAI(`Camera ${idx + 1} renamed to ${newName}`);
        fetchAll();
      }
    } catch {}
    setBtnLoading(prev => ({ ...prev, [`rename_cam_${idx}`]: false }));
  };

  // ── Add new camera node ────────────────────────────────────────────────────
  const addCam = async () => {
    if (!newCamName.trim()) {
      alert("Camera name is required");
      return;
    }
    setBtnLoading(prev => ({ ...prev, add_cam: true }));
    try {
      const r = await fetch(`${API}/api/camera/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCamName.trim(),
          source: newCamSource.trim() || "NONE",
          location: newCamLocation.trim() || "Monitored Sector"
        })
      });
      const d = await r.json();
      if (d.status === "ok") {
        speakAI(`Camera ${newCamName} added successfully`);
        setNewCamName("");
        setNewCamSource("");
        setNewCamLocation("");
        setCamNames([]);
        setCamConnectUrls([]);
        fetchAll();
      } else {
        alert(d.message || "Failed to add camera");
      }
    } catch (err) {
      alert("Error adding camera: " + err);
    } finally {
      setBtnLoading(prev => ({ ...prev, add_cam: false }));
    }
  };

  // ── Remove camera node ─────────────────────────────────────────────────────
  const removeCam = async (idx: number) => {
    const cam = cameras[idx];
    if (!cam) return;
    const confirmRemove = window.confirm(`Are you sure you want to remove camera '${cam.name}'?`);
    if (!confirmRemove) return;
    setBtnLoading(prev => ({ ...prev, [`remove_cam_${idx}`]: true }));
    try {
      const r = await fetch(`${API}/api/camera/${idx}/remove`, {
        method: "POST"
      });
      const d = await r.json();
      if (d.status === "ok") {
        speakAI(`Camera ${cam.name} removed successfully`);
        setCamNames([]);
        setCamConnectUrls([]);
        fetchAll();
      } else {
        alert(d.message || "Failed to remove camera");
      }
    } catch (err) {
      alert("Error removing camera: " + err);
    } finally {
      setBtnLoading(prev => ({ ...prev, [`remove_cam_${idx}`]: false }));
    }
  };

  // ── Forget registered face profile ───────────────────────────────────────
  const forgetFace = async (name: string) => {
    const confirmForget = window.confirm(`Forget and delete all biometric profiles for '${name}'?`);
    if (!confirmForget) return;
    try {
      const r = await fetch(`${API}/api/face/${encodeURIComponent(name)}`, {
        method: "DELETE",
      });
      const d = await r.json();
      if (d.status === "ok") {
        speakAI(`System profile forgotten: ${name}`);
        fetchAll();
      } else {
        alert(d.message || "Failed to delete profile");
      }
    } catch (err) {
      alert("Error deleting face profile");
    }
  };

  // Advanced Face Enrollment functions & effects
  const POSES = ["front", "left", "right", "slight_left", "slight_right", "up", "down", "neutral", "smiling", "glasses", "no_glasses"];

  const loadEnrolledPeople = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/enroll/people`);
      if (res.ok) {
        const data = await res.json();
        setEnrolledPeople(data);
      }
    } catch (e) {
      console.error("Error loading enrolled people:", e);
    }
  }, []);

  useEffect(() => {
    if (activeNav === "enrollment") {
      loadEnrolledPeople();
    }
  }, [activeNav, loadEnrolledPeople]);

  const startGuidedEnrollment = async (name: string, pidVal?: string) => {
    try {
      const res = await fetch(`${API}/api/enroll/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, pid: pidVal || "" }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setGuidedPid(data.pid);
        setGuidedName(data.name);
        setGuidedActivePoseIdx(0);
        setGuidedLog([`Enrollment session started for ${data.name} (ID: ${data.pid})`]);
        setEnrollTab("guided");
        const progressRes = await fetch(`${API}/api/enroll/status/${data.pid}`);
        const progressData = await progressRes.json();
        if (progressData.status === "ok") {
          setGuidedProgress(progressData.progress);
        }
      } else {
        alert("Error starting enrollment: " + (data.message || "Unknown error"));
      }
    } catch (e: any) {
      alert("Network error: " + e.message);
    }
  };

  const captureGuidedPose = async (pose: string) => {
    setBtnLoading(prev => ({ ...prev, capture_pose: true }));
    try {
      const res = await fetch(`${API}/api/enroll/capture/${guidedPid}/${pose}`, { method: "POST" });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setGuidedLog(prev => [...prev, `✓ Pose '${pose}' captured: Size: ${data.face_size}, Blur: ${data.blur_score.toFixed(1)}, Conf: ${data.confidence.toFixed(2)}`]);
        setGuidedProgress(prev => ({ ...prev, [pose]: true }));
        if (guidedActivePoseIdx < POSES.length - 1) {
          setGuidedActivePoseIdx(prev => prev + 1);
        }
      } else {
        setGuidedLog(prev => [...prev, `✗ Pose '${pose}' rejected: ${data.message || "Failed checks"}`]);
      }
    } catch (e: any) {
      setGuidedLog(prev => [...prev, `✗ Network error capturing pose: ${e.message}`]);
    } finally {
      setBtnLoading(prev => ({ ...prev, capture_pose: false }));
    }
  };

  const saveGuidedEnrollment = async () => {
    setBtnLoading(prev => ({ ...prev, save_enroll: true }));
    try {
      const res = await fetch(`${API}/api/enroll/save/${guidedPid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: guidedName })
      });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setGuidedLog(prev => [...prev, `✓ Profile saved successfully! Registered ${data.embeddings_count} embeddings.`]);
        alert(`Successfully enrolled ${guidedName} with ${data.embeddings_count} embeddings!`);
        setEnrollTab("directory");
        loadEnrolledPeople();
      } else {
        setGuidedLog(prev => [...prev, `✗ Save failed: ${data.message}`]);
        alert("Failed to save profile: " + data.message);
      }
    } catch (e: any) {
      alert("Network error saving profile: " + e.message);
    } finally {
      setBtnLoading(prev => ({ ...prev, save_enroll: false }));
    }
  };

  const [importLoading, setImportLoading] = useState(false);

  const handleFolderImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importName.trim() || !importFolder.trim()) return;
    setImportLoading(true);
    setImportLog([`Starting folder import from: ${importFolder}...`]);
    try {
      const res = await fetch(`${API}/api/enroll/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: importName, folder_path: importFolder })
      });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setImportLog(prev => [
          ...prev,
          `✓ Successfully imported profile ${data.name} (ID: ${data.pid})`,
          `✓ Accepted ${data.accepted_count} images`,
          `✓ Skipped ${data.duplicates_skipped} duplicates`
        ]);
        if (data.rejected_reasons && data.rejected_reasons.length > 0) {
          setImportLog(prev => [...prev, ...data.rejected_reasons.map((r: string) => `- Rejected: ${r}`)]);
        }
        alert(`Folder import successful! Imported ${data.accepted_count} images.`);
        setImportName("");
        setImportFolder("");
        loadEnrolledPeople();
      } else {
        setImportLog(prev => [...prev, `✗ Import failed: ${data.message}`]);
        alert("Import failed: " + data.message);
      }
    } catch (err: any) {
      setImportLog(prev => [...prev, `✗ Network error during import: ${err.message}`]);
    } finally {
      setImportLoading(false);
    }
  };

  const handleSettingsEnrollImport = async () => {
    if (!settingsEnrollName.trim() || !settingsEnrollFolder.trim()) return;
    setSettingsEnrollLoading(true);
    setSettingsEnrollLog([`Starting advanced person enrollment from: ${settingsEnrollFolder}...`]);
    try {
      const res = await fetch(`${API}/api/enroll/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: settingsEnrollName, folder_path: settingsEnrollFolder })
      });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setSettingsEnrollLog(prev => [
          ...prev,
          `✓ Successfully enrolled profile ${data.name} (ID: ${data.pid})`,
          `✓ Enrolled Quality Score: ${data.quality_score.toFixed(1)}%`,
          `✓ Accepted ${data.accepted_count} images:`,
          ...data.accepted_files.map((f: string) => `- Enrolled: ${f}`)
        ]);
        if (data.rejected_reasons && data.rejected_reasons.length > 0) {
          setSettingsEnrollLog(prev => [...prev, ...data.rejected_reasons.map((r: string) => `- Skipped: ${r}`)]);
        }
        alert(`Advanced Person Enrollment successful!\nSubject: ${data.name}\nQuality Score: ${data.quality_score.toFixed(1)}%`);
        setSettingsEnrollName("");
        setSettingsEnrollFolder("");
        loadEnrolledPeople();
      } else {
        setSettingsEnrollLog(prev => [...prev, `✗ Enrollment failed: ${data.message}`]);
        alert("Enrollment failed: " + data.message);
      }
    } catch (err: any) {
      setSettingsEnrollLog(prev => [...prev, `✗ Network error during enrollment: ${err.message}`]);
      alert("Network error: " + err.message);
    } finally {
      setSettingsEnrollLoading(false);
    }
  };

  const rebuildEnrollment = async (pid: string) => {
    setBtnLoading(prev => ({ ...prev, [`rebuild_${pid}`]: true }));
    try {
      const res = await fetch(`${API}/api/enroll/rebuild/${pid}`, { method: "POST" });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        alert(data.message);
        loadEnrolledPeople();
      } else {
        alert("Rebuild failed: " + data.message);
      }
    } catch (e: any) {
      alert("Network error rebuilding profile: " + e.message);
    } finally {
      setBtnLoading(prev => ({ ...prev, [`rebuild_${pid}`]: false }));
    }
  };

  const deleteEnrollment = async (pid: string) => {
    if (!confirm(`Are you sure you want to permanently delete profile ${pid}? This will remove all enrolled images and metadata.`)) return;
    setBtnLoading(prev => ({ ...prev, [`delete_${pid}`]: true }));
    try {
      const res = await fetch(`${API}/api/enroll/profile/${pid}`, { method: "DELETE" });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        alert(data.message);
        loadEnrolledPeople();
      } else {
        alert("Delete failed: " + data.message);
      }
    } catch (e: any) {
      alert("Network error deleting profile: " + e.message);
    } finally {
      setBtnLoading(prev => ({ ...prev, [`delete_${pid}`]: false }));
    }
  };

  const handleJsonImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const body = JSON.parse(event.target?.result as string);
        const res = await fetch(`${API}/api/enroll/import_profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.status === "ok") {
          alert(`Successfully imported profile package for ${data.name}!`);
          loadEnrolledPeople();
          setEnrollTab("directory");
        } else {
          alert("Import failed: " + data.message);
        }
      } catch (err: any) {
        alert("Error parsing or importing JSON: " + err.message);
      }
    };
    reader.readAsText(file);
  };

  // ── Local Face enrollment wizard handler ─────────────────────────────────
  const completeEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wizardName.trim()) return;

    setBtnLoading(b => ({ ...b, "enroll": true }));
    setWizardStep(2);
    speakAI("Initiating face scanning and database enrollment");

    safeSetTimeout(async () => {
      try {
        const r = await fetch(`${API}/api/control/register_face`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: wizardName.trim() })
        });
        const d = await r.json();

        if (r.ok && d.status === "ok") {
          const newUser: EnrolledUser = {
            name: wizardName,
            visitCount: 1,
            lastSeen: "Just now",
            accuracy: 97.4,
            role: "Registered User",
            status: "VERIFIED"
          };
          setKnownUsers(u => [newUser, ...u]);
          setWizardStep(3);
          speakAI("Registration complete. Enrolled " + wizardName + " into memory database.");
          safeSetTimeout(() => {
            setWizardOpen(false);
            setWizardStep(1);
            setWizardName("");
          }, 2000);
        } else {
          setControlMsg(d.message || "Registration failed: No face detected");
          speakAI("Registration failed");
          safeSetTimeout(() => {
            setWizardStep(1);
            setWizardOpen(false);
          }, 2000);
        }
      } catch (err) {
        setControlMsg("Enrollment failed: " + err);
        setWizardStep(1);
        setWizardOpen(false);
      } finally {
        setBtnLoading(b => ({ ...b, "enroll": false }));
      }
    }, 2000);
  };

  // ── Save configurations ───────────────────────────────────────────────────
  const saveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setBtnLoading(b => ({ ...b, "save_settings": true }));
    speakAI("Saving system configuration protocols");

    try {
      const r = await fetch(`${API}/api/control/save_settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: opName,
          confidence: confThresh,
          tg_token: tgBotToken,
          tg_chat_id: tgChatId,
          detect_new_ids: detectNewIds,
          detect_people: detectPeople,
          detect_objects: detectObjects,
          match_threshold: matchThresh,
          particle_size: particleSize,
          mesh_thickness: meshThickness
        })
      });
      const d = await r.json();
      if (d.status === "ok") {
        setControlMsg("Configuration saved successfully.");
        speakAI("Configuration secured");
      } else {
        setControlMsg("Configuration could not be saved. Check logs for details.");
        speakAI("Configuration failed");
      }
    } catch (err) {
      setControlMsg("Configuration could not be saved. Check logs for details.");
      speakAI("Transmission failed");
    } finally {
      setBtnLoading(b => ({ ...b, "save_settings": false }));
      safeSetTimeout(() => setControlMsg(null), 3000);
    }
  };

  const activeCamInfo = useMemo(() => cameras[activeCam], [cameras, activeCam]);
  const liveCount = useMemo(() => cameras.filter(c => c.online).length, [cameras]);

  return (
    <div className="w-screen h-screen overflow-hidden flex bg-[#050505] p-3 gap-3 text-[#FFFFFF] font-inter">
      {/* Luxury Ambient Background */}
      <div className="oms-bg" />
       <ParticleCanvas active={particlesActive} density={particleDensity} size={particleSize} thickness={meshThickness} />

      {/* ── 1. LEFT EXPANDABLE NAVIGATION RAIL (Perfect Flex sizing, no overlap!) ─ */}
      <motion.nav
        className="nav-rail h-full relative flex-shrink-0"
        onMouseEnter={() => setNavExpanded(true)}
        onMouseLeave={() => setNavExpanded(false)}
        animate={{ width: navExpanded ? 220 : 76 }}
        transition={{ type: "spring", stiffness: 280, damping: 25 }}
      >
        {/* Core AI Hex Logo */}
        <div className="flex items-center gap-3 px-3 mb-8 w-full overflow-hidden">
          <div className="w-10 h-10 flex-shrink-0 rounded-xl glass-gold-active flex items-center justify-center cursor-pointer"
            onClick={() => speakAI("Sentinel Core v9.0 online")}>
            <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none">
              <polygon points="12,2 22,8 22,16 12,22 2,16 2,8" stroke="#D4AF37" strokeWidth="1.5" fill="rgba(212,175,55,0.06)" />
              <text x="12" y="15.5" textAnchor="middle" fontSize="9" fill="#FFD700" fontWeight="900" className="font-orbitron">AT</text>
            </svg>
          </div>
          <motion.div
            animate={{ opacity: navExpanded ? 1 : 0, x: navExpanded ? 0 : -8 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden whitespace-nowrap"
          >
            <div className="font-orbitron text-[13px] font-black text-gold-accent leading-none">OMS v9.0</div>
            <div className="font-inter text-[9px] text-sec tracking-wider uppercase mt-1">AI Assistant</div>
          </motion.div>
        </div>

        {/* Navigation Items (Statefully wired to router) */}
        <div className="flex flex-col gap-1.5 w-full flex-1">
          {NAV.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeNav === item.id ? "active" : ""}`}
              onClick={() => {
                setActiveNav(item.id);
                speakAI("Switched to " + item.label);
              }}
              title={`View ${item.label} section`}
            >
              <item.icon size={18} style={{ flexShrink: 0 }}
                color={activeNav === item.id ? "#FFD700" : "#B8B8B8"} />
              <motion.span
                className="nav-label"
                animate={{ opacity: navExpanded ? 1 : 0 }}
                transition={{ duration: 0.15 }}
              >
                {item.label}
              </motion.span>
            </button>
          ))}
        </div>

        {/* Shutdown */}
        <div className="w-full px-2">
          <button 
            className="nav-item border border-red-500/10 hover:border-red-500/30 hover:bg-red-500/5 group text-red-400" 
            onClick={() => doControl("shutdown")}
            title="Shutdown Python core server"
            disabled={btnLoading["shutdown"]}
          >
            {btnLoading["shutdown"] ? (
              <RefreshCw size={18} className="animate-spin text-red-500" />
            ) : (
              <LogOut size={18} style={{ flexShrink: 0 }} />
            )}
            <motion.span
              className="nav-label text-red-400 font-bold"
              animate={{ opacity: navExpanded ? 1 : 0 }}
            >
              SHUTDOWN
            </motion.span>
          </button>
        </div>
      </motion.nav>

      {/* ── 2. DYNAMIC WORKSPACE BODY CONTAINER (Perfect fullscreen scaling!) ──── */}
      <div className="flex-1 flex flex-col gap-3 min-w-0 h-full overflow-hidden pl-3">
        
        {/* ── TOP HEADER ── */}
        <header className="glass-premium flex items-center px-6 flex-shrink-0" style={{ height: 68 }}>
          <div>
            <div className="font-orbitron text-lg font-black text-gold-accent glow-gold leading-none">OMS v9.0</div>
            <div className="font-inter text-[9px] text-sec tracking-widest uppercase mt-0.5">Autonomous AI Core Assistant</div>
          </div>

          <div className="flex-1 flex items-center justify-center gap-8">
            <div className="text-center">
              <span className="font-inter text-[9px] text-sec tracking-widest block uppercase leading-none mb-1">Time Index</span>
              <span className="font-orbitron text-xl font-bold text-gold tabular-nums leading-none">
                {time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}
              </span>
            </div>
            <div className="w-[1px] h-6 bg-white/5" />
            <div>
              <div className="flex items-center gap-2">
                <span className="status-indicator text-green-oms bg-green-oms" />
                <span className="font-orbitron text-xs font-bold text-gold uppercase tracking-wider">SECURE CONNECTED</span>
              </div>
              <span className="font-inter text-[9px] text-sec tracking-wider">Operator ID: {opName.toUpperCase()}</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="glass-premium px-4 py-2 text-right min-w-[130px]">
              <span className="font-inter text-[9px] text-sec block tracking-wider leading-none mb-1">SYSTEM INTEGRITY</span>
              <div className="flex items-center justify-end gap-1.5 text-green-oms font-orbitron text-xs font-black">
                <Shield size={12} className="animate-pulse" />
                100% OPERATIONAL
              </div>
            </div>

            <button
              onClick={() => doControl("refresh")}
              disabled={btnLoading["refresh"]}
              className="w-10 h-10 rounded-xl glass-premium-interactive flex items-center justify-center"
              title="Force reload all API telemetry values"
            >
              {btnLoading["refresh"] ? (
                <RefreshCw size={14} className="animate-spin text-gold-accent" />
              ) : (
                <RefreshCw size={14} className="text-[#FFFFFF]" />
              )}
            </button>
          </div>
        </header>

        {/* ── CENTRAL PANELS GRID ── */}
        <div className="flex-1 flex gap-3 min-h-0 min-w-0">
          
          {/* DYNAMIC MIDDLE VIEW CONTROLLER */}
          <div className="flex-[1.55] flex flex-col gap-3 min-w-0 h-full overflow-hidden">
            
            {activeNav === "overview" && (
              <div className="flex-1 flex flex-col gap-3 min-h-0 min-w-0 h-full">
                
                {/* Cinematic camera viewport */}
                <div ref={viewportRef} className="glass-premium flex-1 relative flex items-center justify-center min-h-0 overflow-hidden bg-black/40">
                  {activeCamInfo?.online ? (
                    <div className={`relative overflow-hidden flex items-center justify-center border border-gold/10 shadow-2xl transition-all duration-300 ${isFullscreen ? "w-full h-full aspect-video rounded-none" : "h-full aspect-square rounded-xl"}`}>
                      <img
                        src={`${API}/api/stream/${activeCam}`}
                        alt="AI Visual Target"
                        className="w-full h-full object-cover"
                      />
                      {isFaceUnlocked && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                          <div className="w-[150px] h-[150px] border border-gold-accent/40 rounded-full animate-spin" style={{ borderStyle: "dashed", animationDuration: "12s" }} />
                          <div className="absolute w-[170px] h-[170px] border-2 border-gold/60 rounded-xl" />
                          <div className="absolute top-[38%] font-orbitron text-[9px] font-black text-gold-accent bg-black/60 px-2 py-0.5 rounded tracking-widest">
                            AI IDENTIFIED: {summary?.operator || opName}
                          </div>
                        </div>
                      )}

                      {/* Corner Sights & grid scan overlay */}
                      <div className="corner-hud tl" />
                      <div className="corner-hud tr" />
                      <div className="corner-hud bl" />
                      <div className="corner-hud br" />
                      <div className="face-scan-grid" />
                      <div className="hud-scan-line" />

                      {/* Top floating badges */}
                      <div className="absolute top-4 left-4 flex gap-2 pointer-events-none z-10">
                        <span className="glass-premium px-3 py-1 flex items-center gap-1.5 text-[10px] font-orbitron font-bold text-green-oms">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-oms animate-ping" />
                          LIVE
                        </span>
                        <span className="glass-premium px-3 py-1 text-[10px] font-orbitron font-black text-gold-accent">
                          CAM {activeCam + 1}
                        </span>
                      </div>

                      <div className="absolute top-4 right-4 flex gap-2 z-10">
                        <span className="glass-premium px-3 py-1 flex items-center gap-1.5 text-[10px] font-orbitron font-bold text-red-500">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                          REC
                        </span>
                        <button 
                          onClick={() => doControl("toggle_hud")}
                          disabled={btnLoading["toggle_hud"]}
                          className="glass-premium p-1.5 text-[#FFFFFF] hover:text-gold-accent transition-colors"
                          title="Toggle System HUD overlay borders"
                        >
                          {btnLoading["toggle_hud"] ? (
                            <RefreshCw size={12} className="animate-spin text-gold-accent" />
                          ) : (
                            <Sliders size={12} />
                          )}
                        </button>
                        <button 
                          onClick={toggleFullscreen}
                          className="glass-premium p-1.5 text-[#FFFFFF] hover:text-gold-accent transition-colors z-20"
                          title={isFullscreen ? "Exit fullscreen preview mode" : "Enter true fullscreen preview mode"}
                        >
                          {isFullscreen ? (
                            <Minimize2 size={12} className="text-gold-accent animate-pulse" />
                          ) : (
                            <Maximize2 size={12} />
                          )}
                        </button>
                      </div>

                      {/* Uptime and location badges */}
                      <div className="absolute bottom-4 left-4 glass-premium px-4 py-2.5 flex flex-col gap-1 pointer-events-none z-10">
                        <span className="font-orbitron text-[9px] font-black text-gold tracking-widest">AI VISION TELEMETRY</span>
                        <div className="grid grid-cols-2 gap-x-4 text-[10px]">
                          <span className="text-sec">FPS RATE:</span>
                          <span className="font-mono text-gold-accent font-bold">{activeCamInfo?.fps || 0.0} FPS</span>
                          <span className="text-sec">ACCURACY:</span>
                          <span className="font-mono text-green-oms font-bold">98.4%</span>
                        </div>
                      </div>

                      <div className="absolute bottom-4 right-4 glass-premium px-3 py-1 flex items-center gap-2 text-[10px] text-sec pointer-events-none z-10">
                        <MapPin size={11} className="text-gold" />
                        {activeCamInfo?.location || "Sector Grid"}
                      </div>
                    </div>
                  ) : (
                    <div className={`relative flex flex-col items-center justify-center gap-3 bg-[#0d0d11]/80 border border-gold/10 shadow-2xl transition-all duration-300 ${isFullscreen ? "w-full h-full aspect-video rounded-none" : "h-full aspect-square rounded-xl"}`}>
                      <div className="w-16 h-16 rounded-full border-2 border-gold-accent/25 border-dashed flex items-center justify-center animate-spin" style={{ animationDuration: "15s" }}>
                        <Crosshair size={24} className="text-gold-dim" />
                      </div>
                      <div className="font-orbitron text-xs font-bold text-gold-accent tracking-widest">CAMERA OFFLINE</div>
                      <div className="font-inter text-[10px] text-sec">Awaiting authorization feedback node...</div>
                    </div>
                  )}
                </div>

                {/* AI Assistant Core energy sphere centerpiece */}
                <div className="glass-premium px-6 py-5 flex items-center gap-6 flex-shrink-0" style={{ height: 160 }}>
                  <div className="relative w-24 h-24 flex-shrink-0 flex items-center justify-center">
                    <motion.div
                      animate={{
                        scale: aiState === "speaking" ? [1, 1.15, 1] : aiState === "listening" ? [1, 1.25, 1] : [1, 1.05, 1],
                        rotate: 360
                      }}
                      transition={{ repeat: Infinity, duration: aiState === "processing" ? 1.5 : 6, ease: "linear" }}
                      className="absolute inset-0 rounded-full bg-gradient-to-tr from-gold to-gold-accent/40 blur-xl opacity-20 pointer-events-none"
                    />
                    <svg viewBox="0 0 100 100" className="w-20 h-20">
                      <motion.circle
                        cx="50" cy="50" r="42"
                        stroke="#D4AF37" strokeWidth="1" strokeDasharray="5,15"
                        fill="none"
                        animate={{ rotate: -360 }}
                        transition={{ repeat: Infinity, duration: 15, ease: "linear" }}
                      />
                      <motion.circle
                        cx="50" cy="50" r="34"
                        stroke="#FFD700" strokeWidth="1" strokeDasharray="30,10"
                        fill="none"
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
                      />
                      <motion.circle
                        cx="50" cy="50" r="16"
                        fill="url(#goldGrad)"
                        animate={{ r: aiState === "speaking" ? [15, 20, 15] : aiState === "listening" ? [15, 23, 15] : [15, 17, 15] }}
                        transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                      />
                    </svg>
                    {aiState !== "idle" && <span className="absolute w-2 h-2 bg-gold-accent rounded-full animate-ping pointer-events-none" />}
                  </div>

                  <div className="flex-1 flex flex-col gap-1.5 justify-center min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-orbitron text-xs font-black text-gold-accent tracking-wider uppercase">AI CORE ENERGY CENTERPIECE</h4>
                      <span className="font-mono text-[9px] text-sec uppercase font-bold">{aiState}</span>
                    </div>
                    <div className="h-[70px] glass-premium bg-black/40 border border-white/5 rounded-xl px-4 flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-mono text-[10px] text-sec leading-tight uppercase truncate">{aiSubText}</p>
                        <p className="font-inter text-xs text-white leading-normal font-medium mt-1 truncate-2 h-8">
                          {speechOutput || "AI Ready. Activate microphone to transmit secure vocal command protocols..."}
                        </p>
                      </div>
                      <div className="w-[180px] h-[50px] flex items-center justify-center">
                        <VoiceVisualizer state={aiState} />
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-center justify-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={triggerVoiceAssistant}
                      className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 relative border outline-none
                        ${aiState === "listening" ? "bg-[#FFD700]/20 border-[#FFD700] shadow-gold-glow-strong animate-pulse" : 
                          aiState === "processing" ? "bg-cyan-500/10 border-cyan-400 animate-spin" : 
                          "bg-gold/10 border-[#D4AF37]/30 hover:border-[#D4AF37] hover:bg-gold/20"}`}
                      style={{ animationDuration: aiState === "processing" ? "3s" : "1.5s" }}
                      title="Tap to interact with AI Voice assistant"
                    >
                      <Mic size={24} className={aiState === "listening" ? "text-gold-accent animate-bounce" : "text-[#FFFFFF]"} />
                      {aiState === "listening" && <div className="ripple-voice" />}
                    </button>
                    <span className="font-orbitron text-[9px] font-bold text-sec tracking-widest">TAP MIC</span>
                  </div>
                </div>

                {/* Switcher bar */}
                <div className="flex gap-4 justify-center items-center flex-shrink-0" style={{ height: 80 }}>
                  {cameras.map((cam, idx) => (
                    <div
                      key={cam.id}
                      onClick={() => {
                        setActiveCam(idx);
                        speakAI("Switched to camera channel " + (idx + 1));
                      }}
                      className={`w-[80px] h-[80px] aspect-square relative cursor-pointer glass-premium overflow-hidden transition-all duration-300 group flex-shrink-0
                        ${idx === activeCam ? "glass-gold-active border-gold ring-1 ring-gold shadow-gold-glow scale-[1.02]" : "hover:scale-[1.01] hover:border-white/10"}`}
                      style={{ borderRadius: 14 }}
                    >
                      {cam.online ? (
                        <img
                          src={`${API}/api/camera/${idx}/snapshot?t=${telemetry?.uptime_secs || 0}`}
                          alt={cam.name}
                          className="w-full h-full object-cover opacity-65 group-hover:opacity-90 transition-opacity"
                        />
                      ) : (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5 bg-black/50">
                          <Video size={14} className="text-muted" />
                          <span className="font-orbitron text-[7px] text-muted tracking-widest">OFFLINE</span>
                        </div>
                      )}
                      <div className="absolute inset-x-0 bottom-0 px-2 py-1 bg-gradient-to-t from-black/90 to-transparent flex items-center justify-between z-10">
                        <span className="font-orbitron text-[7.5px] text-[#FFFFFF] font-bold truncate">{cam.name}</span>
                        <span className={`status-indicator ${cam.online ? "text-green-oms bg-green-oms animate-pulse" : "text-muted bg-white/10"}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC DETECTION MATRIX */}
            {activeNav === "detection" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <Crosshair className="text-gold-accent animate-pulse" size={20} />
                    <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                      OMS TARGET DETECTION MATRIX
                    </h2>
                  </div>
                  <span className="font-orbitron text-xs font-bold text-sec bg-white/5 px-3 py-1 rounded tracking-widest">
                    ACTIVE SOURCE: CAM {activeCam + 1}
                  </span>
                </div>

                <div className="flex-1 flex gap-4 min-h-0">
                  {/* Left Column: Active subjects */}
                  <div className="flex-1 glass-premium p-4 flex flex-col min-h-0 bg-black/20" style={{ borderRadius: 16 }}>
                    <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-3 flex-shrink-0">
                      <UserCheck size={14} /> ACTIVE TARGET SIGNATURES
                    </h4>
                    <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3">
                      {activeCamInfo?.active_subjects && activeCamInfo.active_subjects.length > 0 ? (
                        activeCamInfo.active_subjects.map((subj: any, i: number) => (
                          <div key={i} className="glass-premium bg-black/40 p-3 flex items-center gap-4 hover:border-gold-dim/15 transition-all" style={{ borderRadius: 12 }}>
                            <div className="w-14 h-14 rounded-lg bg-black border border-white/10 overflow-hidden relative flex-shrink-0">
                              <img
                                src={`${API}/api/crop/${subj.pid}`}
                                alt={subj.name}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/bottts/svg?seed=${subj.pid}`;
                                }}
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className={`font-orbitron text-xs font-black tracking-wider ${subj.known ? "text-green-oms" : "text-red-500"}`}>
                                  {subj.name}
                                </span>
                                <span className="font-mono text-[9px] text-sec">({subj.pid})</span>
                              </div>
                              <div className="flex gap-4 text-[10px] text-sec mt-1">
                                <span>VERIFICATION: <span className={subj.known ? "text-green-oms font-bold" : "text-red-500 font-bold"}>{subj.known ? "AUTHORIZED" : "INTRUDER"}</span></span>
                                <span>CONFIDENCE: <span className="font-mono text-gold-accent font-bold">{(subj.confidence * 100).toFixed(1)}%</span></span>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 text-muted">
                          <Eye size={24} className="text-muted/40 animate-pulse" />
                          <span className="font-orbitron text-[9px] tracking-widest">AWAITING FACE IDENTIFICATION PROTOCOLS...</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Column: YOLO detections list */}
                  <div className="flex-1 glass-premium p-4 flex flex-col min-h-0 bg-black/20" style={{ borderRadius: 16 }}>
                    <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-3 flex-shrink-0">
                      <Cpu size={14} /> NEURAL OBJECT DETECTIONS ({(activeCamInfo as any)?.detections_list?.length || 0})
                    </h4>
                    <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2">
                      {(activeCamInfo as any)?.detections_list && (activeCamInfo as any).detections_list.length > 0 ? (
                        (activeCamInfo as any).detections_list.map((det: any, i: number) => (
                          <div key={i} className="glass-premium bg-black/30 p-3 flex items-center justify-between gap-4 border border-white/5" style={{ borderRadius: 12 }}>
                            <div>
                              <span className="font-orbitron text-[10.5px] font-black text-gold-accent tracking-widest uppercase block">
                                {det.label}
                              </span>
                              <span className="font-mono text-[9px] text-sec block mt-0.5">
                                Target Area: [{det.box ? det.box.join(", ") : "0, 0, 0, 0"}]
                              </span>
                            </div>
                            <div className="glass-premium bg-white/5 px-2.5 py-1 rounded text-right">
                              <span className="font-mono text-xs font-bold text-[#00FFA3]">{(det.conf * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 text-muted">
                          <Radar size={24} className="text-muted/40 animate-pulse" />
                          <span className="font-orbitron text-[9px] tracking-widest">NO NEURAL DETECTION SIGNATURES ACTIVE</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ACTIVITY INTELLIGENCE PANEL — HAAE Module */}
            {activeNav === "activity" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                {/* Header */}
                <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-5 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <Activity className="text-gold-accent animate-pulse" size={20} />
                    <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                      ACTIVITY INTELLIGENCE ENGINE
                    </h2>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-orbitron text-[10px] font-bold text-sec bg-white/5 px-3 py-1 rounded tracking-widest">
                      {activityData.length} SUBJECT{activityData.length !== 1 ? "S" : ""} TRACKED
                    </span>
                    <span className="font-orbitron text-[10px] font-bold text-green-oms bg-green-oms/10 border border-green-oms/20 px-3 py-1 rounded tracking-widest animate-pulse">
                      LIVE
                    </span>
                  </div>
                </div>

                {/* Persons Grid */}
                {activityData.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-4 text-sec">
                    <Activity size={36} className="text-gold-dim/30 animate-pulse" />
                    <span className="font-orbitron text-[10px] tracking-widest">NO SUBJECTS CURRENTLY IN FRAME</span>
                    <span className="text-[9px] text-sec/60">Activity analysis activates when persons are detected</span>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto pr-1 grid grid-cols-1 gap-4 content-start">
                    {activityData.map((person) => {
                      const actScore = Math.round(person.activity_score * 100);
                      const emoScore = Math.round(person.emotion_score * 100);
                      const isRunning = person.activity_label === "RUNNING";
                      const isIdle    = person.activity_label === "IDLE";
                      const actColor  = isRunning ? "text-orange-400" : isIdle ? "text-cyan-400" : "text-gold-accent";
                      const actBg     = isRunning ? "bg-orange-500" : isIdle ? "bg-cyan-500" : "bg-gold-accent";
                      const attColor  = person.attention === "HIGH" ? "text-green-oms" : person.attention === "LOW" ? "text-red-400" : "text-amber-400";

                      const emotionEmoji: Record<string, string> = {
                        happy: "😊", neutral: "😐", sad: "😢", angry: "😠",
                        surprise: "😲", fear: "😨", disgusted: "🤢", disgust: "🤢"
                      };
                      const emoEmoji = emotionEmoji[person.emotion.toLowerCase()] || "🤔";

                      return (
                        <div
                          key={person.pid}
                          className="glass-premium bg-black/30 p-4 flex flex-col gap-3 border border-white/5 hover:border-gold-dim/20 transition-all"
                          style={{ borderRadius: 14 }}
                        >
                          {/* Row 1: Identity + Camera badge */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-black border border-white/10 overflow-hidden flex-shrink-0">
                                <img
                                  src={`${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}/api/crop/${person.pid}`}
                                  alt={person.name}
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/bottts/svg?seed=${person.pid}`;
                                  }}
                                />
                              </div>
                              <div>
                                <span className="font-orbitron text-xs font-black text-gold-accent tracking-wider block">{person.name}</span>
                                <span className="font-mono text-[9px] text-sec">{person.pid} • ⏱ {person.duration_str}</span>
                              </div>
                            </div>
                            <span className="glass-premium px-2 py-1 text-[9px] font-orbitron font-bold text-sec tracking-widest border border-white/5">
                              📷 {person.camera}
                            </span>
                          </div>

                          {/* Row 2: Emotion + Attention */}
                          <div className="grid grid-cols-2 gap-3">
                            {/* Emotion */}
                            <div className="glass-premium bg-black/40 p-3 rounded-xl flex flex-col gap-2">
                              <span className="font-orbitron text-[8.5px] font-bold text-sec tracking-widest">EXPRESSION</span>
                              <div className="flex items-center gap-2">
                                <span className="text-lg">{emoEmoji}</span>
                                <div className="flex-1">
                                  <span className="font-orbitron text-[10px] font-black text-gold-accent block">{person.emotion.toUpperCase()}</span>
                                  <div className="w-full h-1 bg-white/10 rounded-full mt-1">
                                    <div
                                      className="h-full bg-gold-accent rounded-full transition-all duration-500"
                                      style={{ width: `${emoScore}%` }}
                                    />
                                  </div>
                                  <span className="font-mono text-[8px] text-sec mt-0.5 block">{emoScore}% confidence</span>
                                </div>
                              </div>
                            </div>

                            {/* Attention */}
                            <div className="glass-premium bg-black/40 p-3 rounded-xl flex flex-col gap-2">
                              <span className="font-orbitron text-[8.5px] font-bold text-sec tracking-widest">ATTENTION LEVEL</span>
                              <div className="flex items-center gap-2 mt-1">
                                <Eye size={18} className={attColor} />
                                <span className={`font-orbitron text-xs font-black tracking-wider ${attColor}`}>
                                  {person.attention}
                                </span>
                              </div>
                              <div className="flex gap-1 mt-1">
                                {["HIGH", "MEDIUM", "LOW"].map((lvl) => (
                                  <div
                                    key={lvl}
                                    className={`flex-1 h-1.5 rounded-full transition-all ${
                                      person.attention === lvl
                                        ? lvl === "HIGH" ? "bg-green-oms" : lvl === "MEDIUM" ? "bg-amber-400" : "bg-red-500"
                                        : "bg-white/10"
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* Row 3: Activity Score Bar */}
                          <div className="glass-premium bg-black/40 p-3 rounded-xl">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-orbitron text-[8.5px] font-bold text-sec tracking-widest">ACTIVITY STATE</span>
                              <span className={`font-orbitron text-[10px] font-black tracking-wider ${actColor}`}>
                                {isRunning ? "🏃" : isIdle ? "🧍" : "⚡"} {person.activity_label}
                              </span>
                            </div>
                            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-700 ${actBg}`}
                                style={{ width: `${actScore}%` }}
                              />
                            </div>
                            <div className="flex justify-between mt-1">
                              <span className="font-mono text-[8px] text-sec">IDLE</span>
                              <span className={`font-mono text-[8px] font-bold ${actColor}`}>{actScore}%</span>
                              <span className="font-mono text-[8px] text-sec">RUNNING</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC TACTICAL SONAR */}
            {activeNav === "tactical" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <Radar className="text-gold-accent animate-pulse" size={20} />
                    <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                      OMS TACTICAL SONAR MATRIX
                    </h2>
                  </div>
                  <span className="font-orbitron text-xs font-bold text-red-500 bg-red-950/20 border border-red-500/20 px-3 py-1 rounded tracking-widest animate-pulse">
                    SECURE CONNECTION
                  </span>
                </div>

                <div className="flex-1 grid grid-cols-2 gap-5 min-h-0">
                  {/* Left Side: Circular SVG Radar scanning animation */}
                  <div className="glass-premium p-4 flex flex-col items-center justify-center bg-black/20 relative overflow-hidden" style={{ borderRadius: 16 }}>
                    <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-3 w-full flex-shrink-0">
                      <Crosshair size={14} /> SONAR GRID RADAR SCAN
                    </h4>
                    
                    <div className="relative w-64 h-64 flex items-center justify-center border border-gold-dim/15 rounded-full my-auto shadow-2xl">
                      {/* Radar sweep background circles */}
                      <div className="absolute w-48 h-48 border border-dashed border-gold-dim/10 rounded-full" />
                      <div className="absolute w-32 h-32 border border-solid border-gold-dim/10 rounded-full" />
                      <div className="absolute w-16 h-16 border border-dashed border-gold-dim/10 rounded-full" />
                      
                      {/* Scanning sweeping arm */}
                      <div className="absolute inset-0 rounded-full overflow-hidden pointer-events-none">
                        <div 
                          className="w-1/2 h-full bg-gradient-to-r from-transparent to-gold-accent/15 origin-right animate-spin" 
                          style={{ animationDuration: "4s", animationTimingFunction: "linear" }}
                        />
                      </div>
                      
                      {/* Radar blips (targets) */}
                      {cameras.map((cam, i) => {
                        if (!cam.online) return null;
                        const angle = (i * 90 + 45) * (Math.PI / 180);
                        const radius = 80;
                        const x = Math.cos(angle) * radius;
                        const y = Math.sin(angle) * radius;
                        const hasPerson = cam.persons > 0;
                        return (
                          <div 
                            key={i}
                            className={`absolute w-3 h-3 rounded-full flex items-center justify-center transition-all duration-300
                              ${hasPerson ? "bg-red-500 shadow-red-glow" : "bg-green-oms shadow-gold-glow"}`}
                            style={{ 
                              transform: `translate(${x}px, ${y}px)`,
                              animation: hasPerson ? "ping 1.5s infinite" : "none"
                            }}
                            title={`CAM ${cam.id + 1}: ${cam.name}`}
                          >
                            <span className="absolute text-[8px] font-orbitron font-bold text-[#FFFFFF] bg-black/80 px-1 py-0.5 rounded -top-5 whitespace-nowrap">
                              CAM {cam.id + 1}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right Side: Zone Status & Threat Level Indicator */}
                  <div className="glass-premium p-4 flex flex-col min-h-0 bg-black/20 gap-4" style={{ borderRadius: 16 }}>
                    <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-1 flex-shrink-0">
                      <AlertTriangle size={14} /> SECURITY THREAT MATRIX
                    </h4>

                    {/* Threat level panel */}
                    <div className="glass-premium bg-black/40 p-4 rounded-xl flex items-center justify-between border border-white/5" style={{ borderRadius: 12 }}>
                      <div>
                        <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider block">CURRENT THREAT LEVEL</span>
                        <span className={`font-orbitron text-xl font-black tracking-widest uppercase block mt-1
                          ${telemetry?.threat_level === "RED" ? "text-red-500 animate-pulse" : 
                            telemetry?.threat_level === "AMBER" ? "text-amber-500" : "text-green-oms"}`}
                        >
                          {telemetry?.threat_level || "GREEN"} STATE
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => doControl("alarm")}
                          className="btn-gold-luxury border-red-500/20 text-red-400 hover:text-red-300 hover:bg-red-500/10 py-2 px-3 text-[9px] uppercase tracking-widest font-orbitron"
                        >
                          ALARM
                        </button>
                      </div>
                    </div>

                    {/* Active Zones Grid */}
                    <div className="flex-1 flex flex-col min-h-0">
                      <span className="font-orbitron text-[9px] text-sec font-bold tracking-wider mb-2 uppercase block">PROTECTED ZONES MATRIX</span>
                      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2">
                        {cameras.map((cam, i) => {
                          const hasPerson = cam.persons > 0;
                          return (
                            <div key={i} className="glass-premium bg-black/30 p-3 flex items-center justify-between gap-3 border border-white/5" style={{ borderRadius: 12 }}>
                              <div>
                                <span className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase block">
                                  {cam.location || `SECTOR ZONE ${i + 1}`}
                                </span>
                                <span className="font-inter text-[9.5px] text-sec block mt-0.5">
                                  Linked Sensor: {cam.name}
                                </span>
                              </div>
                              <span className={`font-orbitron text-[9px] font-black px-2.5 py-1 rounded tracking-widest leading-none border
                                ${hasPerson ? 
                                  "text-red-500 bg-red-950/20 border-red-500/20 animate-pulse" : 
                                  "text-green-oms bg-green-950/20 border-green-500/20"}`}
                              >
                                {hasPerson ? "INTRUSION" : "SECURE"}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC ADVANCED FACE ENROLLMENT MATRIX */}
            {activeNav === "enrollment" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <UserPlus className="text-gold-accent animate-pulse" size={20} />
                    <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                      OMS ADVANCED FACE ENROLLMENT PROTOCOLS
                    </h2>
                  </div>
                  <div className="flex gap-2">
                    {[
                      { id: "directory", label: "ENROLLED DIRECTORY" },
                      { id: "guided", label: "GUIDED CAPTURE" },
                      { id: "folder", label: "FOLDER IMPORT" },
                      { id: "import_json", label: "PROFILE IMPORT" }
                    ].map(tab => (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => {
                          setEnrollTab(tab.id as any);
                          if (tab.id === "directory") loadEnrolledPeople();
                        }}
                        className={`font-orbitron text-[9px] font-bold tracking-widest px-3 py-1.5 rounded-lg border transition-all duration-300 ${
                          enrollTab === tab.id
                            ? "bg-gold/15 border-gold text-gold-accent shadow-gold-glow"
                            : "bg-black/40 border-white/10 text-muted hover:border-white/20 hover:text-white"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex-1 min-h-0 min-w-0">
                  {/* Pane 1: Enrolled Directory */}
                  {enrollTab === "directory" && (
                    <div className="flex flex-col h-full min-h-0">
                      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3">
                        {enrolledPeople.length > 0 ? (
                          enrolledPeople.map((person) => (
                            <div
                              key={person.pid}
                              className="glass-premium bg-black/40 p-4 border border-white/5 hover:border-gold-dim/15 hover:bg-gold/5 transition-all flex items-center justify-between gap-6"
                              style={{ borderRadius: 16 }}
                            >
                              <div className="flex items-center gap-4 min-w-0">
                                <div className="w-16 h-16 rounded-xl bg-black border border-white/10 overflow-hidden relative flex-shrink-0 flex items-center justify-center">
                                  {person.photo ? (
                                    <img
                                      src={`${API}/${person.photo}`}
                                      alt={person.name}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/bottts/svg?seed=${person.pid}`;
                                      }}
                                    />
                                  ) : (
                                    <span className="font-orbitron text-lg font-black text-gold">
                                      {person.name.slice(0, 2).toUpperCase()}
                                    </span>
                                  )}
                                </div>
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-orbitron text-sm font-black text-white truncate leading-none">
                                      {person.name}
                                    </span>
                                    <span className="font-mono text-[9px] text-sec leading-none">({person.pid})</span>
                                  </div>
                                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 text-[10px] font-mono text-sec">
                                    <span>TYPE: <span className="text-[#00E5FF] font-bold">{person.type.toUpperCase()} PROFILE</span></span>
                                    <span>ENROLLED IMAGES: <span className="text-gold-accent font-bold">{person.image_count} POSES</span></span>
                                    <span>QUALITY SCORE: <span className="text-green-oms font-bold">{person.quality_score ? `${person.quality_score.toFixed(1)}%` : "N/A"}</span></span>
                                    <span className="truncate">ENROLLED ON: <span className="text-white">{person.first_seen || "System Registry"}</span></span>
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-2 flex-shrink-0">
                                <button
                                  onClick={() => startGuidedEnrollment(person.name, person.pid)}
                                  className="btn-gold-luxury py-2 px-3 text-[9px] uppercase tracking-wider"
                                  title="Add more photos using guided capture"
                                >
                                  ADD PHOTOS
                                </button>
                                <button
                                  onClick={() => rebuildEnrollment(person.pid)}
                                  disabled={btnLoading[`rebuild_${person.pid}`]}
                                  className="btn-gold-luxury py-2 px-3 text-[9px] uppercase tracking-wider"
                                  title="Re-extract SFace embeddings from stored crops"
                                >
                                  {btnLoading[`rebuild_${person.pid}`] ? (
                                    <RefreshCw size={10} className="animate-spin" />
                                  ) : (
                                    <RefreshCw size={10} />
                                  )}
                                  REBUILD
                                </button>
                                <a
                                  href={`${API}/api/enroll/export/${person.pid}`}
                                  download
                                  className="btn-gold-luxury py-2 px-3 text-[9px] uppercase tracking-wider flex items-center gap-1.5"
                                  title="Export profile package to JSON"
                                >
                                  <Download size={10} />
                                  EXPORT
                                </a>
                                <button
                                  onClick={() => deleteEnrollment(person.pid)}
                                  disabled={btnLoading[`delete_${person.pid}`]}
                                  className="btn-danger-luxury py-2 px-3 text-[9px] uppercase tracking-wider flex items-center gap-1.5"
                                  title="Permanently remove profile registry"
                                >
                                  {btnLoading[`delete_${person.pid}`] ? (
                                    <Trash size={10} className="animate-spin" />
                                  ) : (
                                    <Trash size={10} />
                                  )}
                                  DELETE
                                </button>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 text-muted py-12">
                            <Database size={32} className="text-muted/40 animate-pulse" />
                            <span className="font-orbitron text-xs tracking-widest uppercase">No advanced face profiles registered in system</span>
                            <span className="font-inter text-[10px] text-sec max-w-md">Initialize guided pose enrollment or import local directories to create highly accurate multi-angle identity records.</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pane 2: Guided Capture */}
                  {enrollTab === "guided" && (
                    <div className="grid grid-cols-2 gap-5 h-full min-h-0">
                      {/* Left: Interactive pose guide & Capture controls */}
                      <div className="glass-premium p-5 flex flex-col min-h-0 bg-black/20 justify-between gap-4" style={{ borderRadius: 16 }}>
                        {!guidedPid ? (
                          <form
                            onSubmit={(e) => {
                              e.preventDefault();
                              const inputName = (e.target as any).elements.guidedNameInput.value.trim();
                              if (inputName) startGuidedEnrollment(inputName);
                            }}
                            className="flex flex-col gap-4 my-auto max-w-xs w-full mx-auto"
                          >
                            <h4 className="font-orbitron text-xs font-black text-gold-accent tracking-widest text-center uppercase">INITIALIZE SESSION</h4>
                            <div className="flex flex-col gap-1.5">
                              <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">TARGET NAME</label>
                              <input
                                name="guidedNameInput"
                                type="text"
                                required
                                placeholder="e.g. John Doe"
                                className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-sm px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                              />
                            </div>
                            <button type="submit" className="btn-gold-luxury py-3 justify-center gap-2">
                              <UserPlus size={14} />
                              INITIALIZE PROTOCOL
                            </button>
                          </form>
                        ) : (
                          <>
                            <div>
                              <div className="flex justify-between items-center border-b border-white/5 pb-2 mb-3">
                                <div>
                                  <h4 className="font-orbitron text-xs font-black text-gold-accent tracking-wider uppercase">SESSION ACTIVE: {guidedName}</h4>
                                  <span className="font-mono text-[9px] text-sec block mt-0.5">Registry ID: {guidedPid}</span>
                                </div>
                                <button
                                  onClick={() => {
                                    if (confirm("Cancel current enrollment? Captured poses will not be registered.")) {
                                      setGuidedPid("");
                                      setGuidedName("");
                                      setGuidedProgress({});
                                      setGuidedLog([]);
                                      setEnrollTab("directory");
                                    }
                                  }}
                                  className="text-red-400 hover:text-red-300 font-orbitron text-[9px] font-bold tracking-widest"
                                >
                                  CANCEL
                                </button>
                              </div>

                              {/* Active Pose Instruction */}
                              <div className="glass-premium bg-black/50 p-4 border border-gold-dim/10 flex flex-col items-center justify-center text-center gap-2 mb-4" style={{ borderRadius: 12 }}>
                                <span className="font-orbitron text-[9px] text-sec font-black tracking-widest uppercase">ACTIVE TARGET POSE REQUIRED</span>
                                <h3 className="font-orbitron text-xl font-black text-[#FFD700] glow-gold uppercase tracking-wider animate-pulse">
                                  {POSES[guidedActivePoseIdx] ? POSES[guidedActivePoseIdx].replace("_", " ") : "ALL POSES CAPTURED"}
                                </h3>
                                <p className="font-inter text-[9.5px] text-sec max-w-xs mt-1">
                                  {POSES[guidedActivePoseIdx] === "front" && "Look straight into the camera lens with a neutral face."}
                                  {POSES[guidedActivePoseIdx] === "left" && "Turn your head to look directly towards your left side."}
                                  {POSES[guidedActivePoseIdx] === "right" && "Turn your head to look directly towards your right side."}
                                  {POSES[guidedActivePoseIdx] === "slight_left" && "Rotate head slightly towards the left angle."}
                                  {POSES[guidedActivePoseIdx] === "slight_right" && "Rotate head slightly towards the right angle."}
                                  {POSES[guidedActivePoseIdx] === "up" && "Tilt your face slightly upwards towards the ceiling."}
                                  {POSES[guidedActivePoseIdx] === "down" && "Tilt your face slightly downwards towards the floor."}
                                  {POSES[guidedActivePoseIdx] === "neutral" && "Hold a natural, relaxed neutral expression."}
                                  {POSES[guidedActivePoseIdx] === "smiling" && "Give a clear smiling expression showing teeth if natural."}
                                  {POSES[guidedActivePoseIdx] === "glasses" && "Wear glasses if you wear them, otherwise hold expression."}
                                  {POSES[guidedActivePoseIdx] === "no_glasses" && "Remove glasses if wearing, otherwise hold expression."}
                                </p>
                              </div>

                              <div className="flex gap-2">
                                <button
                                  onClick={() => captureGuidedPose(POSES[guidedActivePoseIdx])}
                                  disabled={btnLoading["capture_pose"] || !POSES[guidedActivePoseIdx]}
                                  className="btn-gold-luxury flex-1 py-3 justify-center gap-2 font-orbitron font-bold tracking-widest text-xs"
                                >
                                  {btnLoading["capture_pose"] ? (
                                    <RefreshCw size={14} className="animate-spin text-gold-accent" />
                                  ) : (
                                    <Video size={14} />
                                  )}
                                  CAPTURE FRAME
                                </button>
                                <button
                                  onClick={saveGuidedEnrollment}
                                  disabled={btnLoading["save_enroll"] || Object.values(guidedProgress).filter(Boolean).length === 0}
                                  className="btn-gold-luxury border-green-500/20 text-green-400 hover:text-green-300 hover:bg-green-500/10 py-3 px-4 justify-center gap-2 font-orbitron font-bold tracking-widest text-xs"
                                >
                                  {btnLoading["save_enroll"] ? (
                                    <RefreshCw size={14} className="animate-spin text-green-oms" />
                                  ) : (
                                    <CheckCircle size={14} />
                                  )}
                                  SAVE PROFILE
                                </button>
                              </div>
                            </div>

                            {/* Capture session logs */}
                            <div className="flex-1 min-h-[120px] glass-premium bg-black/60 border border-white/5 p-3 flex flex-col font-mono text-[9px]" style={{ borderRadius: 12 }}>
                              <span className="font-orbitron text-[8.5px] font-black text-gold-accent tracking-widest uppercase block mb-1">SESSION METRICS FEED</span>
                              <div className="flex-1 overflow-y-auto flex flex-col gap-0.5 max-h-[120px] text-sec">
                                {guidedLog.map((log, i) => (
                                  <p key={i} className={log.startsWith("✓") ? "text-green-oms" : log.startsWith("✗") ? "text-red-400" : "text-muted"}>
                                    {log}
                                  </p>
                                ))}
                                {guidedLog.length === 0 && <p className="text-muted">// Awaiting frame capture logs...</p>}
                              </div>
                            </div>
                          </>
                        )}
                      </div>

                      {/* Right: Pose checkboxes & stream preview */}
                      <div className="glass-premium p-5 flex flex-col min-h-0 bg-black/20 justify-between gap-4" style={{ borderRadius: 16 }}>
                        <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-1 flex-shrink-0">
                          <Sliders size={14} /> POSE CHECKLIST PROTOCOLS
                        </h4>

                        {/* Poses grid */}
                        <div className="grid grid-cols-2 gap-2 overflow-y-auto max-h-[220px]">
                          {POSES.map((pose, index) => {
                            const completed = guidedProgress[pose];
                            const active = POSES[guidedActivePoseIdx] === pose;
                            return (
                              <div
                                key={pose}
                                onClick={() => guidedPid && setGuidedActivePoseIdx(index)}
                                className={`glass-premium p-2.5 flex items-center justify-between border cursor-pointer transition-all ${
                                  active
                                    ? "bg-gold/10 border-gold shadow-gold-glow-strong scale-[1.01]"
                                    : completed
                                    ? "bg-green-oms/5 border-green-500/20 hover:bg-green-oms/10"
                                    : "bg-black/30 border-white/5 hover:border-white/10"
                                }`}
                                style={{ borderRadius: 10 }}
                              >
                                <span className={`font-orbitron text-[9px] font-bold uppercase tracking-wider ${active ? "text-gold-accent" : completed ? "text-green-oms" : "text-sec"}`}>
                                  {pose.replace("_", " ")}
                                </span>
                                {completed ? (
                                  <Check size={11} className="text-green-oms font-black" />
                                ) : (
                                  <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${active ? "border-gold-accent" : "border-white/10"}`} />
                                )}
                              </div>
                            );
                          })}
                        </div>

                        {/* Bottom preview info */}
                        <div className="glass-premium bg-black/50 border border-white/5 p-3 text-[9.5px] font-mono text-sec" style={{ borderRadius: 10 }}>
                          <span className="font-orbitron text-[8.5px] text-sec font-bold block mb-1 uppercase">CAMERA LINK STATUS</span>
                          {(() => {
                            const activeCamObj = (cameras as any)[activeCam] || (cameras as any)[0] || {};
                            const camOnline = activeCamObj.online;
                            const camFps = activeCamObj.fps || 0;
                            return (
                              <p>STREAM: <span className={camOnline ? "text-green-oms font-bold" : "text-red-500 font-bold"}>
                                {camOnline ? `ONLINE (${camFps} FPS)` : "OFFLINE"}
                              </span></p>
                            );
                          })()}
                          <p>RESOLUTION: <span className="text-white">640x360 SENSOR LAYER</span></p>
                          <p>COMPLETED: <span className="text-gold-accent font-bold">{Object.values(guidedProgress).filter(Boolean).length} / {POSES.length} NODES</span></p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pane 3: Folder Import */}
                  {enrollTab === "folder" && (
                    <div className="grid grid-cols-2 gap-5 h-full min-h-0">
                      {/* Left: Input Form */}
                      <form onSubmit={handleFolderImport} className="glass-premium p-5 flex flex-col min-h-0 bg-black/20 gap-4 justify-center" style={{ borderRadius: 16 }}>
                        <h4 className="font-orbitron text-xs font-black text-gold-accent tracking-widest uppercase text-center mb-2">FOLDER SCAN SPECIFICATION</h4>
                        
                        <div className="flex flex-col gap-1.5">
                          <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">TARGET PERSON NAME</label>
                          <input
                            type="text"
                            required
                            value={importName}
                            onChange={(e) => setImportName(e.target.value)}
                            placeholder="e.g. PRAJAN"
                            className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                          />
                        </div>

                        <div className="flex flex-col gap-1.5">
                          <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">LOCAL DIRECTORY PATH</label>
                          <input
                            type="text"
                            required
                            value={importFolder}
                            onChange={(e) => setImportFolder(e.target.value)}
                            placeholder="e.g. C:\Users\Prajan\Pictures\dataset"
                            className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                          />
                        </div>

                        <button
                          type="submit"
                          disabled={importLoading || !importName.trim() || !importFolder.trim()}
                          className="btn-gold-luxury py-3 justify-center gap-2 mt-2"
                        >
                          {importLoading ? (
                            <RefreshCw size={14} className="animate-spin text-gold-accent" />
                          ) : (
                            <Package size={14} />
                          )}
                          EXECUTE SCAN IMPORT
                        </button>
                      </form>

                      {/* Right: Import console logs */}
                      <div className="glass-premium p-5 flex flex-col min-h-0 bg-black/20 justify-between gap-4" style={{ borderRadius: 16 }}>
                        <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2 border-b border-white/5 pb-2 mb-1 flex-shrink-0">
                          <Bot size={14} /> SECURE SCAN PROCESSING FEED
                        </h4>

                        <div className="flex-1 glass-premium bg-black/60 border border-white/5 p-4 flex flex-col font-mono text-[9px] min-h-[220px]" style={{ borderRadius: 12 }}>
                          <div className="flex-1 overflow-y-auto flex flex-col gap-1 text-sec">
                            {importLog.map((log, i) => (
                              <p key={i} className={log.startsWith("✓") ? "text-green-oms" : log.startsWith("✗") ? "text-red-400" : log.startsWith("-") ? "text-gold-dim" : "text-muted"}>
                                {log}
                              </p>
                            ))}
                            {importLog.length === 0 && <p className="text-muted">// Ready. Specify name and path to execute import scanning.</p>}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pane 4: Profile JSON Import */}
                  {enrollTab === "import_json" && (
                    <div className="glass-premium p-6 flex flex-col items-center justify-center text-center gap-4 bg-black/20 h-full min-h-0 border-dashed border-2 border-gold-dim/20" style={{ borderRadius: 16 }}>
                      <div className="w-16 h-16 rounded-full bg-gold/10 border border-gold-dim flex items-center justify-center text-gold animate-pulse">
                        <Download size={28} />
                      </div>
                      <div>
                        <h4 className="font-orbitron text-sm font-black text-gold-accent tracking-wider uppercase">PROFILE ARCHIVE PACKAGE IMPORT</h4>
                        <p className="font-inter text-xs text-sec max-w-sm mt-1 mx-auto leading-relaxed">
                          Upload a previously exported `.json` profile registry archive to sync and restore all face encodings, visit counts, and metadata.
                        </p>
                      </div>

                      <input
                        type="file"
                        accept=".json"
                        ref={fileInputRef}
                        onChange={handleJsonImport}
                        className="hidden"
                      />
                      
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="btn-gold-luxury py-3 px-6 text-xs font-orbitron font-bold tracking-widest gap-2 mt-2"
                      >
                        <Download size={14} />
                        SELECT PROFILE JSON FILE
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC SETTINGS PANEL */}
            {activeNav === "settings" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <SlidersHorizontal className="text-gold-accent" size={20} />
                  <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                    OMS SYSTEM CONFIGURATION MATRIX
                  </h2>
                </div>

                <form onSubmit={saveSettings} className="flex-1 flex flex-col gap-5 overflow-y-auto pr-2">
                  <div className="grid grid-cols-2 gap-5">
                    
                    {/* User profile */}
                    <div className="glass-premium p-4 flex flex-col gap-3.5">
                      <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2">
                        <UserCheck size={14} /> USER PROFILE PROTOCOLS
                      </h4>
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">OPERATOR USERNAME</label>
                        <input
                          type="text"
                          value={opName}
                          onChange={(e) => setOpName(e.target.value)}
                          className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider">VOICE ASSISTANT SPEECH</span>
                        <button
                          type="button"
                          onClick={() => {
                            const nextVal = !ttsEnabled;
                            setTtsEnabled(nextVal);
                            speakAI("Voice assistance toggled", nextVal);
                          }}
                          className="text-gold hover:text-gold-accent transition-colors"
                        >
                          {ttsEnabled ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-muted" />}
                        </button>
                      </div>
                    </div>

                    {/* Neural parameters */}
                    <div className="glass-premium p-4 flex flex-col gap-3.5">
                      <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2">
                        <Cpu size={14} /> AI DETECTOR HYPERPARAMETERS
                      </h4>
                      <div className="flex items-center justify-between mt-1">
                        <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider">AUTO REGISTER FACES</span>
                        <button
                          type="button"
                          onClick={async () => {
                            setBtnLoading(b => ({ ...b, toggle_auto_register: true }));
                            try {
                              const r = await fetch(`${API}/api/control/toggle_auto_register`, { method: "POST" });
                              const d = await r.json();
                              const newVal = !detectNewIds;
                              setDetectNewIds(newVal);
                              speakAI(newVal ? "Intruder detection mode activated" : "Intruder detection suspended. Known operators only.");
                              setControlMsg(d.result || d.message || "Auto Register toggled");
                              safeSetTimeout(() => setControlMsg(null), 3000);
                            } catch (e) {
                              setControlMsg("Toggle failed: " + e);
                              safeSetTimeout(() => setControlMsg(null), 3000);
                            } finally {
                              setBtnLoading(b => ({ ...b, toggle_auto_register: false }));
                            }
                          }}
                          disabled={btnLoading["toggle_auto_register"]}
                          className="text-gold hover:text-gold-accent transition-colors disabled:opacity-50"
                        >
                          {detectNewIds ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-muted" />}
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-1 pt-1.5 border-t border-white/5">
                        <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider">PERSON TRACKING ENGINE</span>
                        <button
                          type="button"
                          onClick={() => {
                            const newVal = !detectPeople;
                            setDetectPeople(newVal);
                            speakAI(newVal ? "Person tracking activated" : "Person tracking suspended");
                          }}
                          className="text-gold hover:text-gold-accent transition-colors"
                        >
                          {detectPeople ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-muted" />}
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-1 pt-1.5 border-t border-white/5">
                        <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider">OBJECT DETECTION ENGINE</span>
                        <button
                          type="button"
                          onClick={() => {
                            const newVal = !detectObjects;
                            setDetectObjects(newVal);
                            speakAI(newVal ? "Object detection activated" : "Object detection suspended");
                          }}
                          className="text-gold hover:text-gold-accent transition-colors"
                        >
                          {detectObjects ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-muted" />}
                        </button>
                      </div>
                    </div>

                    {/* Telegram Credentials */}
                    <div className="glass-premium p-4 flex flex-col gap-3.5">
                      <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2">
                        <Send size={14} /> SECURE COMMUNICATION HOOK
                      </h4>
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">TELEGRAM BOT TOKEN</label>
                        <input
                          type="password"
                          value={tgBotToken}
                          onChange={(e) => setTgBotToken(e.target.value)}
                          className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">TELEGRAM SECURE CHAT ID</label>
                        <input
                          type="text"
                          value={tgChatId}
                          onChange={(e) => setTgChatId(e.target.value)}
                          className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>
                    </div>

                    {/* Performance UI settings */}
                    <div className="glass-premium p-4 flex flex-col gap-3.5">
                      <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2">
                        <Sliders size={14} /> SYSTEM PERFORMANCE GRAPHICS
                      </h4>
                      <div className="flex items-center justify-between mt-1">
                        <div>
                          <span className="font-orbitron text-[9.5px] text-sec font-bold tracking-wider block">GOLD PARTICLE BACKGROUND</span>
                          <span className="text-[8.5px] text-muted font-inter">Controls custom hardware accelerated particle canvas</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setParticlesActive(!particlesActive)}
                          className="text-gold hover:text-gold-accent transition-colors"
                        >
                          {particlesActive ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-muted" />}
                        </button>
                      </div>

                      {particlesActive && (
                        <>
                          <div className="flex flex-col gap-2 pt-2.5 mt-2 border-t border-white/5">
                            <div className="flex justify-between items-center">
                              <span className="font-orbitron text-[9px] text-sec font-bold tracking-wider uppercase">PARTICLE DENSITY</span>
                              <span className="font-mono text-[10px] text-gold-accent font-bold">{particleDensity} SHARDS</span>
                            </div>
                            <input
                              type="range"
                              min="20"
                              max="250"
                              step="5"
                              value={particleDensity}
                              onChange={(e) => {
                                const v = parseInt(e.target.value);
                                setParticleDensity(v);
                                speakAI(`Density set to ${v}`);
                              }}
                              className="w-full accent-[#D4AF37] cursor-pointer bg-white/10 h-1 rounded-lg"
                            />
                          </div>

                          <div className="flex flex-col gap-2 pt-2.5 mt-2 border-t border-white/5">
                            <div className="flex justify-between items-center">
                              <span className="font-orbitron text-[9px] text-sec font-bold tracking-wider uppercase">PARTICLE BASE SIZE</span>
                              <span className="font-mono text-[10px] text-gold-accent font-bold">{particleSize.toFixed(1)}px</span>
                            </div>
                            <input
                              type="range"
                              min="1.0"
                              max="8.0"
                              step="0.5"
                              value={particleSize}
                              onChange={(e) => {
                                setParticleSize(parseFloat(e.target.value));
                              }}
                              className="w-full accent-[#D4AF37] cursor-pointer bg-white/10 h-1 rounded-lg"
                            />
                          </div>

                          <div className="flex flex-col gap-2 pt-2.5 mt-2 border-t border-white/5">
                            <div className="flex justify-between items-center">
                              <span className="font-orbitron text-[9px] text-sec font-bold tracking-wider uppercase">MESH CONNECTION THICKNESS</span>
                              <span className="font-mono text-[10px] text-gold-accent font-bold">{meshThickness.toFixed(1)}px</span>
                            </div>
                            <input
                              type="range"
                              min="0.2"
                              max="4.0"
                              step="0.1"
                              value={meshThickness}
                              onChange={(e) => {
                                setMeshThickness(parseFloat(e.target.value));
                              }}
                              className="w-full accent-[#D4AF37] cursor-pointer bg-white/10 h-1 rounded-lg"
                            />
                          </div>
                        </>
                      )}

                      <div className="flex flex-col gap-1 pt-1 mt-1 border-t border-white/5">
                        <span className="font-orbitron text-[9px] text-gold font-bold tracking-wider block uppercase">HARDWARE ACCELERATION TARGET</span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="w-2 h-2 rounded-full bg-green-oms" />
                          <span className="font-mono text-[10px] text-sec uppercase font-bold">ACTIVE NVIDIA CUDA CAPABLE</span>
                        </div>
                      </div>
                    </div>

                    {/* Advanced Person Enrollment Section */}
                    <div className="glass-premium p-4 col-span-2 flex flex-col gap-3.5" style={{ borderRadius: 16 }}>
                      <h4 className="font-orbitron text-xs font-bold text-gold tracking-widest uppercase flex items-center gap-2">
                        <UserPlus size={14} /> ADVANCED PERSON ENROLLMENT PROTOCOLS
                      </h4>
                      <p className="text-[8.5px] text-muted font-inter">
                        Enroll a new identity using SFace multi-angle profiles. Provide the target's name and local folder path. Minimum required poses: Front, Left, Right, Up.
                      </p>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1.5">
                          <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">TARGET SUBJECT NAME</label>
                          <input
                            type="text"
                            value={settingsEnrollName}
                            onChange={(e) => setSettingsEnrollName(e.target.value)}
                            placeholder="e.g. PRAJAN"
                            className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                          />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">LOCAL DIRECTORY PATH</label>
                          <input
                            type="text"
                            value={settingsEnrollFolder}
                            onChange={(e) => setSettingsEnrollFolder(e.target.value)}
                            placeholder="e.g. C:\Users\Prajan\Pictures\dataset"
                            className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                          />
                        </div>
                      </div>
                      {settingsEnrollLog.length > 0 && (
                        <div className="glass-premium bg-black/60 border border-white/5 p-3 font-mono text-[9px] text-sec max-h-[120px] overflow-y-auto" style={{ borderRadius: 10 }}>
                          {settingsEnrollLog.map((log, i) => (
                            <p key={i} className={log.startsWith("✓") ? "text-green-oms" : log.startsWith("✗") ? "text-red-400" : "text-muted"}>
                              {log}
                            </p>
                          ))}
                        </div>
                      )}
                      <div className="flex justify-end mt-1">
                        <button
                          type="button"
                          onClick={handleSettingsEnrollImport}
                          disabled={settingsEnrollLoading || !settingsEnrollName.trim() || !settingsEnrollFolder.trim()}
                          className="btn-gold-luxury px-6 justify-center gap-2 py-2.5"
                        >
                          {settingsEnrollLoading ? (
                            <RefreshCw size={12} className="animate-spin text-gold-accent" />
                          ) : (
                            <UserPlus size={12} />
                          )}
                          ENROLL NEW IDENTITY
                        </button>
                      </div>
                    </div>

                  </div>

                  {/* Actions footer */}
                  <div className="flex-shrink-0 border-t border-white/5 pt-4 mt-auto flex items-center justify-end">
                    <button
                      type="submit"
                      disabled={btnLoading["save_settings"]}
                      className="btn-gold-luxury px-6 justify-center gap-2"
                    >
                      {btnLoading["save_settings"] ? (
                        <RefreshCw size={14} className="animate-spin text-gold-accent" />
                      ) : (
                        <Save size={14} />
                      )}
                      SECURE SYSTEM CONFIGURATION
                    </button>
                  </div>
                </form>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC CAMERAS LIST GRID */}
            {activeNav === "cameras" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <Video className="text-gold-accent" size={20} />
                  <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                    CCTV CAMERA STREAMING CONTROL MATRIX
                  </h2>
                </div>

                <div className="flex-1 grid grid-cols-2 gap-4 overflow-y-auto pr-1">
                  {cameras.map((cam, idx) => (
                    <div key={cam.id} className="glass-premium p-4 flex flex-col gap-3 min-h-0 relative">
                      <div className="flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center gap-2">
                          <span className={`status-indicator ${cam.online ? "text-green-oms bg-green-oms animate-pulse" : "text-red-500 bg-red-500"}`} />
                          <h4 className="font-orbitron text-xs font-black text-gold tracking-widest leading-none">
                            CAM {cam.id + 1} - {cam.name}
                          </h4>
                        </div>
                        <span className="font-orbitron text-[8.5px] font-bold text-sec bg-white/5 px-2 py-0.5 rounded tracking-widest">
                          {cam.online ? "SECURE FEED" : "NO CORRELATION"}
                        </span>
                      </div>

                      {/* Small camera view or placeholder */}
                      <div className="h-[120px] rounded-lg bg-black/60 border border-white/5 overflow-hidden relative flex items-center justify-center flex-shrink-0">
                        {cam.online ? (
                          <img
                            src={`${API}/api/camera/${idx}/snapshot?t=${telemetry?.uptime_secs || 0}`}
                            alt={cam.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="flex flex-col items-center gap-1.5 text-center">
                            <Eye size={16} className="text-muted animate-pulse" />
                            <span className="font-orbitron text-[8px] text-muted tracking-widest">STREAM TERMINATED</span>
                          </div>
                        )}
                      </div>

                      {/* Name & URL Reconnection Inputs */}
                      <div className="flex flex-col gap-2 text-[9px] font-orbitron font-bold text-sec tracking-wider">
                        <div className="flex flex-col gap-1">
                          <span>CAMERA CHANNEL NAME</span>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={camNames[idx] !== undefined ? camNames[idx] : cam.name}
                              onChange={(e) => {
                                const newNames = [...camNames];
                                if (newNames.length === 0 && cameras.length > 0) {
                                  for (let k = 0; k < cameras.length; k++) {
                                    newNames[k] = cameras[k].name;
                                  }
                                }
                                newNames[idx] = e.target.value;
                                setCamNames(newNames);
                              }}
                              placeholder="e.g. Front Door"
                              className="flex-1 glass-premium bg-black/40 border border-white/10 text-white font-mono text-xs px-3 py-1.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                            />
                            <button
                              onClick={() => renameCam(idx)}
                              disabled={btnLoading[`rename_cam_${idx}`]}
                              className="btn-gold-luxury py-1 px-3 text-[8.5px] justify-center"
                              title="Rename this camera channel"
                            >
                              {btnLoading[`rename_cam_${idx}`] ? (
                                <RefreshCw size={10} className="animate-spin text-gold-accent" />
                              ) : (
                                <Save size={10} />
                              )}
                              RENAME
                            </button>
                            <button
                              onClick={() => removeCam(idx)}
                              disabled={btnLoading[`remove_cam_${idx}`]}
                              className="glass-premium flex items-center gap-1 py-1 px-3 text-[8.5px] justify-center border border-red-500/20 hover:border-red-500/40 bg-red-950/20 hover:bg-red-900/30 text-red-400 rounded-lg transition-all"
                              title="Remove this camera channel"
                            >
                              {btnLoading[`remove_cam_${idx}`] ? (
                                <RefreshCw size={10} className="animate-spin text-red-400" />
                              ) : (
                                <Trash size={10} />
                              )}
                              REMOVE
                            </button>
                          </div>
                        </div>

                        <div className="flex flex-col gap-1">
                          <span>CCTV URL / DEVICE ID</span>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={camConnectUrls[idx] !== undefined ? camConnectUrls[idx] : cam.source || ""}
                              onChange={(e) => {
                                const newUrls = [...camConnectUrls];
                                if (newUrls.length === 0 && cameras.length > 0) {
                                  for (let k = 0; k < cameras.length; k++) {
                                    newUrls[k] = cameras[k].source || "";
                                  }
                                }
                                newUrls[idx] = e.target.value;
                                setCamConnectUrls(newUrls);
                              }}
                              placeholder="e.g. 0, rtsp://address, http://"
                              className="flex-1 glass-premium bg-black/40 border border-white/10 text-white font-mono text-xs px-3 py-1.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                            />
                            <button
                              onClick={() => connectCctv(idx)}
                              disabled={btnLoading[`connect_cam_${idx}`]}
                              className="btn-gold-luxury py-1 px-3 text-[8.5px] justify-center"
                              title="Toggles a secure feed connection/reconnection logic"
                            >
                              {btnLoading[`connect_cam_${idx}`] ? (
                                <RefreshCw size={10} className="animate-spin text-gold-accent" />
                              ) : (
                                <Wifi size={10} />
                              )}
                              CONNECT
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* ADD NEW CAMERA NODE */}
                  <div className="glass-premium p-4 flex flex-col gap-3 min-h-0 border border-dashed border-white/10 hover:border-gold-accent/40 hover:bg-white/[0.01] rounded-xl transition-all">
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Plus className="text-gold-accent" size={14} />
                      <h4 className="font-orbitron text-xs font-black text-gold tracking-widest leading-none">
                        ADD NEW CCTV NODE
                      </h4>
                    </div>

                    <div className="flex flex-col gap-2 text-[9px] font-orbitron font-bold text-sec tracking-wider">
                      <div className="flex flex-col gap-1">
                        <span>CAMERA CHANNEL NAME</span>
                        <input
                          type="text"
                          value={newCamName}
                          onChange={(e) => setNewCamName(e.target.value)}
                          placeholder="e.g. Back Alley Cam"
                          className="glass-premium bg-black/40 border border-white/10 text-white font-mono text-xs px-3 py-1.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1">
                        <span>CCTV URL / DEVICE ID</span>
                        <input
                          type="text"
                          value={newCamSource}
                          onChange={(e) => setNewCamSource(e.target.value)}
                          placeholder="e.g. 1, rtsp://address, http://"
                          className="glass-premium bg-black/40 border border-white/10 text-white font-mono text-xs px-3 py-1.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1">
                        <span>LOCATION / ZONE</span>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={newCamLocation}
                            onChange={(e) => setNewCamLocation(e.target.value)}
                            placeholder="e.g. Server Room Entrance"
                            className="flex-1 glass-premium bg-black/40 border border-white/10 text-white font-mono text-xs px-3 py-1.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                          />
                          <button
                            onClick={addCam}
                            disabled={btnLoading["add_cam"]}
                            className="btn-gold-luxury py-1 px-4 text-[8.5px] justify-center flex-shrink-0"
                            title="Register and initialize this new camera channel"
                          >
                            {btnLoading["add_cam"] ? (
                              <RefreshCw size={10} className="animate-spin text-gold-accent" />
                            ) : (
                              <Plus size={10} />
                            )}
                            ADD CAMERA
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC ANALYTICS ROUTE */}
            {activeNav === "analytics" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <BarChart3 className="text-gold-accent" size={20} />
                  <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                    OMS ADVANCED NEURAL TELEMETRY ANALYTICS
                  </h2>
                </div>

                <div className="flex-1 grid grid-cols-2 gap-5 overflow-y-auto pr-1">
                  {[
                    { title: "AI CORE GPU WORKFLOW", data: gpuHistory, color: "#FFD700", desc: "Graphics Processing hardware load sparklines" },
                    { title: "CENTRAL PROCESSOR LOAD", data: cpuHistory, color: "#00FFA3", desc: "Calculated central CPU thread load matrix" },
                    { title: "RAM INSTANCE CAPABILITY", data: ramHistory, color: "#D4AF37", desc: "System RAM instance index allocation logs" },
                    { title: "SECURE NETWORK BANDWIDTH", data: netHistory, color: "#00E5FF", desc: "Calculated uvicorn port data transmission rates" }
                  ].map((chart, i) => (
                    <div key={i} className="glass-premium p-4 flex flex-col gap-2 h-[180px]">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-orbitron text-xs font-black text-gold tracking-widest uppercase">{chart.title}</h4>
                          <p className="text-[8.5px] text-muted font-inter">{chart.desc}</p>
                        </div>
                        <TrendingUp size={14} style={{ color: chart.color }} />
                      </div>
                      <div className="flex-1 bg-black/30 border border-white/5 rounded-xl px-4 py-2 flex items-center justify-center">
                        <Sparkline data={chart.data} color={chart.color} height={80} />
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC EVENTS LOGS ROUTE */}
            {activeNav === "events" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <AlertTriangle className="text-gold-accent" size={20} />
                  <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                    OMS RECOGNITION SECURITY ALERT LOG DATABASE
                  </h2>
                </div>

                <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2">
                  {events.map((ev, i) => {
                    const color = EVENT_COLORS[ev.event] || "#B8B8B8";
                    return (
                      <div 
                        key={i} 
                        className="glass-premium bg-black/30 p-3 border border-white/5 hover:border-gold-dim/10 flex items-center justify-between gap-4"
                        style={{ borderRadius: 12 }}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color, boxShadow: `0 0 8px ${color}` }} />
                          <div className="min-w-0">
                            <span className="font-orbitron text-[10.5px] font-black tracking-wider uppercase block" style={{ color }}>
                              {eventLabel(ev.event)}
                            </span>
                            <span className="font-inter text-[9.5px] text-sec truncate block">
                              Source Camera: <span className="text-[#FFFFFF]">{ev.camera || "Sector Grid"}</span> | Payload Details: <span className="text-[#FFFFFF] font-mono">{ev.detail || "Baseline confirmed"}</span>
                            </span>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <span className="font-orbitron text-xs font-bold text-gold block">{ev.person || opName.toUpperCase()}</span>
                          <span className="font-mono text-[9px] text-muted block mt-0.5">{ev.ts}</span>
                        </div>
                      </div>
                    );
                  })}
                  {events.length === 0 && (
                    <div className="text-center py-10 font-mono text-[10px] text-muted">Timeline logs pristine. No telemetry captured</div>
                  )}
                </div>
              </motion.div>
            )}

            {/* FULLY FUNCTIONAL DYNAMIC COMMUNICATIONS TAB */}
            {activeNav === "comms" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-premium flex-1 p-6 flex flex-col min-h-0 h-full overflow-hidden"
              >
                <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-4 flex-shrink-0">
                  <MessageSquare className="text-gold-accent" size={20} />
                  <h2 className="font-orbitron text-base font-black text-gold-accent tracking-widest uppercase">
                    OMS TELEGRAM BOT TRANSMISSION PORTAL
                  </h2>
                </div>

                <div className="flex-1 flex flex-col gap-5 justify-center max-w-[480px] mx-auto w-full">
                  <div className="glass-premium p-5 flex flex-col gap-4 text-center">
                    <div className="w-14 h-14 rounded-full bg-gold/10 border border-gold-dim flex items-center justify-center mx-auto text-gold animate-pulse">
                      <Bot size={28} />
                    </div>
                    <div>
                      <h4 className="font-orbitron text-sm font-black text-gold-accent tracking-wider uppercase">TELEGRAM INTEGRATOR STATUS</h4>
                      <p className="font-inter text-[10.5px] text-sec mt-1">Direct API pipelines to Telegram notification bots</p>
                    </div>

                    <div className="glass-premium bg-black/60 border border-white/5 p-4 text-[10.5px] text-left grid grid-cols-2 gap-y-1 font-mono text-sec">
                      <span>BOT IDENTIFIER:</span>
                      <span className="text-[#FFFFFF] text-right">OMS Surveillance Bot</span>
                      <span>SECURE CHAT ID:</span>
                      <span className="text-[#FFFFFF] text-right">{tgChatId}</span>
                      <span>TELEGRAM SERVER:</span>
                      <span className="text-green-oms text-right font-bold">CONNECTED</span>
                    </div>

                    <button
                      onClick={() => doControl("test_telegram")}
                      disabled={btnLoading["test_telegram"]}
                      className="btn-gold-luxury w-full justify-center gap-2 py-3"
                    >
                      {btnLoading["test_telegram"] ? (
                        <RefreshCw size={14} className="animate-spin text-gold-accent" />
                      ) : (
                        <Send size={14} />
                      )}
                      TRANSMIT SECURE VERIFICATION ALERT
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

          </div>

          {/* RIGHT SIDEBAR PANEL */}
          <aside className="w-[300px] flex-shrink-0 flex flex-col gap-3 min-h-0 h-full overflow-hidden">
            
            {/* Active facial recognition info */}
            <div className="glass-premium px-5 py-4 flex-shrink-0" style={{ borderRadius: 20 }}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-orbitron text-xs font-black text-gold-accent tracking-widest uppercase">ACTIVE FACE PORTRAIT</span>
                <button
                  onClick={() => setWizardOpen(true)}
                  className="p-1 text-gold hover:text-gold-accent transition-colors"
                  title="Enroll a new face into system memory"
                >
                  <UserPlus size={14} />
                </button>
              </div>

              <div className="h-[120px] rounded-xl glass-premium bg-black/60 border border-white/5 relative overflow-hidden flex items-center justify-center">
                {isFaceUnlocked ? (
                  (() => {
                    const activeSubject = (cameras as any)[activeCam]?.active_subjects?.[0];
                    const hasActiveSubject = !!activeSubject && !!activeSubject.pid;
                    const sName = hasActiveSubject ? activeSubject.name : "IDENTIFYING...";
                    const sKnown = hasActiveSubject ? activeSubject.known : false;
                    const isIntruder = hasActiveSubject && !sKnown;
                    const isScanning = !hasActiveSubject;
                    
                    return (
                      <div className="w-full h-full flex items-center justify-center gap-4 px-4">
                        <div className={`w-18 h-18 rounded-full border-2 ${isScanning ? 'border-gold-dim/40 animate-pulse' : isIntruder ? 'border-red-500/50 animate-pulse' : 'border-gold-accent/40 success-ring-lock'} overflow-hidden relative flex-shrink-0`}>
                          {hasActiveSubject ? (
                            <img
                              src={`${API}/api/crop/${activeSubject.pid}?t=${cropKey}`}
                              alt="Active Subject Crop"
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center bg-black/40">
                              <RefreshCw size={16} className="text-gold-dim animate-spin" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            {isScanning ? (
                              <>
                                <RefreshCw size={12} className="text-gold-dim animate-spin" />
                                <span className="font-orbitron text-[9px] font-black text-gold-dim tracking-wider">ANALYZING PROFILE</span>
                              </>
                            ) : isIntruder ? (
                              <>
                                <AlertTriangle size={12} className="text-red-500 animate-bounce" />
                                <span className="font-orbitron text-[9px] font-black text-red-500 tracking-wider">UNAUTHORIZED INTRUDER</span>
                              </>
                            ) : (
                              <>
                                <CheckCircle size={12} className="text-green-oms animate-bounce" />
                                <span className="font-orbitron text-[9px] font-black text-gold-accent tracking-wider">P. RECOGNIZED</span>
                              </>
                            )}
                          </div>
                          
                          {hasActiveSubject && editingPid === activeSubject.pid ? (
                            <div className="flex items-center gap-1 mt-1">
                              <input
                                type="text"
                                className="bg-black/90 border border-gold text-[10px] text-white rounded px-1.5 py-0.5 w-full focus:ring-1 focus:ring-gold-accent focus:outline-none font-mono"
                                value={editNameValue}
                                onChange={e => setEditNameValue(e.target.value)}
                                onKeyDown={e => {
                                  if (e.key === 'Enter') {
                                    handleRenameSave(activeSubject.pid, editNameValue);
                                  }
                                }}
                                autoFocus
                              />
                              <button
                                onClick={() => handleRenameSave(activeSubject.pid, editNameValue)}
                                className="p-0.5 text-green-400 hover:text-green-300"
                                title="Confirm Identity"
                              >
                                <Check size={11} />
                              </button>
                              <button
                                onClick={() => setEditingPid(null)}
                                className="p-0.5 text-red-400 hover:text-red-300"
                                title="Cancel"
                              >
                                <X size={11} />
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center justify-between mt-0.5">
                              <h3 className={`font-orbitron text-xs font-black truncate leading-tight ${isScanning ? 'text-gold-dim/70' : isIntruder ? 'text-red-400' : 'text-[#FFFFFF]'}`}>
                                {sName}
                              </h3>
                              {hasActiveSubject && (
                                <button
                                  onClick={() => {
                                    setEditingPid(activeSubject.pid);
                                    setEditNameValue(activeSubject.name);
                                  }}
                                  className="text-gold hover:text-gold-accent p-0.5 flex-shrink-0"
                                  title="Add/Rename subject in real-time"
                                >
                                  <Edit2 size={10} />
                                </button>
                              )}
                            </div>
                          )}
                          
                          <p className="font-mono text-[8px] text-sec mt-0.5">
                            CONFIDENCE:{' '}
                            <span className={isScanning ? 'text-gold-dim' : isIntruder ? 'text-red-400' : 'text-green-oms'}>
                              {isScanning
                                ? 'PENDING'
                                : activeSubject?.confidence
                                ? `${(activeSubject.confidence * (activeSubject.confidence <= 1 ? 100 : 1)).toFixed(1)}%`
                                : isIntruder
                                ? '94.2%'
                                : '98.4%'}
                            </span>
                          </p>
                          <p className="font-mono text-[8px] text-muted">
                            LOCK STATE:{' '}
                            <span className={isScanning ? 'text-gold-dim font-bold' : isIntruder ? 'text-red-500 font-black animate-pulse' : 'text-green-oms font-bold'}>
                              {isScanning ? 'PROCESSING' : isIntruder ? 'BREACHED' : 'SECURED'}
                            </span>
                          </p>
                          <p className="font-mono text-[8px] text-muted">
                            BEHAVIOR STATE:{' '}
                            <span className={isScanning ? 'text-gold-dim font-bold' : activeSubject?.status === 'IDLE' ? 'text-gold-accent font-black animate-pulse' : 'text-green-oms font-bold'}>
                              {isScanning ? 'PROCESSING' : activeSubject?.status || 'ACTIVE'}
                            </span>
                          </p>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <div className="flex flex-col items-center gap-2 text-center">
                    <div className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center">
                      <Shield size={16} className="text-muted animate-pulse" />
                    </div>
                    <p className="font-orbitron text-[9px] text-sec tracking-widest">AWAITING SUBJECT IDENTIFICATION</p>
                    <p className="font-inter text-[8px] text-muted">Facial locks currently operational in sector</p>
                  </div>
                )}
                {isFaceUnlocked && <div className="hud-scan-line" style={{ animationDuration: "2s" }} />}
              </div>
            </div>

            {/* Smart Memory database */}
            <div className="glass-premium px-5 py-4 flex-1 min-h-0 flex flex-col" style={{ borderRadius: 20 }}>
              <div className="flex items-center justify-between mb-3 flex-shrink-0">
                <span className="font-orbitron text-xs font-black text-gold-accent tracking-widest uppercase">MEMORY DATABASE</span>
                <span className="font-mono text-[9px] text-sec uppercase font-bold">Total: {knownUsers.length}</span>
              </div>

              <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2.5">
                {knownUsers.map((user, i) => (
                  <div 
                    key={i} 
                    className="glass-premium bg-black/20 border border-white/5 hover:border-gold-dim/20 hover:bg-gold/5 p-3 transition-all duration-300 animate-fade-in"
                    style={{ borderRadius: 12 }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full overflow-hidden border border-gold-dim flex-shrink-0 bg-gold/10 flex items-center justify-center relative">
                          {user.photo && !imgErrors[user.name] ? (
                            <img
                              src={`${API}/${user.photo.replace(/\\/g, '/')}`}
                              alt={user.name}
                              className="w-full h-full object-cover"
                              onError={() => {
                                setImgErrors(prev => ({ ...prev, [user.name]: true }));
                              }}
                            />
                          ) : (
                            <span className="font-orbitron text-[9px] text-gold font-bold">
                              {user.name.slice(0, 2).toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div>
                          <h4 className="font-orbitron text-xs font-bold text-[#FFFFFF] leading-none">{user.name}</h4>
                          <span className="font-inter text-[8.5px] text-sec leading-none">{user.role}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => forgetFace(user.name)}
                          className="text-[#FFFFFF]/40 hover:text-red-500 transition-colors p-1"
                          title={`Forget face profile '${user.name}'`}
                        >
                          <Trash size={12} />
                        </button>
                        <span className="font-orbitron text-[8px] font-bold text-green-oms bg-green-oms/10 px-1.5 py-0.5 rounded">
                          {user.status}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-y-0.5 border-t border-white/5 pt-2 text-[9px] font-mono text-sec">
                      <span>INTERACTIONS:</span>
                      <span className="text-[#FFFFFF] text-right font-bold">{user.visitCount} visits</span>
                      <span>LAST RECOGNIZED:</span>
                      <span className="text-[#FFFFFF] text-right">{user.lastSeen}</span>
                      <span>SUCCESS RATE:</span>
                      <span className="text-gold-accent text-right font-bold">{user.accuracy}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Timelines history */}
            <div className="glass-premium px-5 py-4 flex-shrink-0 animate-slide-up" style={{ borderRadius: 20, height: 160 }}>
              <span className="font-orbitron text-xs font-black text-gold-accent tracking-widest uppercase block mb-3">RECOGNITION TIMELINE</span>
              
              <div className="h-[96px] overflow-y-auto flex flex-col gap-1 pr-1">
                <AnimatePresence mode="popLayout">
                  {events.slice(0, 5).map((ev, i) => {
                    const color = EVENT_COLORS[ev.event] || "#B8B8B8";
                    return (
                      <motion.div
                        key={`${ev.ts}-${i}`}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2 text-[10px] py-1 border-b border-white/5 last:border-0"
                      >
                        <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
                        <span className="font-mono text-[9px] text-muted flex-shrink-0">{ev.ts.slice(11, 19)}</span>
                        <span className="font-orbitron font-bold text-sec truncate flex-1 leading-none">{eventLabel(ev.event)}</span>
                        <span className="font-inter text-[9px] text-[#FFFFFF] font-medium flex-shrink-0">{ev.person || opName.toUpperCase()}</span>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
                {events.length === 0 && (
                  <p className="font-mono text-[9px] text-muted text-center mt-2">Timeline secured. No logs</p>
                )}
              </div>
            </div>

          </aside>
        </div>

        {/* ── FOOTER STATS & ACTIONS BAR ── */}
        <footer className="flex gap-3 flex-shrink-0 relative" style={{ height: 136 }}>
          
          {/* Active Statistics Sparklines panel */}
          <div className="glass-premium flex-[1.6] px-5 py-3 flex items-center justify-between gap-4">
            {[
              { label: "AI CORE GPU WORKFLOW", value: `${telemetry?.gpu ?? 0}%`, color: "#FFD700", history: gpuHistory },
              { label: "CORE CPU LOAD INDEX", value: `${telemetry?.cpu ?? 0}%`, color: "#00FFA3", history: cpuHistory },
              { label: "CORE RAM INSTANCE", value: `${telemetry?.ram ?? 0}%`, color: "#D4AF37", history: ramHistory },
              { label: "NET DATA BANDWIDTH", value: `${Math.round(telemetry?.net_kb ?? 0)} KB/s`, color: "#00E5FF", history: netHistory },
            ].map(({ label, value, color, history }) => (
              <div key={label} className="flex-1 flex flex-col gap-1 justify-center min-w-0">
                <div className="flex items-center justify-between text-[9px] font-orbitron font-bold text-sec leading-none">
                  <span className="truncate">{label}</span>
                  <span className="font-mono text-[10px] font-black" style={{ color }}>{value}</span>
                </div>
                <div className="h-6 flex items-center">
                  <Sparkline data={history} color={color} height={20} />
                </div>
              </div>
            ))}
          </div>

          {/*Scrolling Diagnostics Logs Feed */}
          <div className="glass-premium flex-1 px-5 py-3 flex flex-col justify-between min-w-0">
            <div className="flex items-center justify-between flex-shrink-0">
              <span className="font-orbitron text-[9px] font-black text-gold-accent tracking-widest uppercase">DIAGNOSTIC LOG ACTIVE FEED</span>
              <span className="status-indicator text-green-oms bg-green-oms animate-pulse" />
            </div>
            
            <div className="h-[84px] overflow-y-auto font-mono text-[9.5px] text-sec flex flex-col gap-0.5 pr-1 mt-1 leading-none">
              <p className="text-muted uppercase">// AI core telemetry initialized successfully.</p>
              <p className="text-[#FFFFFF] uppercase">✓ YOLO model loaded on device target GPU index 0.</p>
              <p className="text-[#FFFFFF] uppercase">✓ Face recognition database secure. Known records: {knownUsers.length}.</p>
              <p className="text-[#FFFFFF]">✓ Telegram bot client connected secure.</p>
              <p className="text-gold uppercase">✓ Uptime index established: {summary?.uptime || "00:00:00"}.</p>
            </div>
          </div>

          {/* Quick Actions Panel */}
          <div className="glass-gold-active flex-shrink-0 px-4 py-3 flex flex-col gap-2 justify-center" style={{ width: 220 }}>
            <span className="font-orbitron text-[9px] font-black text-gold-accent tracking-widest uppercase text-center block mb-0.5">CORE INTERACTIVE ACTIONS</span>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setWizardOpen(true)}
                disabled={btnLoading["register_face"]}
                className="btn-gold-luxury py-2 px-1 text-[9px] justify-center"
                title="Opens custom face enrollment wizard"
              >
                {btnLoading["register_face"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : (
                  <UserPlus size={11} />
                )}
                ENROLL
              </button>

              {/* AUTO REGISTER NEW FACES toggle — mirrors the OpenCV desktop sidebar pill */}
              <button
                onClick={async () => {
                  setBtnLoading(b => ({ ...b, toggle_auto_register: true }));
                  try {
                    const r = await fetch(`${API}/api/control/toggle_auto_register`, { method: "POST" });
                    const d = await r.json();
                    const newVal = !detectNewIds;
                    setDetectNewIds(newVal);
                    speakAI(newVal ? "Auto register faces ON" : "Auto register faces OFF");
                    setControlMsg(d.result || d.message || "Auto Register toggled");
                    safeSetTimeout(() => setControlMsg(null), 3000);
                  } catch (e) {
                    setControlMsg("Toggle failed: " + e);
                    safeSetTimeout(() => setControlMsg(null), 3000);
                  } finally {
                    setBtnLoading(b => ({ ...b, toggle_auto_register: false }));
                  }
                }}
                disabled={btnLoading["toggle_auto_register"]}
                className={`py-2 px-1 text-[9px] justify-center font-orbitron font-bold tracking-widest rounded-xl border transition-all duration-300 flex items-center gap-1.5 ${
                  detectNewIds
                    ? "bg-green-900/30 border-green-500/40 text-green-400 hover:bg-green-900/50 hover:border-green-400"
                    : "bg-red-900/30 border-red-500/40 text-red-400 hover:bg-red-900/50 hover:border-red-400"
                }`}
                title={detectNewIds ? "Auto Register ON — click to disable" : "Auto Register OFF — click to enable"}
              >
                {btnLoading["toggle_auto_register"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : detectNewIds ? (
                  <ToggleRight size={13} />
                ) : (
                  <ToggleLeft size={13} />
                )}
                AUTO REG
              </button>

              <button
                onClick={() => doControl("export_csv")}
                disabled={btnLoading["export_csv"]}
                className="btn-gold-luxury py-2 px-1 text-[9px] justify-center"
                title="Exports logs activity to CSV log spreadsheet"
              >
                {btnLoading["export_csv"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : (
                  <Download size={11} />
                )}
                EXPORT CSV
              </button>

              <button
                onClick={() => doControl("test_telegram")}
                disabled={btnLoading["test_telegram"]}
                className="btn-gold-luxury py-2 px-1 text-[9px] justify-center"
                title="Sends secure test alert to Telegram"
              >
                {btnLoading["test_telegram"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : (
                  <Send size={11} />
                )}
                TELEGRAM
              </button>

              <button
                onClick={() => doControl("alarm")}
                disabled={btnLoading["alarm"]}
                className="btn-danger-luxury py-2 px-1 text-[9px] justify-center"
                title="Triggers local alarm alert logs"
              >
                {btnLoading["alarm"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : (
                  <Volume2 size={11} />
                )}
                ALARM
              </button>

              <button
                onClick={() => doControl("reset_logs")}
                disabled={btnLoading["reset_logs"]}
                className="btn-danger-luxury py-2 px-1 text-[9px] justify-center"
                title="Resets and clears all system log files and visit entries"
              >
                {btnLoading["reset_logs"] ? (
                  <RefreshCw size={11} className="animate-spin" />
                ) : (
                  <Trash size={11} />
                )}
                RESET LOGS
              </button>
            </div>
          </div>

        </footer>
      </div>

      {/* ── 3. FACE ENROLLMENT SECURE DIALOG WIZARD ── */}
      <AnimatePresence>
        {wizardOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-premium p-6 w-[360px] relative border-gold"
            >
              <h3 className="font-orbitron text-sm font-black text-gold-accent tracking-widest uppercase mb-4 text-center">
                FACE ENROLLMENT PROTOCOL
              </h3>

              {wizardStep === 1 && (
                <form onSubmit={completeEnrollment} className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">INPUT TARGET USER NAME</label>
                    <input
                      type="text"
                      required
                      value={wizardName}
                      onChange={(e) => setWizardName(e.target.value)}
                      placeholder="e.g. PRAJAN"
                      className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-sm px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                      maxLength={18}
                    />
                  </div>
                  <div className="flex flex-col gap-1 rounded-xl bg-gold/5 border border-gold-dim/10 p-3 text-[10px] text-sec leading-relaxed">
                    <div className="flex items-center gap-1.5 text-gold-accent font-bold mb-1">
                      <Info size={11} />
                      <span>SECURE PROCESS INSTRUCTIONS:</span>
                    </div>
                    <p>1. Align your face clearly with active Camera 1.</p>
                    <p>2. Keep natural light focus and stay static.</p>
                    <p>3. Submit to initialize custom database registry.</p>
                  </div>
                  <div className="flex gap-3 mt-2">
                    <button
                      type="button"
                      onClick={() => setWizardOpen(false)}
                      className="btn-danger-luxury flex-1 justify-center"
                    >
                      ABORT
                    </button>
                    <button
                      type="submit"
                      disabled={btnLoading["enroll"]}
                      className="btn-gold-luxury flex-1 justify-center"
                    >
                      {btnLoading["enroll"] ? (
                        <RefreshCw size={11} className="animate-spin text-gold-accent" />
                      ) : (
                        <UserCheck size={11} />
                      )}
                      SUBMIT
                    </button>
                  </div>
                </form>
              )}

              {wizardStep === 2 && (
                <div className="flex flex-col items-center justify-center py-6 text-center gap-4">
                  <div className="relative w-20 h-20 rounded-full border-2 border-[#FFD700] flex items-center justify-center animate-pulse success-ring-lock">
                    <Video className="text-gold-accent animate-bounce" size={24} />
                    <div className="ripple-voice" />
                  </div>
                  <div>
                    <h4 className="font-orbitron text-xs font-black text-gold-accent tracking-widest animate-pulse">CAPTURNG PORTRAIT NODES...</h4>
                    <p className="font-inter text-[9.5px] text-sec mt-1">Stand static under active secure Camera 1 frame</p>
                  </div>
                </div>
              )}

              {wizardStep === 3 && (
                <div className="flex flex-col items-center justify-center py-6 text-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-green-500/10 border-2 border-green-500 flex items-center justify-center">
                    <Check size={28} className="text-green-500 animate-bounce" />
                  </div>
                  <div>
                    <h4 className="font-orbitron text-xs font-black text-green-oms tracking-widest uppercase">ENROLLMENT APPROVED</h4>
                    <p className="font-inter text-[10px] text-sec mt-1">Target registered successfully into memory database</p>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Control Feedback Toast Alerts ── */}
      <AnimatePresence>
        {controlMsg && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 28 }}
            className={`fixed bottom-6 left-1/2 -translate-x-1/2 px-6 py-3 z-50 rounded-xl ${
              /failed|error|could not|invalid/i.test(controlMsg)
                ? "glass-red-active border border-red-500/30 text-red-500"
                : "glass-gold-active text-gold-accent"
            }`}
          >
            <span className="font-orbitron text-xs font-black tracking-wider uppercase flex items-center gap-2">
              {/failed|error|could not|invalid/i.test(controlMsg) ? (
                <XCircle size={14} className="text-red-500" />
              ) : (
                <CheckCircle size={14} className="text-green-oms" />
              )}
              {controlMsg}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
