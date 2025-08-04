<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  job: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'apply', 'reject'])

const closeModal = () => {
  emit('close')
}

const applyToJob = () => {
  emit('apply', props.job.id)
}

const rejectJob = () => {
  emit('reject', props.job.id)
}

const formatText = (text) => {
  return text.replace(/\n/g, '<br>')
}
</script>

<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 z-50" @click="closeModal">
    <div class="flex items-center justify-center min-h-screen p-4" @click.stop>
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 class="text-2xl font-bold text-gray-800">{{ job.title }}</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <!-- Modal Content -->
        <div class="p-6 space-y-6">
          <!-- Job Details -->
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-2">Job Details</h3>
            <p class="text-gray-600 mb-4">{{ job.employer }}</p>
            <div class="text-gray-700 leading-relaxed" v-html="formatText(job.fullDescription)"></div>
          </div>

          <!-- URLs Section -->
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-3">Application URLs</h3>
            <div class="space-y-2">
              <a 
                v-for="(url, index) in job.urls" 
                :key="index"
                :href="url.url" 
                target="_blank"
                rel="noopener noreferrer"
                class="block p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                :class="{
                  'bg-blue-50 border-blue-200': index === 0,
                  'bg-green-50 border-green-200': index === 1,
                  'bg-purple-50 border-purple-200': index === 2
                }"
              >
                <span 
                  class="font-medium block"
                  :class="{
                    'text-blue-800': index === 0,
                    'text-green-800': index === 1,
                    'text-purple-800': index === 2
                  }"
                >
                  {{ url.name }}
                </span>
                <span 
                  class="text-sm block mt-1"
                  :class="{
                    'text-blue-600': index === 0,
                    'text-green-600': index === 1,
                    'text-purple-600': index === 2
                  }"
                >
                  {{ url.url }}
                </span>
              </a>
            </div>
          </div>

          <!-- AI Generated Content -->
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-3">AI Generated Content</h3>
            
            <!-- CV Section -->
            <div class="mb-4">
              <h4 class="font-medium text-gray-700 mb-2">Tailored CV</h4>
              <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{{ job.cv }}</div>
              </div>
            </div>

            <!-- Cover Letter Section -->
            <div>
              <h4 class="font-medium text-gray-700 mb-2">Cover Letter</h4>
              <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{{ job.coverLetter }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="flex items-center justify-between p-6 border-t border-gray-200">
          <div class="flex space-x-3">
            <button 
              @click="applyToJob"
              class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors"
            >
              Apply
            </button>
            <button 
              @click="rejectJob"
              class="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
            >
              Reject
            </button>
          </div>
          <button 
            @click="closeModal"
            class="px-6 py-2 bg-gray-300 hover:bg-gray-400 text-gray-700 font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Modal animations */
.fixed {
  animation: fadeIn 0.3s ease;
}

.bg-white {
  animation: slideIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* URL links hover effect */
a:hover {
  transform: translateX(4px);
  transition: transform 0.2s ease;
}
</style> 