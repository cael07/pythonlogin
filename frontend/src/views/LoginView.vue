<template>
  <div class="auth-page">
    <div class="auth-card-wide glass" style="padding: 2.5rem;">
      <!-- Header -->
      <div class="auth-header">
        <div class="auth-logo">
          <svg viewBox="0 0 24 24"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>
        </div>
        <h1 class="auth-title">{{ step === 1 ? 'Welcome back' : 'Face Verification' }}</h1>
        <p class="auth-subtitle">{{ step === 1 ? 'Sign in to your account' : 'Verify your identity to continue' }}</p>
      </div>

      <!-- App badge -->
      <div v-if="appId" class="app-badge">
        <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/></svg>
        Signing in to <strong>{{ appId }}</strong>
      </div>

      <!-- Error -->
      <Transition name="fade">
        <div v-if="error" class="alert alert-error" role="alert">
          <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
          {{ error }}
        </div>
      </Transition>

      <!-- Step 1: Credentials -->
      <Transition name="slide-up" mode="out-in">
        <form v-if="step === 1" @submit.prevent="proceedToFaceScan" novalidate>
          <div class="form-group">
            <label class="form-label" for="username">Username</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="form-input"
              :class="{ error: fieldError('username') }"
              placeholder="Enter your username"
              autocomplete="username"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="password">Password</label>
            <div class="input-wrap">
              <input
                id="password"
                v-model="form.password"
                :type="showPwd ? 'text' : 'password'"
                class="form-input"
                :class="{ error: fieldError('password') }"
                placeholder="Enter your password"
                autocomplete="current-password"
                required
              />
              <button type="button" class="eye-btn" @click="showPwd = !showPwd" :aria-label="showPwd ? 'Hide password' : 'Show password'">
                <svg v-if="!showPwd" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
              </button>
            </div>
          </div>

          <button id="login-btn" type="submit" class="btn btn-primary" :disabled="loading">
            <span>Continue to Face ID</span>
          </button>

          <!-- Biometric Login Option -->
          <div v-if="biometricSupported" class="biometric-login-wrap">
            <div class="divider"><span>OR</span></div>
            <button type="button" class="btn btn-outline biometric-btn" @click="handleBiometricLogin" :disabled="loading">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M17.81 4.47c-.08 0-.16-.02-.23-.06C15.66 3.42 14 3 12.01 3c-1.98 0-3.86.44-5.57 1.31-.28.14-.62.03-.76-.25-.14-.28-.03-.62.25-.76 1.88-.96 3.94-1.45 6.08-1.45 2.15 0 4.02.48 5.7 1.4.28.15.38.49.23.77-.09.16-.24.25-.43.25zm3.22 5.46c-.07 0-.14-.02-.22-.05-1.94-.77-4.12-1.16-6.48-1.16-2.49 0-4.74.41-6.69 1.21-.28.12-.6.01-.71-.26-.12-.28-.01-.6.26-.71 2.11-.86 4.54-1.3 7.14-1.3 2.52 0 4.86.41 6.95 1.24.27.11.41.42.3.69-.09.21-.3.34-.55.34zm-14.8 5.16c-.06 0-.12-.01-.19-.04-1.27-.47-2.11-1.17-2.58-2.18-.36-.78-.44-1.87-.24-3.23.04-.31.33-.53.64-.49.31.04.53.33.49.64-.17 1.15-.12 2.02.16 2.62.33.72.96 1.23 1.91 1.58.29.11.43.43.32.72-.09.24-.31.38-.51.38zm11.75 3.32c-.11 0-.22-.03-.32-.09-2.01-1.21-4.7-1.82-7.98-1.82-1.74 0-3.51.17-5.26.51-.31.06-.6-.15-.66-.46-.06-.31.15-.6.46-.66 1.86-.36 3.73-.54 5.46-.54 3.49 0 6.36.65 8.52 1.95.27.16.35.5.19.77-.1.17-.28.34-.41.34zm-4.32 2.1c-.08 0-.17-.02-.24-.07-2.61-1.63-3.66-2.55-5.26-2.55-1.12 0-2.22.25-3.37.75-.28.12-.61-.01-.73-.29-.12-.28.01-.61.29-.73 1.3-.57 2.58-.87 3.81-.87 1.98 0 3.33.99 6.22 2.8.26.16.34.5.18.76-.11.17-.28.2-.4.2zM12 21c-.28 0-.5-.22-.5-.5s.22-.5.5-.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2c0 .28-.22.5-.5.5s-.5-.22-.5-.5c0-1.65 1.35-3 3-3s3 1.35 3 3-1.35 3-3 3z"/></svg>
              Sign in with Biometrics
            </button>
          </div>
        </form>
      </Transition>

      <!-- Step 2: Face Scan -->
      <Transition name="slide-up" mode="out-in">
        <div v-if="step === 2">
          <FaceCapture @captured="handleFaceLogin" />
          <button class="btn btn-ghost" style="margin-top:1rem; width:100%;" @click="step = 1">
            ↩ Back to password
          </button>
        </div>
      </Transition>

      <div class="auth-footer">
        Don't have an account?
        <RouterLink to="/register">Create one</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import FaceCapture from '../components/FaceCapture.vue'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

const appId = computed(() => route.query.app || null)

const step      = ref(1)
const form      = ref({ username: '', password: '' })
const faceImage = ref(null)
const loading   = ref(false)
const error     = ref('')
const showPwd   = ref(false)
const touched   = ref({})

const biometricSupported = ref(window.PublicKeyCredential && 
  (window.location.protocol === 'https:' || window.location.hostname === 'localhost'))

function fieldError(f) { return touched.value[f] && !form.value[f] }
function touch(f) { touched.value[f] = true }

async function handleBiometricLogin() {
  error.value = ''
  try {
    // Check if platform authenticator (fingerprint/face) is available
    if (window.PublicKeyCredential && 
        PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
      const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
      if (!available) {
        error.value = "Biometric sensors not found on this device."
        return
      }
    }

    // In a real WebAuthn app, we would get a challenge from the server here.
    // Since we are mocking the biometric flow for the demo:
    // 1. Trigger the OS biometric prompt
    const challenge = new Uint8Array(32)
    window.crypto.getRandomValues(challenge)

    // This triggers the Fingerprint/FaceID prompt on phone
    await navigator.credentials.get({
      publicKey: {
        challenge,
        timeout: 60000,
        userVerification: 'required',
        allowCredentials: [] // In real app, we'd pass IDs of registered keys
      }
    }).catch(e => {
      // If we have no credentials registered yet, it might fail.
      // But we just want to show the prompt.
      console.log('Biometric prompt triggered:', e)
    })

    // For the demo: if they interact with the prompt, we'll ask for username 
    // to "link" the biometric if it's the first time, OR just proceed if they have a saved session.
    if (!form.value.username) {
      error.value = "Please enter your username first to link your fingerprint."
      return
    }

    // Mock success: Auto-login since the user verified themselves to the OS
    loading.value = true
    // We reuse the login but maybe with a "biometric" flag or bypass
    // For this prototype, we'll require password once then link, but here we'll just mock the bypass.
    await auth.login(form.value.username, 'biometric_bypass_mock', appId.value)
    router.push(route.query.redirect || '/dashboard')
    
  } catch (e) {
    error.value = "Biometric authentication failed or was cancelled."
  } finally {
    loading.value = false
  }
}

async function proceedToFaceScan() {
  touch('username'); touch('password')
  if (!form.value.username || !form.value.password) {
    error.value = 'Please enter your credentials.'
    return
  }
  error.value = ''
  step.value = 2
}

async function handleFaceLogin(img) {
  faceImage.value = img
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.value.username, form.value.password, appId.value, faceImage.value)
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || 'Face login failed.'
    step.value = 1 // Go back to try again
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.app-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: var(--text-2);
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.85rem;
  margin-bottom: 1.5rem;
}
.app-badge strong { color: var(--primary-light); }

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

.biometric-login-wrap {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--text-3);
  font-size: 0.75rem;
  font-weight: 600;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border);
}

.divider:not(:empty)::before { margin-right: .75rem; }
.divider:not(:empty)::after { margin-left: .75rem; }

.biometric-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font-weight: 600;
}
</style>
