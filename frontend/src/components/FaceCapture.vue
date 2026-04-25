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
      <div class="fc-video-wrap">
        <video ref="videoEl" class="fc-video" autoplay muted playsinline></video>
        <canvas ref="overlayEl" class="fc-canvas"></canvas>

        <!-- Blink counter overlay -->
        <div class="fc-blink-hud">
          <div
            v-for="n in 2"
            :key="n"
            :class="['fc-blink-dot', { active: blinkCount >= n, pulse: blinkCount === n - 1 && faceAligned }]"
          >
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
            <span>{{ n }}</span>
          </div>
        </div>
      </div>

      <!-- Instruction bar -->
      <div class="fc-instruction-bar">
        <div class="fc-instruction-icon">
          <span v-if="!faceAligned">👁</span>
          <span v-else-if="blinkCount === 0">😊</span>
          <span v-else-if="blinkCount === 1">😉</span>
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
const blinkCount = ref(0)
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

// Blink detection state
const EAR_THRESHOLD  = 0.22
const MIN_CONSEC     = 2
let conseqClosed = 0
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
  // Larger oval for better face fitting
  return {
    cx: w / 2,
    cy: h / 2,
    rx: minDim * 0.38,
    ry: minDim * 0.52
  }
}

function isFaceInOval(box, w, h) {
  const { cx, cy, rx, ry } = getOval(w, h)
  const fcx = box.x + box.width  / 2
  const fcy = box.y + box.height / 2
  const dx = (fcx - cx) / (rx * 1.4)
  const dy = (fcy - cy) / (ry * 1.3)
  return dx * dx + dy * dy <= 1
}

/* ── Canvas drawing ─────────────────────────────────────── */
function drawOverlay(aligned, blinks) {
  const canvas = overlayEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = canvas.width, h = canvas.height
  const { cx, cy, rx, ry } = getOval(w, h)

  ctx.clearRect(0, 0, w, h)

  // Dark vignette
  ctx.fillStyle = 'rgba(4,7,30,0.62)'
  ctx.fillRect(0, 0, w, h)

  // Punch out oval (clear area = camera shows through)
  ctx.save()
  ctx.globalCompositeOperation = 'destination-out'
  ctx.beginPath()
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()

  // Oval border
  let color = 'rgba(255,255,255,0.3)'
  let glow  = 'rgba(255,255,255,0.1)'
  if (aligned && blinks === 0) { color = '#6366f1'; glow = 'rgba(99,102,241,0.5)' }
  if (aligned && blinks === 1) { color = '#f59e0b'; glow = 'rgba(245,158,11,0.5)' }
  if (aligned && blinks >= 2) { color = '#10b981'; glow = 'rgba(16,185,129,0.6)' }

  ctx.save()
  ctx.shadowColor = glow
  ctx.shadowBlur  = 22
  ctx.beginPath()
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
  ctx.strokeStyle = color
  ctx.lineWidth = 3
  ctx.stroke()
  ctx.restore()

  // Corner tick marks
  const corners = [0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2]
  corners.forEach(angle => {
    const px = cx + rx * Math.cos(angle)
    const py = cy + ry * Math.sin(angle)
    ctx.beginPath()
    ctx.arc(px, py, 5, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()
  })
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
      const pos = detection.landmarks.positions

      // Eye slices from 68-point model
      const leftEye  = pos.slice(36, 42)
      const rightEye = pos.slice(42, 48)
      const avgEAR   = (calcEAR(leftEye) + calcEAR(rightEye)) / 2

      if (avgEAR < EAR_THRESHOLD) {
        conseqClosed++
        wasEyeClosed = true
      } else {
        if (wasEyeClosed && conseqClosed >= MIN_CONSEC) {
          blinkCount.value++
          if (blinkCount.value === 1) {
            hint.value = 'Great! One more blink…'
          } else if (blinkCount.value >= 2) {
            hint.value = '📸 Capturing…'
            triggerCapture()
            return
          }
        }
        conseqClosed = 0
        wasEyeClosed = false
      }

      if (blinkCount.value === 0 && !wasEyeClosed) {
        hint.value = 'Face aligned ✓ — Blink twice to capture'
      }
    } else {
      if (blinkCount.value < 2) {
        blinkCount.value = 0
        conseqClosed = 0
        wasEyeClosed = false
      }
      hint.value = detection
        ? 'Move your face inside the oval'
        : 'Look straight at the camera'
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
  border-radius: var(--radius-md);
  overflow: hidden;
  width: 100%;
  max-width: 440px;
  aspect-ratio: 3/4; /* Taller for mobile */
  background: #000;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px var(--border);
}

.fc-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: scaleX(-1); /* Mirror for selfie */
}

.fc-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: scaleX(-1); /* Mirror to match video */
}

/* ── Blink HUD ── */
.fc-blink-hud {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  z-index: 10;
}

.fc-blink-dot {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: rgba(0,0,0,0.55);
  border: 2px solid rgba(255,255,255,0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 0.6rem;
  color: rgba(255,255,255,0.4);
  transition: all .3s;
  backdrop-filter: blur(8px);
}

.fc-blink-dot svg { width: 18px; height: 18px; }

.fc-blink-dot.active {
  background: rgba(16,185,129,0.25);
  border-color: var(--success);
  color: var(--success);
  box-shadow: 0 0 16px rgba(16,185,129,0.4);
}

.fc-blink-dot.pulse {
  animation: dotPulse 1.2s ease-in-out infinite;
  border-color: var(--primary);
  color: var(--primary-light);
}

@keyframes dotPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
  50%       { box-shadow: 0 0 0 10px rgba(99,102,241,0); }
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
  max-width: 520px;
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
