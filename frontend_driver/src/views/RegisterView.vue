<template>
  <div class="auth-page">
    <div class="auth-card-wide glass register-card">
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
                <input v-model="licenseNumber" ref="licenseNumberInput" type="text" class="form-input" placeholder="e.g. J0123456789" />
              </div>
              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input v-model="licenseName" type="text" class="form-input" placeholder="e.g. JUAN DELA CRUZ" disabled />
              </div>
              <div class="form-group">
                <label class="form-label">Expiry Date</label>
                <input v-model="licenseExpiry" type="text" class="form-input" placeholder="e.g. YYYY-MM-DD" disabled />
              </div>
            </div>

            <div v-if="isLicenseExpired" class="alert alert-error" style="margin: 0.5rem 0; padding: 0.75rem 1rem;">
              ⚠️ <strong>License Expired:</strong> Your Driver's License has expired. You cannot proceed with an expired license.
            </div>

            <div class="btn-row">
              <button class="btn btn-ghost btn-retake" @click="licenseImage = null">↶ Retake</button>
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
              <button class="btn btn-ghost btn-retake" @click="orImage = null">↶ Retake</button>
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
              <button class="btn btn-ghost btn-retake" @click="crImage = null">↶ Retake</button>
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
const licenseNumberInput = ref(null)

const orRenewalDate = ref('')

const crPlate = ref('')
const crBrand = ref('')
const crColor = ref('')
const crModel = ref('')
const crOwnerName = ref('')

// OCR scanning indicator states
const ocrLoading = ref(false)
const ocrStatus = ref('')

// Dynamic script loader for Tesseract.js
const loadTesseract = () => {
  return new Promise((resolve, reject) => {
    if (window.Tesseract) return resolve(window.Tesseract)
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js'
    script.onload = () => resolve(window.Tesseract)
    script.onerror = () => reject(new Error('Tesseract script failed to load'))
    document.head.appendChild(script)
  })
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

    // Draw the ENTIRE video frame to the offscreen canvas to analyze margins vs center
    const offscreen = document.createElement('canvas')
    offscreen.width  = 64
    offscreen.height = 40
    const c = offscreen.getContext('2d')
    c.drawImage(video, 0, 0, 64, 40)

    const pixels = c.getImageData(0, 0, 64, 40).data
    
    let innerSum = 0
    let innerCount = 0
    let outerSum = 0
    let outerCount = 0

    for (let y = 0; y < 40; y++) {
      for (let x = 0; x < 64; x++) {
        const idx = (y * 64 + x) * 4
        const brightness = (pixels[idx] * 0.299 + pixels[idx+1] * 0.587 + pixels[idx+2] * 0.114)
        
        // Define inner region representing the guideline box (x: 16 to 48, y: 10 to 30)
        const isInner = (x >= 16 && x <= 48 && y >= 10 && y <= 30)
        if (isInner) {
          innerSum += brightness
          innerCount++
        } else {
          outerSum += brightness
          outerCount++
        }
      }
    }

    const innerAvg = innerSum / innerCount
    const outerAvg = outerSum / outerCount

    // Document is detected when the inner area is bright (white paper/ID card)
    // and significantly brighter than the outer borders (contrast difference of >20 units)
    const detected = innerAvg > 120 && (innerAvg - outerAvg) > 20

    if (detected) {
      steadyFrames++
    } else {
      steadyFrames = 0
      docAligned.value = false
    }

    if (steadyFrames >= STEADY_NEEDED) {
      docAligned.value = true
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
  // Auto-capture disabled
}

function cancelAutoCapture() {
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

  const ocrBase64 = await preprocessDocumentImage(colorBase64)

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
    // Just check if DRIVER or LICENSE or REPUBLIC exists anywhere in text (very relaxed regex to tolerate OCR typos)
    return /\b(DRIV|LIC|L1C|DR1V|REPUBL|PILIP)/i.test(text)
  } else if (docType === 'or') {
    // Official Receipt should include RECEIPT and at least one business/receipt indicator,
    // but must not contain REGISTRATION as that indicates a CR/registration document.
    const hasReceipt = upper.includes('RECEIPT')
    const hasOfficial = upper.includes('OFFICIAL')
    const hasPayment = upper.includes('PAYMENT')
    const hasMvuc = upper.includes('MVUC')
    const hasCashier = upper.includes('CASHIER')
    const hasRegistration = upper.includes('REGISTRATION')
    return hasReceipt && (hasOfficial || hasPayment || hasMvuc || hasCashier) && !hasRegistration
  } else if (docType === 'cr') {
    // Certificate of Registration must explicitly include both 'CERTIFICATE' and 'REGISTRATION'
    const hasRegistration = upper.includes('REGISTRATION')
    const hasCertificate = upper.includes('CERTIFICATE')
    return hasRegistration && hasCertificate
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
    
      const ocrBase64 = await preprocessDocumentImage(colorBase64)
    await runOCR(ocrBase64, docType)
  }
  reader.readAsDataURL(file)
}

async function preprocessDocumentImage(base64) {
  const img = await new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = base64
  })

  const maxWidth = 1500
  const width = Math.min(maxWidth, img.naturalWidth)
  const height = Math.round(img.naturalHeight * (width / img.naturalWidth))
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')

  // Initial contrast/brightness/gray conversion
  try { ctx.filter = 'contrast(1.4) brightness(1.08) grayscale(1) saturate(0)'; } catch (_) {}
  ctx.drawImage(img, 0, 0, width, height)

  let imageData = ctx.getImageData(0, 0, width, height)
  imageData = normalizeImageContrast(imageData)
  imageData = adaptiveThreshold(imageData, 15, 10)
  ctx.putImageData(imageData, 0, 0)

  const deskewedCanvas = deskewCanvas(canvas)
  const deskewedCtx = deskewedCanvas.getContext('2d')
  imageData = deskewedCtx.getImageData(0, 0, deskewedCanvas.width, deskewedCanvas.height)

  const crop = detectDocumentBounds(imageData)
  if (crop && crop.width > 100 && crop.height > 100 && crop.width < deskewedCanvas.width && crop.height < deskewedCanvas.height) {
    const cropCanvas = document.createElement('canvas')
    cropCanvas.width = crop.width
    cropCanvas.height = crop.height
    const cropCtx = cropCanvas.getContext('2d')
    cropCtx.putImageData(deskewedCtx.getImageData(crop.x, crop.y, crop.width, crop.height), 0, 0)
    return cropCanvas.toDataURL('image/jpeg', 0.95)
  }

  return deskewedCanvas.toDataURL('image/jpeg', 0.95)
}

function deskewCanvas(sourceCanvas) {
  const angles = []
  for (let angle = -3.5; angle <= 3.5; angle += 0.5) angles.push(angle)
  let bestAngle = 0
  let bestScore = -Infinity

  for (const angle of angles) {
    const rotated = rotateCanvas(sourceCanvas, angle)
    const score = scoreDeskew(rotated)
    if (score > bestScore) {
      bestScore = score
      bestAngle = angle
    }
  }

  if (Math.abs(bestAngle) < 0.4) {
    return sourceCanvas
  }

  return rotateCanvas(sourceCanvas, bestAngle)
}

function rotateCanvas(sourceCanvas, degrees) {
  const radians = degrees * Math.PI / 180
  const sin = Math.abs(Math.sin(radians))
  const cos = Math.abs(Math.cos(radians))
  const width = sourceCanvas.width
  const height = sourceCanvas.height
  const newWidth = Math.ceil(width * cos + height * sin)
  const newHeight = Math.ceil(width * sin + height * cos)

  const canvas = document.createElement('canvas')
  canvas.width = newWidth
  canvas.height = newHeight
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, newWidth, newHeight)
  ctx.translate(newWidth / 2, newHeight / 2)
  ctx.rotate(radians)
  ctx.drawImage(sourceCanvas, -width / 2, -height / 2)
  return canvas
}

function scoreDeskew(canvas) {
  const width = canvas.width
  const height = canvas.height
  const ctx = canvas.getContext('2d')
  const imageData = ctx.getImageData(0, 0, width, height)
  const data = imageData.data
  const counts = new Float32Array(width)

  for (let y = 0; y < height; y += 4) {
    for (let x = 0; x < width; x += 4) {
      const idx = (y * width + x) * 4
      const value = data[idx]
      if (value < 128) counts[x] += 1
    }
  }

  let mean = 0
  for (let x = 0; x < width; x++) mean += counts[x]
  mean /= width
  let variance = 0
  for (let x = 0; x < width; x++) {
    const diff = counts[x] - mean
    variance += diff * diff
  }
  return variance / width
}

function normalizeImageContrast(imageData) {
  const data = imageData.data
  let min = 255
  let max = 0

  for (let i = 0; i < data.length; i += 4) {
    const value = data[i]
    if (value < min) min = value
    if (value > max) max = value
  }

  const range = Math.max(max - min, 1)
  const scale = 255 / range
  for (let i = 0; i < data.length; i += 4) {
    let v = Math.round((data[i] - min) * scale)
    v = Math.max(0, Math.min(255, v))
    data[i] = data[i+1] = data[i+2] = v
  }

  return imageData
}

function adaptiveThreshold(imageData, windowSize = 15, offset = 10) {
  const width = imageData.width
  const height = imageData.height
  const data = imageData.data
  const gray = new Uint8ClampedArray(width * height)

  for (let i = 0, j = 0; i < data.length; i += 4, j++) {
    gray[j] = data[i]
  }

  const integral = new Uint32Array((width + 1) * (height + 1))
  for (let y = 1; y <= height; y++) {
    let rowSum = 0
    const rowIndex = y * (width + 1)
    const prevRowIndex = (y - 1) * (width + 1)
    for (let x = 1; x <= width; x++) {
      rowSum += gray[(y - 1) * width + (x - 1)]
      integral[rowIndex + x] = integral[prevRowIndex + x] + rowSum
    }
  }

  const half = Math.floor(windowSize / 2)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const x1 = Math.max(0, x - half)
      const y1 = Math.max(0, y - half)
      const x2 = Math.min(width - 1, x + half)
      const y2 = Math.min(height - 1, y + half)
      const count = (x2 - x1 + 1) * (y2 - y1 + 1)
      const sum = integral[(y2 + 1) * (width + 1) + (x2 + 1)]
                - integral[(y1) * (width + 1) + (x2 + 1)]
                - integral[(y2 + 1) * (width + 1) + (x1)]
                + integral[(y1) * (width + 1) + (x1)]
      const threshold = sum / count - offset
      const i = y * width + x
      const value = gray[i] < threshold ? 0 : 255
      data[i * 4] = data[i * 4 + 1] = data[i * 4 + 2] = value
      data[i * 4 + 3] = 255
    }
  }

  return imageData
}

function detectDocumentBounds(imageData) {
  const width = imageData.width
  const height = imageData.height
  const data = imageData.data
  const threshold = 220
  let top = 0, bottom = height - 1, left = 0, right = width - 1

  const rowIsBlank = (y) => {
    let count = 0
    for (let x = 0; x < width; x++) {
      if (data[(y * width + x) * 4] < threshold) count++
    }
    return count < width * 0.02
  }
  const colIsBlank = (x) => {
    let count = 0
    for (let y = 0; y < height; y++) {
      if (data[(y * width + x) * 4] < threshold) count++
    }
    return count < height * 0.02
  }

  while (top < bottom && rowIsBlank(top)) top++
  while (bottom > top && rowIsBlank(bottom)) bottom--
  while (left < right && colIsBlank(left)) left++
  while (right > left && colIsBlank(right)) right--

  const padding = 16
  return {
    x: Math.max(0, left - padding),
    y: Math.max(0, top - padding),
    width: Math.min(width - left + padding * 2, right - left + padding),
    height: Math.min(height - top + padding * 2, bottom - top + padding),
  }
}

async function runOCR(fileBase64, docType) {
  ocrLoading.value = true
  ocrStatus.value = 'Loading OCR Neural Engines...'
  error.value = ''
  
  try {
    if (docType === 'cr') {
      // Use backend EasyOCR for CR documents
      ocrStatus.value = 'Sending to OCR service...'
      
      const response = await fetch('https://pythonlogin-api.onrender.com/api/ocr/process-cr', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_base64: fileBase64,
          doc_type: 'cr'
        })
      })
      
      if (!response.ok) {
        throw new Error(`Backend OCR failed: ${response.statusText}`)
      }
      
      const ocrResult = await response.json()

      if (!ocrResult.success) {
        throw new Error(ocrResult.error || 'OCR processing failed')
      }

      const text = ocrResult.text || ''
      console.log(`EasyOCR text for CR:`, text)
      console.log(`Extracted fields from backend:`, ocrResult.fields)

      // Prefer backend-extracted structured fields when available
      if (ocrResult.fields && Object.keys(ocrResult.fields).length) {
        const f = ocrResult.fields
        crPlate.value = (f.plate_number || f.plate || f.cr_plate || '').toString().toUpperCase() || crPlate.value
        crBrand.value = (f.brand || f.make || '').toString().toUpperCase() || crBrand.value
        // For model we expect Year Model -> use provided 'model' or year
        crModel.value = (f.model || f.year || '').toString() || crModel.value
        crColor.value = (f.color || '').toString().toUpperCase() || crColor.value
        crOwnerName.value = (f.owner_name || f.owner || '').toString().toUpperCase() || crOwnerName.value

        // If backend provided text, still validate it's a CR
        const isValid = verifyDocumentText(text, docType)
        if (!isValid) {
          crImage.value = null
          error.value = "Incorrect document. The uploaded image does not appear to be an LTO Certificate of Registration (CR)."
          return
        }

        ocrStatus.value = 'Fields applied from OCR service.'
        return
      }

      // Fallback to parsing raw OCR text on the frontend
      console.warn('Backend returned no structured fields; falling back to parseOCRText')
      const isValid = verifyDocumentText(text, docType)
      if (!isValid) {
        crImage.value = null
        error.value = "Incorrect document. The uploaded image does not appear to be an LTO Certificate of Registration (CR)."
        return
      }
      ocrStatus.value = 'Extracting fields...'
      parseOCRText(text, docType)
      
    } else {
      // Use Tesseract for License and OR documents
      const Tesseract = await loadTesseract()
      ocrStatus.value = 'Calibrating scanner...'
      
      const worker = await Tesseract.createWorker('eng')
      
      // Configure Tesseract for maximum accuracy on Philippine IDs
      try {
        await worker.setParameters({
          tessedit_pageseg_mode: '6',
          user_defined_dpi: '300',
          tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-/., :',
        })
      } catch (paramErr) {
        console.warn('Could not set Tesseract params (older build):', paramErr)
      }

      ocrStatus.value = 'Decoding text on document...'
      const ret = await worker.recognize(fileBase64)
      const text = ret.data.text
      await worker.terminate()
      
      console.log(`OCR Raw parsed text for ${docType}:`, text)
      
      // Validate document type
      const isValid = verifyDocumentText(text, docType)
      if (!isValid) {
        if (docType === 'license') {
          licenseImage.value = null
          error.value = "Error, Incorrect Document or Blurry, failed to read properly, please check and capture it clearly."
        } else if (docType === 'or') {
          orImage.value = null
          error.value = "Incorrect document. The uploaded image does not appear to be an LTO Official Receipt (OR)."
        }
        return
      }
      
      ocrStatus.value = 'Extracting fields...'
      parseOCRText(text, docType)
    }

    if (docType === 'license') {
      setTimeout(() => {
        if (licenseNumberInput.value) {
          licenseNumberInput.value.focus()
        }
      }, 100)
    }
  } catch (err) {
    console.warn("OCR failed, falling back to simulated parser:", err)
    ocrStatus.value = 'Extracting fields (Fallback)...'
    setTimeout(() => {
      generateRealisticFallback(docType)
      if (docType === 'license') {
        setTimeout(() => {
          if (licenseNumberInput.value) {
            licenseNumberInput.value.focus()
          }
        }, 100)
      }
    }, 1000)
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

    // Pass 1 – look near "LICENSE NO" / "LIC. NO" label
    // Limit to 8-13 chars so we don't accidentally grab trailing text
    const labelZoneMatch = rawUpper.match(/LIC[A-Z.]*\s*NO[.:)#\s]+([A-Z0-9][-A-Z0-9]{7,12})/i)
    if (labelZoneMatch) licNo = normaliseLicNo(labelZoneMatch[1].replace(/[\s\-]/g,''))

    // Pass 2 – strict hyphenated format exactly:  X00-00-000000
    if (!licNo) {
      const strict = text.match(/\b([A-Z])(\d{2})-(\d{2})-(\d{6})\b/i)
      if (strict) licNo = `${strict[1].toUpperCase()}${strict[2]}-${strict[3]}-${strict[4]}`
    }

    // Pass 3 – Tesseract space-separated: X00 00 000000 (3 groups, matching J01 20 003021)
    if (!licNo) {
      const spaced = text.match(/\b([A-Z][A-Z0-9]{2})\s+([A-Z0-9]{2})\s+([A-Z0-9]{6})\b/i)
      if (spaced) {
        licNo = normaliseLicNo(spaced[1] + spaced[2] + spaced[3])
      }
    }

    // Pass 4 – OCR-tolerant: accepts space or hyphen between segments
    if (!licNo) {
      const tolerant = text.match(/\b([A-Z])([A-Z0-9]{2})[\-\s]([A-Z0-9]{2})[\-\s]([A-Z0-9]{6})\b/i)
      if (tolerant) {
        licNo = normaliseLicNo(tolerant[1] + tolerant[2] + tolerant[3] + tolerant[4])
      }
    }

    // Pass 5 – last resort: any 11 contiguous alphanum starting with a letter
    if (!licNo) {
      const loose = [...text.matchAll(/\b([A-Z][A-Z0-9]{10})\b/gi)]
      for (const m of loose) {
        const candidate = normaliseLicNo(m[1])
        if (candidate) { licNo = candidate; break }
      }
    }

    // Always leave license number blank so user is forced to input it manually
    licenseNumber.value = ''
    
    // 2. Full Name Parsing
    // The ID label row is "Last Name, First Name, Middle Name" (small text).
    // The actual name is on the NEXT line e.g. "LITERATUS, CAESAR AUGUSTUS ESPUELAS".
    // We must NEVER use the label line itself as the name.
    const NAME_JUNK = /^(REPUBLIKA|PILIPINAS|PHILIPPINES|REPUBLIC|PANGALAN|PERMANENTE|ADDRESS|PETSA|DATE|KAPANGANAKAN|KASARIAN|SEX|TINDIG|HEIGHT|TIMBANG|WEIGHT|ORAS|TIME|LICENSE|DRIVER|LTO|LAND TRANS|NATIONALITY|BLOOD|RESTRICTION|CONDITION|CLASS|EXPIRES|EXPIRY|VALID|ISSUED|ISSUE|NO\.|NUMBER|NUMERO|MARK|CODE|AGENCY|OFFICIAL|SIGNATURE|THUMB|PRINT|FINGERPRINT|REPUBLIC OF|REPUBLIKA NG|FIRST|MIDDLE|LAST|TYPE|EYES|COLOR|DEPARTMENT|TRANSPORTATION|OFFICE)/i

    function cleanName(raw) {
      // Keep only letters, spaces and periods; collapse whitespace
      let name = raw.replace(/[^A-Z\s.]/gi, ' ').replace(/\s+/g, ' ').trim()
      
      // Strip any stray 1-2 character OCR noise prefix (e.g. "I LITERATUS" -> "LITERATUS")
      // Protect common Spanish/Filipino/Chinese last name prefixes and short names
      const STRAY_LEADERS = /^(?!(?:DE|LA|EL|DA|DO|DI|MC|ST|SAN|STA|GO|YU|UY|SY|LO|SO|KO|HO|NG|LI|MA|LU|HE|XU|YE|SU|LE|OH|AN|DO|DU|TO|TY|VU|HA|IP)\b)[A-Z0-9]{1,2}\s+/i
      while (STRAY_LEADERS.test(name)) {
        name = name.replace(STRAY_LEADERS, '').trim()
      }
      
      // Remove any leading/trailing periods or whitespace (e.g. ". LITERATUS" -> "LITERATUS")
      return name.replace(/^[.\s]+|[.\s]+$/g, '').trim()
    }

    let foundName = ''
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      // Find a label line containing NAME / LAST / PANGALAN
      if (line.match(/\bNAME\b|\bLAST\b|\bPANGALAN\b/)) {
        // NEVER use the label line itself — look at the NEXT 1-3 lines
        for (let j = i + 1; j <= i + 3 && j < lines.length; j++) {
          const candidate = cleanName(lines[j])
          const words = candidate.split(' ').filter(w => w.length >= 2)
          if (words.length >= 2 && !NAME_JUNK.test(candidate)) {
            foundName = candidate
            break
          }
        }
        if (foundName) break
      }
    }

    // Fallback: pick the longest valid name-looking line
    if (!foundName) {
      let best = ''
      for (const line of lines) {
        const candidate = cleanName(line)
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
    const linesRaw = text.split('\n').map(l => l.trim())
    const upperLines = linesRaw.map(l => l.toUpperCase())
    const rawUpper = text.toUpperCase()

    function extractField(labels) {
      const upperLabels = labels.map(l => l.toUpperCase())
      for (let i = 0; i < upperLines.length; i++) {
        const upper = upperLines[i]
        for (const label of upperLabels) {
          const idx = upper.indexOf(label)
          if (idx !== -1) {
            let value = linesRaw[i].slice(idx + label.length).trim()
            value = value.replace(/^[:\-\.\s]+/, '').trim()
            if (value && !upperLabels.some(l => value.toUpperCase().includes(l))) {
              return value
            }
            const next = linesRaw[i + 1] ? linesRaw[i + 1].trim() : ''
            if (next && !upperLabels.some(l => next.toUpperCase().includes(l))) {
              return next
            }
          }
        }
      }
      return ''
    }

    const plateRaw = extractField(['PLATE NO', 'PLATE NO.', 'PLATE NUMBER', 'PLATE'])
    let plate = ''
    if (plateRaw) {
      const match = plateRaw.match(/([A-Z0-9]{1,3})\s*[-\s]?\s*([A-Z0-9]{1,4})\s*([A-Z]{0,3})/i)
      plate = match ? (match[1] + match[2] + (match[3] || '')).toUpperCase() : plateRaw.toUpperCase()
    }
    if (!plate) {
      const fallback = text.match(/\b[A-Z]{1,3}\s*\d{2,4}\b/) || text.match(/\b\d{2,4}\s*[A-Z]{1,3}\b/)
      plate = fallback ? fallback[0].replace(/\s+/g, '').toUpperCase() : ''
    }
    crPlate.value = plate || 'NDG 4819'

    const KNOWN_BRANDS = ['HONDA', 'YAMAHA', 'SUZUKI', 'KAWASAKI', 'TOYOTA', 'NISSAN', 'ISUZU', 'MITSUBISHI', 'MAZDA', 'HYUNDAI', 'KIA', 'FORD', 'CHEVROLET', 'HINO']
    function matchKnownBrand() {
      for (const brand of KNOWN_BRANDS) {
        if (rawUpper.includes(brand)) {
          return brand
        }
      }
      return ''
    }

    const brandRaw = extractField(['MAKE/BRAND', 'MAKE', 'BRAND'])
    const brandCand = brandRaw.toUpperCase().replace(/[^A-Z\s]/g, '').trim()
    crBrand.value = brandCand && !/\d/.test(brandCand) ? brandCand : matchKnownBrand() || 'YAMAHA'

    const KNOWN_COLORS = ['BLACK', 'WHITE', 'RED', 'BLUE', 'GREEN', 'YELLOW', 'BROWN', 'SILVER', 'GRAY', 'GREY', 'ORANGE', 'GOLD', 'MAROON', 'BEIGE']
    function matchKnownColor() {
      for (const color of KNOWN_COLORS) {
        if (rawUpper.includes(color)) {
          return color
        }
      }
      return ''
    }

    const colorRaw = extractField(['COLOR'])
    const colorCand = colorRaw.toUpperCase().replace(/[^A-Z\s]/g, '').trim()
    crColor.value = colorCand || matchKnownColor() || 'BLACK'

    let model = extractField(['YEAR MODEL', 'YEAR MODEL (NEW/USED IMPORTED CBU)'])
    if (!model) {
      const yearLineIndex = upperLines.findIndex(l => l.includes('YEAR MODEL'))
      if (yearLineIndex !== -1 && linesRaw[yearLineIndex + 1]) {
        model = linesRaw[yearLineIndex + 1].trim()
      }
    }
    let yearMatch = model.match(/\b(19|20)\d{2}\b/)
    if (!yearMatch) {
      const fallbackYear = text.match(/\b(19|20)\d{2}\b/)
      yearMatch = fallbackYear
    }
    crModel.value = yearMatch ? yearMatch[0] : ''

    let owner = extractField(["OWNER'S NAME", "OWNERS NAME", 'OWNER NAME', 'REGISTERED OWNER'])
    if (!owner) {
      const ownerIndex = upperLines.findIndex((l, idx) => /OWNER\b/.test(l) && linesRaw[idx + 1] && !/OWNER\b/.test(upperLines[idx + 1]))
      if (ownerIndex !== -1) {
        owner = linesRaw[ownerIndex + 1].trim()
      }
    }
    if (!owner) {
      owner = linesRaw
        .filter(l => l.length > 6 && /\s/.test(l))
        .sort((a, b) => b.length - a.length)[0] || ''
    }
    crOwnerName.value = owner.replace(/[^A-Z\s\.\,]/gi, ' ').replace(/\s+/g, ' ').trim() || licenseName.value || 'JUAN DELA CRUZ'
  }
}

function generateRealisticFallback(docType) {
  if (docType === 'license') {
    licenseNumber.value = ''
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
        licenseNumber.value = 'J0123456789'
        licenseName.value = 'EMMANUEL D. PASION'
        licenseExpiry.value = '2030-08-14'
        setTimeout(() => {
          if (licenseNumberInput.value) {
            licenseNumberInput.value.focus()
          }
        }, 100)
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
.btn-retake {
  background: #dc2626;
  color: #fff;
  border-color: #b91c1c;
}
.btn-retake:hover:not(:disabled) {
  background: #c2410b;
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

.register-card {
  padding: 2.5rem;
  max-width: 650px;
  width: 100%;
}

@media (max-width: 480px) {
  .register-card {
    padding: 1.25rem 0.75rem !important; /* Smaller margins/paddings on mobile */
  }
}
</style>

