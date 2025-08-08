<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div>
    <nav class="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-12 flex items-center justify-between">
        <div class="flex items-center gap-4 text-sm">
          <RouterLink to="/" class="text-gray-700 hover:text-blue-700">Jobs</RouterLink>
          <RouterLink to="/triage" class="text-gray-700 hover:text-blue-700">Triage</RouterLink>
        </div>
      </div>
    </nav>
    <RouterView />
  </div>
</template>

<style>
/* Global styles */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}
</style>
