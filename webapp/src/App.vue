<script setup>
import { ref } from 'vue'
import WorkflowSection from './components/WorkflowSection.vue'
import ApplicationsSection from './components/ApplicationsSection.vue'

// Reactive data for communication between components
const crawledJobs = ref([])
const jobsProcessed = ref(0)

// Methods to handle communication
const handleJobsProcessed = (count) => {
  jobsProcessed.value = count
  console.log(`Processed ${count} new jobs from workflow`)
}

const handleWorkflowCompleted = (jobs) => {
  crawledJobs.value = jobs || []
  console.log(`Workflow completed with ${jobs?.length || 0} jobs`)
}
</script>

<template>
  <div class="bg-gray-200 min-h-screen flex items-center justify-center rounded-lg p-4">
    <div class="flex w-full max-w-6xl">
      <!-- Workflow Section -->
      <WorkflowSection 
        class="w-1/3 mr-8" 
        @workflow-completed="handleWorkflowCompleted"
      />
      
      <!-- Applications Section -->
      <ApplicationsSection 
        class="w-2/3" 
        :crawled-jobs="crawledJobs"
        @jobs-processed="handleJobsProcessed"
      />
    </div>
  </div>
</template>

<style scoped>
/* Global styles can be added here if needed */
</style>
