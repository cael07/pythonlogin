<template>
  <div class="fc-root">

    <!-- ── Loading models ────────────────────────── -->
    <div v-if="uiState === 'loading'" class="fc-center">
      <div class="spinner"></div>
      <p class="fc-hint">{{ hint }}</p>
    </div>

    <!-- ── Camera error ───────────────────────────── -->
    <div v-else-if="uiState === 'error'" class="fc-center fc-error-state">
      <div class="fc-icon-wrap error">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
      </div>
      <p class="fc-hint error">{{ hint }}</p>
      <button class="btn btn-ghost" style="margin-top:1rem;" @click="init">Try Again</button>
    </div>

    <!-- ── Camera active ──────────────────────────── -->
    <div v-show="uiState === 'scanning'" class="fc-camera-section">
      <div class="fc-video-wrap" :class="{ 'face-aligned': faceAligned, 'scan-success': isScanSuccess }">
        <div class="fc-video-container">
          <video ref="videoEl" class="fc-video" autoplay muted playsinline></video>
          
          <!-- SVG Overlay Outline -->
          <svg class="fc-overlay" viewBox="0 0 100 100">
            <circle 
              cx="50" cy="50" r="46" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="1.5" 
              stroke-dasharray="289"
              :stroke-dashoffset="faceAligned ? 0 : 289"
              class="fc-outline-path"
            />
          </svg>
        </div>
        
        <!-- Pose HUD -->
        <div class="fc-pose-hud">
          <Transition name="fade-scale" mode="out-in">
            <div
              :key="isScanSuccess ? 'countdown-' + faceCountdown : currentStepKey"
              class="fc-pose-step pulse"
              :class="{ success: isScanSuccess }"
            >
              <span v-if="isScanSuccess && faceCountdown > 0">{{ faceCountdown }}</span>
              <span v-else>{{ stepLabels[currentStepIdx] || 'Success!' }}</span>
            </div>
          </Transition>
        </div>
      </div>

      <!-- Instruction bar -->
      <div class="fc-instruction-bar" :class="{ 'success': isScanSuccess }">
        <div class="fc-instruction-icon">
          <Transition name="fade" mode="out-in">
            <span :key="isScanSuccess ? 'countdown-' + faceCountdown : currentStepIdx">
              <span v-if="isScanSuccess && faceCountdown > 0">🕒</span>
              <span v-else-if="isScanSuccess">✅</span>
              <span v-else-if="!faceAligned">👁</span>
              <span v-else-if="currentStepIdx === 0">⬅️</span>
              <span v-else-if="currentStepIdx === 1">➡️</span>
              <span v-else-if="currentStepIdx === 2">🎯</span>
              <span v-else>📸</span>
            </span>
          </Transition>
        </div>
        <Transition name="slide-fade" mode="out-in">
          <p :key="hint" class="fc-instruction-text">{{ hint }}</p>
        </Transition>
      </div>
    </div>

    <!-- ── Captured ────────────────────────────────── -->
    <div v-if="uiState === 'captured'" class="fc-captured-section">
      <div class="fc-captured-frame">
        <img :src="capturedImg" alt="Your captured face" class="fc-captured-img" />
        <div class="fc-captured-badge">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </div>
      </div>
      <!-- <p class="fc-captured-label">Face verified! ✓</p> -->
      <button class="btn btn-ghost fc-retake-btn" @click="retake">↩ Retake photo</button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
    FaceLandmarker,
    FilesetResolver,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14"

const emit = defineEmits(['captured'])

/* ── Configuration ──────────────────────────────────────── */
const FLIP_LR = false
const TURN_HI = 0.62      // head clearly turned to one side
const TURN_LO = 0.38      // head clearly turned to the other side
const FRONT_MIN = 0.44    // facing forward band
const FRONT_MAX = 0.56
const FRONT_HOLD_MS = 600    // must hold "front" this long before countdown
const COUNTDOWN_MS = 2000    // 2·1
const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

/* ── State ──────────────────────────────────────────────── */
const uiState = ref('loading')
const hint = ref('Loading face model…')
const faceAligned = ref(false)
const isScanSuccess = ref(false)
const faceCountdown = ref(0)
const capturedImg = ref(null)
const currentStepIdx = ref(0)
const stepLabels = ['⬅️ Turn your head to the LEFT', '➡️ Turn your head to the RIGHT', '🙂 Now face the camera']

/* ── Template refs ──────────────────────────────────────– */
const videoEl = ref(null)

/* ── Internals ──────────────────────────────────────────── */
let landmarker = null
let stream = null
let rafId = null
let stopFlag = false
let stepDefs = []
let stepsCompleted = []
let frontHeldSince = 0
let counting = false
let countStart = 0
let countdownLastShown = -1

const currentStepKey = () => stepDefs[currentStepIdx.value]?.key || 'unknown'

async function ensureLandmarker() {
    if (landmarker) return landmarker
    const fileset = await FilesetResolver.forVisionTasks(WASM_URL)
    try {
        landmarker = await FaceLandmarker.createFromOptions(fileset, {
            baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
            runningMode: "VIDEO",
            numFaces: 1,
        })
    } catch (_) {
        landmarker = await FaceLandmarker.createFromOptions(fileset, {
            baseOptions: { modelAssetPath: MODEL_URL, delegate: "CPU" },
            runningMode: "VIDEO",
            numFaces: 1,
        })
    }
    return landmarker
}

function yawRatio(lm) {
    const nose = lm[1]
    const left = lm[234]
    const right = lm[454]
    const denom = (right.x - left.x) || 1e-6
    return (nose.x - left.x) / denom
}

function captureFrame(video, canvas) {
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL("image/jpeg", 0.92)
}

function isFront(p) {
    return p !== null && p >= FRONT_MIN && p <= FRONT_MAX
}

function cleanup() {
    stopFlag = true
    if (rafId) cancelAnimationFrame(rafId)
    try { stream?.getTracks().forEach((t) => t.stop()) } catch (_) {}
    if (videoEl.value) videoEl.value.srcObject = null
    stream = null
}

async function detectionLoop() {
    if (stopFlag) return
    
    const video = videoEl.value
    if (!video) return

    let res = null
    try { res = landmarker.detectForVideo(video, performance.now()) } catch (_) {}
    const hasFace = !!(res?.faceLandmarks?.length)
    const p = hasFace ? yawRatio(res.faceLandmarks[0]) : null

    // ── During countdown: face must stay present and front
    if (counting) {
        if (!hasFace || !isFront(p)) {
            counting = false
            frontHeldSince = 0
            countdownLastShown = -1
            hint.value = hasFace
                ? "⚠️ Keep facing the camera — hold still"
                : "⚠️ Face lost — look at the camera"
        } else {
            const elapsed = performance.now() - countStart
            if (elapsed >= COUNTDOWN_MS) {
                faceCountdown.value = 0
                const canvas = document.createElement("canvas")
                const dataUrl = captureFrame(video, canvas)
                hint.value = "Captured ✓"
                cleanup()
                capturedImg.value = dataUrl
                uiState.value = 'captured'
                emit('captured', dataUrl)
                return
            }
            const remaining = Math.max(1, Math.ceil((COUNTDOWN_MS - elapsed) / 1000))
            if (remaining !== countdownLastShown) {
                countdownLastShown = remaining
                faceCountdown.value = remaining
                hint.value = `Hold still… capturing in ${remaining}`
            }
        }
        rafId = requestAnimationFrame(detectionLoop)
        return
    }

    // ── Guided steps: left → right → front
    if (hasFace) {
        const step = stepDefs[currentStepIdx.value]
        faceAligned.value = true
        hint.value = step.label

        if (step.test(p)) {
            if (step.key === "front") {
                if (!frontHeldSince) {
                    frontHeldSince = performance.now()
                }
                if (performance.now() - frontHeldSince >= FRONT_HOLD_MS) {
                    counting = true
                    countStart = performance.now()
                    countdownLastShown = -1
                    faceCountdown.value = 2
                    isScanSuccess.value = true
                    hint.value = "Hold still… capturing in 2"
                }
            } else {
                stepsCompleted.push(step.key)
                currentStepIdx.value += 1
                frontHeldSince = 0
            }
        } else if (step.key === "front") {
            frontHeldSince = 0
        }
    } else {
        faceAligned.value = false
        if (stepDefs[currentStepIdx.value]?.key === "front") {
            frontHeldSince = 0
        }
        hint.value = "No face detected — center your face in the frame"
    }

    rafId = requestAnimationFrame(detectionLoop)
}

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false,
        })
    } catch (err) {
        hint.value = "Could not open camera: " + (err?.message || err)
        uiState.value = 'error'
        return
    }

    const video = videoEl.value
    if (!video) return
    video.srcObject = stream
    try { await video.play() } catch (_) {}

    hint.value = 'Align your face inside the circle'
    uiState.value = 'scanning'
    rafId = requestAnimationFrame(detectionLoop)
}

async function init() {
    uiState.value = 'loading'
    hint.value = 'Loading face model…'
    stopFlag = false

    if (!navigator.mediaDevices?.getUserMedia) {
        hint.value = "Camera not supported in this browser."
        uiState.value = 'error'
        return
    }

    try {
        await ensureLandmarker()
    } catch (err) {
        hint.value = "Failed to load face model (check your connection)."
        uiState.value = 'error'
        return
    }

    stepDefs = [
        { key: "left",  label: "⬅️ Turn your head to the LEFT",
          test: (p) => (FLIP_LR ? p < TURN_LO : p > TURN_HI) },
        { key: "right", label: "➡️ Turn your head to the RIGHT",
          test: (p) => (FLIP_LR ? p > TURN_HI : p < TURN_LO) },
        { key: "front", label: "🙂 Now face the camera",
          test: (p) => p >= FRONT_MIN && p <= FRONT_MAX },
    ]

    stepsCompleted = []
    currentStepIdx.value = 0
    faceAligned.value = false
    isScanSuccess.value = false
    frontHeldSince = 0
    counting = false
    countdownLastShown = -1

    await startCamera()
}

function retake() {
    capturedImg.value = null
    init()
}

onMounted(init)
onUnmounted(() => {
    cleanup()
})
</script>

<style scoped>
.fc-root {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

/* ── Centered states ── */
.fc-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 2rem;
  min-height: 320px;
  justify-content: center;
}

.fc-hint { font-size: 0.9rem; color: var(--text-2); text-align: center; max-width: 300px; }
.fc-hint.error { color: #fca5a5; }

.fc-icon-wrap {
  width: 64px; height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.fc-icon-wrap.error { background: rgba(239,68,68,0.12); color: #ef4444; }
.fc-icon-wrap svg { width: 32px; height: 32px; }

/* ── Camera section ── */
.fc-camera-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.fc-video-wrap {
  position: relative;
  border-radius: 50%;
  overflow: hidden;
  width: 280px;
  height: 280px;
  aspect-ratio: 1/1;
  background: #000;
  box-shadow: var(--shadow-card);
  margin: 1rem 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 4px solid rgba(255,255,255,0.05);
}

.fc-video-wrap.face-aligned {
  border-color: rgba(99,102,241,0.2);
  box-shadow: 0 0 40px rgba(99,102,241,0.3);
}

.fc-video-wrap.scan-success {
  border-color: rgba(16, 185, 129, 0.4);
  box-shadow: 0 0 40px rgba(16, 185, 129, 0.4);
}

.fc-video-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fc-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* Mirror for user */
}

.fc-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
  color: rgba(255,255,255,0.3);
  transition: color 0.4s;
}

.fc-video-wrap.face-aligned .fc-overlay {
  color: #6366f1; /* Primary blue when aligned */
}

.fc-video-wrap.scan-success .fc-overlay {
  color: #10b981; /* Success green when done */
}

.fc-outline-path {
  transition: stroke-dashoffset 0.6s ease, stroke 0.4s;
}

@media (max-width: 480px) {
  .fc-video-wrap { width: 260px; height: 260px; }
}

/* ── Pose HUD ── */
.fc-pose-hud {
  position: absolute;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.fc-pose-step {
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(0,0,0,0.7);
  border: 1px solid rgba(255,255,255,0.2);
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  transition: all .4s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
}

.fc-pose-step.active {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
  transform: scale(1.05);
}

.fc-pose-step.success {
  background: #10b981 !important;
  border-color: #10b981 !important;
  color: #fff;
}

.fc-pose-step.pulse {
  animation: posePulse 1.5s infinite;
}

@keyframes posePulse {
  0%, 100% { opacity: 1; transform: scale(1.05); }
  50% { opacity: 0.7; transform: scale(1); }
}

/* ── Instruction bar ── */
.fc-instruction-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  width: 100%;
  max-width: 360px;
  transition: all 0.3s;
}

.fc-instruction-bar.success {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.fc-instruction-icon { font-size: 1.5rem; line-height: 1; flex-shrink: 0; }

.fc-instruction-text {
  font-size: 0.95rem;
  color: var(--text-1);
  font-weight: 500;
}

/* ── Captured section ── */
.fc-captured-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem 0;
}

.fc-captured-frame {
  position: relative;
  width: 180px; height: 180px;
  border-radius: 50%;
  overflow: hidden;
  border: 4px solid var(--success);
  box-shadow: 0 0 40px var(--success-glow), 0 12px 32px rgba(0,0,0,0.4);
}

.fc-captured-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.fc-captured-badge {
  position: absolute;
  bottom: 8px; right: 8px;
  width: 36px; height: 36px;
  background: var(--success);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.fc-captured-badge svg { width: 20px; height: 20px; fill: #fff; }

.fc-captured-label {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--success);
}

.fc-retake-btn { padding: 0.6rem 1.5rem; font-size: 0.9rem; }

/* ── Transitions ── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.fade-scale-enter-active, .fade-scale-leave-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.fade-scale-enter-from { opacity: 0; transform: scale(0.8) translateY(10px); }
.fade-scale-leave-to { opacity: 0; transform: scale(1.1) translateY(-10px); }

.slide-fade-enter-active { transition: all 0.4s ease-out; }
.slide-fade-leave-active { transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from { transform: translateX(20px); opacity: 0; }
.slide-fade-leave-to { transform: translateX(-20px); opacity: 0; }
</style>
