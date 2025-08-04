<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import JobModal from './JobModal.vue'

// Props
const props = defineProps({
  crawledJobs: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['jobs-processed'])

// Reactive data
const applications = ref([])
const selectedApplications = ref(new Set())
const currentSort = ref('status-creation')
const showModal = ref(false)
const selectedJob = ref(null)
const loading = ref(false)
const error = ref('')

// API base URL
const API_BASE_URL = 'http://localhost:5000/api'

// Computed properties
const sortedApplications = computed(() => {
  const apps = [...applications.value]
  
  switch (currentSort.value) {
    case 'title':
      return apps.sort((a, b) => a.job_title.localeCompare(b.job_title))
    
    case 'employer':
      return apps.sort((a, b) => a.employer.localeCompare(b.employer))
    
    case 'status-creation':
    default:
      const statusOrder = { 'new': 0, 'applied': 1, 'rejected': 2 }
      return apps.sort((a, b) => {
        const statusA = statusOrder[a.status] || 0
        const statusB = statusOrder[b.status] || 0
        
        if (statusA !== statusB) {
          return statusA - statusB
        }
        
        return new Date(b.created_at) - new Date(a.created_at)
      })
  }
})

const selectedCount = computed(() => selectedApplications.value.size)

// Methods
const loadJobs = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await fetch(`${API_BASE_URL}/jobs`)
    if (!response.ok) {
      throw new Error('Failed to load jobs')
    }
    
    const data = await response.json()
    applications.value = data.jobs || []
    
  } catch (err) {
    console.error('Error loading jobs:', err)
    error.value = 'Failed to load jobs from database'
  } finally {
    loading.value = false
  }
}

const toggleSelection = (applicationId) => {
  if (selectedApplications.value.has(applicationId)) {
    selectedApplications.value.delete(applicationId)
  } else {
    selectedApplications.value.add(applicationId)
  }
}

const rejectApplication = async (applicationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${applicationId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: 'rejected' })
    })
    
    if (response.ok) {
      // Update local state
      const app = applications.value.find(a => a.id === applicationId)
      if (app) {
        app.status = 'rejected'
        selectedApplications.value.delete(applicationId)
      }
    } else {
      throw new Error('Failed to update job status')
    }
  } catch (error) {
    console.error('Error rejecting application:', error)
    alert('Failed to reject application')
  }
}

const deleteApplication = async (applicationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${applicationId}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      // Remove from local state
      applications.value = applications.value.filter(a => a.id !== applicationId)
      selectedApplications.value.delete(applicationId)
    } else {
      throw new Error('Failed to delete job')
    }
  } catch (error) {
    console.error('Error deleting application:', error)
    alert('Failed to delete application')
  }
}

const openJobModal = (application) => {
  selectedJob.value = application
  showModal.value = true
}

const closeJobModal = () => {
  showModal.value = false
  selectedJob.value = null
}

const applyToJob = async (applicationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${applicationId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: 'applied' })
    })
    
    if (response.ok) {
      // Update local state
      const app = applications.value.find(a => a.id === applicationId)
      if (app) {
        app.status = 'applied'
      }
      closeJobModal()
    } else {
      throw new Error('Failed to update job status')
    }
  } catch (error) {
    console.error('Error applying to job:', error)
    alert('Failed to apply to job')
  }
}

const rejectAllSelected = async () => {
  if (selectedApplications.value.size > 0) {
    if (confirm(`Reject ${selectedApplications.value.size} selected applications?`)) {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/bulk-update`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            job_ids: Array.from(selectedApplications.value),
            status: 'rejected'
          })
        })
        
        if (response.ok) {
          // Update local state
          applications.value.forEach(app => {
            if (selectedApplications.value.has(app.id)) {
              app.status = 'rejected'
            }
          })
          selectedApplications.value.clear()
        } else {
          throw new Error('Failed to bulk update jobs')
        }
      } catch (error) {
        console.error('Error bulk rejecting applications:', error)
        alert('Failed to reject applications')
      }
    }
  }
}

const deleteAllSelected = async () => {
  if (selectedApplications.value.size > 0) {
    if (confirm(`Delete ${selectedApplications.value.size} selected applications? This action cannot be undone.`)) {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/bulk-delete`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            job_ids: Array.from(selectedApplications.value)
          })
        })
        
        if (response.ok) {
          // Remove from local state
          applications.value = applications.value.filter(
            app => !selectedApplications.value.has(app.id)
          )
          selectedApplications.value.clear()
        } else {
          throw new Error('Failed to bulk delete jobs')
        }
      } catch (error) {
        console.error('Error bulk deleting applications:', error)
        alert('Failed to delete applications')
      }
    }
  }
}

const resetSort = () => {
  currentSort.value = 'status-creation'
}

const getStatusClass = (status) => {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-700'
    case 'applied':
      return 'bg-green-100 text-green-700'
    case 'rejected':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

// Watch for crawled jobs and refresh the list
watch(() => props.crawledJobs, (newJobs) => {
  if (newJobs && newJobs.length > 0) {
    // Refresh the job list from database
    loadJobs()
    emit('jobs-processed', newJobs.length)
  }
}, { deep: true })

// Load jobs on component mount
onMounted(() => {
  loadJobs()
})
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4 text-gray-700">Applications</h2>
    
    <!-- Loading and Error States -->
    <div v-if="loading" class="mb-6 p-4 bg-blue-50 rounded-lg">
      <div class="flex items-center">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
        <span class="text-blue-600">Loading jobs...</span>
      </div>
    </div>
    
    <div v-if="error" class="mb-6 p-4 bg-red-50 rounded-lg">
      <p class="text-red-600">{{ error }}</p>
      <button 
        @click="loadJobs"
        class="mt-2 px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
      >
        Retry
      </button>
    </div>
    
    <!-- Controls Bar -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
      <!-- Sorting Controls -->
      <div class="flex items-center space-x-3">
        <label class="text-sm font-medium text-gray-700">Sort by:</label>
        <select 
          v-model="currentSort"
          class="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="status-creation">Status & Creation Time</option>
          <option value="title">Job Title</option>
          <option value="employer">Employer Name</option>
        </select>
        <button 
          @click="resetSort"
          class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md transition-colors"
        >
          Reset Sorting
        </button>
      </div>
      
      <!-- Bulk Actions -->
      <div 
        v-if="selectedCount > 0"
        class="flex items-center space-x-2"
      >
        <span class="text-sm text-gray-600">{{ selectedCount }} selected</span>
        <button 
          @click="rejectAllSelected"
          class="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors"
        >
          Reject All
        </button>
        <button 
          @click="deleteAllSelected"
          class="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors"
        >
          Delete All
        </button>
      </div>
    </div>

    <!-- Applications Grid -->
    <div v-if="!loading && applications.length === 0" class="text-center py-8">
      <p class="text-gray-500">No jobs found. Start a workflow to crawl for jobs!</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="application in sortedApplications"
        :key="application.id"
        class="application-tile bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
        @click="openJobModal(application)"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center space-x-2">
            <input 
              type="checkbox" 
              :checked="selectedApplications.has(application.id)"
              @click.stop="toggleSelection(application.id)"
              class="application-checkbox w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            >
            <span 
              class="status-indicator px-2 py-1 text-xs rounded-full"
              :class="getStatusClass(application.status)"
            >
              {{ application.status === 'new' ? 'New' : 
                 application.status === 'applied' ? 'Applied' : 'Rejected' }}
            </span>
          </div>
          <div class="flex space-x-1">
            <button 
              @click.stop="rejectApplication(application.id)"
              class="reject-btn p-1 text-gray-400 hover:text-red-500 transition-colors"
              title="Reject"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
            <button 
              @click.stop="deleteApplication(application.id)"
              class="delete-btn p-1 text-gray-400 hover:text-red-600 transition-colors"
              title="Delete"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <h3 class="job-title text-lg font-semibold text-gray-800 mb-2 hover:text-blue-600 transition-colors">
          {{ application.job_title }}
        </h3>
        
        <p class="employer-name text-sm text-gray-600 mb-3">
          {{ application.employer }}
        </p>
        
        <p class="job-description text-sm text-gray-700 line-clamp-3">
          {{ application.job_description }}
        </p>
        
        <!-- Show location if available -->
        <p v-if="application.job_location" class="text-xs text-gray-500 mt-2">
          📍 {{ application.job_location }}
        </p>
        
        <!-- Show creation date -->
        <p class="text-xs text-gray-400 mt-1">
          {{ new Date(application.created_at).toLocaleDateString() }}
        </p>
      </div>
    </div>

    <!-- Job Modal -->
    <JobModal
      v-if="showModal && selectedJob"
      :job="selectedJob"
      @close="closeJobModal"
      @apply="applyToJob"
      @reject="rejectApplication"
    />
  </div>
</template>

<style scoped>
/* Applications Section Styles */
.application-tile {
  transition: all 0.2s ease-in-out;
  position: relative;
}

.application-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Status indicator animations */
.status-indicator {
  transition: all 0.2s ease;
}

.status-indicator:hover {
  transform: scale(1.05);
}

/* Checkbox styling */
.application-checkbox {
  transition: all 0.2s ease;
}

.application-checkbox:checked {
  transform: scale(1.1);
}

/* Action buttons hover effects */
.reject-btn:hover,
.delete-btn:hover {
  transform: scale(1.1);
}

/* Sort controls styling */
select:focus {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
}

/* Responsive grid adjustments */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
  
  .application-tile {
    margin-bottom: 1rem;
  }
}

@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 