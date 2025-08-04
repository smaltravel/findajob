<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// Emits
const emit = defineEmits(['workflow-completed'])

// Reactive data
const keywords = ref('')
const location = ref('')
const workflowStarted = ref(false)
const workflowStatus = ref('idle')
const workflowProgress = ref(0)
const workflowMessage = ref('')
const jobsFound = ref(0)
const pipelineStage = ref(0)
const statusInterval = ref(null)

// Pipeline stages data
const pipelineStages = ref([
  { id: 1, name: 'Job Search', description: 'Searching for job opportunities', status: 'stand' },
  { id: 2, name: 'Data Collection', description: 'Collecting job data', status: 'stand' },
  { id: 3, name: 'Data Processing', description: 'Processing collected data', status: 'stand' },
  { id: 4, name: 'Data Analysis', description: 'Analyzing processed data', status: 'stand' },
  { id: 5, name: 'Results Export', description: 'Exporting final results', status: 'stand' }
])

// API base URL
const API_BASE_URL = 'http://localhost:5000/api'

// Methods
const startWorkflow = async () => {
  // Validate inputs
  if (!keywords.value.trim()) {
    alert('Please enter keywords')
    return
  }
  if (!location.value.trim()) {
    alert('Please enter location')
    return
  }

  try {
    workflowStarted.value = true
    workflowMessage.value = 'Starting workflow...'
    
    // Update first stage to in-progress
    updateStageStatus(1, 'in-progress')
    
    // Call the backend API
    const response = await fetch(`${API_BASE_URL}/start-workflow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        keywords: keywords.value.trim(),
        location: location.value.trim()
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Failed to start workflow')
    }
    
    // Start polling for status
    startStatusPolling()
    
  } catch (error) {
    console.error('Error starting workflow:', error)
    workflowMessage.value = `Error: ${error.message}`
    workflowStarted.value = false
    updateStageStatus(1, 'finished-failed')
  }
}

const startStatusPolling = () => {
  statusInterval.value = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow-status`)
      if (response.ok) {
        const status = await response.json()
        updateWorkflowStatus(status)
      }
    } catch (error) {
      console.error('Error polling status:', error)
    }
  }, 2000) // Poll every 2 seconds
}

const updateWorkflowStatus = (status) => {
  workflowStatus.value = status.current_stage
  workflowProgress.value = status.progress
  workflowMessage.value = status.message
  jobsFound.value = status.jobs_found
  pipelineStage.value = status.pipeline_stage || 0
  
  // Update pipeline stages based on status
  if (status.current_stage === 'searching') {
    updateStageStatus(1, 'in-progress')
  } else if (status.current_stage === 'completed') {
    // Handle pipeline stages
    if (status.pipeline_stage >= 1) {
      updateStageStatus(1, 'finished-success')
    }
    
    if (status.pipeline_stage >= 2) {
      updateStageStatus(2, 'finished-success')
    }
    
    if (status.pipeline_stage >= 3) {
      updateStageStatus(3, 'finished-success')
    }
    
    if (status.pipeline_stage >= 4) {
      updateStageStatus(4, 'finished-success')
      updateStageStatus(5, 'finished-success')
      workflowStarted.value = false
      workflowMessage.value = `Pipeline completed! Generated ${jobsFound.value} application tiles.`
      stopStatusPolling()
      
      // Emit workflow completion with results
      if (status.results) {
        emit('workflow-completed', status.results)
      }
    }
  } else if (status.current_stage === 'error') {
    // Mark current stage as failed
    if (pipelineStage.value > 0) {
      updateStageStatus(pipelineStage.value, 'finished-failed')
    } else {
      updateStageStatus(1, 'finished-failed')
    }
    workflowStarted.value = false
    workflowMessage.value = `Workflow failed: ${status.message}`
    stopStatusPolling()
  }
}

const updateStageStatus = (stageId, status) => {
  const stage = pipelineStages.value.find(s => s.id === stageId)
  if (stage) {
    stage.status = status
  }
}

const stopStatusPolling = () => {
  if (statusInterval.value) {
    clearInterval(statusInterval.value)
    statusInterval.value = null
  }
}

const viewLogs = (stageId, status) => {
  console.log(`Viewing logs for stage ${stageId} (${status})`)
  
  let logMessage = ''
  switch (stageId) {
    case 1:
      logMessage = 'Job Search Stage:\n- Crawled LinkedIn for job listings\n- Extracted job details and metadata\n- Stored jobs in database'
      break
    case 2:
      logMessage = 'Data Collection Stage:\n- Gathered jobs from database\n- Filtered jobs with status "new"\n- Prepared data for AI processing'
      break
    case 3:
      logMessage = 'Data Processing Stage:\n- Sent job data to Ollama AI\n- Generated short descriptions\n- Created updated CV sections\n- Generated personalized cover letters'
      break
    case 4:
      logMessage = 'Data Analysis Stage:\n- Analyzed AI-generated content\n- Validated job requirements\n- Prepared application data'
      break
    case 5:
      logMessage = 'Results Export Stage:\n- Generated application tiles\n- Combined job data with AI content\n- Made jobs available for application'
      break
    default:
      logMessage = `Stage ${stageId} - ${status}`
  }
  
  alert(logMessage)
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

const getStageDescription = (stageId) => {
  switch (stageId) {
    case 1:
      return 'Crawling LinkedIn for job listings'
    case 2:
      return 'Gathering and filtering job data'
    case 3:
      return 'Processing with AI (Ollama)'
    case 4:
      return 'Analyzing and preparing data'
    case 5:
      return 'Generating application tiles'
    default:
      return 'Processing...'
  }
}

// Cleanup on component unmount
onUnmounted(() => {
  stopStatusPolling()
})
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4 text-gray-700">Workflow</h2>
    
    <!-- Input Fields -->
    <div class="space-y-4 mb-6">
      <div>
        <label for="keywords" class="block text-sm font-medium text-gray-700 mb-2">
          Keywords <span class="text-red-500">*</span>
        </label>
        <input
          v-model="keywords"
          type="text"
          id="keywords"
          placeholder="e.g., Python Developer, React"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          :disabled="workflowStarted"
        />
      </div>
      
      <div>
        <label for="location" class="block text-sm font-medium text-gray-700 mb-2">
          Location <span class="text-red-500">*</span>
        </label>
        <input
          v-model="location"
          type="text"
          id="location"
          placeholder="e.g., San Francisco, CA"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          :disabled="workflowStarted"
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
      {{ workflowStarted ? 'Workflow Running...' : 'Start Workflow' }}
    </button>

    <!-- Workflow Status -->
    <div v-if="workflowMessage" class="mb-6 p-4 bg-gray-50 rounded-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Status:</span>
        <span class="text-sm text-gray-600">{{ workflowStatus }}</span>
      </div>
      <div class="mb-2">
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${workflowProgress}%` }"
          ></div>
        </div>
      </div>
      <p class="text-sm text-gray-600">{{ workflowMessage }}</p>
      <p v-if="jobsFound > 0" class="text-sm text-green-600 font-medium mt-1">
        Jobs found: {{ jobsFound }}
      </p>
      <p v-if="pipelineStage > 0" class="text-sm text-blue-600 font-medium mt-1">
        Pipeline Stage: {{ pipelineStage }}/4
      </p>
    </div>

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
            <p class="text-sm text-gray-500">{{ getStageDescription(stage.id) }}</p>
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