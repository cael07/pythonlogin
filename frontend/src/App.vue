<template>
  <div>
    <div style="position: fixed; top: 0; left: 0; background: red; color: white; z-index: 9999; padding: 5px;">DEBUG: APP MOUNTED</div>
    <RouterView v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>
