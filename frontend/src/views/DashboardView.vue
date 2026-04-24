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
        <div class="user-avatar">{{ initials }}</div>
        <div class="user-info">
          <span class="user-name">{{ user?.full_name }}</span>
          <span class="user-email">{{ user?.email }}</span>
          <span class="user-username">@{{ user?.username }}</span>
        </div>
        <div v-if="user?.face_image_path" class="user-face-badge">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9.5 11.5c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5.448-1.5 1-1.5 1 .672 1 1.5zm5 0c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5.448-1.5 1-1.5 1 .672 1 1.5zM12 18c-2.28 0-4.22-.97-5.49-2.5h10.98C16.22 17.03 14.28 18 12 18zM22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z"/></svg>
          Face ID Active
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth  = useAuthStore()
const router = useRouter()
const user   = computed(() => auth.user)

const initials = computed(() => {
  if (!user.value?.full_name) return '?'
  return user.value.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

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

.user-avatar {
  width: 60px; height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}
.user-name     { font-size: 1.05rem; font-weight: 600; }
.user-email    { font-size: 0.85rem; color: var(--text-2); }
.user-username { font-size: 0.8rem; color: var(--text-3); }

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
