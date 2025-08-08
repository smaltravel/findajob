<script setup>
const props = defineProps({
  job: { type: Object, required: true },
  focused: { type: Boolean, default: false },
  isStarred: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'toggleStar', 'updateStatus', 'openExternal', 'copyCL', 'applied', 'rejected'])

const formatDate = (dateString) => new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })

const getStatusClass = (status) => {
  switch (status) {
    case 'new': return 'bg-blue-100 text-blue-700'
    case 'applied': return 'bg-green-100 text-green-700'
    case 'user_rejected':
    case 'filter_rejected':
    case 'employer_rejected': return 'bg-red-100 text-red-700'
    case 'interview_scheduled': return 'bg-yellow-100 text-yellow-700'
    case 'interview_completed': return 'bg-purple-100 text-purple-700'
    case 'offer_received': return 'bg-indigo-100 text-indigo-700'
    case 'offer_accepted': return 'bg-green-100 text-green-700'
    case 'offer_rejected': return 'bg-red-100 text-red-700'
    case 'not_answered': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-600'
  }
}

const getStatusText = (status) => {
  const map = {
    new: 'New', applied: 'Applied', user_rejected: 'Rejected', filter_rejected: 'Filtered',
    employer_rejected: 'Rejected', interview_scheduled: 'Interview', interview_completed: 'Completed',
    offer_received: 'Offer', offer_accepted: 'Accepted', offer_rejected: 'Rejected', not_answered: 'No Reply',
  }
  return map[status] || status
}

const truncateText = (text, maxLength = 150) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getJobSummaryText = (job) => {
  if (job.job_summary_parsed?.summary) {
    let summary = job.job_summary_parsed.summary
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
</script>

<template>
  <div
    :class="[
      'job-tile bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 cursor-pointer',
      focused ? 'ring-2 ring-blue-400' : ''
    ]"
    @click="$emit('open', job.id)"
  >
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <h3 class="text-lg font-semibold text-gray-900 mb-1 line-clamp-2 text-left">{{ job.job_title }}</h3>
        <p class="text-sm text-gray-600 text-left">{{ job.employer }}</p>
      </div>
      <div class="ml-4">
        <div class="flex items-center space-x-2">
          <button @click.stop="$emit('toggleStar', job.id)" :aria-pressed="isStarred" :title="isStarred ? 'Unstar' : 'Star'" class="p-1 rounded hover:bg-gray-100">
            <svg :class="['w-4 h-4', isStarred ? 'text-yellow-500' : 'text-gray-400']" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.803 2.036a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.803-2.036a1 1 0 00-1.176 0l-2.803 2.036c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </button>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getStatusClass(job.status)">{{ getStatusText(job.status) }}</span>
          <select @change="$emit('updateStatus', $event.target.value)" :value="job.status" @click.stop class="px-1 py-0.5 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900">
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

    <div class="mb-4">
      <p class="text-sm text-gray-700 line-clamp-3 text-left">{{ truncateText(getJobSummaryText(job)) }}</p>
    </div>

    <div class="flex items-center space-x-3 mb-3">
      <button @click.stop="$emit('openExternal', job)" class="text-xs text-blue-600 hover:text-blue-700">Open</button>
      <button @click.stop="$emit('copyCL', job)" class="text-xs text-gray-600 hover:text-gray-800">Copy CL</button>
      <button @click.stop="$emit('applied', job.id)" class="text-xs text-green-600 hover:text-green-700">Applied</button>
      <button @click.stop="$emit('rejected', job.id)" class="text-xs text-red-600 hover:text-red-700">Reject</button>
    </div>

    <div class="space-y-2 mb-4">
      <div v-if="job.job_location" class="flex items-center text-sm text-gray-500">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        <span class="text-left">{{ job.job_location }}</span>
      </div>
      <div v-if="job.employment_type" class="flex items-center text-sm text-gray-500">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"/></svg>
        <span class="text-left">{{ job.employment_type }}</span>
      </div>
      <div v-if="job.seniority_level" class="flex items-center text-sm text-gray-500">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <span class="text-left">{{ job.seniority_level }}</span>
      </div>
    </div>

    <div class="flex items-center justify-between text-xs text-gray-400">
      <span class="text-left">Processed: {{ formatDate(job.created_at) }}</span>
      <span class="text-blue-600 hover:text-blue-700">View Details →</span>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.line-clamp-3{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.job-tile:hover{transform:translateY(-2px)}
</style>

