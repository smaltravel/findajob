<script setup>
import { ref, onMounted } from 'vue'

// Reactive data
const keywords = ref('')
const location = ref('')
const workflowStarted = ref(false)

// Pipeline stages data
const pipelineStages = ref([
  { id: 1, name: 'Job Search', description: 'Searching for job opportunities', status: 'stand' },
  { id: 2, name: 'Data Collection', description: 'Collecting job data', status: 'in-progress' },
  { id: 3, name: 'Data Processing', description: 'Processing collected data', status: 'finished-success' },
  { id: 4, name: 'Data Analysis', description: 'Analyzing processed data', status: 'finished-failed' },
  { id: 5, name: 'Results Export', description: 'Exporting final results', status: 'stand' }
])

// Methods
const startWorkflow = () => {
  console.log('Starting workflow...')
  workflowStarted.value = true
  
  // Simulate workflow progression (remove this in real implementation)
  setTimeout(() => {
    workflowStarted.value = false
  }, 2000)
}

const viewLogs = (stageId, status) => {
  console.log(`Viewing logs for stage ${stageId} (${status})`)
  alert(`Viewing logs for Stage ${stageId} - ${status}`)
}

const getStatusClass = (status) => {
  switch (status) {
    case 'stand':
      return 'bg-gray-100 text-gray-600'
    case 'in-progress':
      return 'bg-blue-100 text-blue-700'
    case 'finished-success':
      return 'bg-green-100 text-green-700'
    case 'finished-failed':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

const getIndicatorClass = (status) => {
  switch (status) {
    case 'stand':
      return 'bg-gray-300'
    case 'in-progress':
      return 'bg-blue-500 animate-pulse'
    case 'finished-success':
      return 'bg-green-500'
    case 'finished-failed':
      return 'bg-red-500'
    default:
      return 'bg-gray-300'
  }
}
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4 text-gray-700">Workflow</h2>
    
    <!-- Input Fields -->
    <div class="space-y-4 mb-6">
      <div>
        <label for="keywords" class="block text-sm font-medium text-gray-700 mb-2">
          Keywords
        </label>
        <input
          v-model="keywords"
          type="text"
          id="keywords"
          placeholder="e.g., Python Developer, React"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        />
      </div>
      
      <div>
        <label for="location" class="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <input
          v-model="location"
          type="text"
          id="location"
          placeholder="e.g., San Francisco, CA"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        />
      </div>
    </div>

    <!-- Start Button -->
    <button
      @click="startWorkflow"
      :disabled="workflowStarted"
      class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg shadow-md transition-colors duration-200 mb-6"
      :class="{ 'opacity-75': workflowStarted, 'bg-green-600 hover:bg-green-700': workflowStarted }"
    >
      {{ workflowStarted ? 'Starting...' : 'Start Workflow' }}
    </button>

    <!-- Pipeline Stages -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold text-gray-700 mb-3">Pipeline Stages</h3>
      
      <div
        v-for="stage in pipelineStages"
        :key="stage.id"
        class="pipeline-stage p-4 rounded-lg transition-all duration-200 hover:bg-gray-50"
        :data-stage="stage.id"
        :data-status="stage.status"
      >
        <div class="flex items-center space-x-3">
          <div 
            class="stage-indicator w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
            :class="getIndicatorClass(stage.status)"
          >
            {{ stage.id }}
          </div>
          <div class="flex-1">
            <h4 class="font-medium text-gray-700">{{ stage.name }}</h4>
            <p class="text-sm text-gray-500">{{ stage.description }}</p>
          </div>
          <div class="stage-status flex items-center space-x-2">
            <span 
              class="px-2 py-1 text-xs rounded-full"
              :class="getStatusClass(stage.status)"
            >
              {{ stage.status === 'stand' ? 'Stand' : 
                 stage.status === 'in-progress' ? 'In Progress' :
                 stage.status === 'finished-success' ? 'Success' : 'Failed' }}
            </span>
            <button 
              v-if="stage.status.includes('finished')"
              @click="viewLogs(stage.id, stage.status)"
              class="view-logs-btn px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 rounded transition-colors"
            >
              View Logs
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Pipeline Stage Styles */
.pipeline-stage {
  position: relative;
  border: 1px solid transparent;
}

.pipeline-stage:hover {
  border-color: #e5e7eb;
  transform: translateY(-1px);
}

.pipeline-stage:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 1rem;
  top: 100%;
  width: 2px;
  height: 1rem;
  background: linear-gradient(to bottom, #d1d5db, transparent);
  z-index: 1;
}

.stage-indicator {
  position: relative;
  z-index: 2;
  transition: all 0.3s ease;
}

.stage-indicator:hover {
  transform: scale(1.1);
}

/* Animation for in-progress stages */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Status badge animations */
.stage-status span {
  transition: all 0.2s ease;
}

.stage-status span:hover {
  transform: scale(1.05);
}

/* View logs button hover effect */
.view-logs-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Input field focus effects */
input:focus {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
}

/* Start button loading state */
button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}
</style> 