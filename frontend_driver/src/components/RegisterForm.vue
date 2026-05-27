<template>
  <div class="rf-root">
    <!-- ── Face preview ─────────────────────────── -->
    <div class="rf-face-row">
      <div class="rf-face-wrap">
        <img :src="faceImage" alt="Captured face" class="rf-face-img" />
        <div class="rf-face-ok">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </div>
      </div>
      <div class="rf-face-info">
        <p class="rf-face-title">Face captured ✓</p>
        <p class="rf-face-sub">Your photo will be used for Face ID login.</p>
        <button class="btn btn-ghost rf-retake" type="button" @click="$emit('retake-face')">
          ↩ Retake photo
        </button>
      </div>
    </div>

    <!-- ── Document Details ─────────────────────── -->
    <div class="doc-sections">

      <!-- Driver's License -->
      <div class="doc-section">
        <div class="doc-section-header">
          <span class="doc-section-icon">🪪</span>
          <span class="doc-section-label">Driver's License</span>
          <button class="btn-retake-doc" type="button" @click="$emit('retake-license')">
            ↩ Retake
          </button>
        </div>
        <div class="doc-info-grid">
          <div class="doc-info-row">
            <span class="doc-info-key">Full Name</span>
            <span class="doc-info-val">{{ props.licenseName || '—' }}</span>
          </div>
          <div class="doc-info-row">
            <span class="doc-info-key">License Number</span>
            <span class="doc-info-val">{{ props.licenseNumber || '—' }}</span>
          </div>
          <div class="doc-info-row">
            <span class="doc-info-key">Expiry Date</span>
            <span class="doc-info-val">{{ props.licenseExpiry || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- OR -->
      <div class="doc-section">
        <div class="doc-section-header">
          <span class="doc-section-icon">🧾</span>
          <span class="doc-section-label">Official Receipt (OR)</span>
          <button class="btn-retake-doc" type="button" @click="$emit('retake-or')">
            ↩ Retake
          </button>
        </div>
        <div class="doc-info-grid">
          <div class="doc-info-row">
            <span class="doc-info-key">Renewal Date</span>
            <span class="doc-info-val">{{ props.orRenewalDate || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- CR -->
      <div class="doc-section">
        <div class="doc-section-header">
          <span class="doc-section-icon">🏍️</span>
          <span class="doc-section-label">Certificate of Registration (CR)</span>
          <button class="btn-retake-doc" type="button" @click="$emit('retake-cr')">
            ↩ Retake
          </button>
        </div>
        <div class="doc-info-grid">
          <div class="doc-info-row">
            <span class="doc-info-key">Plate Number</span>
            <span class="doc-info-val">{{ props.plateNumber || '—' }}</span>
          </div>
          <div class="doc-info-row">
            <span class="doc-info-key">Brand</span>
            <span class="doc-info-val">{{ props.crBrand || '—' }}</span>
          </div>
          <div class="doc-info-row">
            <span class="doc-info-key">Color</span>
            <span class="doc-info-val">{{ props.crColor || '—' }}</span>
          </div>
          <div class="doc-info-row">
            <span class="doc-info-key">Year</span>
            <span class="doc-info-val">{{ props.crYear || '—' }}</span>
          </div>
        </div>
      </div>

    </div>

    <div class="divider">Account details</div>

    <!-- ── Registration form ─────────────────────── -->
    <form @submit.prevent="handleSubmit" novalidate>
      <div class="form-group">
        <label class="form-label" for="rf-fullname">Full name</label>
        <input
          id="rf-fullname"
          v-model="form.full_name"
          type="text"
          class="form-input"
          :class="{ error: touched.full_name && !form.full_name }"
          placeholder="Juan Dela Cruz"
          autocomplete="name"
          @blur="touch('full_name')"
        />
        <span v-if="touched.full_name && !form.full_name" class="field-err">Full name is required</span>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label" for="rf-username">Username</label>
          <input
            id="rf-username"
            v-model="form.username"
            type="text"
            class="form-input"
            :class="{ error: touched.username && usernameErr }"
            placeholder="juandelacruz"
            autocomplete="username"
            @blur="touch('username')"
          />
          <span v-if="touched.username && usernameErr" class="field-err">{{ usernameErr }}</span>
        </div>

        <div class="form-group">
          <label class="form-label" for="rf-email">Email</label>
          <input
            id="rf-email"
            v-model="form.email"
            type="email"
            class="form-input"
            :class="{ error: touched.email && emailErr }"
            placeholder="juan@example.com"
            autocomplete="email"
            @blur="touch('email')"
          />
          <span v-if="touched.email && emailErr" class="field-err">{{ emailErr }}</span>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label" for="rf-password">Password</label>
          <div class="input-wrap">
            <input
              id="rf-password"
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              class="form-input"
              :class="{ error: touched.password && passwordErr }"
              placeholder="Min. 8 characters"
              autocomplete="new-password"
              @blur="touch('password')"
            />
            <button type="button" class="eye-btn" @click="showPwd = !showPwd">
              <svg v-if="!showPwd" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
              <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
            </button>
          </div>
          <div v-if="form.password" class="strength-bar">
            <div class="strength-fill" :style="{ width: strengthPct + '%', background: strengthColor }"></div>
          </div>
          <span v-if="touched.password && passwordErr" class="field-err">{{ passwordErr }}</span>
        </div>

        <div class="form-group">
          <label class="form-label" for="rf-confirm">Confirm password</label>
          <input
            id="rf-confirm"
            v-model="form.confirm_password"
            :type="showPwd ? 'text' : 'password'"
            class="form-input"
            :class="{ error: touched.confirm_password && confirmErr }"
            placeholder="Repeat password"
            autocomplete="new-password"
            @blur="touch('confirm_password')"
          />
          <span v-if="touched.confirm_password && confirmErr" class="field-err">{{ confirmErr }}</span>
        </div>
      </div>

      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input
            type="checkbox"
            v-model="confirmDetails"
          />
          <span>I confirm all these details are correct.</span>
        </label>
      </div>

      <button
        id="register-submit-btn"
        type="submit"
        class="btn btn-success"
        :disabled="loading || !canSubmit"
        style="margin-top: 0.5rem;"
      >
        <span v-if="loading" class="spinner spinner-sm"></span>
        <span>{{ loading ? 'Creating account…' : 'Create account' }}</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  faceImage:      { type: String, required: true },
  licenseNumber:  { type: String, default: '' },
  licenseName:    { type: String, default: '' },
  licenseExpiry:  { type: String, default: '' },
  orRenewalDate:  { type: String, default: '' },
  plateNumber:    { type: String, default: '' },
  crBrand:        { type: String, default: '' },
  crColor:        { type: String, default: '' },
  crYear:         { type: String, default: '' },
  loading:        { type: Boolean, default: false },
  initialFullName:{ type: String, default: '' },
})
const emit = defineEmits(['submit', 'retake-face', 'retake-license', 'retake-or', 'retake-cr'])

const form = ref({
  full_name:        props.initialFullName || '',
  username:         '',
  email:            '',
  password:         '',
  confirm_password: '',
})
const confirmDetails = ref(false)
const showPwd = ref(false)
const touched = ref({})

function touch(f) { touched.value[f] = true }

/* ── Validation ── */
const usernameErr = computed(() => {
  const u = form.value.username
  if (!u) return 'Username is required'
  if (u.length < 3) return 'At least 3 characters'
  if (!/^[a-zA-Z0-9_]+$/.test(u)) return 'Letters, numbers and _ only'
  return ''
})

const emailErr = computed(() => {
  const e = form.value.email
  if (!e) return 'Email is required'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return 'Invalid email address'
  return ''
})

const passwordErr = computed(() => {
  const p = form.value.password
  if (!p) return 'Password is required'
  if (p.length < 8) return 'At least 8 characters'
  return ''
})

const confirmErr = computed(() => {
  if (!form.value.confirm_password) return 'Please confirm your password'
  if (form.value.password !== form.value.confirm_password) return 'Passwords do not match'
  return ''
})

/* ── Password strength ── */
const strengthScore = computed(() => {
  const p = form.value.password
  if (!p) return 0
  let score = 0
  if (p.length >= 8)  score++
  if (p.length >= 12) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  return score
})

const strengthPct   = computed(() => (strengthScore.value / 5) * 100)
const strengthColor = computed(() => {
  if (strengthScore.value <= 1) return '#ef4444'
  if (strengthScore.value <= 2) return '#f59e0b'
  if (strengthScore.value <= 3) return '#6366f1'
  return '#10b981'
})

const canSubmit = computed(() =>
  !usernameErr.value && !emailErr.value && !passwordErr.value && !confirmErr.value && form.value.full_name && confirmDetails.value
)

/* ── Submit ── */
function handleSubmit() {
  ['full_name','username','email','password','confirm_password'].forEach(touch)
  if (!confirmDetails.value) return
  if (!canSubmit.value) return
  emit('submit', { ...form.value })
}
</script>

<style scoped>
.rf-root { width: 100%; }

/* ── Face preview row ── */
.rf-face-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: rgba(16,185,129,0.06);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: var(--radius-md);
  padding: 1.1rem 1.25rem;
  margin-bottom: 1rem;
}

.rf-face-wrap {
  position: relative;
  width: 72px; height: 72px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid var(--success);
  box-shadow: 0 0 16px var(--success-glow);
}

.rf-face-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.rf-face-ok {
  position: absolute;
  bottom: 2px; right: 2px;
  width: 22px; height: 22px;
  background: var(--success);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.rf-face-ok svg { width: 13px; height: 13px; fill: #fff; }

.rf-face-title { font-size: 0.9rem; font-weight: 600; color: var(--success); }
.rf-face-sub   { font-size: 0.78rem; color: var(--text-2); margin-top: 0.2rem; line-height: 1.4; }

.rf-retake {
  margin-top: 0.6rem;
  padding: 0.35rem 0.85rem;
  font-size: 0.78rem;
}

/* ── Document sections ── */
.doc-sections {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 0.5rem;
}

.doc-section {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: border-color 0.2s;
}
.doc-section:hover {
  border-color: rgba(99,102,241,0.3);
}

.doc-section-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--border);
}

.doc-section-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.doc-section-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-1);
  flex: 1;
  letter-spacing: 0.01em;
}

.btn-retake-doc {
  background: none;
  border: 1px solid rgba(99,102,241,0.35);
  border-radius: 6px;
  color: #818cf8;
  font-size: 0.73rem;
  font-weight: 500;
  padding: 0.25rem 0.65rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-retake-doc:hover {
  background: rgba(99,102,241,0.12);
  border-color: #818cf8;
  color: #a5b4fc;
}

.doc-info-grid {
  padding: 0.5rem 1rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.doc-info-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.82rem;
  line-height: 1.5;
}

.doc-info-key {
  color: var(--text-3);
  min-width: 110px;
  flex-shrink: 0;
  font-size: 0.78rem;
}

.doc-info-val {
  color: var(--text-1);
  font-weight: 500;
  word-break: break-all;
}

/* ── Password strength ── */
.strength-bar {
  height: 3px;
  background: var(--border);
  border-radius: 99px;
  margin-top: 6px;
  overflow: hidden;
}
.strength-fill {
  height: 100%;
  border-radius: 99px;
  transition: width .4s ease, background .4s ease;
}

/* ── Input with eye toggle ── */
.input-wrap { position: relative; }
.input-wrap .form-input { padding-right: 2.75rem; }

.eye-btn {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-3);
  padding: 0.25rem;
  display: flex;
  transition: color .2s;
}
.eye-btn:hover { color: var(--text-1); }
.eye-btn svg { width: 18px; height: 18px; }

/* ── Field error ── */
.field-err {
  font-size: 0.75rem;
  color: #fca5a5;
  margin-top: 0.15rem;
  display: block;
}

.checkbox-group {
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.95rem;
  color: var(--text-1);
}

.checkbox-label input {
  margin-top: 0.15rem;
  width: 1rem;
  height: 1rem;
}
</style>
