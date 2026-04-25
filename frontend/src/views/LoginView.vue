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

function fieldError(f) { return touched.value[f] && !form.value[f] }
function touch(f) { touched.value[f] = true }

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
</style>
