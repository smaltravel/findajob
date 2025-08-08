<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  uniqueStatuses: {
    type: Array,
    default: () => [],
  },
  uniqueSeniorities: {
    type: Array,
    default: () => [],
  },
  sortBy: {
    type: String,
    default: 'default',
  },
  viewMode: {
    type: String,
    default: 'grid',
  },
  hasActiveFilters: {
    type: Boolean,
    default: false,
  },
  filteredCount: {
    type: Number,
    default: 0,
  },
  totalCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits([
  'update:modelValue',
  'update:sortBy',
  'update:viewMode',
  'clear',
])

const internalFilters = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const toggleViewMode = () => {
  emit('update:viewMode', props.viewMode === 'grid' ? 'list' : 'grid')
}

const getStatusText = (status) => {
  const map = {
    new: 'New',
    applied: 'Applied',
    user_rejected: 'Rejected',
    filter_rejected: 'Filtered',
    employer_rejected: 'Rejected',
    interview_scheduled: 'Interview',
    interview_completed: 'Completed',
    offer_received: 'Offer',
    offer_accepted: 'Accepted',
    offer_rejected: 'Rejected',
    not_answered: 'No Reply',
  }
  return map[status] || status
}
</script>

<template>
  <div class="mb-6 space-y-4">
    <div class="flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <button
          @click="internalFilters = { ...internalFilters, _toggle: !internalFilters._toggle }"
          class="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-muted-700 bg-white border border-muted-300 rounded-md hover:bg-muted-50 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
          </svg>
          <span>Filters</span>
          <span v-if="hasActiveFilters" class="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-white bg-brand-600 rounded-full">
            {{ Object.values(internalFilters).filter(v => v !== '' && v !== false && v !== undefined && v !== null && v !== internalFilters._toggle).length }}
          </span>
        </button>
        <div class="text-sm text-muted-600">
          Showing {{ filteredCount }} of {{ totalCount }} jobs
        </div>
      </div>

      <div class="flex items-center bg-white rounded-lg shadow-sm border border-muted-200 p-1">
        <button
          @click="toggleViewMode"
          :class="[
            'px-3 py-2 rounded-md text-sm font-medium transition-colors',
            viewMode === 'grid' ? 'bg-brand-100 text-brand-700' : 'text-muted-500 hover:text-muted-700'
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
            viewMode === 'list' ? 'bg-brand-100 text-brand-700' : 'text-muted-500 hover:text-muted-700'
          ]"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="internalFilters._toggle" class="bg-white border border-muted-200 rounded-lg p-6 shadow-sm">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label for="status-filter" class="block text-sm font-medium text-muted-700 mb-2">Status</label>
          <select
            id="status-filter"
            v-model="internalFilters.status"
            class="w-full px-3 py-2 text-sm border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900"
          >
            <option value="">All Statuses</option>
            <option v-for="status in uniqueStatuses" :key="status" :value="status">{{ getStatusText(status) }}</option>
          </select>
        </div>

        <div>
          <label for="seniority-filter" class="block text-sm font-medium text-muted-700 mb-2">Seniority Level</label>
          <select
            id="seniority-filter"
            v-model="internalFilters.seniority"
            class="w-full px-3 py-2 text-sm border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900"
          >
            <option value="">All Levels</option>
            <option v-for="seniority in uniqueSeniorities" :key="seniority" :value="seniority">{{ seniority }}</option>
          </select>
        </div>

        <div>
          <label for="employer-filter" class="block text-sm font-medium text-muted-700 mb-2">Employer</label>
          <input
            id="employer-filter"
            v-model="internalFilters.employer"
            type="text"
            placeholder="Search employers..."
            class="w-full px-3 py-2 text-sm border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900"
          />
        </div>

        <div>
          <label for="title-filter" class="block text-sm font-medium text-muted-700 mb-2">Job Title</label>
          <input
            id="title-filter"
            v-model="internalFilters.title"
            type="text"
            placeholder="Search job titles..."
            class="w-full px-3 py-2 text-sm border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900"
          />
        </div>

        <div class="flex items-end">
          <label class="inline-flex items-center space-x-2 text-sm text-muted-700">
            <input type="checkbox" v-model="internalFilters.starredOnly" class="rounded border-muted-300 text-brand-600 focus:ring-brand-500" />
            <span>Starred only</span>
          </label>
        </div>
      </div>

      <div class="flex justify-end mt-4 pt-4 border-t border-muted-200">
        <button
          @click="$emit('clear')"
          class="px-4 py-2 text-sm font-medium text-muted-700 bg-muted-100 border border-muted-300 rounded-md hover:bg-muted-200 focus:outline-none focus:ring-2 focus:ring-muted-500 focus:border-muted-500"
        >
          Clear All Filters
        </button>
      </div>
    </div>

    <div class="flex items-center space-x-2">
      <label for="sort-select" class="text-sm font-medium text-muted-700">Sort by:</label>
      <select
        id="sort-select"
        :value="sortBy"
        @change="$emit('update:sortBy', $event.target.value)"
        class="px-3 py-2 text-sm border border-muted-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white text-muted-900 shadow-sm"
      >
        <option value="default">Default (No sorting)</option>
        <option value="status">By Status (New first, Rejected last)</option>
        <option value="seniority">By Seniority Level</option>
        <option value="title">By Job Title</option>
        <option value="employer">By Employer Name</option>
      </select>
    </div>
  </div>
</template>

<style scoped></style>

