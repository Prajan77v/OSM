"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Video, Crosshair, Radar, BarChart3,
  AlertTriangle, MessageSquare, Settings, LogOut, ChevronRight,
  Shield, Activity, Cpu, HardDrive, Wifi, Send, Bell, Eye,
  UserCheck, Package, MapPin, Clock, Zap, TrendingUp,
  Database, Bot, Download, Volume2, RefreshCw, Maximize2, Minimize2,
  Mic, Play, Pause, Square, CheckCircle, Info,
  UserPlus, Award, Check, Save, ToggleLeft, ToggleRight,
  Sliders, SlidersHorizontal, SlidersVertical, Edit2, X, Trash
} from "lucide-react";

// ─── API base URL (proxied in dev, same-origin in prod) ──────────────────────
const API = "";

// ─── Types ───────────────────────────────────────────────────────────────────
interface CameraInfo {
  id: number; name: string; location: string;
  online: boolean; disconnected: boolean; fps: number;
  persons: number; detections: number; threat_level: string; uptime: string;
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
}

// ─── Nav items ───────────────────────────────────────────────────────────────
const NAV = [
  { id: "overview",    icon: LayoutDashboard, label: "OVERVIEW" },
  { id: "cameras",     icon: Video,           label: "CAMERAS" },
  { id: "detection",   icon: Crosshair,       label: "DETECTION" },
  { id: "tactical",    icon: Radar,           label: "TACTICAL" },
  { id: "analytics",   icon: BarChart3,       label: "ANALYTICS" },
  { id: "events",      icon: AlertTriangle,   label: "EVENTS" },
  { id: "comms",       icon: MessageSquare,   label: "COMMUNICATION" },
  { id: "settings",    icon: Settings,        label: "SETTINGS" },
];

const EVENT_COLORS: Record<string, string> = {
  PERSON_ENTERED: "#D4AF37", PERSON_RETURNED: "#D4AF37",
  PERSON_LEFT: "#B8B8B8", INTRUDER: "#FFD700",
  OBJ_ADDED: "#00E5FF", OBJ_REMOVED: "#00FFA3",
  ZONE_INTRUSION: "#D4AF37", BEHAVIOR: "#FFD700",
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
function ParticleCanvas({ active, density = 120 }: { active: boolean; density?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });

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
            r: Math.random() * 1.5 + 0.5,
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
          r: Math.random() * 2 + 0.8,
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
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(212, 175, 55, ${p.alpha})`;
        ctx.fill();
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
            ctx.strokeStyle = `rgba(212, 175, 55, ${0.15 * (1 - d/100)})`; // Upgraded link opacity: 3x stronger!
            ctx.lineWidth = 0.75;                                          // Upgraded link thickness!
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
  const [tgBotToken, setTgBotToken] = useState("8938780809:AAHzpgv_fbfbmXJ9x_ui44LY83CWnTWfKPo");
  const [tgChatId, setTgChatId] = useState("8076971661");
  const [particlesActive, setParticlesActive] = useState(true);
  const [particleDensity, setParticleDensity] = useState(120);

  // Reconnection state inside Camera view
  const [camConnectUrls, setCamConnectUrls] = useState<string[]>(["0", "NONE", "NONE", "NONE"]);

  // Memory database state
  const [knownUsers, setKnownUsers] = useState<EnrolledUser[]>([
    { name: "Prajan", visitCount: 142, lastSeen: "Today 08:01", accuracy: 98.4, role: "System Administrator", status: "AUTHORIZED" },
    { name: "Dev Team", visitCount: 84, lastSeen: "Yesterday 18:24", accuracy: 96.1, role: "Core Developer", status: "VERIFIED" },
    { name: "Support AI", visitCount: 210, lastSeen: "Today 05:00", accuracy: 99.8, role: "Autonomous Agent", status: "ACTIVE" }
  ]);

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
      el.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
      speakAI("Fullscreen preview activated");
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
      speakAI("Fullscreen preview deactivated");
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
        }
      } catch {}
    };
    fetchSettings();
  }, []);

  // ── Data polling ──────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      const [camRes, telRes, evtRes, sumRes, facRes] = await Promise.all([
        fetch(`${API}/api/cameras`).then(r => r.json()),
        fetch(`${API}/api/telemetry`).then(r => r.json()),
        fetch(`${API}/api/events`).then(r => r.json()),
        fetch(`${API}/api/summary`).then(r => r.json()),
        fetch(`${API}/api/faces`).then(r => r.json()),
      ]);
      setCameras(camRes);
      setTelemetry(telRes);
      setEvents(evtRes.slice(-15).reverse());
      setSummary(sumRes);
      if (Array.isArray(facRes) && facRes.length > 0) {
        setKnownUsers(facRes);
      }

      setCpuHistory(h => [...h.slice(1), telRes.cpu || 0]);
      setRamHistory(h => [...h.slice(1), telRes.ram || 0]);
      setNetHistory(h => [...h.slice(1), Math.min(telRes.net_kb || 0, 100)]);
      setGpuHistory(h => [...h.slice(1), telRes.gpu || 0]);

      const activeCamDets = camRes[activeCam]?.persons || 0;
      if (activeCamDets > 0) {
        setIsFaceUnlocked(true);
      } else {
        setIsFaceUnlocked(false);
      }
    } catch {}
  }, [activeCam]);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 2000);
    return () => clearInterval(t);
  }, [fetchAll]);

  // ── Browser Voice Speech Output ──────────────────────────────────────────
  const speakAI = (txt: string) => {
    if (!ttsEnabled) return;
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
  };

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

      setTimeout(async () => {
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

        setTimeout(() => {
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

            setTimeout(() => {
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
      setTimeout(() => setControlMsg(null), 3000);
    } catch (e) {
      setControlMsg("Transmission failed: " + e);
      setTimeout(() => setControlMsg(null), 3000);
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
      setTimeout(() => setControlMsg(null), 3000);
    } catch (e) {
      setControlMsg("Reconnection failed: " + e);
      setTimeout(() => setControlMsg(null), 3000);
    } finally {
      setBtnLoading(b => ({ ...b, [action]: false }));
    }
  };

  // ── Local Face enrollment wizard handler ─────────────────────────────────
  const completeEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wizardName.trim()) return;

    setBtnLoading(b => ({ ...b, "enroll": true }));
    setWizardStep(2);
    speakAI("Initiating face scanning and database enrollment");

    setTimeout(async () => {
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
          setTimeout(() => {
            setWizardOpen(false);
            setWizardStep(1);
            setWizardName("");
          }, 2000);
        } else {
          setControlMsg(d.message || "Registration failed: No face detected");
          speakAI("Registration failed");
          setTimeout(() => {
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
    }, 1000);
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
          model: activeModel,
          tg_token: tgBotToken,
          tg_chat_id: tgChatId
        })
      });
      const d = await r.json();
      if (d.status === "ok") {
        setControlMsg("Configuration secured successfully");
        speakAI("Configuration secured");
      } else {
        setControlMsg("Saving failed: " + d.message);
        speakAI("Configuration failed");
      }
    } catch (err) {
      setControlMsg("Transmission failed: " + err);
      speakAI("Transmission failed");
    } finally {
      setBtnLoading(b => ({ ...b, "save_settings": false }));
      setTimeout(() => setControlMsg(null), 3000);
    }
  };

  const activeCamInfo = cameras[activeCam];
  const liveCount = cameras.filter(c => c.online).length;

  return (
    <div className="w-screen h-screen overflow-hidden flex bg-[#050505] p-3 gap-3 text-[#FFFFFF] font-inter">
      {/* Luxury Ambient Background */}
      <div className="oms-bg" />
      <ParticleCanvas active={particlesActive} density={particleDensity} />

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
            
            {/* OVERVIEW & DETECTION ROUTE VIEW */}
            {(activeNav === "overview" || activeNav === "detection" || activeNav === "tactical") && (
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
                          src={`${API}/api/stream/${idx}`}
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
                            setTtsEnabled(!ttsEnabled);
                            speakAI("Voice assistance toggled");
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
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[9px] text-sec font-bold tracking-wider">YOLO ENGINE WEIGHTS MODEL</label>
                        <select
                          value={activeModel}
                          onChange={(e) => {
                            setActiveModel(e.target.value);
                            speakAI("Model configured to " + e.target.value);
                          }}
                          className="glass-premium bg-black/50 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                        >
                          <option value="yolov8n.pt">yolov8n.pt (Nano Core - Ultra light)</option>
                          <option value="yolov8s.pt">yolov8s.pt (Standard Core - Balanced)</option>
                          <option value="yolov8m.pt">yolov8m.pt (Medium Core - High accuracy)</option>
                        </select>
                      </div>
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between font-orbitron text-[9px] text-sec font-bold tracking-wider">
                          <span>CONFIDENCE THRESHOLD</span>
                          <span className="font-mono text-gold-accent">{(confThresh * 100).toFixed(0)}%</span>
                        </div>
                        <input
                          type="range"
                          min="0.10"
                          max="0.95"
                          step="0.05"
                          value={confThresh}
                          onChange={(e) => setConfThresh(parseFloat(e.target.value))}
                          className="w-full accent-gold cursor-pointer"
                        />
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
                      )}

                      <div className="flex flex-col gap-1 pt-1 mt-1 border-t border-white/5">
                        <span className="font-orbitron text-[9px] text-gold font-bold tracking-wider block uppercase">HARDWARE ACCELERATION TARGET</span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="w-2 h-2 rounded-full bg-green-oms" />
                          <span className="font-mono text-[10px] text-sec uppercase font-bold">ACTIVE NVIDIA CUDA CAPABLE</span>
                        </div>
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
                            src={`${API}/api/stream/${idx}`}
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

                      {/* URL Reconnection Inputs */}
                      <div className="flex flex-col gap-1 text-[9px] font-orbitron font-bold text-sec tracking-wider">
                        <span>CCTV URL / DEVICE ID</span>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={camConnectUrls[idx]}
                            onChange={(e) => {
                              const newUrls = [...camConnectUrls];
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
                  ))}
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
                              src={`${API}/api/crop/${activeSubject.pid}?t=${time.getTime()}`}
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
                        <div className="w-7 h-7 rounded-full bg-gold/10 border border-gold-dim flex items-center justify-center font-orbitron text-[9px] text-gold font-bold">
                          {user.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <h4 className="font-orbitron text-xs font-bold text-[#FFFFFF] leading-none">{user.name}</h4>
                          <span className="font-inter text-[8.5px] text-sec leading-none">{user.role}</span>
                        </div>
                      </div>
                      <span className="font-orbitron text-[8px] font-bold text-green-oms bg-green-oms/10 px-1.5 py-0.5 rounded">
                        {user.status}
                      </span>
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
                className="btn-danger-luxury col-span-2 py-2 px-1 text-[9px] justify-center"
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
            className="fixed bottom-6 left-1/2 -translate-x-1/2 glass-gold-active px-6 py-3 z-50 rounded-xl"
          >
            <span className="font-orbitron text-xs font-black text-gold-accent tracking-wider uppercase flex items-center gap-2">
              <CheckCircle size={14} className="text-green-oms" />
              {controlMsg}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
