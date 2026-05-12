<template>
  <div class="auth-page">
    <div class="auth-card-wide glass" style="padding: 2.5rem;">
      <!-- Header -->
      <div class="auth-header">
        <div class="auth-logo">
          <svg viewBox="0 0 24 24"><path d="M9.5 11.5c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5.448-1.5 1-1.5 1 .672 1 1.5zm5 0c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5.448-1.5 1-1.5 1 .672 1 1.5zM12 18c-2.28 0-4.22-.97-5.49-2.5h10.98C16.22 17.03 14.28 18 12 18zM22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z"/></svg>
        </div>
        <h1 class="auth-title">Create your account</h1>
        <p class="auth-subtitle">Face scan required to complete registration</p>
      </div>

      <!-- Step indicator -->
      <div class="steps">
        <div :class="['step', step >= 1 ? 'active' : '', step > 1 ? 'done' : '']">
          <div class="step-num">{{ step > 1 ? '✓' : '1' }}</div>
          <span>Face Scan</span>
        </div>
        <div class="step-line"></div>
        <div :class="['step', step >= 2 ? 'active' : '']">
          <div class="step-num">2</div>
          <span>Your Details</span>
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

      <!-- Step 1: Face capture -->
      <Transition name="slide-up" mode="out-in">
        <FaceCapture v-if="step === 1" @captured="onFaceCaptured" />
      </Transition>

      <!-- Step 2: Registration form -->
      <Transition name="slide-up" mode="out-in">
        <RegisterForm
          v-if="step === 2"
          :face-image="faceImage"
          :loading="loading"
          @submit="handleRegister"
          @retake="retake"
        />
      </Transition>

      <div class="auth-footer">
        Already have an account?
        <RouterLink to="/login">Sign in</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
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

function onFaceCaptured(base64) {
  faceImage.value = base64
  step.value = 2
}

function retake() {
  faceImage.value = null
  step.value = 1
  error.value = ''
}

async function handleRegister(formData) {
  error.value = ''
  loading.value = true
  try {
    const registrationData = { ...formData, role: 'passenger' }
    await auth.register(registrationData, faceImage.value, appId.value)
    router.push('/passenger')
  } catch (e) {
    error.value = e.message || 'Registration failed. Please try again.'
    loading.value = false
  }
}
</script>
