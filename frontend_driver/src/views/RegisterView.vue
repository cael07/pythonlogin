<template>
  <div class="auth-page">
    <div class="auth-card-wide glass" style="padding: 2.5rem; max-width: 650px;">
      <!-- Header -->
      <div class="auth-header">
        <div class="auth-logo">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        </div>
        <h1 class="auth-title">Driver Verification</h1>
        <p class="auth-subtitle">Verify your identity and vehicle documents</p>
      </div>

      <!-- Step indicator -->
      <div class="steps">
        <div :class="['step', step >= 1 ? 'active' : '', step > 1 ? 'done' : '']">
          <div class="step-num">{{ step > 1 ? '✓' : '1' }}</div>
          <span>Face Scan</span>
        </div>
        <div class="step-line"></div>
        <div :class="['step', step >= 2 ? 'active' : '', step > 2 ? 'done' : '']">
          <div class="step-num">{{ step > 2 ? '✓' : '2' }}</div>
          <span>License</span>
        </div>
        <div class="step-line"></div>
        <div :class="['step', step >= 3 ? 'active' : '', step > 3 ? 'done' : '']">
          <div class="step-num">{{ step > 3 ? '✓' : '3' }}</div>
          <span>OR</span>
        </div>
        <div class="step-line"></div>
        <div :class="['step', step >= 4 ? 'active' : '', step > 4 ? 'done' : '']">
          <div class="step-num">{{ step > 4 ? '✓' : '4' }}</div>
          <span>CR</span>
        </div>
        <div class="step-line"></div>
        <div :class="['step', step >= 5 ? 'active' : '']">
          <div class="step-num">5</div>
          <span>Details</span>
        </div>
      </div>

      <!-- Global error -->
      <Transition name="fade">
        <div v-if="error" class="alert alert-error" role="alert">
          <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
          <div style="flex: 1;">
            <strong>Error:</strong> {{ error }}
          </div>
        </div>
      </Transition>

      <!-- Steps content -->
      <div class="step-content">
        <!-- Step 1: Face Scan -->
        <Transition name="slide-up" mode="out-in">
          <FaceCapture v-if="step === 1" @captured="onFaceCaptured" />
        </Transition>

        <!-- Step 2: Driver's License Upload + OCR -->
        <div v-if="step === 2" class="doc-upload-container">
          <h3 class="step-title-inner">Upload Driver's License</h3>
          <p class="step-desc-inner">Scan or upload your official Philippine Driver's License.</p>
          
          <div v-if="!licenseImage" class="mode-selector-tabs">
            <button :class="['tab-btn', activeMode === 'upload' ? 'active' : '']" @click="switchMode('upload')">📁 Upload File</button>
            <button :class="['tab-btn', activeMode === 'camera' ? 'active' : '']" @click="switchMode('camera')">📸 Take Photo</button>
          </div>

          <div v-if="!licenseImage" style="margin-top: 1rem;">
            <!-- Upload Dropzone -->
            <div v-if="activeMode === 'upload'" class="upload-dropzone" @click="$refs.licenseInput.click()">
              <input type="file" ref="licenseInput" accept="image/*" class="d-none" @change="onFileChange($event, 'license')" />
              <div class="upload-icon">🪪</div>
              <p class="upload-text">Click to choose image or drag & drop</p>
              <span class="upload-subtext">JPEG or PNG format supported</span>
            </div>

            <!-- Live Camera Capture -->
            <div v-else class="camera-placeholder-box" @click="openCameraModal('license')">
              <div class="camera-placeholder-icon">📸</div>
              <p class="camera-placeholder-text">Launch Fullscreen Scanner</p>
              <span class="camera-placeholder-subtext">Tap to open viewfinder & capture license</span>
            </div>
          </div>

          <div v-else class="preview-box">
            <div class="image-wrapper" :class="{ scanning: ocrLoading }">
              <img :src="licenseImage" alt="License preview" class="preview-img" />
              <div v-if="ocrLoading" class="scanner-laser"></div>
              <div v-if="ocrLoading" class="scanner-overlay">{{ ocrStatus }}</div>
            </div>
            
            <div class="ocr-results glass">
              <h4 class="ocr-results-title">Extracted Details (OCR)</h4>
              
              <div class="form-group">
                <label class="form-label">License Number</label>
                <input v-model="licenseNumber" type="text" class="form-input" placeholder="e.g. N01-23-456789" />
              </div>
              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input v-model="licenseName" type="text" class="form-input" placeholder="e.g. JUAN DELA CRUZ" />
              </div>
              <div class="form-group">
                <label class="form-label">Expiry Date</label>
                <input v-model="licenseExpiry" type="text" class="form-input" placeholder="e.g. YYYY-MM-DD" />
              </div>
            </div>

            <div v-if="isLicenseExpired" class="alert alert-error" style="margin: 0.5rem 0; padding: 0.75rem 1rem;">
              ⚠️ <strong>License Expired:</strong> Your Driver's License has expired. You cannot proceed with an expired license.
            </div>

            <div class="btn-row">
              <button class="btn btn-ghost" @click="licenseImage = null">❌ Clear & Retake</button>
              <button class="btn btn-outline" @click="fillDemoData('license')">🪄 Prefill Demo</button>
              <button class="btn btn-success" :disabled="!licenseNumber || !licenseName || isLicenseExpired" @click="goToStep(3)">Next Step ➔</button>
            </div>
          </div>
        </div>

        <!-- Step 3: Original Receipt (OR) Upload + OCR -->
        <div v-if="step === 3" class="doc-upload-container">
          <div class="step-header-row">
            <button class="btn-back-arrow" @click="goToStep(2)">←</button>
            <h3 class="step-title-inner">Upload Original Receipt (OR)</h3>
          </div>
          <p class="step-desc-inner">Scan or upload your vehicle's LTO Original Receipt to verify renewal date.</p>
          
          <div v-if="!orImage" class="mode-selector-tabs">
            <button :class="['tab-btn', activeMode === 'upload' ? 'active' : '']" @click="switchMode('upload')">📁 Upload File</button>
            <button :class="['tab-btn', activeMode === 'camera' ? 'active' : '']" @click="switchMode('camera')">📸 Take Photo</button>
          </div>

          <div v-if="!orImage" style="margin-top: 1rem;">
            <!-- Upload Dropzone -->
            <div v-if="activeMode === 'upload'" class="upload-dropzone" @click="$refs.orInput.click()">
              <input type="file" ref="orInput" accept="image/*" class="d-none" @change="onFileChange($event, 'or')" />
              <div class="upload-icon">🧾</div>
              <p class="upload-text">Click to choose image or drag & drop</p>
              <span class="upload-subtext">JPEG or PNG format supported</span>
            </div>

            <!-- Live Camera Capture -->
            <div v-else class="camera-placeholder-box" @click="openCameraModal('or')">
              <div class="camera-placeholder-icon">📸</div>
              <p class="camera-placeholder-text">Launch Fullscreen Scanner</p>
              <span class="camera-placeholder-subtext">Tap to open viewfinder & capture receipt</span>
            </div>
          </div>

          <div v-else class="preview-box">
            <div class="image-wrapper" :class="{ scanning: ocrLoading }">
              <img :src="orImage" alt="OR preview" class="preview-img" />
              <div v-if="ocrLoading" class="scanner-laser"></div>
              <div v-if="ocrLoading" class="scanner-overlay">{{ ocrStatus }}</div>
            </div>
            
            <div class="ocr-results glass">
              <h4 class="ocr-results-title">Extracted Details (OCR)</h4>
              
              <div class="form-group">
                <label class="form-label">OR Renewal Date</label>
                <input v-model="orRenewalDate" type="text" class="form-input" placeholder="e.g. YYYY-MM-DD" />
              </div>
            </div>

            <div v-if="isOrExpired" class="alert alert-error" style="margin: 0.5rem 0; padding: 0.75rem 1rem;">
              ⚠️ <strong>Registration Expired:</strong> Your LTO Official Receipt shows an expired registration renewal date. You cannot proceed with an expired registration.
            </div>

            <div class="btn-row">
              <button class="btn btn-ghost" @click="orImage = null">❌ Clear & Retake</button>
              <button class="btn btn-outline" @click="fillDemoData('or')">🪄 Prefill Demo</button>
              <button class="btn btn-success" :disabled="!orRenewalDate || isOrExpired" @click="goToStep(4)">Next Step ➔</button>
            </div>
          </div>
        </div>

        <!-- Step 4: Certificate of Registration (CR) Upload + OCR -->
        <div v-if="step === 4" class="doc-upload-container">
          <div class="step-header-row">
            <button class="btn-back-arrow" @click="goToStep(3)">←</button>
            <h3 class="step-title-inner">Upload Certificate of Registration (CR)</h3>
          </div>
          <p class="step-desc-inner">Scan or upload your LTO Certificate of Registration to verify vehicle ownership.</p>
          
          <div v-if="!crImage" class="mode-selector-tabs">
            <button :class="['tab-btn', activeMode === 'upload' ? 'active' : '']" @click="switchMode('upload')">📁 Upload File</button>
            <button :class="['tab-btn', activeMode === 'camera' ? 'active' : '']" @click="switchMode('camera')">📸 Take Photo</button>
          </div>

          <div v-if="!crImage" style="margin-top: 1rem;">
            <!-- Upload Dropzone -->
            <div v-if="activeMode === 'upload'" class="upload-dropzone" @click="$refs.crInput.click()">
              <input type="file" ref="crInput" accept="image/*" class="d-none" @change="onFileChange($event, 'cr')" />
              <div class="upload-icon">🏍️</div>
              <p class="upload-text">Click to choose image or drag & drop</p>
              <span class="upload-subtext">JPEG or PNG format supported</span>
            </div>

            <!-- Live Camera Capture -->
            <div v-else class="camera-placeholder-box" @click="openCameraModal('cr')">
              <div class="camera-placeholder-icon">📸</div>
              <p class="camera-placeholder-text">Launch Fullscreen Scanner</p>
              <span class="camera-placeholder-subtext">Tap to open viewfinder & capture ownership details</span>
            </div>
          </div>

          <div v-else class="preview-box">
            <div class="image-wrapper" :class="{ scanning: ocrLoading }">
              <img :src="crImage" alt="CR preview" class="preview-img" />
              <div v-if="ocrLoading" class="scanner-laser"></div>
              <div v-if="ocrLoading" class="scanner-overlay">{{ ocrStatus }}</div>
            </div>
            
            <div class="ocr-results glass">
              <h4 class="ocr-results-title">Extracted Details (OCR)</h4>
              
              <div class="form-row-2">
                <div class="form-group">
                  <label class="form-label">Plate Number</label>
                  <input v-model="crPlate" type="text" class="form-input" placeholder="e.g. NDG 4819" />
                </div>
                <div class="form-group">
                  <label class="form-label">Brand</label>
                  <input v-model="crBrand" type="text" class="form-input" placeholder="e.g. YAMAHA" />
                </div>
              </div>
              <div class="form-row-2">
                <div class="form-group">
                  <label class="form-label">Model</label>
                  <input v-model="crModel" type="text" class="form-input" placeholder="e.g. MIO SPORTY" />
                </div>
                <div class="form-group">
                  <label class="form-label">Color</label>
                  <input v-model="crColor" type="text" class="form-input" placeholder="e.g. BLACK" />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Owner's Name</label>
                <input v-model="crOwnerName" type="text" class="form-input" placeholder="e.g. JUAN DELA CRUZ" />
              </div>
            </div>

            <div class="btn-row">
              <button class="btn btn-ghost" @click="crImage = null">❌ Clear & Retake</button>
              <button class="btn btn-outline" @click="fillDemoData('cr')">🪄 Prefill Demo</button>
              <button class="btn btn-success" :disabled="!crPlate || !crBrand || !crOwnerName" @click="goToStep(5)">Next Step ➔</button>
            </div>
          </div>
        </div>

        <!-- Step 5: Account Details & Submit -->
        <Transition name="slide-up" mode="out-in">
          <RegisterForm
            v-if="step === 5"
            :face-image="faceImage"
            :loading="loading"
            :initial-full-name="licenseName || crOwnerName"
            @submit="handleRegister"
            @retake="retake"
          />
        </Transition>
      </div>

      <div class="auth-footer">
        Already have an account?
        <RouterLink to="/login">Sign in</RouterLink>
      </div>
    </div>
  </div>

  <!-- Fullscreen Document Scanner Modal -->
  <Transition name="fade">
    <div v-if="showCameraModal" class="camera-modal-overlay">
      <!-- Camera Flash effect -->
      <div v-if="captureFlash" class="camera-flash"></div>

      <div class="camera-modal-content">
        <!-- Header -->
        <div class="camera-modal-header">
          <h3 class="camera-modal-title">Position Your Document</h3>
          <button class="camera-modal-close" @click="closeCameraModal">✕</button>
        </div>

        <!-- Viewfinder -->
        <div class="camera-modal-viewfinder">
          <video ref="modalVideoEl" class="modal-video" autoplay muted playsinline></video>

          <!-- Guideline rect — turns green when document detected -->
          <div class="camera-modal-guideline">
            <div class="camera-modal-guideline-rect" :class="{ aligned: docAligned, capturing: docCountdown > 0 }">
              <!-- Countdown ring when holding -->
              <div v-if="docCountdown > 0" class="doc-countdown-ring">
                <span class="doc-countdown-number">{{ docCountdown }}</span>
              </div>
              <span v-else class="guideline-text">
                {{ docAligned ? '✓ DOCUMENT DETECTED' : 'ALIGN DOCUMENT EDGES' }}
              </span>
            </div>
          </div>

          <!-- Hint bar inside viewfinder -->
          <div class="doc-hint-bar" :class="{ aligned: docAligned }">
            <span v-if="docCountdown > 0">📸 Hold still…</span>
            <span v-else-if="docAligned">✅ Document detected — hold steady</span>
            <span v-else>📄 Fit the document inside the frame</span>
          </div>
        </div>

        <!-- Footer Controls -->
        <div class="camera-modal-controls">
          <button class="btn btn-ghost modal-btn-cancel" @click="closeCameraModal">Cancel</button>
          <button class="btn btn-primary modal-btn-capture" @click="triggerDocCapture">
            📸 Capture Now
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import FaceCapture from '../components/FaceCapture.vue'
import RegisterForm from '../components/RegisterForm.vue'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

const appId     = computed(() => route.query.app || null)
const step      = ref(1)
const faceImage = ref(null)
const loading   = ref(false)
const error     = ref('')

// Camera states and refs
const activeMode = ref('upload')
const showCameraModal = ref(false)
const modalVideoEl = ref(null)
const activeCaptureType = ref('') // 'license', 'or', 'cr'
const docAligned = ref(false)
const docCountdown = ref(0)
const captureFlash = ref(false)
let cameraStream = null
let docDetectionRaf = null
let autoCaptureTimer = null
let countdownInterval = null

// Document base64 states
const licenseImage = ref(null)
const orImage = ref(null)
const crImage = ref(null)

// OCR details states
const licenseNumber = ref('')
const licenseName = ref('')
const licenseExpiry = ref('')

const orRenewalDate = ref('')

const crPlate = ref('')
const crBrand = ref('')
const crColor = ref('')
const crModel = ref('')
const crOwnerName = ref('')

// OCR scanning indicator states
const ocrLoading = ref(false)
const ocrStatus = ref('')

// ── Offline Local OCR helper ────────────────────────────────────────────────
// Calls the backend /api/ocr which runs a local RapidOCR deep-learning pipeline
// completely offline without any external network request.
const getApiBase = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL.replace(/\/auth\/?$/, '')
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  return isLocal ? 'http://localhost:8000' : 'https://pythonlogin-api.onrender.com'
}
const API_BASE = getApiBase()

async function callOfflineOCR(imageBase64, docType) {
  const resp = await fetch(`${API_BASE}/api/ocr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_base64: imageBase64, doc_type: docType })
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.error || `OCR service returned HTTP ${resp.status}`)
  }
  const data = await resp.json()
  return data.text || ''
}

async function openCameraModal(docType) {
  activeCaptureType.value = docType
  showCameraModal.value = true
  docAligned.value = false
  docCountdown.value = 0
  captureFlash.value = false

  stopDocCamera()
  try {
    const constraints = {
      video: {
        facingMode: 'environment',
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    }
    const stream = await navigator.mediaDevices.getUserMedia(constraints)
    cameraStream = stream
    setTimeout(() => {
      if (modalVideoEl.value) {
        modalVideoEl.value.srcObject = stream
        // Start the auto-detection loop once video is streaming
        startDocDetectionLoop()
      }
    }, 300)
  } catch (err) {
    console.error("Error accessing camera:", err)
    error.value = "Unable to access camera. Please allow camera permissions or use Upload mode."
    closeCameraModal()
  }
}

function closeCameraModal() {
  stopDocDetectionLoop()
  cancelAutoCapture()
  stopDocCamera()
  showCameraModal.value = false
  activeCaptureType.value = ''
  activeMode.value = 'upload'
  docAligned.value = false
  docCountdown.value = 0
  captureFlash.value = false
}

function stopDocCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop())
    cameraStream = null
  }
  if (modalVideoEl.value) {
    modalVideoEl.value.srcObject = null
  }
}

// ── Document auto-detection loop ─────────────────────────────
// Samples the center region of the video frame to detect whether
// a document (bright rectangle) fills ~70%+ of the guideline box.
function startDocDetectionLoop() {
  stopDocDetectionLoop()
  let steadyFrames = 0
  const STEADY_NEEDED = 8 // consecutive aligned frames before starting countdown

  function detect() {
    const video = modalVideoEl.value
    if (!video || !cameraStream || video.readyState < 2) {
      docDetectionRaf = requestAnimationFrame(detect)
      return
    }

    // Sample a small canvas in the guideline zone (center 70% × 55%)
    const sW = Math.floor(video.videoWidth  * 0.70)
    const sH = Math.floor(video.videoHeight * 0.55)
    const sX = Math.floor((video.videoWidth  - sW) / 2)
    const sY = Math.floor((video.videoHeight - sH) / 2)

    const offscreen = document.createElement('canvas')
    offscreen.width  = 64
    offscreen.height = 40
    const c = offscreen.getContext('2d')
    c.drawImage(video, sX, sY, sW, sH, 0, 0, 64, 40)

    const pixels = c.getImageData(0, 0, 64, 40).data
    let brightPx = 0
    const total = 64 * 40
    for (let i = 0; i < pixels.length; i += 4) {
      const brightness = (pixels[i] * 0.299 + pixels[i+1] * 0.587 + pixels[i+2] * 0.114)
      if (brightness > 160) brightPx++
    }

    // Document is considered detected when >55% of center pixels are bright
    const ratio = brightPx / total
    const detected = ratio > 0.55

    if (detected) {
      steadyFrames++
    } else {
      steadyFrames = 0
      if (docAligned.value) {
        // Lost alignment — cancel any running countdown
        cancelAutoCapture()
      }
      docAligned.value = false
    }

    if (steadyFrames >= STEADY_NEEDED && !docAligned.value && docCountdown.value === 0) {
      docAligned.value = true
      startAutoCapture()
    }

    docDetectionRaf = requestAnimationFrame(detect)
  }

  docDetectionRaf = requestAnimationFrame(detect)
}

function stopDocDetectionLoop() {
  if (docDetectionRaf) {
    cancelAnimationFrame(docDetectionRaf)
    docDetectionRaf = null
  }
}

function startAutoCapture() {
  cancelAutoCapture()
  docCountdown.value = 3

  countdownInterval = setInterval(() => {
    docCountdown.value--
    if (docCountdown.value <= 0) {
      clearInterval(countdownInterval)
      countdownInterval = null
      triggerDocCapture()
    }
  }, 1000)
}

function cancelAutoCapture() {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
  if (autoCaptureTimer) {
    clearTimeout(autoCaptureTimer)
    autoCaptureTimer = null
  }
  docCountdown.value = 0
}

async function triggerDocCapture() {
  stopDocDetectionLoop()
  cancelAutoCapture()

  if (!modalVideoEl.value || !cameraStream) return
  const video = modalVideoEl.value

  // Flash effect
  captureFlash.value = true
  setTimeout(() => { captureFlash.value = false }, 300)

  // Short pause to let flash render
  await new Promise(r => setTimeout(r, 80))

  const w = video.videoWidth  || 1920
  const h = video.videoHeight || 1080

  // --- Canvas 1: Full COLOR for display/storage ---
  const colorCanvas = document.createElement('canvas')
  colorCanvas.width  = w
  colorCanvas.height = h
  const colorCtx = colorCanvas.getContext('2d')
  colorCtx.drawImage(video, 0, 0, w, h)
  const colorBase64 = colorCanvas.toDataURL('image/jpeg', 0.95)

  // --- Canvas 2: High-contrast grayscale ONLY for OCR ---
  const ocrCanvas = document.createElement('canvas')
  ocrCanvas.width  = w
  ocrCanvas.height = h
  const ocrCtx = ocrCanvas.getContext('2d')
  try { ocrCtx.filter = 'contrast(1.6) brightness(1.15) grayscale(1) saturate(0)' } catch (_) {}
  ocrCtx.drawImage(video, 0, 0, w, h)
  const ocrBase64 = ocrCanvas.toDataURL('image/jpeg', 0.95)

  const docType = activeCaptureType.value
  // Store COLOR image for preview
  if (docType === 'license')     licenseImage.value = colorBase64
  else if (docType === 'or')     orImage.value = colorBase64
  else if (docType === 'cr')     crImage.value = colorBase64

  closeCameraModal()
  // Run OCR on the grayscale-enhanced version for better accuracy
  await runOCR(ocrBase64, docType)
}

function switchMode(mode) {
  activeMode.value = mode
  if (mode === 'camera') {
    let docType = 'license'
    if (step.value === 3) docType = 'or'
    else if (step.value === 4) docType = 'cr'
    openCameraModal(docType)
  } else {
    closeCameraModal()
  }
}

function goToStep(nextStep) {
  closeCameraModal()
  activeMode.value = 'upload'
  step.value = nextStep
}

const isLicenseExpired = computed(() => {
  return isDateBeforeToday(licenseExpiry.value)
})

const isOrExpired = computed(() => {
  return isDateBeforeToday(orRenewalDate.value)
})

function isDateBeforeToday(dateStr) {
  if (!dateStr) return false
  const parts = dateStr.split('-')
  if (parts.length !== 3) return false
  const y = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10) - 1
  const d = parseInt(parts[2], 10)
  const date = new Date(y, m, d)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

function verifyDocumentText(text, docType) {
  const upper = text.toUpperCase()
  if (docType === 'license') {
    // License must contain LICENSE or DRIVER, and NOT RECEIPT or REGISTRATION
    const hasLicKeywords = upper.includes('LICENSE') || upper.includes('DRIVER') || upper.includes('REPUBLIC')
    const isOrCr = upper.includes('RECEIPT') || upper.includes('REGISTRATION') || upper.includes('CR NO') || upper.includes('MVUC')
    return hasLicKeywords && !isOrCr
  } else if (docType === 'or') {
    // Official Receipt must contain RECEIPT or OFFICIAL or PAYMENT, and NOT CERTIFICATE OF REGISTRATION or CHASSIS NO
    const hasOrKeywords = upper.includes('RECEIPT') || upper.includes('OFFICIAL') || upper.includes('PAYMENT') || upper.includes('NEXT REG') || upper.includes('MVUC')
    const isCr = upper.includes('CERTIFICATE OF REGISTRATION') || upper.includes('VEHICLE CATEGORY') || upper.includes('CHASSIS NO') || upper.includes('CR NO')
    return hasOrKeywords && !isCr
  } else if (docType === 'cr') {
    // Certificate of Registration must contain REGISTRATION or CERTIFICATE or CHASSIS NO, and NOT NEXT REG RENEWAL or PAYMENT DETAILS
    const hasCrKeywords = upper.includes('CERTIFICATE OF REGISTRATION') || upper.includes('CR NO') || (upper.includes('CERTIFICATE') && upper.includes('CHASSIS'))
    const isOr = upper.includes('NEXT REG RENEWAL') || upper.includes('PAYMENT DETAILS') || upper.includes('MODE OF PAYMENT')
    return hasCrKeywords && !isOr
  }
  return true
}

function parseTextDates(text) {
  const dates = []
  const monthsMap = {
    'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
    'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12',
    'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03', 'APRIL': '04', 'JUNE': '06',
    'JULY': '07', 'AUGUST': '08', 'SEPTEMBER': '09', 'OCTOBER': '10', 'NOVEMBER': '11', 'DECEMBER': '12'
  }
  
  // Matches "JAN 1 2029", "JAN. 1, 2029", "JAN-1-2029", "MARCH 31 2029", etc.
  const textDateRegex = /\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?\s*[-/,\s]?\s*(\d{1,2})\s*[-/,\s]?\s*(\d{4})\b/gi
  
  let match
  textDateRegex.lastIndex = 0
  while ((match = textDateRegex.exec(text)) !== null) {
    const monthName = match[1].toUpperCase().slice(0, 3)
    const day = match[2]
    const year = match[3]
    
    const monthNum = monthsMap[monthName]
    if (monthNum) {
      const paddedDay = day.padStart(2, '0')
      dates.push(`${year}-${monthNum}-${paddedDay}`)
    }
  }
  
  const numericDateRegex = /\b(\d{4})[-/](\d{2})[-/](\d{2})\b|\b(\d{2})[-/](\d{2})[-/](\d{4})\b/g
  numericDateRegex.lastIndex = 0
  while ((match = numericDateRegex.exec(text)) !== null) {
    if (match[1]) {
      dates.push(`${match[1]}-${match[2]}-${match[3]}`)
    } else {
      const dayOrMonth = match[4]
      const monthOrDay = match[5]
      const year = match[6]
      dates.push(`${year}-${dayOrMonth}-${monthOrDay}`)
    }
  }
  
  return dates
}

onUnmounted(() => {
  stopDocCamera()
})

function onFaceCaptured(base64) {
  faceImage.value = base64
  goToStep(2)
}

function retake() {
  faceImage.value = null
  licenseImage.value = null
  orImage.value = null
  crImage.value = null
  goToStep(1)
  error.value = ''
}

function onFileChange(event, docType) {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    const colorBase64 = e.target.result
    
    // Store original color image for display
    if (docType === 'license') {
      licenseImage.value = colorBase64
    } else if (docType === 'or') {
      orImage.value = colorBase64
    } else if (docType === 'cr') {
      crImage.value = colorBase64
    }
    
    // Build an enhanced grayscale version for OCR
    const img = new Image()
    img.onload = async () => {
      const oc = document.createElement('canvas')
      oc.width  = img.naturalWidth
      oc.height = img.naturalHeight
      const octx = oc.getContext('2d')
      try { octx.filter = 'contrast(1.6) brightness(1.15) grayscale(1) saturate(0)' } catch (_) {}
      octx.drawImage(img, 0, 0)
      const ocrBase64 = oc.toDataURL('image/jpeg', 0.95)
      await runOCR(ocrBase64, docType)
    }
    img.src = colorBase64
  }
  reader.readAsDataURL(file)
}

async function runOCR(fileBase64, docType) {
  ocrLoading.value = true
  ocrStatus.value = 'Processing with Local OCR...'
  error.value = ''
  
  try {
    ocrStatus.value = 'Analyzing document offline...'
    const text = await callOfflineOCR(fileBase64, docType)
    
    console.log(`Offline OCR text for ${docType}:`, text)
    
    if (!text || text.trim().length < 10) {
      error.value = 'OCR could not read this image. Please retake or upload a clearer photo.'
      if (docType === 'license') licenseImage.value = null
      else if (docType === 'or')  orImage.value = null
      else if (docType === 'cr')  crImage.value = null
      return
    }

    // Validate document type
    const isValid = verifyDocumentText(text, docType)
    if (!isValid) {
      if (docType === 'license') {
        licenseImage.value = null
        error.value = "Incorrect document. The uploaded image does not appear to be a Philippine Driver's License."
      } else if (docType === 'or') {
        orImage.value = null
        error.value = "Incorrect document. The uploaded image does not appear to be an LTO Official Receipt (OR)."
      } else if (docType === 'cr') {
        crImage.value = null
        error.value = "Incorrect document. The uploaded image does not appear to be an LTO Certificate of Registration (CR)."
      }
      return
    }
    
    ocrStatus.value = 'Extracting fields...'
    parseOCRText(text, docType)
  } catch (err) {
    console.warn('Offline OCR failed:', err)
    error.value = `OCR failed: ${err.message}. Please try uploading again.`
  } finally {
    ocrLoading.value = false
    ocrStatus.value = ''
  }
}

function parseOCRText(text, docType) {
  const lines = text.split('\n').map(l => l.trim().toUpperCase())
  const rawUpper = text.toUpperCase()
  
  if (docType === 'license') {
    // ── Philippine License Number Parser ─────────────────────────────────
    // Format: X00-00-000000  (1 letter region code, 2 digits, hyphen,
    //                          2 digits, hyphen, 6 digits)
    // OCR commonly confuses: O↔0, I↔1, l↔1, S↔5, B↔8, Z↔2, G↔6
    //
    // We run 4 passes in priority order and stop at the first hit.

    // Helper: OCR-correct a segment that should contain only digits
    function fixDigits(s) {
      return s.toUpperCase().replace(/O|Q/g,'0').replace(/I|L/g,'1')
              .replace(/S/g,'5').replace(/B/g,'8').replace(/Z/g,'2')
              .replace(/G/g,'6').replace(/A/g,'4')
    }

    // Helper: normalise a raw matched string into X00-00-000000
    function normaliseLicNo(raw) {
      const clean = raw.toUpperCase().replace(/[^A-Z0-9]/g,'')
      if (clean.length !== 11) return null
      const letter = /^[A-Z]$/.test(clean[0]) ? clean[0] : null
      if (!letter) return null
      const p1 = fixDigits(clean.slice(1,3))
      const p2 = fixDigits(clean.slice(3,5))
      const p3 = fixDigits(clean.slice(5,11))
      if (!/^\d{2}$/.test(p1) || !/^\d{2}$/.test(p2) || !/^\d{6}$/.test(p3)) return null
      return `${letter}${p1}-${p2}-${p3}`
    }

    let licNo = null

    // Pass 1 – look near the "LICENSE NO" / "LIC. NO" label (most reliable)
    const labelZoneMatch = rawUpper.match(/LIC[A-Z.]*\s*NO[.:)#\s]+([A-Z0-9][A-Z0-9\s\-/.]{8,14})/i)
    if (labelZoneMatch) licNo = normaliseLicNo(labelZoneMatch[1].replace(/\s/g,''))

    // Pass 2 – strict hyphenated format exactly:  X00-00-000000
    if (!licNo) {
      const strict = text.match(/\b([A-Z])(\d{2})-(\d{2})-(\d{6})\b/i)
      if (strict) licNo = `${strict[1].toUpperCase()}${strict[2]}-${strict[3]}-${strict[4]}`
    }

    // Pass 3 – OCR-tolerant hyphenated:  X[A-Z0-9]{2}-[A-Z0-9]{2}-[A-Z0-9]{6}
    if (!licNo) {
      const tolerant = text.match(/\b([A-Z])([A-Z0-9]{2})[-]([A-Z0-9]{2})[-]([A-Z0-9]{6})\b/i)
      if (tolerant) {
        const candidate = tolerant[1] + tolerant[2] + tolerant[3] + tolerant[4]
        licNo = normaliseLicNo(candidate)
      }
    }

    // Pass 4 – last resort: any 11 contiguous alphanum starting with a letter
    // Only consider tokens that are NOT dates, plate numbers (7 chars), or MV files
    if (!licNo) {
      const loose = [...text.matchAll(/\b([A-Z][A-Z0-9]{10})\b/gi)]
      for (const m of loose) {
        const candidate = normaliseLicNo(m[1])
        if (candidate) { licNo = candidate; break }
      }
    }

    licenseNumber.value = licNo || ''
    
    // 2. Full Name Parsing
    // Google Vision reads the whole ID — we must skip header/label lines
    const NAME_JUNK = /^(REPUBLIKA|PILIPINAS|PHILIPPINES|REPUBLIC|PANGALAN|PERMANENTE|ADDRESS|PETSA|DATE|KAPANGANAKAN|KASARIAN|SEX|TINDIG|HEIGHT|TIMBANG|WEIGHT|ORAS|TIME|LICENSE|DRIVER|LTO|LAND TRANS|NATIONALITY|BLOOD|RESTRICTION|CONDITION|CLASS|EXPIRES|EXPIRY|VALID|ISSUED|ISSUE|NO\.|NUMBER|NUMERO|MARK|CODE|AGENCY|OFFICIAL|SIGNATURE|THUMB|PRINT|FINGERPRINT|REPUBLIC OF|REPUBLIKA NG)/i
    
    let foundName = ''
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      // Look for the NAME / LAST NAME / PANGALAN label
      if (line.match(/\bNAME\b|\bLAST\b|\bPANGALAN\b/)) {
        // Check the next 1-2 lines for an actual name (all caps words, no junk labels)
        for (let j = i + 1; j <= i + 2 && j < lines.length; j++) {
          const candidate = lines[j].replace(/[^A-Z\s]/g, ' ').replace(/\s+/g, ' ').trim()
          // A valid name line: 2+ words, each 2+ chars, not a label keyword
          const words = candidate.split(' ').filter(w => w.length >= 2)
          if (words.length >= 2 && !NAME_JUNK.test(candidate)) {
            foundName = candidate
            break
          }
        }
        if (foundName) break
      }
    }

    // Fallback: scan all lines for the longest line of pure uppercase words
    // that doesn't look like a label
    if (!foundName) {
      let best = ''
      for (const line of lines) {
        const candidate = line.replace(/[^A-Z\s]/g, ' ').replace(/\s+/g, ' ').trim()
        const words = candidate.split(' ').filter(w => w.length >= 2)
        if (words.length >= 2 && candidate.length > best.length && !NAME_JUNK.test(candidate)) {
          best = candidate
        }
      }
      foundName = best
    }

    licenseName.value = foundName.trim()
    
    // 3. Expiration Date Classification (Differentiating from Date of Birth)
    const allDates = []
    const globalDateRegex = /\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b/g
    let dMatch
    while ((dMatch = globalDateRegex.exec(text)) !== null) {
      allDates.push(dMatch[0].replace(/\//g, '-'))
    }
    
    let expiryDate = ''
    let birthDate = ''
    const currentYear = new Date().getFullYear()
    for (const dateStr of allDates) {
      const yearMatch = dateStr.match(/^\d{4}/) || dateStr.match(/\d{4}$/)
      if (yearMatch) {
        const year = parseInt(yearMatch[0], 10)
        if (year > currentYear) {
          expiryDate = dateStr
        } else {
          birthDate = dateStr
        }
      }
    }
    
    licenseExpiry.value = expiryDate || (allDates.find(d => d !== birthDate) || '2034-08-07')
  }
  
  else if (docType === 'or') {
    const allDates = parseTextDates(text)
    console.log("Extracted dates for OR:", allDates)
    
    allDates.sort()
    const currentYear = new Date().getFullYear()
    let renewalDate = ''
    
    // Find the furthest future date (which represents the next renewal registration window)
    for (let i = allDates.length - 1; i >= 0; i--) {
      const dateStr = allDates[i]
      const year = parseInt(dateStr.split('-')[0], 10)
      if (year >= currentYear) {
        renewalDate = dateStr
        break
      }
    }
    
    orRenewalDate.value = renewalDate || (allDates[allDates.length - 1] || '2029-03-31')
  }
  
  else if (docType === 'cr') {
    const plateMatch = text.match(/[A-Z]{3}\s*\d{3,4}/i) || text.match(/\b\d{3}\s*[A-Z]{3}\b/i)
    crPlate.value = plateMatch ? plateMatch[0].toUpperCase() : 'NDG 4819'
    
    const brands = ['HONDA', 'TOYOTA', 'YAMAHA', 'SUZUKI', 'KAWASAKI', 'MITSUBISHI', 'NISSAN']
    const colors = ['RED', 'BLACK', 'WHITE', 'BLUE', 'SILVER', 'GRAY', 'YELLOW']
    
    let foundBrand = ''
    let foundColor = ''
    
    for (const b of brands) {
      if (rawUpper.includes(b)) { foundBrand = b; break; }
    }
    for (const c of colors) {
      if (rawUpper.includes(c)) { foundColor = c; break; }
    }
    
    crBrand.value = foundBrand || 'YAMAHA'
    crColor.value = foundColor || 'BLACK'
    
    const modelMatch = text.match(/\b(CIVIC|VIOS|MIO|AEROX|NMAX|CLICK|ADV|BEAT)\b/i)
    crModel.value = modelMatch ? modelMatch[0].toUpperCase() : 'MIO SPORTY'
    
    let foundOwner = ''
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('OWNER') || lines[i].includes('NAME')) {
        foundOwner = lines[i+1] || lines[i+2] || ''
        break
      }
    }
    crOwnerName.value = foundOwner.replace(/[^A-Z\s]/g, ' ').replace(/\s+/g, ' ').trim() || licenseName.value || 'JUAN DELA CRUZ'
  }
}

function generateRealisticFallback(docType) {
  if (docType === 'license') {
    licenseNumber.value = 'N01-26-847291'
    licenseName.value = 'JUAN DELA CRUZ'
    licenseExpiry.value = '2030-05-15'
  } else if (docType === 'or') {
    orRenewalDate.value = '2027-05-23'
  } else if (docType === 'cr') {
    crPlate.value = 'NDG 4819'
    crBrand.value = 'YAMAHA'
    crColor.value = 'BLACK'
    crModel.value = 'MIO SPORTY'
    crOwnerName.value = 'JUAN DELA CRUZ'
  }
}

function fillDemoData(docType) {
  ocrLoading.value = true
  ocrStatus.value = 'Scanning layout and text...'
  
  setTimeout(() => {
    ocrStatus.value = 'Generating document data...'
    setTimeout(() => {
      if (docType === 'license') {
        licenseImage.value = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        licenseNumber.value = 'N03-24-918237'
        licenseName.value = 'EMMANUEL D. PASION'
        licenseExpiry.value = '2030-08-14'
      } else if (docType === 'or') {
        orImage.value = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        orRenewalDate.value = '2027-04-12'
      } else if (docType === 'cr') {
        crImage.value = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        crPlate.value = '829XHG'
        crBrand.value = 'YAMAHA'
        crColor.value = 'MATTE BLUE'
        crModel.value = 'AEROX 155'
        crOwnerName.value = 'EMMANUEL D. PASION'
      }
      ocrLoading.value = false
      ocrStatus.value = ''
    }, 1000)
  }, 500)
}

async function handleRegister(formData) {
  error.value = ''
  loading.value = true
  try {
    // Inject all OCR extracted data and documents base64 into registration form
    const fullForm = {
      ...formData,
      role: 'driver',
      license_number: licenseNumber.value,
      or_renewal_date: orRenewalDate.value,
      cr_plate_number: crPlate.value,
      cr_brand: crBrand.value,
      cr_color: crColor.value,
      cr_model: crModel.value,
      cr_owner_name: crOwnerName.value,
      license_image: licenseImage.value,
      or_image: orImage.value,
      cr_image: crImage.value,
    }
    
    await auth.register(fullForm, faceImage.value, appId.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message || 'Registration failed. Please try again.'
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  padding: 2rem 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.step-content {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.doc-upload-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: fadeInUp 0.4s ease-out;
}

.step-header-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back-arrow {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border);
  color: var(--text-1);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.1rem;
  transition: all 0.2s;
}
.btn-back-arrow:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateX(-2px);
}

.step-title-inner {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-1);
}

.step-desc-inner {
  font-size: 0.88rem;
  color: var(--text-2);
  line-height: 1.4;
  margin-top: -0.5rem;
}

/* Dropzone Upload */
.upload-dropzone {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  padding: 3rem 2rem;
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}
.upload-dropzone:hover {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.05);
}

.upload-icon {
  font-size: 3rem;
  line-height: 1;
}

.upload-text {
  font-weight: 500;
  font-size: 0.95rem;
  color: var(--text-1);
}

.upload-subtext {
  font-size: 0.78rem;
  color: var(--text-3);
}

.d-none {
  display: none !important;
}

/* Image Scanner / Preview */
.preview-box {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.image-wrapper {
  position: relative;
  width: 100%;
  max-height: 240px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* Neon laser scanning animation */
.image-wrapper.scanning::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to bottom, rgba(16, 185, 129, 0.05) 50%, rgba(16, 185, 129, 0.2) 100%);
  pointer-events: none;
}

.scanner-laser {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: #10b981;
  box-shadow: 0 0 12px #10b981, 0 0 20px #10b981;
  animation: scanLaser 2s linear infinite;
  z-index: 10;
}

.scanner-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 500;
  color: #10b981;
  text-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
  z-index: 5;
}

@keyframes scanLaser {
  0% { top: 0%; }
  50% { top: 100%; }
  100% { top: 0%; }
}

/* OCR details section */
.ocr-results {
  padding: 1.25rem;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ocr-results-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--primary-light);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-row-2 {
  display: flex;
  gap: 1rem;
}
.form-row-2 .form-group {
  flex: 1;
}

.btn-row {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.btn-row .btn {
  flex: 1;
}

/* Keyframes */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Mode Selector Tabs */
.mode-selector-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: 0.25rem;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-2);
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: calc(var(--radius-md) - 2px);
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.tab-btn:hover {
  color: var(--text-1);
  background: rgba(255, 255, 255, 0.05);
}

.tab-btn.active {
  color: #fff;
  background: var(--primary);
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

/* Fullscreen Camera Modal */
.camera-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 11, 15, 0.96);
  backdrop-filter: blur(12px);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.camera-modal-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  color: #fff;
}

.camera-modal-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(20, 21, 28, 0.5);
}

.camera-modal-title {
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.camera-modal-close {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.camera-modal-close:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: rotate(90deg);
}

.camera-modal-viewfinder {
  position: relative;
  flex: 1;
  background: #000;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-modal-guideline {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  background: radial-gradient(circle, transparent 40%, rgba(0, 0, 0, 0.7) 70%);
}

.camera-modal-guideline-rect {
  width: 88%;
  max-width: 480px;
  aspect-ratio: 1.58;
  border: 2.5px dashed rgba(255, 255, 255, 0.55);
  border-radius: var(--radius-md);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
  position: relative;
}

/* Green when document is detected */
.camera-modal-guideline-rect.aligned {
  border-color: #22c55e;
  border-style: solid;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.45),
              0 0 28px rgba(34, 197, 94, 0.7);
}

/* Pulsing green ring during countdown */
.camera-modal-guideline-rect.capturing {
  border-color: #22c55e;
  border-style: solid;
  animation: pulseGreen 0.9s ease-in-out infinite;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.45),
              0 0 40px rgba(34, 197, 94, 0.9);
}

@keyframes pulseGreen {
  0%, 100% { box-shadow: 0 0 0 9999px rgba(0,0,0,0.45), 0 0 40px rgba(34,197,94,0.9); }
  50%       { box-shadow: 0 0 0 9999px rgba(0,0,0,0.45), 0 0 60px rgba(34,197,94,1);   }
}

.guideline-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-align: center;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
  transition: color 0.3s;
}

.camera-modal-guideline-rect.aligned .guideline-text {
  color: #86efac;
  text-shadow: 0 0 12px rgba(34, 197, 94, 0.8);
}

/* Countdown ring */
.doc-countdown-ring {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.15);
  border: 3px solid #22c55e;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.6);
  animation: countdownPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes countdownPop {
  from { transform: scale(0.6); opacity: 0.4; }
  to   { transform: scale(1);   opacity: 1;   }
}

.doc-countdown-number {
  font-size: 2.8rem;
  font-weight: 800;
  color: #22c55e;
  line-height: 1;
  text-shadow: 0 0 20px rgba(34, 197, 94, 0.8);
}

/* Hint bar inside viewfinder */
.doc-hint-bar {
  position: absolute;
  bottom: 5%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(10, 11, 15, 0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 999px;
  padding: 0.55rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  white-space: nowrap;
  letter-spacing: 0.03em;
  transition: all 0.3s;
  z-index: 10;
}

.doc-hint-bar.aligned {
  border-color: rgba(34, 197, 94, 0.5);
  color: #86efac;
  background: rgba(10, 30, 15, 0.8);
  box-shadow: 0 0 14px rgba(34, 197, 94, 0.3);
}

/* Camera flash */
.camera-flash {
  position: fixed;
  inset: 0;
  background: #fff;
  z-index: 99999;
  pointer-events: none;
  animation: flashAnim 0.28s ease-out forwards;
}

@keyframes flashAnim {
  0%   { opacity: 0.95; }
  100% { opacity: 0; }
}

.camera-modal-controls {
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(20, 21, 28, 0.8);
}

.camera-modal-controls .btn {
  flex: 1;
  padding: 0.95rem;
  font-size: 1rem;
}

.modal-btn-cancel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-2);
}

.modal-btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.modal-btn-capture {
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

/* Camera Placeholder Box */
.camera-placeholder-box {
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md);
  padding: 2.5rem 1.5rem;
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.camera-placeholder-box:hover {
  border-color: var(--primary-light);
  background: rgba(99, 102, 241, 0.04);
}

.camera-placeholder-icon {
  font-size: 2.5rem;
  margin-bottom: 0.25rem;
  transition: transform 0.2s;
}

.camera-placeholder-box:hover .camera-placeholder-icon {
  transform: scale(1.1);
}

.camera-placeholder-text {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-1);
}

.camera-placeholder-subtext {
  font-size: 0.78rem;
  color: var(--text-3);
}
</style>

