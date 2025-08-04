<script setup>
import WorkflowSection from './components/WorkflowSection.vue'
import ApplicationsSection from './components/ApplicationsSection.vue'
</script>

<template>
  <div class="bg-gray-200 min-h-screen flex items-center justify-center rounded-lg p-4">
    <div class="flex w-full max-w-6xl">
      <!-- Workflow Section -->
      <WorkflowSection class="w-1/3 mr-8" />
      
      <!-- Applications Section -->
      <ApplicationsSection class="w-2/3" />
    </div>
  </div>
</template>

<style scoped>
/* Global styles can be added here if needed */
</style>
