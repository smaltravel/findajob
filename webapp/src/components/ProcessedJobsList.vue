<script setup>
import { ref, onMounted, computed } from 'vue'

// Reactive data
const jobs = ref([])
const selectedJob = ref(null)
const showModal = ref(false)
const loading = ref(false)
const error = ref('')
const viewMode = ref('grid') // 'grid' or 'list'
const sortBy = ref('default') // 'default', 'status', 'seniority', 'title', 'employer'

// Filter state
const filters = ref({
  status: '',
  seniority: '',
  employer: '',
  title: ''
})
const showFilters = ref(false)

// API base URL
const API_BASE_URL = 'http://localhost:3000/api'

// Computed properties for unique filter options
const uniqueStatuses = computed(() => {
  const statuses = [...new Set(jobs.value.map(job => job.status).filter(Boolean))]
  return statuses.sort()
})

const uniqueSeniorities = computed(() => {
  const seniorities = [...new Set(jobs.value.map(job => job.seniority_level).filter(Boolean))]
  return seniorities.sort()
})

const uniqueEmployers = computed(() => {
  const employers = [...new Set(jobs.value.map(job => job.employer).filter(Boolean))]
  return employers.sort()
})

// Computed property for filtered jobs
const filteredJobs = computed(() => {
  return jobs.value.filter(job => {
    // Status filter
    if (filters.value.status && job.status !== filters.value.status) {
      return false
    }
    
    // Seniority filter
    if (filters.value.seniority && job.seniority_level !== filters.value.seniority) {
      return false
    }
    
    // Employer filter (case-insensitive partial match)
    if (filters.value.employer && !job.employer?.toLowerCase().includes(filters.value.employer.toLowerCase())) {
      return false
    }
    
    // Title filter (case-insensitive partial match)
    if (filters.value.title && !job.job_title?.toLowerCase().includes(filters.value.title.toLowerCase())) {
      return false
    }
    
    return true
  })
})

// Computed property for sorted jobs (now based on filtered jobs)
const sortedJobs = computed(() => {
  const jobsToSort = filteredJobs.value
  
  if (sortBy.value === 'default') {
    return jobsToSort
  }
  
  const sorted = [...jobsToSort]
  
  switch (sortBy.value) {
    case 'status':
      // Sort by status: new first, rejected last, others in middle
      const statusOrder = {
        'new': 1,
        'applied': 2,
        'interview_scheduled': 3,
        'interview_completed': 4,
        'offer_received': 5,
        'offer_accepted': 6,
        'not_answered': 7,
        'filter_rejected': 8,
        'user_rejected': 9,
        'employer_rejected': 10,
        'offer_rejected': 11
      }
      return sorted.sort((a, b) => {
        const aOrder = statusOrder[a.status] || 999
        const bOrder = statusOrder[b.status] || 999
        return aOrder - bOrder
      })
      
    case 'seniority':
      // Sort by seniority level
      const seniorityOrder = {
        'internship': 1,
        'entry level': 2,
        'associate': 3,
        'mid-senior level': 4,
        'director': 5,
        'executive': 6
      }
      return sorted.sort((a, b) => {
        const aLevel = (a.seniority_level || '').toLowerCase()
        const bLevel = (b.seniority_level || '').toLowerCase()
        const aOrder = seniorityOrder[aLevel] || 999
        const bOrder = seniorityOrder[bLevel] || 999
        return aOrder - bOrder
      })
      
    case 'title':
      // Sort by job title alphabetically
      return sorted.sort((a, b) => {
        const aTitle = (a.job_title || '').toLowerCase()
        const bTitle = (b.job_title || '').toLowerCase()
        return aTitle.localeCompare(bTitle)
      })
      
    case 'employer':
      // Sort by employer name alphabetically
      return sorted.sort((a, b) => {
        const aEmployer = (a.employer || '').toLowerCase()
        const bEmployer = (b.employer || '').toLowerCase()
        return aEmployer.localeCompare(bEmployer)
      })
      
    default:
      return sorted
  }
})

// Filter methods
const clearFilters = () => {
  filters.value = {
    status: '',
    seniority: '',
    employer: '',
    title: ''
  }
}

const hasActiveFilters = computed(() => {
  return Object.values(filters.value).some(value => value !== '')
})

const getFilteredCount = computed(() => {
  return filteredJobs.value.length
})

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
    // Parse JSON fields for each job
    jobs.value = (data.jobs || []).map(job => ({
      ...job,
      job_summary_parsed: parseJobSummary(job.job_summary),
      cover_letter_parsed: parseCoverLetter(job.cover_letter)
    }))
    
  } catch (err) {
    console.error('Error loading jobs:', err)
    error.value = 'Failed to load processed jobs'
  } finally {
    loading.value = false
  }
}

const parseJobSummary = (jobSummaryJson) => {
  if (!jobSummaryJson) return null
  
  // If it's already an object, return it
  if (typeof jobSummaryJson === 'object') {
    return jobSummaryJson
  }
  
  // If it's a string, try to parse it
  if (typeof jobSummaryJson === 'string') {
    try {
      return JSON.parse(jobSummaryJson)
    } catch (e) {
      console.error('Error parsing job summary JSON:', e)
      console.log('Raw job summary:', jobSummaryJson)
      return null
    }
  }
  
  return null
}

const parseCoverLetter = (coverLetterJson) => {
  if (!coverLetterJson) return null
  
  // If it's already an object, return it
  if (typeof coverLetterJson === 'object') {
    return coverLetterJson
  }
  
  // If it's a string, try to parse it
  if (typeof coverLetterJson === 'string') {
    try {
      return JSON.parse(coverLetterJson)
    } catch (e) {
      console.error('Error parsing cover letter JSON:', e)
      console.log('Raw cover letter:', coverLetterJson)
      return null
    }
  }
  
  return null
}

const openJobModal = async (jobId) => {
  try {
    console.log('Opening modal for job ID:', jobId)
    
    const response = await fetch(`${API_BASE_URL}/processed-jobs/${jobId}`)
    if (!response.ok) {
      throw new Error(`Failed to load job details: ${response.status}`)
    }
    
    const jobData = await response.json()
    console.log('Job data received:', jobData)
    
    // Parse JSON fields with error handling
    let jobSummaryParsed = null
    let coverLetterParsed = null
    
    try {
      jobSummaryParsed = parseJobSummary(jobData.job_summary)
    } catch (e) {
      console.warn('Failed to parse job summary:', e)
    }
    
    try {
      coverLetterParsed = parseCoverLetter(jobData.cover_letter)
    } catch (e) {
      console.warn('Failed to parse cover letter:', e)
    }
    
    selectedJob.value = {
      ...jobData,
      job_summary_parsed: jobSummaryParsed,
      cover_letter_parsed: coverLetterParsed
    }
    
    console.log('Selected job set:', selectedJob.value)
    showModal.value = true
    console.log('Modal should be visible now')
    
  } catch (err) {
    console.error('Error loading job details:', err)
    alert(`Failed to load job details: ${err.message}`)
  }
}

const closeModal = () => {
  showModal.value = false
  selectedJob.value = null
}

const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
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

const getJobSummaryText = (job) => {
  if (job.job_summary_parsed?.summary) {
    let summary = job.job_summary_parsed.summary
    
    // Add alignment info if available
    if (job.job_summary_parsed.background_aligns) {
      const alignmentText = getAlignmentText(job.job_summary_parsed.background_aligns)
      summary += ` (${alignmentText})`
    }
    
    return summary
  }
  return job.job_summary || ''
}

const getAlignmentText = (score) => {
  if (score <= 1) return 'Poor alignment'
  if (score <= 2) return 'Fair alignment'
  if (score <= 3) return 'Good alignment'
  if (score <= 4) return 'Very good alignment'
  return 'Excellent alignment'
}

const formatJobDescription = (description) => {
  if (!description) return ''
  
  // Convert to string if it's not already
  let formatted = String(description)
  
  // Replace common HTML entities
  formatted = formatted.replace(/&amp;/g, '&')
  formatted = formatted.replace(/&lt;/g, '<')
  formatted = formatted.replace(/&gt;/g, '>')
  formatted = formatted.replace(/&quot;/g, '"')
  formatted = formatted.replace(/&#39;/g, "'")
  
  // Convert line breaks to <br> tags
  formatted = formatted.replace(/\n/g, '<br>')
  
  // Convert bullet points and lists
  formatted = formatted.replace(/^\s*[-•*]\s+/gm, '• ')
  formatted = formatted.replace(/^\s*\d+\.\s+/gm, (match) => {
    const num = match.match(/\d+/)[0]
    return `${num}. `
  })
  
  // Wrap in paragraphs for better readability
  const paragraphs = formatted.split('<br><br>')
  formatted = paragraphs.map(p => `<p class="mb-3">${p}</p>`).join('')
  
  return formatted
}

const getStatusClass = (status) => {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-700'
    case 'applied':
      return 'bg-green-100 text-green-700'
    case 'user_rejected':
    case 'filter_rejected':
    case 'employer_rejected':
      return 'bg-red-100 text-red-700'
    case 'interview_scheduled':
      return 'bg-yellow-100 text-yellow-700'
    case 'interview_completed':
      return 'bg-purple-100 text-purple-700'
    case 'offer_received':
      return 'bg-indigo-100 text-indigo-700'
    case 'offer_accepted':
      return 'bg-green-100 text-green-700'
    case 'offer_rejected':
      return 'bg-red-100 text-red-700'
    case 'not_answered':
      return 'bg-gray-100 text-gray-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'new':
      return 'New'
    case 'applied':
      return 'Applied'
    case 'user_rejected':
      return 'Rejected'
    case 'filter_rejected':
      return 'Filtered'
    case 'employer_rejected':
      return 'Rejected'
    case 'interview_scheduled':
      return 'Interview'
    case 'interview_completed':
      return 'Completed'
    case 'offer_received':
      return 'Offer'
    case 'offer_accepted':
      return 'Accepted'
    case 'offer_rejected':
      return 'Rejected'
    case 'not_answered':
      return 'No Reply'
    default:
      return status
  }
}

const updateJobStatus = async (jobId, newStatus) => {
  try {
    const response = await fetch(`${API_BASE_URL}/processed-jobs/${jobId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: newStatus })
    })
    
    if (!response.ok) {
      throw new Error('Failed to update job status')
    }
    
    // Update the local job data
    const job = jobs.value.find(j => j.id === jobId)
    if (job) {
      job.status = newStatus
    }
    
    // Update selected job if it's the same one
    if (selectedJob.value && selectedJob.value.id === jobId) {
      selectedJob.value.status = newStatus
    }
    
    console.log('Job status updated successfully')
  } catch (err) {
    console.error('Error updating job status:', err)
    alert('Failed to update job status')
  }
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
      <div v-else-if="error" class="py-12">
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <p class="text-red-600 mb-4 text-left">{{ error }}</p>
          <button 
            @click="loadJobs"
            class="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="jobs.length === 0" class="py-12">
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-8 max-w-md">
          <svg class="h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
          </svg>
          <h3 class="text-lg font-medium text-gray-900 mb-2 text-left">No processed jobs found</h3>
          <p class="text-gray-600 text-left">Jobs will appear here after they have been processed by the AI system.</p>
        </div>
      </div>

      <!-- View Toggle and Jobs -->
      <div v-else>
              <!-- Filters and Controls -->
      <div class="mb-6 space-y-4">
        <!-- Filter Toggle and Results Count -->
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-4">
            <button
              @click="showFilters = !showFilters"
              class="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z"></path>
              </svg>
              <span>Filters</span>
              <span v-if="hasActiveFilters" class="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-white bg-blue-600 rounded-full">
                {{ Object.values(filters).filter(v => v !== '').length }}
              </span>
            </button>
            
            <div class="text-sm text-gray-600">
              Showing {{ getFilteredCount }} of {{ jobs.length }} jobs
            </div>
          </div>

          <!-- View Toggle -->
          <div class="flex items-center bg-white rounded-lg shadow-sm border border-gray-200 p-1">
            <button
              @click="toggleViewMode"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                viewMode === 'grid' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2-2v-2z"></path>
              </svg>
            </button>
            <button
              @click="toggleViewMode"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                viewMode === 'list' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Filter Panel -->
        <div v-if="showFilters" class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Status Filter -->
            <div>
              <label for="status-filter" class="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                id="status-filter"
                v-model="filters.status"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              >
                <option value="">All Statuses</option>
                <option v-for="status in uniqueStatuses" :key="status" :value="status">
                  {{ getStatusText(status) }}
                </option>
              </select>
            </div>

            <!-- Seniority Filter -->
            <div>
              <label for="seniority-filter" class="block text-sm font-medium text-gray-700 mb-2">Seniority Level</label>
              <select
                id="seniority-filter"
                v-model="filters.seniority"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              >
                <option value="">All Levels</option>
                <option v-for="seniority in uniqueSeniorities" :key="seniority" :value="seniority">
                  {{ seniority }}
                </option>
              </select>
            </div>

            <!-- Employer Filter -->
            <div>
              <label for="employer-filter" class="block text-sm font-medium text-gray-700 mb-2">Employer</label>
              <input
                id="employer-filter"
                v-model="filters.employer"
                type="text"
                placeholder="Search employers..."
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              />
            </div>

            <!-- Job Title Filter -->
            <div>
              <label for="title-filter" class="block text-sm font-medium text-gray-700 mb-2">Job Title</label>
              <input
                id="title-filter"
                v-model="filters.title"
                type="text"
                placeholder="Search job titles..."
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              />
            </div>
          </div>

          <!-- Filter Actions -->
          <div class="flex justify-end mt-4 pt-4 border-t border-gray-200">
            <button
              @click="clearFilters"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
            >
              Clear All Filters
            </button>
          </div>
        </div>

        <!-- Sorting -->
        <div class="flex items-center space-x-2">
          <label for="sort-select" class="text-sm font-medium text-gray-700">Sort by:</label>
          <select
            id="sort-select"
            v-model="sortBy"
            class="px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm"
          >
            <option value="default">Default (No sorting)</option>
            <option value="status">By Status (New first, Rejected last)</option>
            <option value="seniority">By Seniority Level</option>
            <option value="title">By Job Title</option>
            <option value="employer">By Employer Name</option>
          </select>
        </div>
      </div>

        <!-- Jobs Grid View -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="job in sortedJobs"
            :key="job.id"
            class="job-tile bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 cursor-pointer"
            @click="openJobModal(job.id)"
          >
            <!-- Job Header -->
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-900 mb-1 line-clamp-2 text-left">
                  {{ job.job_title }}
                </h3>
                <p class="text-sm text-gray-600 text-left">{{ job.employer }}</p>
              </div>
              <div class="ml-4">
                <div class="flex items-center space-x-2">
                  <span 
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getStatusClass(job.status)"
                  >
                    {{ getStatusText(job.status) }}
                  </span>
                  <select 
                    @change="updateJobStatus(job.id, $event.target.value)"
                    :value="job.status"
                    @click.stop
                    class="px-1 py-0.5 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    <option value="new">New</option>
                    <option value="applied">Applied</option>
                    <option value="user_rejected">Rejected</option>
                    <option value="filter_rejected">Filtered</option>
                    <option value="interview_scheduled">Interview</option>
                    <option value="interview_completed">Completed</option>
                    <option value="offer_received">Offer</option>
                    <option value="offer_accepted">Accepted</option>
                    <option value="offer_rejected">Rejected</option>
                    <option value="not_answered">No Reply</option>
                    <option value="employer_rejected">Rejected</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Job Summary -->
            <div class="mb-4">
              <p class="text-sm text-gray-700 line-clamp-3 text-left">
                {{ truncateText(getJobSummaryText(job)) }}
              </p>
            </div>

            <!-- Job Details -->
            <div class="space-y-2 mb-4">
              <div v-if="job.job_location" class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span class="text-left">{{ job.job_location }}</span>
              </div>
              
              <div v-if="job.employment_type" class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
                </svg>
                <span class="text-left">{{ job.employment_type }}</span>
              </div>

              <div v-if="job.seniority_level" class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-left">{{ job.seniority_level }}</span>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-between text-xs text-gray-400">
              <span class="text-left">Processed: {{ formatDate(job.created_at) }}</span>
              <span class="text-blue-600 hover:text-blue-700">View Details →</span>
            </div>
          </div>
        </div>

        <!-- Jobs List View -->
        <div v-else class="space-y-4">
          <div
            v-for="job in sortedJobs"
            :key="job.id"
            class="job-tile bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 cursor-pointer"
            @click="openJobModal(job.id)"
          >
            <div class="flex items-start space-x-4">
              <!-- Job Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between mb-2">
                  <h3 class="text-lg font-semibold text-gray-900 line-clamp-2 text-left">
                    {{ job.job_title }}
                  </h3>
                  <div class="flex items-center space-x-2 ml-4 flex-shrink-0">
                    <span 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusClass(job.status)"
                    >
                      {{ getStatusText(job.status) }}
                    </span>
                    <select 
                      @change="updateJobStatus(job.id, $event.target.value)"
                      :value="job.status"
                      @click.stop
                      class="px-1 py-0.5 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      <option value="new">New</option>
                      <option value="applied">Applied</option>
                      <option value="user_rejected">Rejected</option>
                      <option value="filter_rejected">Filtered</option>
                      <option value="interview_scheduled">Interview</option>
                      <option value="interview_completed">Completed</option>
                      <option value="offer_received">Offer</option>
                      <option value="offer_accepted">Accepted</option>
                      <option value="offer_rejected">Rejected</option>
                      <option value="not_answered">No Reply</option>
                      <option value="employer_rejected">Rejected</option>
                    </select>
                  </div>
                </div>
                
                <p class="text-sm text-gray-600 mb-2 text-left">{{ job.employer }}</p>
                
                <div class="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                  <div v-if="job.job_location" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <span class="text-left">{{ job.job_location }}</span>
                  </div>
                  
                  <div v-if="job.employment_type" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
                    </svg>
                    <span class="text-left">{{ job.employment_type }}</span>
                  </div>
                  
                  <div v-if="job.seniority_level" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="text-left">{{ job.seniority_level }}</span>
                  </div>
                </div>
                
                <p class="text-sm text-gray-700 line-clamp-2 text-left">
                  {{ truncateText(getJobSummaryText(job), 200) }}
                </p>
              </div>
              
              <!-- Right side info -->
              <div class="flex flex-col items-end space-y-2 text-xs text-gray-400">
                <span class="text-left">Processed: {{ formatDate(job.created_at) }}</span>
                <span class="text-blue-600 hover:text-blue-700">View Details →</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Job Details Modal -->
      <div v-if="showModal && selectedJob" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <!-- Debug Info (remove in production) -->
          <div class="bg-yellow-100 p-2 text-xs text-gray-600">
            Debug: Modal visible, selectedJob: {{ selectedJob ? 'Yes' : 'No' }}, 
            Job ID: {{ selectedJob?.id }}, 
            Title: {{ selectedJob?.job_title }}
          </div>
          
          <!-- Modal Header -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900 text-left">{{ selectedJob.job_title }}</h2>
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
                <h3 class="text-lg font-semibold text-gray-900 mb-3 text-left">Job Overview</h3>
                <div class="space-y-3">
                  <div class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Company:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.employer }}</p>
                  </div>
                  <div v-if="selectedJob.job_location" class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Location:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.job_location }}</p>
                  </div>
                  <div v-if="selectedJob.employment_type" class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Employment Type:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.employment_type }}</p>
                  </div>
                  <div v-if="selectedJob.seniority_level" class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Seniority Level:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.seniority_level }}</p>
                  </div>
                  <div v-if="selectedJob.job_function" class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Job Function:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.job_function }}</p>
                  </div>
                  <div v-if="selectedJob.industries" class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Industries:</span>
                    <p class="text-gray-900 text-left">{{ selectedJob.industries }}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3 text-left">Processing Info</h3>
                <div class="space-y-3">
                  <div class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Run ID:</span>
                    <p class="text-gray-900 font-mono text-sm text-left">{{ selectedJob.runid }}</p>
                  </div>
                  <div class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Processed:</span>
                    <p class="text-gray-900 text-left">{{ formatDate(selectedJob.created_at) }}</p>
                  </div>
                  <div class="text-left">
                    <span class="text-sm font-medium text-gray-500 text-left">Status:</span>
                    <div class="flex items-center space-x-2 mt-1">
                      <span 
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getStatusClass(selectedJob.status)"
                      >
                        {{ getStatusText(selectedJob.status) }}
                      </span>
                      <select 
                        @change="updateJobStatus(selectedJob.id, $event.target.value)"
                        :value="selectedJob.status"
                        class="ml-2 px-2 py-1 text-xs border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="new">New</option>
                        <option value="applied">Applied</option>
                        <option value="user_rejected">Rejected</option>
                        <option value="filter_rejected">Filtered</option>
                        <option value="interview_scheduled">Interview Scheduled</option>
                        <option value="interview_completed">Interview Completed</option>
                        <option value="offer_received">Offer Received</option>
                        <option value="offer_accepted">Offer Accepted</option>
                        <option value="offer_rejected">Offer Rejected</option>
                        <option value="not_answered">No Reply</option>
                        <option value="employer_rejected">Employer Rejected</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- AI Generated Summary -->
            <div v-if="selectedJob.job_summary_parsed || selectedJob.job_summary">
              <h3 class="text-lg font-semibold text-gray-900 mb-3 text-left">AI Summary</h3>
              <div v-if="selectedJob.job_summary_parsed" class="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4 text-left">
                <!-- Summary -->
                <div class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Summary</h4>
                  <div 
                    class="text-gray-900 prose prose-sm max-w-none text-left"
                    v-html="typeof selectedJob.job_summary_parsed.summary === 'string' ? formatJobDescription(selectedJob.job_summary_parsed.summary) : selectedJob.job_summary_parsed.summary"
                  ></div>
                </div>
                
                <!-- Responsibilities -->
                <div v-if="selectedJob.job_summary_parsed.responsibilities" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Key Responsibilities</h4>
                  <div 
                    class="text-gray-900 prose prose-sm max-w-none text-left"
                    v-html="typeof selectedJob.job_summary_parsed.responsibilities === 'string' ? formatJobDescription(selectedJob.job_summary_parsed.responsibilities) : selectedJob.job_summary_parsed.responsibilities"
                  ></div>
                </div>
                
                <!-- Requirements -->
                <div v-if="selectedJob.job_summary_parsed.requirements && selectedJob.job_summary_parsed.requirements.length > 0" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Requirements</h4>
                  <ul class="list-disc list-inside text-gray-900 space-y-1 text-left">
                    <li v-for="(req, index) in selectedJob.job_summary_parsed.requirements" :key="index" class="text-left">
                      {{ req }}
                    </li>
                  </ul>
                </div>
                
                <!-- Opportunity Interest -->
                <div v-if="selectedJob.job_summary_parsed.opportunity_interest" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Opportunity Interest</h4>
                  <div 
                    class="text-gray-900 prose prose-sm max-w-none text-left"
                    v-html="typeof selectedJob.job_summary_parsed.opportunity_interest === 'string' ? formatJobDescription(selectedJob.job_summary_parsed.opportunity_interest) : selectedJob.job_summary_parsed.opportunity_interest"
                  ></div>
                </div>
                
                <!-- Background Alignment -->
                <div v-if="selectedJob.job_summary_parsed.background_aligns" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Background Alignment</h4>
                  <div class="flex items-center space-x-3">
                    <div class="flex items-center space-x-1">
                      <span 
                        v-for="i in 5" 
                        :key="i"
                        class="w-4 h-4 rounded-full border-2"
                        :class="i <= selectedJob.job_summary_parsed.background_aligns 
                          ? 'bg-blue-500 border-blue-500' 
                          : 'bg-gray-200 border-gray-300'"
                      ></span>
                    </div>
                    <span class="text-sm text-gray-600">
                      {{ selectedJob.job_summary_parsed.background_aligns }}/5 alignment
                    </span>
                  </div>
                  <div class="mt-2 text-xs text-gray-500">
                    <span v-if="selectedJob.job_summary_parsed.background_aligns <= 1">Poor alignment</span>
                    <span v-else-if="selectedJob.job_summary_parsed.background_aligns <= 2">Fair alignment</span>
                    <span v-else-if="selectedJob.job_summary_parsed.background_aligns <= 3">Good alignment</span>
                    <span v-else-if="selectedJob.job_summary_parsed.background_aligns <= 4">Very good alignment</span>
                    <span v-else>Excellent alignment</span>
                  </div>
                </div>
              </div>
              
              <!-- Fallback for old format -->
              <div v-else class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                <div 
                  class="text-gray-900 prose prose-sm max-w-none text-left"
                  v-html="formatJobDescription(selectedJob.job_summary)"
                ></div>
              </div>
            </div>

            <!-- Original Job Description -->
            <div v-if="selectedJob.job_description">
              <h3 class="text-lg font-semibold text-gray-900 mb-3 text-left">Original Job Description</h3>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                <div 
                  class="text-gray-900 prose prose-sm max-w-none text-left"
                  v-html="formatJobDescription(selectedJob.job_description)"
                ></div>
              </div>
            </div>

            <!-- AI Generated Cover Letter -->
            <div v-if="selectedJob.cover_letter_parsed || selectedJob.cover_letter">
              <h3 class="text-lg font-semibold text-gray-900 mb-3 text-left">AI Generated Cover Letter</h3>
              <div v-if="selectedJob.cover_letter_parsed" class="bg-green-50 border border-green-200 rounded-lg p-4 max-h-96 overflow-y-auto space-y-4 text-left">
                <!-- Subject -->
                <div v-if="selectedJob.cover_letter_parsed.subject" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Subject</h4>
                  <div class="text-gray-900 font-medium text-left">
                    {{ selectedJob.cover_letter_parsed.subject }}
                  </div>
                </div>
                
                <!-- Letter Content -->
                <div v-if="selectedJob.cover_letter_parsed.letter_content" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Letter Content</h4>
                  <div 
                    class="text-gray-900 prose prose-sm max-w-none text-left"
                    v-html="typeof selectedJob.cover_letter_parsed.letter_content === 'string' ? formatJobDescription(selectedJob.cover_letter_parsed.letter_content) : selectedJob.cover_letter_parsed.letter_content"
                  ></div>
                </div>
                
                <!-- Letter Closing -->
                <div v-if="selectedJob.cover_letter_parsed.letter_closing" class="text-left">
                  <h4 class="font-medium text-gray-900 mb-2 text-left">Closing</h4>
                  <div 
                    class="text-gray-900 prose prose-sm max-w-none text-left"
                    v-html="typeof selectedJob.cover_letter_parsed.letter_closing === 'string' ? formatJobDescription(selectedJob.cover_letter_parsed.letter_closing) : selectedJob.cover_letter_parsed.letter_closing"
                  ></div>
                </div>
              </div>
              
              <!-- Fallback for old format -->
              <div v-else class="bg-green-50 border border-green-200 rounded-lg p-4 max-h-96 overflow-y-auto text-left">
                <div 
                  class="text-gray-900 prose prose-sm max-w-none text-left"
                  v-html="formatJobDescription(selectedJob.cover_letter)"
                ></div>
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