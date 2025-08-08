<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import FilterBar from './filters/FilterBar.vue'
import JobDetailsModal from './jobs/JobDetailsModal.vue'
import JobCard from './jobs/JobCard.vue'
import JobRow from './jobs/JobRow.vue'

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
  title: '',
  starredOnly: false,
})
const starredIds = ref(new Set())

// Env-aware API base URL (uses dev proxy; same-origin in production)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Dev flag
const isDev = import.meta.env.MODE !== 'production'

// Keyboard navigation / focus management
const focusedIndex = ref(-1)
const jobRefs = ref([])

// Persisted UI state keys
const STORAGE_KEYS = {
  filters: 'processedJobs.filters',
  sortBy: 'processedJobs.sortBy',
  viewMode: 'processedJobs.viewMode',
  starred: 'processedJobs.starred',
}

const restoreStateFromStorage = () => {
  try {
    const savedFilters = localStorage.getItem(STORAGE_KEYS.filters)
    if (savedFilters) {
      const parsed = JSON.parse(savedFilters)
      if (parsed && typeof parsed === 'object') {
        filters.value = {
          status: parsed.status || '',
          seniority: parsed.seniority || '',
          employer: parsed.employer || '',
          title: parsed.title || '',
          starredOnly: !!parsed.starredOnly,
        }
      }
    }
  } catch {}
  const savedSort = localStorage.getItem(STORAGE_KEYS.sortBy)
  if (savedSort) sortBy.value = savedSort
  const savedView = localStorage.getItem(STORAGE_KEYS.viewMode)
  if (savedView) viewMode.value = savedView
  try {
    const savedStarred = JSON.parse(localStorage.getItem(STORAGE_KEYS.starred) || '[]')
    if (Array.isArray(savedStarred)) {
      starredIds.value = new Set(savedStarred)
    }
  } catch {}
}

watch(filters, (val) => {
  try { localStorage.setItem(STORAGE_KEYS.filters, JSON.stringify(val)) } catch {}
}, { deep: true })

watch(sortBy, (val) => {
  try { localStorage.setItem(STORAGE_KEYS.sortBy, val) } catch {}
})

watch(viewMode, (val) => {
  try { localStorage.setItem(STORAGE_KEYS.viewMode, val) } catch {}
})

const persistStarred = () => {
  try { localStorage.setItem(STORAGE_KEYS.starred, JSON.stringify(Array.from(starredIds.value))) } catch {}
}

const toggleStar = (jobId) => {
  if (starredIds.value.has(jobId)) {
    starredIds.value.delete(jobId)
  } else {
    starredIds.value.add(jobId)
  }
  // force reactivity by replacing the Set
  starredIds.value = new Set(starredIds.value)
  persistStarred()
}

const isStarred = (jobId) => starredIds.value.has(jobId)

// Computed properties for unique filter options
const uniqueStatuses = computed(() => {
  const statuses = [...new Set(jobs.value.map(job => job.status).filter(Boolean))]
  return statuses.sort()
})

const uniqueSeniorities = computed(() => {
  const seniorities = [...new Set(jobs.value.map(job => job.seniority_level).filter(Boolean))]
  return seniorities.sort()
})

// Note: employer dropdown removed for simplicity; keep text filter only

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
    // Starred only
    if (filters.value.starredOnly && !isStarred(job.id)) {
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
  const f = filters.value
  return Boolean(
    (f.status && f.status !== '') ||
    (f.seniority && f.seniority !== '') ||
    (f.employer && String(f.employer).trim() !== '') ||
    (f.title && String(f.title).trim() !== '') ||
    f.starredOnly === true
  )
})

const getFilteredCount = computed(() => {
  return filteredJobs.value.length
})

// Methods
// Pagination state
const page = ref(1)
const pageSize = ref(30)
const total = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const loadJobs = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('pageSize', String(pageSize.value))
    if (filters.value.status) params.set('status', filters.value.status)
    if (filters.value.seniority) params.set('seniority', filters.value.seniority)
    if (filters.value.employer) params.set('employer', filters.value.employer)
    if (filters.value.title) params.set('title', filters.value.title)
    if (sortBy.value && sortBy.value !== 'default') params.set('sortBy', sortBy.value)
    const response = await fetch(`${API_BASE_URL}/processed-jobs?${params.toString()}`)
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
    total.value = Number(data.total || 0)
    
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

// Quick actions
const openExternal = (job) => {
  if (job?.job_url) {
    window.open(job.job_url, '_blank', 'noopener')
  }
}

const copyCoverLetter = async (job) => {
  try {
    const content = job?.cover_letter_parsed?.letter_content ?? job?.cover_letter
    if (!content) {
      alert('No cover letter available')
      return
    }
    const text = typeof content === 'string' 
      ? content.replace(/<[^>]*>/g, '')
      : JSON.stringify(content, null, 2)
    await navigator.clipboard.writeText(text)
  } catch (e) {
    console.error('Failed to copy cover letter', e)
    alert('Failed to copy cover letter')
  }
}

const markApplied = (jobId) => updateJobStatus(jobId, 'applied')
const markRejected = (jobId) => updateJobStatus(jobId, 'user_rejected')

// Keyboard shortcuts
const moveFocus = (delta) => {
  const total = sortedJobs.value.length
  if (total === 0) return
  if (focusedIndex.value < 0) focusedIndex.value = 0
  else focusedIndex.value = Math.min(total - 1, Math.max(0, focusedIndex.value + delta))
  nextTick(() => {
    const el = jobRefs.value[focusedIndex.value]
    if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  })
}

const handleKeyDown = (e) => {
  const tag = e.target?.tagName
  if (tag && ['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return
  if (e.key === 'j') { e.preventDefault(); moveFocus(1) }
  if (e.key === 'k') { e.preventDefault(); moveFocus(-1) }
  if (e.key === 'Enter' && focusedIndex.value >= 0) {
    openJobModal(sortedJobs.value[focusedIndex.value].id)
  }
  if (e.key === 'Escape' && showModal.value) {
    closeModal()
  }
  if (e.key.toLowerCase() === 'a' && focusedIndex.value >= 0) {
    markApplied(sortedJobs.value[focusedIndex.value].id)
  }
  if (e.key.toLowerCase() === 'r' && focusedIndex.value >= 0) {
    markRejected(sortedJobs.value[focusedIndex.value].id)
  }
  if (e.key.toLowerCase() === 'o' && focusedIndex.value >= 0) {
    openExternal(sortedJobs.value[focusedIndex.value])
  }
  if (e.key.toLowerCase() === 'c' && focusedIndex.value >= 0) {
    copyCoverLetter(sortedJobs.value[focusedIndex.value])
  }
}

// Load jobs and set up listeners
onMounted(() => {
  restoreStateFromStorage()
  loadJobs()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class="min-h-screen bg-muted-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-muted-900">Processed Jobs</h1>
        <p class="mt-2 text-muted-600">View all AI-processed job opportunities</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
        <span class="ml-3 text-lg text-muted-600">Loading processed jobs...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="py-12">
        <div class="bg-danger-50 border border-danger-200 rounded-lg p-6 max-w-md">
          <p class="text-danger-700 mb-4 text-left">{{ error }}</p>
          <button 
            @click="loadJobs"
            class="px-4 py-2 bg-danger-100 hover:bg-danger-200 text-danger-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="jobs.length === 0" class="py-12">
        <div class="bg-muted-50 border border-muted-200 rounded-lg p-8 max-w-md">
          <svg class="h-12 w-12 text-muted-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
          </svg>
          <h3 class="text-lg font-medium text-muted-900 mb-2 text-left">No processed jobs found</h3>
          <p class="text-muted-600 text-left">Jobs will appear here after they have been processed by the AI system.</p>
        </div>
      </div>

      <!-- View Toggle and Jobs -->
      <div v-else>
        <FilterBar
          v-model="filters"
          :unique-statuses="uniqueStatuses"
          :unique-seniorities="uniqueSeniorities"
          :sort-by="sortBy"
          :view-mode="viewMode"
          :has-active-filters="hasActiveFilters"
          :filtered-count="getFilteredCount"
          :total-count="jobs.length"
          @update:sortBy="(v) => (sortBy = v)"
          @update:viewMode="toggleViewMode()"
          @clear="clearFilters"
        />

        <!-- Jobs Grid View -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <JobCard
            v-for="(job, index) in sortedJobs"
            :key="job.id"
            :job="job"
            :focused="index === focusedIndex"
            :is-starred="isStarred(job.id)"
            :ref="el => jobRefs[index] = el"
            @open="openJobModal"
            @toggleStar="toggleStar"
            @updateStatus="(status) => updateJobStatus(job.id, status)"
            @openExternal="openExternal"
            @copyCL="copyCoverLetter"
            @applied="markApplied"
            @rejected="markRejected"
          />
        </div>

        <!-- Jobs List View -->
        <div v-else class="space-y-4">
          <JobRow
            v-for="(job, index) in sortedJobs"
            :key="job.id"
            :job="job"
            :focused="index === focusedIndex"
            :is-starred="isStarred(job.id)"
            :ref="el => jobRefs[index] = el"
            @open="openJobModal"
            @toggleStar="toggleStar"
            @updateStatus="(status) => updateJobStatus(job.id, status)"
            @openExternal="openExternal"
            @copyCL="copyCoverLetter"
            @applied="markApplied"
            @rejected="markRejected"
          />
        </div>

        <!-- Pagination -->
        <div class="mt-6 flex items-center justify-between">
          <div class="text-sm text-muted-600">Page {{ page }} of {{ totalPages }} ({{ total }} total)</div>
          <div class="space-x-2">
            <button :disabled="page <= 1" @click="page = Math.max(1, page - 1); loadJobs();" class="px-3 py-1.5 border rounded disabled:opacity-50 border-muted-300 text-muted-700 bg-white hover:bg-muted-50">Prev</button>
            <button :disabled="page >= totalPages" @click="page = Math.min(totalPages, page + 1); loadJobs();" class="px-3 py-1.5 border rounded disabled:opacity-50 border-muted-300 text-muted-700 bg-white hover:bg-muted-50">Next</button>
          </div>
        </div>
      </div>

      <!-- Job Details Modal -->
      <JobDetailsModal
        v-if="showModal && selectedJob"
        :job="selectedJob"
        :is-dev="isDev"
        @close="closeModal"
        @open="openExternal(selectedJob)"
        @copyCL="copyCoverLetter(selectedJob)"
        @applied="markApplied(selectedJob.id)"
        @rejected="markRejected(selectedJob.id)"
        @updateStatus="(status) => updateJobStatus(selectedJob.id, status)"
      />
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