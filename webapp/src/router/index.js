import { createRouter, createWebHistory } from 'vue-router'
import ProcessedJobsList from '../components/ProcessedJobsList.vue'
import TriageMode from '../views/TriageMode.vue'

const routes = [
  { path: '/', name: 'jobs', component: ProcessedJobsList },
  { path: '/triage', name: 'triage', component: TriageMode },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

