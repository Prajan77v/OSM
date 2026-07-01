"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Video, Shield, Cpu, HardDrive, Clock, Bell, Settings,
  Eye, Activity, MessageSquare, Send, Bot, AlertTriangle,
  UserPlus, UserCheck, Plus, X, Trash, RefreshCw, Mic,
  Maximize2, Minimize2, ChevronRight, Sliders, Database,
  TrendingUp, Play, Pause, Save, ToggleLeft, ToggleRight, Upload
} from "lucide-react";

const API = "";
const POSES = ["front", "back", "left", "right", "top", "bottom", "left_45", "right_45"];

interface CameraInfo {
  id: number; name: string; location: string; source?: string;
  online: boolean; disconnected: boolean; fps: number;
  persons: number; detections: number; threat_level: string; uptime: string;
  active_subjects?: any[]; detections_list?: any[];
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

export default function Dashboard() {
  const [activeCam, setActiveCam] = useState(0);
  const [cameras, setCameras] = useState<CameraInfo[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [activityData, setActivityData] = useState<any[]>([]);
  const [time, setTime] = useState(new Date());

  const [notification, setNotification] = useState<string | null>(null);
  const [controlMsg, setControlMsg] = useState<string | null>(null);
  const [btnLoading, setBtnLoading] = useState<Record<string, boolean>>({});

  // OS AI dialogue console states
  const [aiState, setAiState] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [aiSubText, setAiSubText] = useState("Awaiting voice command matrix...");
  const [voiceCommandText, setVoiceCommandText] = useState("");
  const [aiConversation, setAiConversation] = useState<Array<{ sender: "user" | "ai" | "system"; text: string; time: string }>>([
    { sender: "system" as const, text: "SENTINEL CORE: Neural nodes loaded. Dynamic surveillance arrays active.", time: new Date().toLocaleTimeString() }
  ]);

  // Modals
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);

  // Settings configurations
  const [opName, setOpName] = useState("Prajan");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [activeModel, setActiveModel] = useState("yolov8s.pt");
  const [confThresh, setConfThresh] = useState(0.45);
  const [tgBotToken, setTgBotToken] = useState("");
  const [tgChatId, setTgChatId] = useState("");
  const [detectNewIds, setDetectNewIds] = useState(true);
  const [useCuda, setUseCuda] = useState(true);
  const [detectPeople, setDetectPeople] = useState(true);
  const [detectObjects, setDetectObjects] = useState(true);
  const [matchThresh, setMatchThresh] = useState(0.36);
  const [particleSize, setParticleSize] = useState(3.0);
  const [meshThickness, setMeshThickness] = useState(1.0);

  // Enrollment states
  const [enrolledPeople, setEnrolledPeople] = useState<EnrolledUser[]>([]);
  const [enrollTab, setEnrollTab] = useState<"directory" | "guided" | "upload">("guided");
  const [guidedName, setGuidedName] = useState("");
  const [guidedPid, setGuidedPid] = useState("");
  const [guidedProgress, setGuidedProgress] = useState<Record<string, boolean>>({});
  const [guidedActivePoseIdx, setGuidedActivePoseIdx] = useState(0);
  const [guidedLog, setGuidedLog] = useState<string[]>([]);
  const [importName, setImportName] = useState("");
  const [importFolder, setImportFolder] = useState("");
  const [importLog, setImportLog] = useState<string[]>([]);
  const [uploadName, setUploadName] = useState("");
  const [uploadFiles, setUploadFiles] = useState<FileList | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadLog, setUploadLog] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Add Camera states
  const [newCamName, setNewCamName] = useState("");
  const [newCamSource, setNewCamSource] = useState("");
  const [newCamLocation, setNewCamLocation] = useState("");

  const [isFullscreen, setIsFullscreen] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const fetchAbortControllerRef = useRef<AbortController | null>(null);

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

  // ── Data Polling Loop ──────────────────────────────────────────────────────
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
        safeFetch(`${API}/api/faces`),
        safeFetch(`${API}/api/activity`),
      ]);

      const camRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const telRes = results[1].status === 'fulfilled' ? results[1].value : null;
      const evtRes = results[2].status === 'fulfilled' ? results[2].value : null;
      const facRes = results[3].status === 'fulfilled' ? results[3].value : null;
      const actRes = results[4].status === 'fulfilled' ? results[4].value : null;

      if (camRes) {
        setCameras(camRes);
      }

      if (telRes) {
        setTelemetry(telRes);
      }

      if (evtRes) {
        const sorted = evtRes.slice(-15).reverse();
        setEvents(sorted);

        // Convert events to Jarvis style conversation logs
        if (sorted.length > 0) {
          const latest = sorted[0];
          setAiConversation(prev => {
            const hasEvent = prev.some(m => m.text.includes(latest.detail));
            if (!hasEvent) {
              setNotification(`New Event: ${latest.detail}`);
              setTimeout(() => setNotification(null), 4000);
              
              return [...prev, {
                sender: "system" as const,
                text: `[${latest.event}] ${latest.detail} on camera node ${latest.camera}`,
                time: new Date().toLocaleTimeString()
              }].slice(-30);
            }
            return prev;
          });
        }
      }

      if (facRes && Array.isArray(facRes)) {
        const mapped: EnrolledUser[] = facRes.map((f: any) => ({
          name: f.name,
          pid: f.pid,
          visitCount: f.visit_count || 1,
          lastSeen: f.last_seen || "Just now",
          accuracy: f.accuracy || 98.4,
          role: f.known ? "OPERATOR" : "SUBJECT",
          status: f.in_scene ? "ACTIVE" : "OFFLINE",
          photo: f.photo
        }));
        setEnrolledPeople(mapped);
      }

      if (actRes && Array.isArray(actRes.persons)) {
        setActivityData(actRes.persons);
      }
    } catch {}
  }, []);

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

  // ── Speech Synthesis Output ────────────────────────────────────────────────
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

  // ── Voice Input Commands ───────────────────────────────────────────────────
  const sendVoiceCommand = async (command: string) => {
    if (!command.trim()) return;
    setAiState("processing");
    setAiSubText("Synthesizing core parameters...");

    setAiConversation(prev => [...prev, {
      sender: "user" as const,
      text: command,
      time: new Date().toLocaleTimeString()
    }]);

    try {
      const res = await fetch(`${API}/api/voice_control`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
      const data = await res.json();
      setAiState("speaking");
      setAiSubText("Sentinel OS outputting parameters...");
      speakAI(data.response);

      setAiConversation(prev => [...prev, {
        sender: "ai" as const,
        text: data.response,
        time: new Date().toLocaleTimeString()
      }]);

      setTimeout(() => {
        setAiState("idle");
        setAiSubText("Awaiting voice command matrix...");
      }, 5000);

      fetchAll();
    } catch {
      setAiState("idle");
      setAiSubText("Core command execution failed.");
    }
  };

  const handleVoiceSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!voiceCommandText.trim()) return;
    sendVoiceCommand(voiceCommandText);
    setVoiceCommandText("");
  };

  const saveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: opName,
          confidence: confThresh,
          model: activeModel,
          tg_token: tgBotToken,
          tg_chat_id: tgChatId,
          detect_new_ids: detectNewIds,
          use_cuda: useCuda,
          detect_people: detectPeople,
          detect_objects: detectObjects,
          match_threshold: matchThresh,
          particle_size: particleSize,
          mesh_thickness: meshThickness
        })
      });
      const data = await res.json();
      if (data.status === "ok") {
        setNotification("Engine configuration matrix updated.");
        setTimeout(() => setNotification(null), 4000);
        setIsSettingsModalOpen(false);
        fetchAll();
      }
    } catch {
      setNotification("Failed to apply configuration matrix.");
      setTimeout(() => setNotification(null), 4000);
    }
  };

  // ── Action Controls ────────────────────────────────────────────────────────
  const triggerControlAction = async (action: string) => {
    setBtnLoading(prev => ({ ...prev, [action]: true }));
    try {
      const r = await fetch(`${API}/api/control/${action}`, { method: "POST" });
      const d = await r.json();
      setControlMsg(d.message || `Action executed successfully.`);
      speakAI(d.message || "Executed command matrix");
      setTimeout(() => setControlMsg(null), 4000);
      fetchAll();
    } catch {
      setControlMsg("Command routing failed.");
      setTimeout(() => setControlMsg(null), 4000);
    } finally {
      setBtnLoading(prev => ({ ...prev, [action]: false }));
    }
  };

  // ── Enrollment Handlers ────────────────────────────────────────────────────
  const startGuidedEnrollment = async () => {
    if (!guidedName.trim()) return;
    setGuidedLog(["[SYSTEM] Connecting guided camera arrays..."]);
    try {
      const res = await fetch(`${API}/api/enroll/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: guidedName }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setGuidedPid(data.pid);
        setGuidedLog(prev => [...prev, `✓ Profile linked: ${data.pid}`, `- Position the object facing the camera for 'front' view`]);
        setGuidedProgress({});
        setGuidedActivePoseIdx(0);
      }
    } catch {
      setGuidedLog(prev => [...prev, "✗ Camera mapping error."]);
    }
  };

  const capturePose = async (pose: string) => {
    if (!guidedPid) return;
    setGuidedLog(prev => [...prev, `[PROCESS] Extracting camera parameters for view: ${pose.toUpperCase()}...`]);
    try {
      const res = await fetch(`${API}/api/enroll/capture/${guidedPid}/${pose}`, { method: "POST" });
      const data = await res.json();
      if (data.status === "ok") {
        setGuidedProgress(prev => ({ ...prev, [pose]: true }));
        setGuidedLog(prev => [...prev, `✓ Angle recorded: ${pose.toUpperCase()}`]);
        
        const nextIdx = guidedActivePoseIdx + 1;
        if (nextIdx < POSES.length) {
          setGuidedActivePoseIdx(nextIdx);
          setGuidedLog(prev => [...prev, `- Next: Position target for '${POSES[nextIdx]}' view`]);
        } else {
          setGuidedLog(prev => [...prev, `✓ All 8 pose vectors recorded successfully. Click COMPILE below.`]);
        }
      } else {
        setGuidedLog(prev => [...prev, `✗ Crop error: Target not centered in feed.`]);
      }
    } catch {
      setGuidedLog(prev => [...prev, "✗ Capture pipeline communication failure."]);
    }
  };

  const saveGuidedEnrollment = async () => {
    if (!guidedPid) return;
    setGuidedLog(prev => [...prev, "[PROCESS] Compiling object neural vectors..."]);
    try {
      const res = await fetch(`${API}/api/enroll/save/${guidedPid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: guidedName }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setGuidedLog(prev => [...prev, "✓ Neural profile created successfully!", "✓ Database compiled."]);
        setGuidedName("");
        setGuidedPid("");
        setGuidedProgress({});
        setGuidedActivePoseIdx(0);
        fetchAll();
      }
    } catch {
      setGuidedLog(prev => [...prev, "✗ Neural compile aborted."]);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadName.trim() || !uploadFiles || uploadFiles.length === 0) return;
    setUploadLoading(true);
    setUploadLog(["[SYSTEM] Packing files to upload vectors..."]);

    const imagePromises = Array.from(uploadFiles).map(file => {
      return new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          resolve(reader.result as string);
        };
        reader.readAsDataURL(file);
      });
    });

    const base64Images = await Promise.all(imagePromises);
    try {
      const res = await fetch(`${API}/api/enroll/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: uploadName, images: base64Images }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setUploadLog(prev => [
          ...prev, 
          `✓ Success: Enrolled '${uploadName}'!`, 
          `✓ Registered ID: ${data.pid}`
        ]);
        setUploadName("");
        setUploadFiles(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        fetchAll();
      } else {
        setUploadLog(prev => [...prev, `✗ Error: ${data.detail || "Upload aborted"}`]);
      }
    } catch {
      setUploadLog(prev => [...prev, "✗ Upload communication link failure."]);
    } finally {
      setUploadLoading(false);
    }
  };

  const runFolderImport = async () => {
    if (!importName.trim() || !importFolder.trim()) return;
    setImportLog(["[SYSTEM] Scanning folder matrix..."]);
    try {
      const res = await fetch(`${API}/api/enroll/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: importName, folder: importFolder }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setImportLog(prev => [
          ...prev, 
          `✓ Success: Folder import complete!`,
          `✓ Registered ID: ${data.pid}`,
          `✓ Vector frames loaded: ${data.images_processed}`
        ]);
        setImportName("");
        setImportFolder("");
        fetchAll();
      }
    } catch {
      setImportLog(prev => [...prev, "✗ Directory link mapping failure."]);
    }
  };

  const deleteProfile = async (pid: string) => {
    if (!confirm(`Are you sure you want to delete profile ${pid}?`)) return;
    try {
      const res = await fetch(`${API}/api/enroll/profile/${pid}`, { method: "DELETE" });
      const data = await res.json();
      if (data.status === "ok") {
        setNotification(`Profile deleted: ${pid}`);
        setTimeout(() => setNotification(null), 4000);
        fetchAll();
      }
    } catch {}
  };

  // ── Camera Administration ──────────────────────────────────────────────────
  const handleAddCamera = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCamName.trim() || !newCamSource.trim()) return;
    try {
      const r = await fetch(`${API}/api/camera/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newCamName, source: newCamSource, location: newCamLocation || "Lobby" }),
      });
      const d = await r.json();
      if (d.status === "ok") {
        setNewCamName("");
        setNewCamSource("");
        setNewCamLocation("");
        setIsCameraModalOpen(false);
        setNotification("Camera node registered successfully!");
        setTimeout(() => setNotification(null), 4000);
        fetchAll();
      }
    } catch {}
  };

  const handleRemoveCamera = async (idx: number) => {
    if (!confirm("Are you sure you want to remove this camera node?")) return;
    try {
      await fetch(`${API}/api/camera/${idx}/remove`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setNotification("Camera node deleted.");
      setTimeout(() => setNotification(null), 4000);
      fetchAll();
    } catch {}
  };

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

  // ── Neural Network Gold Particle Background ────────────────────────────────
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; radius: number }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      init();
    };

    const init = () => {
      particles = [];
      const density = 60;
      for (let i = 0; i < density; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          radius: Math.random() * 1.2 + 0.6
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;

        if (p1.x < 0 || p1.x > canvas.width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > canvas.height) p1.vy *= -1;

        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(212, 175, 55, 0.35)";
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist < 180) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(212, 175, 55, ${0.11 * (1 - dist / 180)})`;
            ctx.stroke();
          }
        }
      }
      animId = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  const activeCameraData = cameras[activeCam] || null;

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#020202] text-white flex flex-col font-inter z-0">
      
      {/* ── Neural Network Background Canvas ── */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none opacity-50" />
      <div className="absolute inset-0 z-0 pointer-events-none bg-radial-gradient from-transparent to-[#020202] opacity-90" />
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.02] bg-[linear-gradient(rgba(212,175,55,0.1)_1px,transparent_1px)_0_0_/_100%_20px,linear-gradient(90deg,rgba(212,175,55,0.1)_1px,transparent_1px)_0_0_/_20px_100%]" />

      {/* ── Top Bar floating glass capsule ── */}
      <header className="relative z-20 mx-6 mt-6 flex-shrink-0 flex items-center justify-between glass-premium px-8 py-3.5 border-white/5 rounded-full shadow-[0_20px_40px_rgba(0,0,0,0.7)]">
        
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-gold-accent animate-pulse shadow-[0_0_10px_#FFD700]" />
          <h1 className="font-orbitron text-xs font-black tracking-[0.25em] text-gold-accent">
            OMS.OS <span className="text-white/40">//</span> SENTINEL
          </h1>
        </div>

        {/* Telemetry Capsule Grid */}
        <div className="hidden lg:flex items-center gap-5">
          <div className="flex items-center gap-2 text-[10px] text-sec font-mono">
            <Cpu size={12} className="text-gold" />
            <span>GPU: {telemetry?.gpu || 0}%</span>
          </div>

          <div className="flex items-center gap-2 text-[10px] text-sec font-mono">
            <HardDrive size={12} className="text-gold" />
            <span>RAM: {telemetry?.ram || 0}%</span>
          </div>

          <div className="flex items-center gap-2 text-[10px] font-mono">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_6px_#00ff00]" />
            <span className="text-green-400">SYS STATUS: ACTIVE</span>
          </div>
        </div>

        {/* Clock & Operator profile */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sec">
            <Clock size={12} className="text-gold" />
            <span className="font-orbitron text-xs tracking-wider font-semibold">{time.toLocaleTimeString()}</span>
          </div>

          <div className="flex items-center gap-2 border-l border-white/10 pl-4">
            <div className="w-6.5 h-6.5 rounded-full bg-gold/15 border border-gold-dim flex items-center justify-center text-[10px] text-gold font-bold">
              {opName.charAt(0).toUpperCase()}
            </div>
            <span className="text-[10px] font-orbitron tracking-widest text-white/90 hidden sm:inline">{opName.toUpperCase()}</span>
          </div>

          <button 
            onClick={() => setIsSettingsModalOpen(true)}
            className="p-1 text-sec hover:text-white transition-colors"
          >
            <Settings size={14} />
          </button>
        </div>
      </header>

      {/* ── Left Floating Icon Dock ── */}
      <nav className="absolute left-6 top-32 bottom-32 w-16 z-20 flex flex-col items-center justify-between py-8 glass-premium border-white/5 shadow-2xl rounded-full hover:border-gold-dim/40 transition-all duration-300">
        <div className="flex flex-col gap-6 items-center">
          <button 
            onClick={() => setIsCameraModalOpen(true)}
            className="group relative p-3 rounded-full hover:bg-gold/15 hover:text-gold-accent transition-all duration-300 text-sec"
          >
            <Plus size={16} />
            <span className="absolute left-18 scale-0 group-hover:scale-100 bg-[#0d0d0d] border border-white/10 px-3 py-1.5 rounded text-[8px] tracking-widest font-orbitron transition-all duration-300 z-50">
              ADD NODE
            </span>
          </button>

          <button 
            onClick={() => setIsEnrollModalOpen(true)}
            className="group relative p-3 rounded-full hover:bg-gold/15 hover:text-gold-accent transition-all duration-300 text-sec"
          >
            <UserPlus size={16} />
            <span className="absolute left-18 scale-0 group-hover:scale-100 bg-[#0d0d0d] border border-white/10 px-3 py-1.5 rounded text-[8px] tracking-widest font-orbitron transition-all duration-300 z-50">
              ADD OBJECT
            </span>
          </button>

          <button 
            onClick={() => triggerControlAction("clear_logs")}
            className="group relative p-3 rounded-full hover:bg-gold/15 hover:text-gold-accent transition-all duration-300 text-sec"
          >
            <Trash size={16} />
            <span className="absolute left-18 scale-0 group-hover:scale-100 bg-[#0d0d0d] border border-white/10 px-3 py-1.5 rounded text-[8px] tracking-widest font-orbitron transition-all duration-300 z-50">
              CLEAR LOGS
            </span>
          </button>
        </div>

        <button 
          onClick={() => triggerControlAction("trigger_alarm")}
          className="group relative p-3 bg-red-500/10 hover:bg-red-500/25 border border-red-500/20 hover:border-red-500 text-red-400 rounded-full transition-all duration-300"
        >
          <AlertTriangle size={16} />
          <span className="absolute left-18 scale-0 group-hover:scale-100 bg-[#0d0d0d] border border-white/10 px-3 py-1.5 rounded text-[8px] tracking-widest font-orbitron transition-all duration-300 z-50">
            TRIGGER ALARM
          </span>
        </button>
      </nav>

      {/* ── Main Workspace ── */}
      <div className="flex-1 pl-28 pr-6 pt-6 pb-6 flex flex-col xl:flex-row gap-6 min-h-0 relative z-10">
        
        {/* Left/Center Area: Large Floating AI Camera feed (Takes 65% width) */}
        <section className="flex-1 flex flex-col gap-6 min-h-0">
          
          {/* Node selection cap-rail */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
            {cameras.map((c, idx) => (
              <button
                key={c.id}
                onClick={() => setActiveCam(idx)}
                className={`px-6 py-2.5 rounded-full font-orbitron text-[9px] tracking-widest transition-all duration-300 flex items-center gap-2 border ${
                  activeCam === idx 
                    ? "bg-gold/10 border-gold-accent text-gold-accent shadow-[0_0_12px_rgba(212,175,55,0.15)] font-bold" 
                    : "glass-premium border-white/5 text-sec hover:text-white"
                }`}
              >
                <Video size={10} />
                {c.name.toUpperCase()}
                {c.online ? (
                  <span className="w-1 h-1 rounded-full bg-green-400 animate-pulse" />
                ) : (
                  <span className="w-1 h-1 rounded-full bg-red-400 animate-pulse" />
                )}
              </button>
            ))}
          </div>

          {/* Floating AI Camera Hero Element */}
          <div ref={viewportRef} className="flex-1 glass-premium border-white/5 shadow-[0_24px_80px_rgba(0,0,0,0.85)] flex flex-col justify-between overflow-hidden relative group" style={{ borderRadius: 28 }}>
            
            {/* Overlay: HUD top parameters */}
            <div className="absolute top-5 left-5 right-5 z-10 pointer-events-none flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="glass-premium px-4 py-1.5 rounded-full text-[9px] font-orbitron tracking-widest border-white/10 bg-black/40 text-white/90">
                  CAMERA: {activeCameraData?.name.toUpperCase() || "LOBBY"}
                </div>
                <div className="glass-premium px-3.5 py-1.5 rounded-full text-[9px] font-orbitron tracking-widest border-white/10 bg-black/40 text-sec">
                  LOC: {activeCameraData?.location.toUpperCase() || "MAIN ENTRANCE SECTOR"}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="glass-premium px-3.5 py-1.5 rounded-full text-[9px] font-orbitron tracking-widest border-white/10 bg-black/40 text-sec flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                  REC ACTIVE
                </div>
                <button 
                  onClick={toggleFullscreen}
                  className="pointer-events-auto glass-premium p-1.5 rounded-full border-white/10 bg-black/40 text-sec hover:text-white transition-all duration-300"
                >
                  {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
                </button>
              </div>
            </div>

            {/* Video feed container */}
            <div className="absolute inset-0 w-full h-full bg-[#050505]/40 flex items-center justify-center overflow-hidden">
              {activeCameraData?.online ? (
                <>
                  <img
                    src={`${API}/api/stream/${activeCam}`}
                    alt="OMS Live Video Feed"
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.01]"
                  />
                  
                  {/* Cyberpunk HUD Scanning Reticle Overlay */}
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <svg className="w-32 h-32 opacity-25 text-gold-accent animate-[spin_25s_linear_infinite]" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="0.5" fill="none" strokeDasharray="5,15" />
                      <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="1" fill="none" strokeDasharray="25,10" />
                    </svg>
                    <svg className="absolute w-40 h-40 opacity-10 text-gold animate-[spin_35s_linear_infinite_reverse]" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="48" stroke="currentColor" strokeWidth="0.5" fill="none" strokeDasharray="1,5" />
                    </svg>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center gap-3 text-sec font-orbitron text-xs tracking-widest">
                  <AlertTriangle size={32} className="text-red-500 animate-pulse" />
                  <span>CAMERA NODE IS OFFLINE</span>
                  <p className="font-inter text-[9px] text-muted tracking-normal">Check source configuration or link parameters</p>
                </div>
              )}
            </div>

            {/* Overlay: HUD bottom parameters */}
            <div className="absolute bottom-5 left-5 right-5 z-10 pointer-events-none flex items-center justify-between">
              <div className="glass-premium px-4 py-2 rounded-full text-[9px] font-orbitron tracking-widest border-white/10 bg-black/40 text-sec flex items-center gap-2">
                <Shield size={10} className="text-gold" />
                THREAT SHIELD: <span className={activeCameraData?.threat_level === "RED" ? "text-red-400 font-bold" : "text-green-400"}>{activeCameraData?.threat_level || "GREEN"}</span>
              </div>

              <div className="glass-premium px-4 py-2 rounded-full text-[9px] font-orbitron tracking-widest border-white/10 bg-black/40 text-sec flex items-center gap-3 font-mono">
                <span>FPS: {activeCameraData?.fps || 0}</span>
                <span>DETS: {activeCameraData?.detections || 0}</span>
              </div>
            </div>
          </div>

        </section>

        {/* Right Area: Target Intelligence Cards panel */}
        <section className="w-96 flex flex-col gap-6 flex-shrink-0 min-h-0">
          
          {/* OS AI Core spinner */}
          <div className="glass-premium p-5 flex flex-col items-center justify-center text-center gap-4 border-white/5 relative overflow-hidden" style={{ borderRadius: 24 }}>
            <h4 className="font-orbitron text-[9px] font-bold text-gold tracking-[0.2em] uppercase">SENTINEL AI OS CORE</h4>
            
            <div className="relative w-28 h-28 flex items-center justify-center">
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 border border-dashed border-gold-dim rounded-full opacity-60"
              />
              <motion.div 
                animate={{ rotate: -360 }}
                transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                className="absolute inset-2 border border-dotted border-gold-accent rounded-full opacity-30"
              />
              <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500 ${
                aiState === "listening" ? "bg-red-500/20 shadow-[0_0_25px_rgba(239,68,68,0.4)]" :
                aiState === "processing" ? "bg-cyan-500/20 shadow-[0_0_25px_rgba(6,182,212,0.4)]" :
                aiState === "speaking" ? "bg-gold/20 shadow-[0_0_25px_rgba(212,175,55,0.4)] animate-pulse" :
                "bg-gold/5 border border-gold-dim/40"
              }`}>
                <Bot size={22} className={aiState === "speaking" ? "text-gold-accent" : "text-white/80"} />
              </div>
            </div>

            <div className="flex flex-col gap-0.5">
              <span className="font-orbitron text-[10px] tracking-widest text-gold-accent uppercase">{aiState.toUpperCase()} STATE</span>
              <p className="text-[9px] text-sec max-w-[200px] leading-relaxed truncate">{aiSubText}</p>
            </div>
          </div>

          {/* Active Target Detections List */}
          <div className="flex-1 glass-premium p-5 flex flex-col min-h-0 border-white/5" style={{ borderRadius: 24 }}>
            <h4 className="font-orbitron text-[10px] font-bold text-gold tracking-wider uppercase border-b border-white/5 pb-2.5 mb-3 flex-shrink-0 flex items-center gap-2">
              <Activity size={12} className="text-gold" /> LIVE RECOGNITION VECTORS
            </h4>

            <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1 scrollbar-thin">
              {activityData.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
                  <p className="text-[9px] text-muted font-orbitron tracking-widest uppercase">// No targets detected in scope</p>
                </div>
              ) : (
                activityData.map((act) => (
                  <div key={act.pid} className="glass-premium p-3 border-white/5 bg-white/[0.01] hover:border-gold-dim/40 transition-colors duration-300" style={{ borderRadius: 16 }}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                        <span className="font-orbitron text-[11px] font-bold text-white uppercase tracking-wider">{act.name}</span>
                      </div>
                      <span className="font-mono text-[9px] text-gold-accent bg-gold/10 px-1.5 py-0.5 rounded-md">ID:{act.pid}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-y-1 gap-x-2 text-[9px] text-sec font-mono">
                      <div className="flex items-center gap-1">
                        <Activity size={10} className="text-gold" />
                        <span>{act.activity_label}</span>
                      </div>
                      <div className="flex items-center gap-1 justify-end">
                        <Shield size={10} className="text-gold" />
                        <span>ATTN: {act.attention}</span>
                      </div>
                      <div className="text-muted col-span-2 text-right mt-1 border-t border-white/5 pt-1">
                        ACTIVE: {act.duration_str}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </section>
      </div>

      {/* ── Bottom Panel ChatGPT-style Console ── */}
      <footer className="relative z-10 mx-6 mb-6 flex-shrink-0 grid grid-cols-1 xl:grid-cols-4 gap-6 items-end">
        
        {/* Conversation Feed */}
        <div className="xl:col-span-3 glass-premium p-5 flex flex-col border-white/5 h-44" style={{ borderRadius: 24 }}>
          <h4 className="font-orbitron text-[9px] font-bold text-gold tracking-widest uppercase border-b border-white/5 pb-2 mb-2 flex-shrink-0 flex items-center gap-1.5">
            <MessageSquare size={12} className="text-gold" /> CORE SENTINEL DIALOGUE INDEX
          </h4>
          
          <div className="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-2 scrollbar-thin font-mono text-[10px]">
            {aiConversation.map((msg, i) => (
              <div 
                key={i} 
                className={`flex gap-2 items-start py-0.5 ${
                  msg.sender === "user" ? "text-gold" : 
                  msg.sender === "ai" ? "text-cyan" : 
                  "text-muted"
                }`}
              >
                <span className="text-white/20 select-none">[{msg.time}]</span>
                <span className="font-bold uppercase tracking-wider select-none">
                  {msg.sender === "user" ? "OP:" : msg.sender === "ai" ? "AI:" : "SYS:"}
                </span>
                <p className="flex-1 whitespace-pre-wrap">{msg.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Voice prompt capsule */}
        <div className="glass-premium p-5 flex flex-col justify-between border-white/5 h-44" style={{ borderRadius: 24 }}>
          <div className="flex flex-col gap-1">
            <span className="font-orbitron text-[9px] text-gold tracking-widest uppercase">VOICE PROMPT CAPSULE</span>
            <p className="text-[8px] text-muted">Submit voice parameters or core commands below.</p>
          </div>

          <form onSubmit={handleVoiceSubmit} className="relative mt-2">
            <input 
              type="text" 
              value={voiceCommandText}
              onChange={(e) => setVoiceCommandText(e.target.value)}
              placeholder="Enter voice command matrix..."
              className="w-full glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs pl-4 pr-10 py-3 rounded-full outline-none focus:border-gold-accent transition-colors"
            />
            <button 
              type="submit"
              className="absolute right-1 top-1 p-2 bg-gold/10 hover:bg-gold text-gold-accent hover:text-black rounded-full transition-all duration-300"
            >
              <Send size={12} />
            </button>
          </form>

          {/* Prompt quick actions */}
          <div className="flex flex-wrap gap-1.5 mt-2 overflow-x-auto scrollbar-none max-h-12 py-1">
            {["/trigger alarm", "/clear logs", "/status", "/add camera"].map((cmd) => (
              <button 
                key={cmd}
                onClick={() => {
                  if (cmd === "/trigger alarm") triggerControlAction("trigger_alarm");
                  else if (cmd === "/clear logs") triggerControlAction("clear_logs");
                  else if (cmd === "/add camera") setIsCameraModalOpen(true);
                  else setVoiceCommandText(cmd);
                }}
                className="glass-premium px-3 py-1 rounded-full text-[8px] font-mono border-white/5 text-muted hover:text-gold-accent hover:border-gold-dim transition-all duration-300"
              >
                {cmd}
              </button>
            ))}
          </div>
        </div>
      </footer>

      {/* ── MODAL: ENROLLMENT DIALOGUE ── */}
      <AnimatePresence>
        {isEnrollModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-4xl max-h-[85vh] glass-premium border-white/10 bg-black/80 flex flex-col p-6 overflow-hidden relative shadow-[0_0_50px_rgba(212,175,55,0.1)]"
              style={{ borderRadius: 28 }}
            >
              <button 
                onClick={() => setIsEnrollModalOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-full glass-premium hover:border-gold hover:text-gold-accent transition-all duration-300 border-white/5 text-sec"
              >
                <X size={16} />
              </button>

              <h3 className="font-orbitron text-sm font-black text-gold-accent tracking-widest uppercase mb-4 flex items-center gap-2">
                <UserPlus size={16} /> ADVANCED OBJECT ENROLLMENT PROTOCOLS
              </h3>

              <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
                {[
                  { id: "directory", label: "DIRECTORY SCAN" },
                  { id: "guided", label: "GUIDED CAPTURE" },
                  { id: "upload", label: "IMAGE UPLOAD" }
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setEnrollTab(t.id as any)}
                    className={`px-4 py-2 rounded-full font-orbitron text-[9px] tracking-widest border transition-all duration-300 ${
                      enrollTab === t.id 
                        ? "bg-gold/10 border-gold text-gold-accent" 
                        : "glass-premium border-white/5 text-sec hover:text-white"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin min-h-[300px]">
                {enrollTab === "directory" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-1">
                    <div className="glass-premium p-5 flex flex-col justify-center bg-black/20 gap-4 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-black text-gold tracking-widest uppercase text-center mb-1">LOCAL FOLDER SCAN MATRIX</h4>
                      
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">TARGET OBJECT NAME</label>
                        <input
                          type="text"
                          required
                          value={importName}
                          onChange={(e) => setImportName(e.target.value)}
                          placeholder="e.g. Mug A"
                          className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">LOCAL DIRECTORY PATH</label>
                        <input
                          type="text"
                          required
                          value={importFolder}
                          onChange={(e) => setImportFolder(e.target.value)}
                          placeholder="e.g. C:\Users\Prajan\Desktop\mug_images"
                          className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>

                      <button
                        onClick={runFolderImport}
                        disabled={!importName.trim() || !importFolder.trim()}
                        className="py-3 glass-premium border-gold-dim hover:border-gold hover:text-gold-accent font-orbitron text-[10px] tracking-widest rounded-full w-full"
                      >
                        RUN FOLDER IMPORT
                      </button>
                    </div>

                    <div className="glass-premium p-5 bg-black/20 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-bold text-gold tracking-widest uppercase mb-3 pb-2 border-b border-white/5">PROCESSING STREAM FEED</h4>
                      <div className="glass-premium bg-black/60 border border-white/5 p-4 flex flex-col font-mono text-[9px] min-h-[160px]" style={{ borderRadius: 12 }}>
                        <div className="flex-1 overflow-y-auto flex flex-col gap-1 text-sec">
                          {importLog.map((log, i) => (
                            <p key={i} className={log.startsWith("✓") ? "text-green-400" : log.startsWith("✗") ? "text-red-400" : "text-muted"}>
                              {log}
                            </p>
                          ))}
                          {importLog.length === 0 && <p className="text-muted">// Ready. Select directory path and object name.</p>}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {enrollTab === "guided" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-1">
                    <div className="glass-premium p-5 flex flex-col bg-black/20 gap-4 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-black text-gold tracking-widest uppercase text-center mb-1">GUIDED SNAPSHOT CALIBRATOR</h4>
                      
                      {!guidedPid ? (
                        <div className="flex flex-col gap-4">
                          <div className="flex flex-col gap-1.5">
                            <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">TARGET OBJECT NAME</label>
                            <input
                              type="text"
                              required
                              value={guidedName}
                              onChange={(e) => setGuidedName(e.target.value)}
                              placeholder="e.g. Blue Coffee Mug"
                              className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                            />
                          </div>

                          <button
                            onClick={startGuidedEnrollment}
                            disabled={!guidedName.trim()}
                            className="py-3 glass-premium border-gold-dim hover:border-gold hover:text-gold-accent font-orbitron text-[10px] tracking-widest rounded-full"
                          >
                            INITIATE SCANNER
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col gap-4">
                          <div className="flex items-center justify-between border-b border-white/5 pb-2">
                            <span className="font-orbitron text-[10px] text-sec">ACTIVE POSE TARGET:</span>
                            <span className="font-mono text-xs text-gold-accent bg-gold/10 px-2 py-0.5 rounded uppercase font-bold">
                              {POSES[guidedActivePoseIdx]}
                            </span>
                          </div>

                          <p className="text-[9px] text-muted leading-relaxed">
                            Place the target object centered in the active camera viewport, rotating it as requested. Click CAPTURE below.
                          </p>

                          <div className="grid grid-cols-2 gap-2">
                            <button
                              onClick={() => capturePose(POSES[guidedActivePoseIdx])}
                              className="py-3 bg-gold text-black hover:bg-gold-accent transition-all duration-300 font-orbitron text-[10px] tracking-widest rounded-full flex items-center justify-center gap-1.5"
                            >
                              <Maximize2 size={12} />
                              CAPTURE VIEW
                            </button>
                            <button
                              onClick={saveGuidedEnrollment}
                              disabled={Object.keys(guidedProgress).length === 0}
                              className="py-3 glass-premium border-gold-dim hover:border-gold hover:text-gold-accent font-orbitron text-[10px] tracking-widest rounded-full flex items-center justify-center gap-1.5"
                            >
                              <Save size={12} />
                              SAVE & COMPILE
                            </button>
                          </div>

                          <div className="grid grid-cols-4 gap-1.5 mt-2">
                            {POSES.map((pose) => (
                              <div 
                                key={pose} 
                                className={`py-1.5 rounded-lg text-[8px] font-mono tracking-widest text-center border ${
                                  guidedProgress[pose] 
                                    ? "bg-green-500/10 border-green-400 text-green-400" 
                                    : "glass-premium border-white/5 text-muted"
                                }`}
                              >
                                {pose.toUpperCase()}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="glass-premium p-5 bg-black/20 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-bold text-gold tracking-widest uppercase mb-3 pb-2 border-b border-white/5">GUIDED TELEMETRY STREAM</h4>
                      <div className="glass-premium bg-black/60 border border-white/5 p-4 flex flex-col font-mono text-[9px] min-h-[220px]" style={{ borderRadius: 12 }}>
                        <div className="flex-1 overflow-y-auto flex flex-col gap-1 text-sec">
                          {guidedLog.map((log, i) => (
                            <p key={i} className={log.startsWith("✓") ? "text-green-400" : log.startsWith("✗") ? "text-red-400" : "text-muted"}>
                              {log}
                            </p>
                          ))}
                          {guidedLog.length === 0 && <p className="text-muted">// Ready. Enter object name to link parameters.</p>}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {enrollTab === "upload" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-1">
                    <form onSubmit={handleFileUpload} className="glass-premium p-5 flex flex-col justify-center bg-black/20 gap-4 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-black text-gold tracking-widest uppercase text-center mb-1">IMAGE FILE UPLOADER</h4>
                      
                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">OBJECT NAME</label>
                        <input
                          type="text"
                          required
                          value={uploadName}
                          onChange={(e) => setUploadName(e.target.value)}
                          placeholder="e.g. Office Chair A"
                          className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">SELECT OBJECT IMAGES (MAX 8)</label>
                        <input
                          type="file"
                          multiple
                          accept="image/*"
                          onChange={(e) => setUploadFiles(e.target.files)}
                          className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors file:bg-gold/10 file:border-none file:text-gold-accent file:font-orbitron file:text-[9px] file:font-bold file:px-2.5 file:py-1 file:rounded-lg"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={uploadLoading || !uploadName.trim() || !uploadFiles || uploadFiles.length === 0}
                        className="py-3 bg-gold text-black hover:bg-gold-accent transition-all duration-300 font-orbitron text-[10px] tracking-widest rounded-full flex items-center justify-center gap-1.5 mt-2"
                      >
                        {uploadLoading ? (
                          <RefreshCw size={14} className="animate-spin text-black" />
                        ) : (
                          <Upload size={14} />
                        )}
                        UPLOAD & ENROLL OBJECT
                      </button>
                    </form>

                    <div className="glass-premium p-5 bg-black/20 border-white/5" style={{ borderRadius: 20 }}>
                      <h4 className="font-orbitron text-[10px] font-bold text-gold tracking-widest uppercase mb-3 pb-2 border-b border-white/5">SECURE UPLOAD PROCESSING</h4>
                      <div className="glass-premium bg-black/60 border border-white/5 p-4 flex flex-col font-mono text-[9px] min-h-[220px]" style={{ borderRadius: 12 }}>
                        <div className="flex-1 overflow-y-auto flex flex-col gap-1 text-sec">
                          {uploadLog.map((log, i) => (
                            <p key={i} className={log.startsWith("✓") ? "text-green-400" : log.startsWith("✗") ? "text-red-400" : "text-muted"}>
                              {log}
                            </p>
                          ))}
                          {uploadLog.length === 0 && <p className="text-muted">// Ready. Select images and specify object name to execute upload.</p>}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── MODAL: CAMERA MANAGEMENT ── */}
      <AnimatePresence>
        {isCameraModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg glass-premium border-white/10 bg-black/80 flex flex-col p-6 overflow-hidden relative shadow-[0_0_50px_rgba(212,175,55,0.1)]"
              style={{ borderRadius: 28 }}
            >
              <button 
                onClick={() => setIsCameraModalOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-full glass-premium hover:border-gold hover:text-gold-accent transition-all duration-300 border-white/5 text-sec"
              >
                <X size={16} />
              </button>

              <h3 className="font-orbitron text-sm font-black text-gold-accent tracking-widest uppercase mb-4 flex items-center gap-2">
                <Video size={16} /> REGISTER CAMERA NODE
              </h3>

              <form onSubmit={handleAddCamera} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">NODE NAME</label>
                  <input
                    type="text"
                    required
                    value={newCamName}
                    onChange={(e) => setNewCamName(e.target.value)}
                    placeholder="e.g. Lab Front Cam 03"
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">VIDEO SOURCE PATH / RTSP FEED URL</label>
                  <input
                    type="text"
                    required
                    value={newCamSource}
                    onChange={(e) => setNewCamSource(e.target.value)}
                    placeholder="e.g. rtsp://192.168.1.100:554/stream1 or 0 for Webcam"
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">LOCATION</label>
                  <input
                    type="text"
                    value={newCamLocation}
                    onChange={(e) => setNewCamLocation(e.target.value)}
                    placeholder="e.g. Computer Science Lab"
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-3 rounded-xl outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex gap-3 mt-2">
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-gold text-black hover:bg-gold-accent transition-all duration-300 font-orbitron text-[10px] tracking-widest rounded-full"
                  >
                    LINK CAMERA NODE
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsCameraModalOpen(false)}
                    className="flex-1 py-3 glass-premium border-white/5 hover:border-gold hover:text-gold-accent font-orbitron text-[10px] tracking-widest rounded-full"
                  >
                    CANCEL
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── MODAL: SYSTEM PARAMETER CONFIGURATION ── */}
      <AnimatePresence>
        {isSettingsModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-2xl glass-premium border-white/10 bg-black/80 flex flex-col p-6 overflow-hidden relative shadow-[0_0_50px_rgba(212,175,55,0.1)]"
              style={{ borderRadius: 28 }}
            >
              <button 
                onClick={() => setIsSettingsModalOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-full glass-premium hover:border-gold hover:text-gold-accent transition-all duration-300 border-white/5 text-sec"
              >
                <X size={16} />
              </button>

              <h3 className="font-orbitron text-sm font-black text-gold-accent tracking-widest uppercase mb-4 flex items-center gap-2">
                <Settings size={16} /> SENTINEL ENGINE PARAMETERS
              </h3>

              <form onSubmit={saveSettings} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">OPERATOR USERNAME</label>
                  <input
                    type="text"
                    value={opName}
                    onChange={(e) => setOpName(e.target.value)}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">CONFIDENCE THRESHOLD</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.0"
                    value={confThresh}
                    onChange={(e) => setConfThresh(parseFloat(e.target.value))}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">ACTIVE YOLO MODEL</label>
                  <input
                    type="text"
                    value={activeModel}
                    onChange={(e) => setActiveModel(e.target.value)}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">MATCH ACCURACY THRESHOLD</label>
                  <input
                    type="number"
                    step="0.02"
                    min="0.1"
                    max="1.0"
                    value={matchThresh}
                    onChange={(e) => setMatchThresh(parseFloat(e.target.value))}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">TELEGRAM BOT TOKEN</label>
                  <input
                    type="text"
                    value={tgBotToken}
                    onChange={(e) => setTgBotToken(e.target.value)}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-orbitron text-[8.5px] text-sec font-bold tracking-wider">TELEGRAM CHAT ID</label>
                  <input
                    type="text"
                    value={tgChatId}
                    onChange={(e) => setTgChatId(e.target.value)}
                    className="glass-premium bg-black/60 border border-white/10 text-white font-mono text-xs px-4 py-2.5 rounded-lg outline-none focus:border-gold-accent transition-colors"
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 glass-premium border-white/5 rounded-lg">
                  <span className="font-orbitron text-[9px] text-sec tracking-wider">DETECT PEOPLE</span>
                  <button 
                    type="button" 
                    onClick={() => setDetectPeople(!detectPeople)}
                    className="text-gold-accent"
                  >
                    {detectPeople ? <ToggleRight size={24} /> : <ToggleLeft size={24} className="text-muted" />}
                  </button>
                </div>

                <div className="flex items-center justify-between p-2.5 glass-premium border-white/5 rounded-lg">
                  <span className="font-orbitron text-[9px] text-sec tracking-wider">DETECT PHYSICAL OBJECTS</span>
                  <button 
                    type="button" 
                    onClick={() => setDetectObjects(!detectObjects)}
                    className="text-gold-accent"
                  >
                    {detectObjects ? <ToggleRight size={24} /> : <ToggleLeft size={24} className="text-muted" />}
                  </button>
                </div>

                <div className="flex items-center justify-between p-2.5 glass-premium border-white/5 rounded-lg">
                  <span className="font-orbitron text-[9px] text-sec tracking-wider">CUDA HARDWARE ACCEL</span>
                  <button 
                    type="button" 
                    onClick={() => setUseCuda(!useCuda)}
                    className="text-gold-accent"
                  >
                    {useCuda ? <ToggleRight size={24} /> : <ToggleLeft size={24} className="text-muted" />}
                  </button>
                </div>

                <div className="flex items-center justify-between p-2.5 glass-premium border-white/5 rounded-lg">
                  <span className="font-orbitron text-[9px] text-sec tracking-wider">AUTO REBUILD DETECTIONS</span>
                  <button 
                    type="button" 
                    onClick={() => setDetectNewIds(!detectNewIds)}
                    className="text-gold-accent"
                  >
                    {detectNewIds ? <ToggleRight size={24} /> : <ToggleLeft size={24} className="text-muted" />}
                  </button>
                </div>

                <div className="col-span-1 md:col-span-2 flex gap-3 mt-4">
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-gold text-black hover:bg-gold-accent transition-all duration-300 font-orbitron text-[10px] tracking-widest rounded-full"
                  >
                    APPLY CONFIG MATRIX
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsSettingsModalOpen(false)}
                    className="flex-1 py-3 glass-premium border-white/5 hover:border-gold hover:text-gold-accent font-orbitron text-[10px] tracking-widest rounded-full"
                  >
                    CANCEL
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
