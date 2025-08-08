<script setup>
const props = defineProps({
  job: { type: Object, required: true },
  isDev: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'open', 'copyCL', 'applied', 'rejected', 'updateStatus'])

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const getStatusClass = (status) => {
  switch (status) {
    case 'new': return 'bg-brand-100 text-brand-700'
    case 'applied': return 'bg-success-100 text-success-700'
    case 'user_rejected':
    case 'filter_rejected':
    case 'employer_rejected': return 'bg-danger-100 text-danger-700'
    case 'interview_scheduled': return 'bg-warning-100 text-warning-700'
    case 'interview_completed': return 'bg-info-100 text-info-700'
    case 'offer_received': return 'bg-brand-100 text-brand-700'
    case 'offer_accepted': return 'bg-success-100 text-success-700'
    case 'offer_rejected': return 'bg-danger-100 text-danger-700'
    case 'not_answered': return 'bg-muted-100 text-muted-700'
    default: return 'bg-muted-100 text-muted-600'
  }
}

const getStatusText = (status) => {
  const map = {
    new: 'New', applied: 'Applied', user_rejected: 'Rejected', filter_rejected: 'Filtered',
    employer_rejected: 'Rejected', interview_scheduled: 'Interview Scheduled', interview_completed: 'Interview Completed',
    offer_received: 'Offer Received', offer_accepted: 'Offer Accepted', offer_rejected: 'Offer Rejected', not_answered: 'No Reply',
  }
  return map[status] || status
}

const formatJobDescription = (description) => {
  if (!description) return ''
  let formatted = String(description)
  formatted = formatted.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  formatted = formatted.replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  formatted = formatted.replace(/\n/g, '<br>')
  formatted = formatted.replace(/^\s*[-•*]\s+/gm, '• ')
  formatted = formatted.replace(/^\s*\d+\.\s+/gm, (m) => `${m.match(/\d+/)[0]}. `)
  const paragraphs = formatted.split('<br><br>')
  return paragraphs.map(p => `<p class="mb-3">${p}</p>`).join('')
}
</script>

<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div v-if="isDev" class="bg-warning-100 p-2 text-xs text-muted-600">
        Debug: Modal visible; Job ID: {{ job?.id }}; Title: {{ job?.job_title }}
      </div>
      <div class="flex items-center justify-between p-6 border-b border-muted-200">
        <h2 class="text-2xl font-bold text-muted-900 text-left">{{ job.job_title }}</h2>
        <button @click="$emit('close')" class="text-muted-400 hover:text-muted-600 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-6 space-y-6">
        <div class="flex items-center gap-3">
          <button @click="$emit('open')" class="inline-flex items-center px-3 py-1.5 bg-brand-600 text-white rounded-md hover:bg-brand-700">Open Posting</button>
          <button @click="$emit('copyCL')" class="inline-flex items-center px-3 py-1.5 bg-muted-100 text-muted-800 rounded-md hover:bg-muted-200">Copy Cover Letter</button>
          <button @click="$emit('applied')" class="inline-flex items-center px-3 py-1.5 bg-success-600 text-white rounded-md hover:bg-success-700">Mark Applied</button>
          <button @click="$emit('rejected')" class="inline-flex items-center px-3 py-1.5 bg-danger-600 text-white rounded-md hover:bg-danger-700">Reject</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 class="text-lg font-semibold text-muted-900 mb-3 text-left">Job Overview</h3>
            <div class="space-y-3">
              <div class="text-left"><span class="text-sm font-medium text-muted-500">Company:</span><p class="text-muted-900">{{ job.employer }}</p></div>
              <div v-if="job.job_location" class="text-left"><span class="text-sm font-medium text-muted-500">Location:</span><p class="text-muted-900">{{ job.job_location }}</p></div>
              <div v-if="job.employment_type" class="text-left"><span class="text-sm font-medium text-muted-500">Employment Type:</span><p class="text-muted-900">{{ job.employment_type }}</p></div>
              <div v-if="job.seniority_level" class="text-left"><span class="text-sm font-medium text-muted-500">Seniority Level:</span><p class="text-muted-900">{{ job.seniority_level }}</p></div>
              <div v-if="job.job_function" class="text-left"><span class="text-sm font-medium text-muted-500">Job Function:</span><p class="text-muted-900">{{ job.job_function }}</p></div>
              <div v-if="job.industries" class="text-left"><span class="text-sm font-medium text-muted-500">Industries:</span><p class="text-muted-900">{{ job.industries }}</p></div>
            </div>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-muted-900 mb-3 text-left">Processing Info</h3>
            <div class="space-y-3">
              <div class="text-left"><span class="text-sm font-medium text-muted-500">Run ID:</span><p class="text-muted-900 font-mono text-sm">{{ job.runid }}</p></div>
              <div class="text-left"><span class="text-sm font-medium text-muted-500">Processed:</span><p class="text-muted-900">{{ formatDate(job.created_at) }}</p></div>
              <div class="text-left">
                <span class="text-sm font-medium text-muted-500">Status:</span>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="getStatusClass(job.status)">{{ getStatusText(job.status) }}</span>
                  <select :value="job.status" @change="$emit('updateStatus', $event.target.value)" class="ml-2 px-2 py-1 text-xs border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900">
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

        <div v-if="job.job_summary_parsed || job.job_summary">
          <h3 class="text-lg font-semibold text-muted-900 mb-3 text-left">AI Summary</h3>
          <div v-if="job.job_summary_parsed" class="bg-brand-50 border border-brand-200 rounded-lg p-4 space-y-4 text-left">
            <div class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Summary</h4>
              <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="typeof job.job_summary_parsed.summary === 'string' ? formatJobDescription(job.job_summary_parsed.summary) : job.job_summary_parsed.summary"></div>
            </div>
            <div v-if="job.job_summary_parsed.responsibilities" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Key Responsibilities</h4>
              <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="typeof job.job_summary_parsed.responsibilities === 'string' ? formatJobDescription(job.job_summary_parsed.responsibilities) : job.job_summary_parsed.responsibilities"></div>
            </div>
            <div v-if="job.job_summary_parsed.requirements && job.job_summary_parsed.requirements.length > 0" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Requirements</h4>
              <ul class="list-disc list-inside text-muted-900 space-y-1 text-left">
                <li v-for="(req, index) in job.job_summary_parsed.requirements" :key="index" class="text-left">{{ req }}</li>
              </ul>
            </div>
            <div v-if="job.job_summary_parsed.opportunity_interest" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Opportunity Interest</h4>
              <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="typeof job.job_summary_parsed.opportunity_interest === 'string' ? formatJobDescription(job.job_summary_parsed.opportunity_interest) : job.job_summary_parsed.opportunity_interest"></div>
            </div>
            <div v-if="job.job_summary_parsed.background_aligns" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Background Alignment</h4>
              <div class="flex items-center space-x-3">
                <div class="flex items-center space-x-1">
                  <span v-for="i in 5" :key="i" class="w-4 h-4 rounded-full border-2" :class="i <= job.job_summary_parsed.background_aligns ? 'bg-brand-500 border-brand-500' : 'bg-muted-200 border-muted-300'"></span>
                </div>
                <span class="text-sm text-muted-600">{{ job.job_summary_parsed.background_aligns }}/5 alignment</span>
              </div>
            </div>
          </div>
          <div v-else class="bg-brand-50 border border-brand-200 rounded-lg p-4 text-left">
            <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="formatJobDescription(job.job_summary)"></div>
          </div>
        </div>

        <div v-if="job.job_description">
          <h3 class="text-lg font-semibold text-muted-900 mb-3 text-left">Original Job Description</h3>
          <div class="bg-muted-50 border border-muted-200 rounded-lg p-4 max-h-64 overflow-y-auto">
            <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="formatJobDescription(job.job_description)"></div>
          </div>
        </div>

        <div v-if="job.cover_letter_parsed || job.cover_letter">
          <h3 class="text-lg font-semibold text-muted-900 mb-3 text-left">AI Generated Cover Letter</h3>
          <div v-if="job.cover_letter_parsed" class="bg-success-50 border border-success-200 rounded-lg p-4 max-h-96 overflow-y-auto space-y-4 text-left">
            <div v-if="job.cover_letter_parsed.subject" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Subject</h4>
              <div class="text-muted-900 font-medium text-left">{{ job.cover_letter_parsed.subject }}</div>
            </div>
            <div v-if="job.cover_letter_parsed.letter_content" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Letter Content</h4>
              <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="typeof job.cover_letter_parsed.letter_content === 'string' ? formatJobDescription(job.cover_letter_parsed.letter_content) : job.cover_letter_parsed.letter_content"></div>
            </div>
            <div v-if="job.cover_letter_parsed.letter_closing" class="text-left">
              <h4 class="font-medium text-muted-900 mb-2 text-left">Closing</h4>
              <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="typeof job.cover_letter_parsed.letter_closing === 'string' ? formatJobDescription(job.cover_letter_parsed.letter_closing) : job.cover_letter_parsed.letter_closing"></div>
            </div>
          </div>
          <div v-else class="bg-success-50 border border-success-200 rounded-lg p-4 max-h-96 overflow-y-auto text-left">
            <div class="text-muted-900 prose prose-sm max-w-none text-left" v-html="formatJobDescription(job.cover_letter)"></div>
          </div>
        </div>

        <div v-if="job.job_url || job.employer_url" class="flex space-x-4">
          <a v-if="job.job_url" :href="job.job_url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
            View Job Posting
          </a>
          <a v-if="job.employer_url" :href="job.employer_url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 bg-muted-700 text-white rounded-lg hover:bg-muted-800 transition-colors">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9"/></svg>
            Company Profile
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>

