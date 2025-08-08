<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import JobDetailsModal from '@/components/jobs/JobDetailsModal.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const isDev = import.meta.env.MODE !== 'production'

const jobs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(1) // triage loads one job at a time
const loading = ref(false)
const error = ref('')
const currentIndex = ref(0)

const selectedJob = computed(() => jobs.value[currentIndex.value] || null)
const hasNext = computed(() => (page.value - 1) * pageSize.value + currentIndex.value + 1 < total.value)
const hasPrev = computed(() => (page.value - 1) * pageSize.value + currentIndex.value > 0)

const fetchJobs = async () => {
  try {
    loading.value = true
    error.value = ''
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('pageSize', String(pageSize.value))
    params.set('sortBy', 'created')
    params.set('order', 'desc')
    const res = await fetch(`${API_BASE_URL}/processed-jobs?${params.toString()}`)
    if (!res.ok) throw new Error('Failed to load job')
    const data = await res.json()
    jobs.value = (data.jobs || []).map(job => ({
      ...job,
      job_summary_parsed: parseJson(job.job_summary),
      cover_letter_parsed: parseJson(job.cover_letter),
    }))
    total.value = Number(data.total || jobs.value.length)
    currentIndex.value = 0
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load job'
  } finally {
    loading.value = false
  }
}

const parseJson = (val) => {
  if (!val) return null
  if (typeof val === 'object') return val
  try { return JSON.parse(val) } catch { return null }
}

const openExternal = (job) => { if (job?.job_url) window.open(job.job_url, '_blank', 'noopener') }
const copyCoverLetter = async (job) => {
  try {
    const content = job?.cover_letter_parsed?.letter_content ?? job?.cover_letter
    if (!content) return
    const text = typeof content === 'string' ? content.replace(/<[^>]*>/g, '') : JSON.stringify(content, null, 2)
    await navigator.clipboard.writeText(text)
  } catch {}
}

const updateJobStatus = async (processedJobId, newStatus) => {
  const res = await fetch(`${API_BASE_URL}/processed-jobs/${processedJobId}/status`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: newStatus })
  })
  if (!res.ok) throw new Error('Failed to update job status')
}

const advance = async () => {
  // Move to next item overall. Since pageSize=1, just increment page
  if (hasNext.value) {
    page.value += 1
    await fetchJobs()
  }
}

const regress = async () => {
  if (hasPrev.value) {
    page.value = Math.max(1, page.value - 1)
    await fetchJobs()
  }
}

const markApplied = async () => {
  if (!selectedJob.value) return
  try { await updateJobStatus(selectedJob.value.id, 'applied') } catch {}
  await advance()
}

const markRejected = async () => {
  if (!selectedJob.value) return
  try { await updateJobStatus(selectedJob.value.id, 'user_rejected') } catch {}
  await advance()
}

const handleKeyDown = (e) => {
  const tag = e.target?.tagName
  if (tag && ['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return
  if (e.key.toLowerCase() === 'a') { e.preventDefault(); markApplied() }
  if (e.key.toLowerCase() === 'r') { e.preventDefault(); markRejected() }
  if (e.key === 'ArrowRight' || e.key === 'j') { e.preventDefault(); advance() }
  if (e.key === 'ArrowLeft' || e.key === 'k') { e.preventDefault(); regress() }
  if (e.key.toLowerCase() === 'o') { e.preventDefault(); openExternal(selectedJob.value) }
  if (e.key.toLowerCase() === 'c') { e.preventDefault(); copyCoverLetter(selectedJob.value) }
}

onMounted(() => {
  fetchJobs()
  window.addEventListener('keydown', handleKeyDown)
})
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Triage Mode</h1>
        <p class="text-gray-600">Review one job at a time. Use keyboard: a (applied), r (rejected), o (open), c (copy), ←/→ (prev/next)</p>
      </div>

      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-lg text-gray-600">Loading job...</span>
      </div>

      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">{{ error }}</div>

      <div v-else-if="!selectedJob" class="bg-gray-50 border border-gray-200 rounded-lg p-6">No jobs found.</div>

      <div v-else class="space-y-4">
        <div class="flex items-center justify-between text-sm text-gray-600">
          <div>Job {{ (page - 1) * pageSize + currentIndex + 1 }} of {{ total }}</div>
          <div class="space-x-2">
            <button :disabled="!hasPrev" @click="regress" class="px-3 py-1.5 border rounded disabled:opacity-50">Prev</button>
            <button :disabled="!hasNext" @click="advance" class="px-3 py-1.5 border rounded disabled:opacity-50">Next</button>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-start justify-between mb-4">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ selectedJob.job_title }}</h2>
              <p class="text-sm text-gray-600">{{ selectedJob.employer }}</p>
            </div>
            <div class="space-x-2">
              <button @click="openExternal(selectedJob)" class="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700">Open</button>
              <button @click="copyCoverLetter(selectedJob)" class="px-3 py-1.5 bg-gray-100 text-gray-800 rounded hover:bg-gray-200">Copy CL</button>
              <button @click="markApplied" class="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700">Applied</button>
              <button @click="markRejected" class="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700">Reject</button>
            </div>
          </div>

          <JobDetailsModal
            v-if="selectedJob"
            :job="selectedJob"
            :is-dev="isDev"
            @close="() => {}"
            @open="openExternal(selectedJob)"
            @copyCL="copyCoverLetter(selectedJob)"
            @applied="markApplied()"
            @rejected="markRejected()"
            @updateStatus="(status) => updateJobStatus(selectedJob.id, status)"
          />
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped></style>

