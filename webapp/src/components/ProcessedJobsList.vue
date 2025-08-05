<script setup>
import { ref, onMounted } from 'vue'

// Reactive data
const jobs = ref([])
const selectedJob = ref(null)
const showModal = ref(false)
const loading = ref(false)
const error = ref('')

// API base URL
const API_BASE_URL = 'http://localhost:3000/api'

// Methods
const loadJobs = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await fetch(`${API_BASE_URL}/processed-jobs`)
    if (!response.ok) {
      throw new Error('Failed to load jobs')
    }
    
    const data = await response.json()
    jobs.value = data.jobs || []
    
  } catch (err) {
    console.error('Error loading jobs:', err)
    error.value = 'Failed to load processed jobs'
  } finally {
    loading.value = false
  }
}

const openJobModal = async (jobId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/processed-jobs/${jobId}`)
    if (!response.ok) {
      throw new Error('Failed to load job details')
    }
    
    selectedJob.value = await response.json()
    showModal.value = true
  } catch (err) {
    console.error('Error loading job details:', err)
    alert('Failed to load job details')
  }
}

const closeModal = () => {
  showModal.value = false
  selectedJob.value = null
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const truncateText = (text, maxLength = 150) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// Load jobs on component mount
onMounted(() => {
  loadJobs()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Processed Jobs</h1>
        <p class="mt-2 text-gray-600">View all AI-processed job opportunities</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-lg text-gray-600">Loading processed jobs...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
          <p class="text-red-600 mb-4">{{ error }}</p>
          <button 
            @click="loadJobs"
            class="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="jobs.length === 0" class="text-center py-12">
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-8 max-w-md mx-auto">
          <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
          </svg>
          <h3 class="text-lg font-medium text-gray-900 mb-2">No processed jobs found</h3>
          <p class="text-gray-600">Jobs will appear here after they have been processed by the AI system.</p>
        </div>
      </div>

      <!-- Jobs Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="job in jobs"
          :key="job.id"
          class="job-tile bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 cursor-pointer"
          @click="openJobModal(job.id)"
        >
          <!-- Job Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
                {{ job.job_title }}
              </h3>
              <p class="text-sm text-gray-600">{{ job.employer }}</p>
            </div>
            <div class="ml-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Processed
              </span>
            </div>
          </div>

          <!-- Job Summary -->
          <div class="mb-4">
            <p class="text-sm text-gray-700 line-clamp-3">
              {{ truncateText(job.job_summary) }}
            </p>
          </div>

          <!-- Job Details -->
          <div class="space-y-2 mb-4">
            <div v-if="job.job_location" class="flex items-center text-sm text-gray-500">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              {{ job.job_location }}
            </div>
            
            <div v-if="job.employment_type" class="flex items-center text-sm text-gray-500">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
              </svg>
              {{ job.employment_type }}
            </div>

            <div v-if="job.seniority_level" class="flex items-center text-sm text-gray-500">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {{ job.seniority_level }}
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between text-xs text-gray-400">
            <span>Processed: {{ formatDate(job.created_at) }}</span>
            <span class="text-blue-600 hover:text-blue-700">View Details →</span>
          </div>
        </div>
      </div>

      <!-- Job Details Modal -->
      <div v-if="showModal && selectedJob" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <!-- Modal Header -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900">{{ selectedJob.job_title }}</h2>
            <button 
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <!-- Modal Content -->
          <div class="p-6 space-y-6">
            <!-- Job Overview -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Job Overview</h3>
                <div class="space-y-3">
                  <div>
                    <span class="text-sm font-medium text-gray-500">Company:</span>
                    <p class="text-gray-900">{{ selectedJob.employer }}</p>
                  </div>
                  <div v-if="selectedJob.job_location">
                    <span class="text-sm font-medium text-gray-500">Location:</span>
                    <p class="text-gray-900">{{ selectedJob.job_location }}</p>
                  </div>
                  <div v-if="selectedJob.employment_type">
                    <span class="text-sm font-medium text-gray-500">Employment Type:</span>
                    <p class="text-gray-900">{{ selectedJob.employment_type }}</p>
                  </div>
                  <div v-if="selectedJob.seniority_level">
                    <span class="text-sm font-medium text-gray-500">Seniority Level:</span>
                    <p class="text-gray-900">{{ selectedJob.seniority_level }}</p>
                  </div>
                  <div v-if="selectedJob.job_function">
                    <span class="text-sm font-medium text-gray-500">Job Function:</span>
                    <p class="text-gray-900">{{ selectedJob.job_function }}</p>
                  </div>
                  <div v-if="selectedJob.industries">
                    <span class="text-sm font-medium text-gray-500">Industries:</span>
                    <p class="text-gray-900">{{ selectedJob.industries }}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Processing Info</h3>
                <div class="space-y-3">
                  <div>
                    <span class="text-sm font-medium text-gray-500">Run ID:</span>
                    <p class="text-gray-900 font-mono text-sm">{{ selectedJob.runid }}</p>
                  </div>
                  <div>
                    <span class="text-sm font-medium text-gray-500">Processed:</span>
                    <p class="text-gray-900">{{ formatDate(selectedJob.created_at) }}</p>
                  </div>
                  <div>
                    <span class="text-sm font-medium text-gray-500">Status:</span>
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {{ selectedJob.processing_status }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- AI Generated Summary -->
            <div v-if="selectedJob.job_summary">
              <h3 class="text-lg font-semibold text-gray-900 mb-3">AI Summary</h3>
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p class="text-gray-900">{{ selectedJob.job_summary }}</p>
              </div>
            </div>

            <!-- Original Job Description -->
            <div v-if="selectedJob.job_description">
              <h3 class="text-lg font-semibold text-gray-900 mb-3">Original Job Description</h3>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                <p class="text-gray-900 whitespace-pre-wrap">{{ selectedJob.job_description }}</p>
              </div>
            </div>

            <!-- AI Generated Cover Letter -->
            <div v-if="selectedJob.cover_letter">
              <h3 class="text-lg font-semibold text-gray-900 mb-3">AI Generated Cover Letter</h3>
              <div class="bg-green-50 border border-green-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                <p class="text-gray-900 whitespace-pre-wrap">{{ selectedJob.cover_letter }}</p>
              </div>
            </div>

            <!-- External Links -->
            <div v-if="selectedJob.job_url || selectedJob.employer_url" class="flex space-x-4">
              <a 
                v-if="selectedJob.job_url"
                :href="selectedJob.job_url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                </svg>
                View Job Posting
              </a>
              <a 
                v-if="selectedJob.employer_url"
                :href="selectedJob.employer_url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9"></path>
                </svg>
                Company Profile
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.job-tile:hover {
  transform: translateY(-2px);
}

/* Modal scrollbar styling */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 