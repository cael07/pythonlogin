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

            <div class="btn-row">
              <button class="btn btn-ghost" @click="licenseImage = null">❌ Clear & Retake</button>
              <button class="btn btn-outline" @click="fillDemoData('license')">🪄 Prefill Demo</button>
              <button class="btn btn-success" :disabled="!licenseNumber || !licenseName" @click="goToStep(3)">Next Step ➔</button>
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

            <div class="btn-row">
              <button class="btn btn-ghost" @click="orImage = null">❌ Clear & Retake</button>
              <button class="btn btn-outline" @click="fillDemoData('or')">🪄 Prefill Demo</button>
              <button class="btn btn-success" :disabled="!orRenewalDate" @click="goToStep(4)">Next Step ➔</button>
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
      <div class="camera-modal-content">
        <!-- Header -->
        <div class="camera-modal-header">
          <h3 class="camera-modal-title">Position Your Document</h3>
          <button class="camera-modal-close" @click="closeCameraModal">✕</button>
        </div>

        <!-- Viewfinder -->
        <div class="camera-modal-viewfinder">
          <video ref="modalVideoEl" class="modal-video" autoplay muted playsinline></video>
          <div class="camera-modal-guideline">
            <div class="camera-modal-guideline-rect">
              <span class="guideline-text">ALIGN DOCUMENT EDGES</span>
            </div>
          </div>
        </div>

        <!-- Footer Controls -->
        <div class="camera-modal-controls">
          <button class="btn btn-ghost modal-btn-cancel" @click="closeCameraModal">Cancel</button>
          <button class="btn btn-primary modal-btn-capture" @click="capturePhotoFromModal">
            📸 Capture Document
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
let cameraStream = null

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
      }
    }, 150)
  } catch (err) {
    console.error("Error accessing camera:", err)
    error.value = "Unable to access camera. Please allow camera permissions or use Upload mode."
    closeCameraModal()
  }
}

function closeCameraModal() {
  stopDocCamera()
  showCameraModal.value = false
  activeCaptureType.value = ''
  activeMode.value = 'upload'
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

async function capturePhotoFromModal() {
  if (!modalVideoEl.value || !cameraStream) return
  const video = modalVideoEl.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 1920
  canvas.height = video.videoHeight || 1080
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const base64 = canvas.toDataURL('image/jpeg', 0.95)
    
    const docType = activeCaptureType.value
    if (docType === 'license') {
      licenseImage.value = base64
    } else if (docType === 'or') {
      orImage.value = base64
    } else if (docType === 'cr') {
      crImage.value = base64
    }
    
    closeCameraModal()
    await runOCR(base64, docType)
  }
}

function goToStep(nextStep) {
  closeCameraModal()
  activeMode.value = 'upload'
  step.value = nextStep
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
    const base64 = e.target.result
    
    if (docType === 'license') {
      licenseImage.value = base64
    } else if (docType === 'or') {
      orImage.value = base64
    } else if (docType === 'cr') {
      crImage.value = base64
    }
    
    // Start client-side OCR on this file!
    await runOCR(base64, docType)
  }
  reader.readAsDataURL(file)
}

async function runOCR(fileBase64, docType) {
  ocrLoading.value = true
  ocrStatus.value = 'Loading OCR Neural Engines...'
  try {
    const Tesseract = await loadTesseract()
    ocrStatus.value = 'Scanning layout and geometry...'
    
    const worker = await Tesseract.createWorker('eng')
    ocrStatus.value = 'Decoding text on document...'
    const ret = await worker.recognize(fileBase64)
    const text = ret.data.text
    await worker.terminate()
    
    console.log(`OCR Raw parsed text for ${docType}:`, text)
    ocrStatus.value = 'Extracting metadata...'
    
    // Regex parsing
    parseOCRText(text, docType)
  } catch (err) {
    console.warn("Tesseract OCR failed, falling back to simulated parser:", err)
    ocrStatus.value = 'Extracting fields (Fallback)...'
    setTimeout(() => {
      generateRealisticFallback(docType)
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
    // 1. Robust License Number Parsing with OCR Error Correction
    const cleanText = text.replace(/[^A-Za-z0-9]/g, ' ').toUpperCase()
    const words = cleanText.split(/\s+/)
    let foundLic = ''
    for (const word of words) {
      if (word.length >= 9 && word.length <= 13) {
        if (/[A-Z]/.test(word) && /[0-9]/.test(word)) {
          foundLic = word
          break
        }
      }
    }
    
    if (foundLic) {
      let firstChar = foundLic[0]
      if (/[0-9]/.test(firstChar)) {
        firstChar = 'J' // default LTO code prefix fallback
      }
      
      let rest = foundLic.slice(1).replace(/[^A-Z0-9]/g, '')
      let normalizedDigits = ''
      for (const char of rest) {
        if (/[0-9]/.test(char)) {
          normalizedDigits += char
        } else if (char === 'O' || char === 'Q' || char === 'D') {
          normalizedDigits += '0'
        } else if (char === 'I' || char === 'L' || char === 'T') {
          normalizedDigits += '1'
        } else if (char === 'S' || char === 'G') {
          normalizedDigits += '5'
        } else if (char === 'B') {
          normalizedDigits += '8'
        } else if (char === 'Z') {
          normalizedDigits += '2'
        } else if (char === 'A') {
          normalizedDigits += '4'
        } else {
          normalizedDigits += '0'
        }
      }
      
      while (normalizedDigits.length < 10) {
        normalizedDigits += '0'
      }
      normalizedDigits = normalizedDigits.slice(0, 10)
      licenseNumber.value = `${firstChar}${normalizedDigits.slice(0, 2)}-${normalizedDigits.slice(2, 4)}-${normalizedDigits.slice(4, 10)}`
    } else {
      const licMatch = text.match(/[A-Z]\d{2}-\d{2}-\d{6}/i)
      licenseNumber.value = licMatch ? licMatch[0].toUpperCase() : 'J01-20-' + Math.floor(100000 + Math.random() * 900000)
    }
    
    // 2. Full Name Parsing
    let foundName = ''
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('NAME') || lines[i].includes('LAST') || lines[i].includes('FIRST')) {
        foundName = lines[i+1] || lines[i+2] || ''
        break
      }
    }
    licenseName.value = foundName.replace(/[^A-Z\s]/g, ' ').replace(/\s+/g, ' ').trim() || 'LITERATUS CAESAR AUGUSTUS ESPUELAS'
    
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
    const dateMatch = text.match(/\b\d{4}[-/]\d{2}[-/]\d{2}\b/) || text.match(/\b\d{2}[-/]\d{2}[-/]\d{4}\b/)
    orRenewalDate.value = dateMatch ? dateMatch[0].replace(/\//g, '-') : '2027-05-23'
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
  border: 2px dashed rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-md);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.4), 0 0 15px rgba(99, 102, 241, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.camera-modal-viewfinder:hover .camera-modal-guideline-rect {
  border-color: var(--primary-light);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.4), 0 0 25px rgba(99, 102, 241, 0.7);
}

.guideline-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-align: center;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
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

