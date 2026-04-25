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
      <div class="fc-video-wrap" :class="{ 'face-aligned': faceAligned }">
        <video ref="videoEl" class="fc-video" autoplay muted playsinline></video>
        
        <!-- Pose HUD -->
        <div class="fc-pose-hud">
          <div
            v-for="(label, idx) in ['Left', 'Right', 'Front']"
            :key="idx"
            :class="['fc-pose-step', { active: scanStage > idx, pulse: scanStage === idx && faceAligned }]"
          >
            <span>{{ label }}</span>
          </div>
        </div>
      </div>

      <!-- Instruction bar -->
      <div class="fc-instruction-bar">
        <div class="fc-instruction-icon">
          <span v-if="!faceAligned">👁</span>
          <span v-else-if="scanStage === 0">⬅️</span>
          <span v-else-if="scanStage === 1">➡️</span>
          <span v-else-if="scanStage === 2">🎯</span>
          <span v-else>📸</span>
        </div>
        <p class="fc-instruction-text">{{ hint }}</p>
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
      <p class="fc-captured-label">Face verified! ✓</p>
      <button class="btn btn-ghost fc-retake-btn" @click="retake">↩ Retake photo</button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as faceapi from 'face-api.js'

const emit = defineEmits(['captured'])

/* ── State ──────────────────────────────────────────────── */
const uiState    = ref('loading')   // loading | scanning | captured | error
const hint       = ref('Loading face detection models…')
const scanStage  = ref(0)           // 0: Left, 1: Right, 2: Front
const faceAligned = ref(false)
const capturedImg = ref(null)

/* ── Template refs ──────────────────────────────────────── */
const videoEl   = ref(null)
const overlayEl = ref(null)

/* ── Internals ──────────────────────────────────────────── */
let stream          = null
let rafId           = null
let modelsReady     = false
let captureInProgress = false
let captureTimer    = null

let wasEyeClosed = false

/* ── Geometry helpers ───────────────────────────────────── */
function euclidean(a, b) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
}

function calcEAR(eye) {
  // eye = 6 {x,y} points (indices 0-5 mapped from landmark slice)
  const A = euclidean(eye[1], eye[5])
  const B = euclidean(eye[2], eye[4])
  const C = euclidean(eye[0], eye[3])
  return C < 0.001 ? 1 : (A + B) / (2 * C)
}

/* ── Oval geometry ──────────────────────────────────────── */
function getOval(w, h) {
  const minDim = Math.min(w, h)
  // Perfect circle guide for circular UI
  return {
    cx: w / 2,
    cy: h / 2,
    rx: minDim * 0.42,
    ry: minDim * 0.42
  }
}

function isFaceInOval(box, w, h) {
  // Simple check if face is roughly centered and fits
  const cx = w / 2, cy = h / 2
  const fcx = box.x + box.width  / 2
  const fcy = box.y + box.height / 2
  const dist = Math.sqrt((fcx - cx)**2 + (fcy - cy)**2)
  return dist < (w * 0.22) && box.width > (w * 0.35)
}

/* ── Canvas drawing ─────────────────────────────────────── */
function drawOverlay() {
  // We no longer draw on canvas, we use CSS for the circle
}

/* ── Detection loop ─────────────────────────────────────── */
async function detectionLoop() {
  const video  = videoEl.value
  const canvas = overlayEl.value

  if (!video || !canvas || !modelsReady || captureInProgress) return

  const opts = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 })

  try {
    const detection = await faceapi
      .detectSingleFace(video, opts)
      .withFaceLandmarks(true) // true = use tiny landmark model

    const aligned = detection
      ? isFaceInOval(detection.detection.box, canvas.width, canvas.height)
      : false

    faceAligned.value = aligned
    drawOverlay(aligned, blinkCount.value)

    if (aligned && detection) {
      const landmarks = detection.landmarks
      const nose  = landmarks.getNose()[3]
      const left  = landmarks.getLeftEye()[0]
      const right = landmarks.getRightEye()[3]

      const distL = Math.abs(nose.x - left.x)
      const distR = Math.abs(nose.x - right.x)
      const ratio = distL / (distR || 1)

      if (scanStage.value === 0) {
        hint.value = 'Turn your head slightly LEFT'
        if (ratio < 0.65) {
          scanStage.value = 1
          hint.value = 'Great! Now turn RIGHT'
        }
      } else if (scanStage.value === 1) {
        hint.value = 'Turn your head slightly RIGHT'
        if (ratio > 1.55) {
          scanStage.value = 2
          hint.value = 'Perfect! Now look FRONT'
        }
      } else if (scanStage.value === 2) {
        hint.value = 'Look straight at the camera'
        if (ratio > 0.8 && ratio < 1.2) {
          scanStage.value = 3
          hint.value = '📸 Hold still…'
          triggerCapture()
          return
        }
      }
    } else {
      hint.value = 'Position your face in the circle'
    }
  } catch (_) { /* skip frame on transient errors */ }

  rafId = requestAnimationFrame(detectionLoop)
}

/* ── Capture photo ──────────────────────────────────────── */
function triggerCapture() {
  if (captureInProgress) return
  captureInProgress = true
  cancelAnimationFrame(rafId)

  captureTimer = setTimeout(() => {
    const video = videoEl.value
    if (!video) return

    const c = document.createElement('canvas')
    c.width  = video.videoWidth
    c.height = video.videoHeight
    c.getContext('2d').drawImage(video, 0, 0)
    capturedImg.value = c.toDataURL('image/jpeg', 0.92)

    stopCamera()
    uiState.value = 'captured'
    emit('captured', capturedImg.value)
  }, 350)
}

/* ── Camera control ─────────────────────────────────────── */
function stopCamera() {
  if (rafId) cancelAnimationFrame(rafId)
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 480 }, height: { ideal: 640 }, facingMode: 'user' },
    })
    const video = videoEl.value
    video.srcObject = stream
    await new Promise(res => { video.onloadedmetadata = res })
    await video.play()

    // Sync canvas to actual video size
    const canvas = overlayEl.value
    canvas.width  = video.videoWidth  || 640
    canvas.height = video.videoHeight || 480

    drawOverlay(false, 0)
    hint.value = 'Align your face inside the oval'
    uiState.value = 'scanning'
    rafId = requestAnimationFrame(detectionLoop)
  } catch (err) {
    hint.value = 'Camera access denied — please allow camera permissions and try again.'
    uiState.value = 'error'
  }
}

/* ── Load models then start camera ─────────────────────── */
async function init() {
  uiState.value = 'loading'
  hint.value    = 'Loading face detection models…'
  try {
    const MODEL_URL = '/models'
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL),
    ])
    modelsReady = true
    await startCamera()
  } catch (err) {
    hint.value  = 'Failed to load face models. Make sure /public/models/ is populated.'
    uiState.value = 'error'
  }
}

/* ── Retake ─────────────────────────────────────────────── */
function retake() {
  capturedImg.value  = null
  blinkCount.value   = 0
  conseqClosed       = 0
  wasEyeClosed       = false
  captureInProgress  = false
  if (captureTimer) clearTimeout(captureTimer)
  startCamera()
}

onMounted(init)
onUnmounted(() => {
  stopCamera()
  if (captureTimer) clearTimeout(captureTimer)
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
  border: 6px solid rgba(255,255,255,0.1);
  box-shadow: var(--shadow-card);
  margin: 1rem 0;
  transition: all 0.4s ease;
}

.fc-video-wrap.face-aligned {
  border-color: #6366f1; /* Turns blue when aligned */
  box-shadow: 0 0 30px rgba(99,102,241,0.4);
}

@media (max-width: 480px) {
  .fc-video-wrap { width: 260px; height: 260px; }
}

/* ── Pose HUD ── */
.fc-pose-hud {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.fc-pose-step {
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(0,0,0,0.6);
  border: 1px solid rgba(255,255,255,0.2);
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  transition: all .3s;
  backdrop-filter: blur(4px);
}

.fc-pose-step.active {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

.fc-pose-step.pulse {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
  animation: posePulse 1.5s infinite;
}

@keyframes posePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ── Instruction bar ── */
.fc-instruction-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.85rem 1.25rem;
  width: 100%;
}

.fc-instruction-icon { font-size: 1.4rem; line-height: 1; flex-shrink: 0; }

.fc-instruction-text {
  font-size: 0.9rem;
  color: var(--text-1);
  font-weight: 500;
}

/* ── Captured section ── */
.fc-captured-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
}

.fc-captured-frame {
  position: relative;
  width: 160px; height: 160px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid var(--success);
  box-shadow: 0 0 32px var(--success-glow), 0 8px 24px rgba(0,0,0,0.4);
}

.fc-captured-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.fc-captured-badge {
  position: absolute;
  bottom: 6px; right: 6px;
  width: 32px; height: 32px;
  background: var(--success);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.fc-captured-badge svg { width: 18px; height: 18px; fill: #fff; }

.fc-captured-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--success);
}

.fc-retake-btn { padding: 0.5rem 1.25rem; font-size: 0.85rem; }
</style>
