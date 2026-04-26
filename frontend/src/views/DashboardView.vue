<template>
  <div class="auth-page">
    <div class="dash-wrap glass">
      <!-- Header -->
      <div class="dash-header">
        <div class="dash-logo">
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
        <div>
          <h1 class="dash-title">Welcome back, {{ user?.full_name?.split(' ')[0] }}!</h1>
          <p class="dash-sub">You're securely authenticated.</p>
        </div>
        <button class="btn btn-ghost logout-btn" @click="handleLogout">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
          Sign out
        </button>
      </div>

      <!-- User card -->
      <div class="user-card glass">
        <div v-if="user?.face_image_base64" class="user-face-container">
          <img :src="user.face_image_base64" alt="User face" class="user-face-img" />
        </div>
        <div v-else class="user-avatar">{{ initials }}</div>
        
        <div class="user-info">
          <span class="user-name">{{ user?.full_name }}</span>
          <span class="user-email">{{ user?.email }}</span>
          <span class="user-username">@{{ user?.username }}</span>
          
          <button 
            v-if="biometricAvailable && !fingerprintEnabled" 
            class="btn btn-outline btn-sm fingerprint-setup-btn"
            @click="setupFingerprint"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M17.81 4.47c-.08 0-.16-.02-.23-.06C15.66 3.42 14 3 12.01 3c-1.98 0-3.86.44-5.57 1.31-.28.14-.62.03-.76-.25-.14-.28-.03-.62.25-.76 1.88-.96 3.94-1.45 6.08-1.45 2.15 0 4.02.48 5.7 1.4.28.15.38.49.23.77-.09.16-.24.25-.43.25zm3.22 5.46c-.07 0-.14-.02-.22-.05-1.94-.77-4.12-1.16-6.48-1.16-2.49 0-4.74.41-6.69 1.21-.28.12-.6.01-.71-.26-.12-.28-.01-.6.26-.71 2.11-.86 4.54-1.3 7.14-1.3 2.52 0 4.86.41 6.95 1.24.27.11.41.42.3.69-.09.21-.3.34-.55.34zm-14.8 5.16c-.06 0-.12-.01-.19-.04-1.27-.47-2.11-1.17-2.58-2.18-.36-.78-.44-1.87-.24-3.23.04-.31.33-.53.64-.49.31.04.53.33.49.64-.17 1.15-.12 2.02.16 2.62.33.72.96 1.23 1.91 1.58.29.11.43.43.32.72-.09.24-.31.38-.51.38zm11.75 3.32c-.11 0-.22-.03-.32-.09-2.01-1.21-4.7-1.82-7.98-1.82-1.74 0-3.51.17-5.26.51-.31.06-.6-.15-.66-.46-.06-.31.15-.6.46-.66 1.86-.36 3.73-.54 5.46-.54 3.49 0 6.36.65 8.52 1.95.27.16.35.5.19.77-.1.17-.28.34-.41.34zm-4.32 2.1c-.08 0-.17-.02-.24-.07-2.61-1.63-3.66-2.55-5.26-2.55-1.12 0-2.22.25-3.37.75-.28.12-.61-.01-.73-.29-.12-.28.01-.61.29-.73 1.3-.57 2.58-.87 3.81-.87 1.98 0 3.33.99 6.22 2.8.26.16.34.5.18.76-.11.17-.28.2-.4.2zM12 21c-.28 0-.5-.22-.5-.5s.22-.5.5-.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2c0 .28-.22.5-.5.5s-.5-.22-.5-.5c0-1.65 1.35-3 3-3s3 1.35 3 3-1.35 3-3 3z"/></svg>
            Allow Fingerprint Login
          </button>
          <div v-else-if="fingerprintEnabled" class="fingerprint-status">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
            Fingerprint Linked
          </div>
        </div>
      </div>

      <!-- App token info -->
      <div class="token-section glass">
        <h3 class="token-title">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>
          Integration Guide
        </h3>
        <p class="token-desc">Other applications can authenticate via this service using JWT. Send users to:</p>
        <div class="code-block">
          <code>GET http://localhost:5173/login?app=<span class="hl">your-app-id</span></code>
        </div>
        <p class="token-desc" style="margin-top:.75rem;">Then verify tokens server-side via:</p>
        <div class="code-block">
          <code>GET http://localhost:8000/auth/me<br>Authorization: Bearer &lt;token&gt;</code>
        </div>
      </div>

      <div class="dash-footer">
        <span>AuthPortal v1.0</span>
        <span>·</span>
        <a href="http://localhost:8000/docs" target="_blank">API Docs ↗</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth  = useAuthStore()
const router = useRouter()
const user   = computed(() => auth.user)

const biometricAvailable = ref(false)
const fingerprintEnabled = ref(false)

onMounted(async () => {
  try {
    const isSecure = window.location.protocol === 'https:' || window.location.hostname === 'localhost'
    biometricAvailable.value = !!(window.PublicKeyCredential && isSecure)
    
    // Check local storage for fingerprint status once user is loaded
    if (user.value?.username) {
      fingerprintEnabled.value = localStorage.getItem(`fp_${user.value.username}`) === 'true'
    }
  } catch (e) {}
})

const initials = computed(() => {
  if (!user.value?.full_name) return '?'
  return user.value.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

async function setupFingerprint() {
  try {
    // In a real app, the server would provide a creation challenge
    const challenge = new Uint8Array(32)
    window.crypto.getRandomValues(challenge)
    const userId = new Uint8Array(16)
    window.crypto.getRandomValues(userId)

    const credential = await navigator.credentials.create({
      publicKey: {
        challenge,
        rp: { name: "PythonLogin Auth" },
        user: {
          id: userId,
          name: user.value.username,
          displayName: user.value.full_name
        },
        pubKeyCredParams: [{ alg: -7, type: "public-key" }],
        timeout: 60000,
        attestation: "direct",
        userVerification: "required",
        authenticatorSelection: {
          authenticatorAttachment: "platform",
          userVerification: "required"
        }
      }
    })

    if (credential) {
      fingerprintEnabled.value = true
      localStorage.setItem(`fp_${user.value.username}`, 'true')
      alert("Fingerprint login has been enabled for this device!")
    }
  } catch (e) {
    console.error("Fingerprint setup failed:", e)
    alert("Could not set up fingerprint login. Please make sure your device supports it and try again.")
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.auth-page { padding: 2rem 1rem; }

.dash-wrap {
  max-width: 740px;
  margin: 0 auto;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.dash-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.dash-logo {
  width: 48px; height: 48px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 16px var(--primary-glow);
}
.dash-logo svg { width: 24px; height: 24px; fill: #fff; }

.dash-title { font-size: 1.4rem; font-weight: 700; }
.dash-sub   { font-size: 0.85rem; color: var(--text-2); }

.logout-btn { margin-left: auto; }

.user-card {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.user-avatar, .user-face-container {
  width: 80px; height: 80px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 3px solid rgba(255,255,255,0.1);
}

.user-avatar {
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.user-face-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}
.user-name     { font-size: 1.2rem; font-weight: 600; }
.user-email    { font-size: 0.9rem; color: var(--text-2); }
.user-username { font-size: 0.85rem; color: var(--text-3); }

.user-face-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--success);
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.25);
  padding: 0.35rem 0.75rem;
  border-radius: 99px;
}
.user-face-badge svg { width: 14px; height: 14px; }

.fingerprint-setup-btn {
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  border-color: var(--primary-light);
  color: var(--primary-light);
  width: fit-content;
}

.fingerprint-status {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--success);
  font-weight: 500;
}

.btn-sm { padding: 0.4rem 0.8rem; font-size: 0.8rem; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-2);
}
.btn-outline:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary-light);
}

.token-section { padding: 1.5rem; }
.token-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.token-desc { font-size: 0.85rem; color: var(--text-2); margin-bottom: 0.5rem; }

.code-block {
  background: rgba(0,0,0,0.4);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  font-family: 'Courier New', monospace;
  font-size: 0.82rem;
  color: #a5b4fc;
  overflow-x: auto;
}
.hl { color: var(--success); }

.dash-footer {
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}
.dash-footer a { color: var(--primary-light); text-decoration: none; }
.dash-footer a:hover { color: var(--text-1); }
</style>
