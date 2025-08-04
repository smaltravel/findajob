<script setup>
import { ref, computed, onMounted } from 'vue'
import JobModal from './JobModal.vue'

// Reactive data
const applications = ref([
  {
    id: 1,
    title: 'Senior Python Developer',
    employer: 'TechCorp Inc.',
    description: 'We are looking for an experienced Python developer to join our team. You will be responsible for developing and maintaining web applications using Django and React.',
    status: 'new',
    fullDescription: 'We are looking for an experienced Python developer to join our dynamic team. You will be responsible for developing and maintaining web applications using Django and React.\n\nRequirements:\n• 5+ years of experience with Python\n• Strong knowledge of Django framework\n• Experience with React and modern JavaScript\n• Knowledge of PostgreSQL and Redis\n• Experience with Docker and AWS\n\nResponsibilities:\n• Develop and maintain web applications\n• Collaborate with cross-functional teams\n• Write clean, maintainable code\n• Participate in code reviews',
    urls: [
      { name: 'Job Application Page', url: 'https://techcorp.com/careers/python-developer' },
      { name: 'Company Website', url: 'https://techcorp.com' },
      { name: 'LinkedIn Job Posting', url: 'https://linkedin.com/jobs/view/python-developer' }
    ],
    cv: 'John Doe\nSenior Python Developer\nEmail: john.doe@email.com | Phone: (555) 123-4567\n\nSummary: Experienced Python developer with 6+ years of expertise in Django, React, and cloud technologies. Proven track record of delivering scalable web applications and leading development teams.\n\nKey Skills: Python, Django, React, PostgreSQL, Redis, Docker, AWS, Git\n\nRelevant Experience:\n• Led development of 3 major web applications using Django and React\n• Implemented CI/CD pipelines reducing deployment time by 60%\n• Mentored 4 junior developers and conducted code reviews\n• Optimized database queries improving performance by 40%',
    coverLetter: 'Dear Hiring Manager,\n\nI am excited to apply for the Senior Python Developer position at TechCorp Inc. With over 6 years of experience in Python development and a strong background in Django and React, I am confident I can contribute significantly to your team.\n\nMy experience aligns perfectly with your requirements. I have extensive experience with Django framework, having built and maintained multiple production applications. I also have strong React skills and have worked extensively with PostgreSQL and Redis for data management.\n\nI am particularly drawn to TechCorp\'s innovative approach to technology and your commitment to building scalable solutions. I would welcome the opportunity to discuss how my skills and experience can benefit your team.\n\nThank you for considering my application. I look forward to hearing from you.\n\nBest regards,\nJohn Doe'
  },
  {
    id: 2,
    title: 'Full Stack Developer',
    employer: 'StartupXYZ',
    description: 'Join our fast-growing startup as a full stack developer. Work with modern technologies including Node.js, React, and PostgreSQL in an agile environment.',
    status: 'applied',
    fullDescription: 'Join our fast-growing startup as a full stack developer. Work with modern technologies including Node.js, React, and PostgreSQL in an agile environment.\n\nRequirements:\n• 3+ years of experience with Node.js and React\n• Experience with PostgreSQL and Redis\n• Knowledge of Docker and cloud platforms\n• Experience with agile development\n\nResponsibilities:\n• Develop full-stack web applications\n• Work in an agile team environment\n• Write clean, maintainable code\n• Participate in code reviews and testing',
    urls: [
      { name: 'Job Application Page', url: 'https://startupxyz.com/careers/full-stack' },
      { name: 'Company Website', url: 'https://startupxyz.com' }
    ],
    cv: 'John Doe\nFull Stack Developer\nEmail: john.doe@email.com | Phone: (555) 123-4567\n\nSummary: Full stack developer with 4+ years of experience in modern web technologies. Proven track record of delivering scalable applications in startup environments.\n\nKey Skills: Node.js, React, PostgreSQL, Redis, Docker, AWS, Git\n\nRelevant Experience:\n• Built 5 production web applications using Node.js and React\n• Implemented real-time features using WebSockets\n• Optimized database performance by 50%\n• Led development of mobile-responsive interfaces',
    coverLetter: 'Dear Hiring Manager,\n\nI am excited to apply for the Full Stack Developer position at StartupXYZ. With 4+ years of experience in modern web development and a passion for building scalable applications, I am confident I can contribute to your team\'s success.\n\nMy experience with Node.js, React, and PostgreSQL aligns perfectly with your technology stack. I have successfully delivered multiple production applications and understand the challenges of building robust systems in a startup environment.\n\nI am particularly drawn to StartupXYZ\'s innovative approach and rapid growth. I would welcome the opportunity to contribute to your mission and grow with the company.\n\nThank you for considering my application.\n\nBest regards,\nJohn Doe'
  },
  {
    id: 3,
    title: 'React Developer',
    employer: 'BigTech Company',
    description: 'We need a React developer with 3+ years of experience to work on our customer-facing applications. Experience with TypeScript and Redux is a plus.',
    status: 'rejected',
    fullDescription: 'We need a React developer with 3+ years of experience to work on our customer-facing applications. Experience with TypeScript and Redux is a plus.\n\nRequirements:\n• 3+ years of experience with React\n• Experience with TypeScript and Redux\n• Knowledge of modern JavaScript (ES6+)\n• Experience with testing frameworks\n\nResponsibilities:\n• Develop customer-facing React applications\n• Work with TypeScript and Redux\n• Write unit and integration tests\n• Collaborate with design and backend teams',
    urls: [
      { name: 'Job Application Page', url: 'https://bigtech.com/careers/react-developer' },
      { name: 'Company Website', url: 'https://bigtech.com' }
    ],
    cv: 'John Doe\nReact Developer\nEmail: john.doe@email.com | Phone: (555) 123-4567\n\nSummary: React developer with 3+ years of experience building modern web applications. Strong focus on user experience and code quality.\n\nKey Skills: React, TypeScript, Redux, JavaScript (ES6+), Jest, Git\n\nRelevant Experience:\n• Built 4 customer-facing React applications\n• Implemented complex state management with Redux\n• Achieved 90%+ test coverage with Jest\n• Optimized application performance by 40%',
    coverLetter: 'Dear Hiring Manager,\n\nI am excited to apply for the React Developer position at BigTech Company. With 3+ years of experience in React development and a strong background in TypeScript and Redux, I am confident I can contribute to your team.\n\nMy experience building customer-facing applications aligns perfectly with your requirements. I have successfully delivered multiple React applications with TypeScript and Redux, ensuring high code quality and excellent user experience.\n\nI am particularly drawn to BigTech Company\'s commitment to innovation and user-centric design. I would welcome the opportunity to contribute to your mission of building exceptional customer experiences.\n\nThank you for considering my application.\n\nBest regards,\nJohn Doe'
  },
  {
    id: 4,
    title: 'DevOps Engineer',
    employer: 'CloudTech Solutions',
    description: 'Looking for a DevOps engineer to manage our cloud infrastructure. Experience with AWS, Docker, and Kubernetes required. Help us scale our platform.',
    status: 'new',
    fullDescription: 'Looking for a DevOps engineer to manage our cloud infrastructure. Experience with AWS, Docker, and Kubernetes required. Help us scale our platform.\n\nRequirements:\n• 4+ years of experience with AWS\n• Experience with Docker and Kubernetes\n• Knowledge of CI/CD pipelines\n• Experience with monitoring and logging\n\nResponsibilities:\n• Manage cloud infrastructure on AWS\n• Implement and maintain CI/CD pipelines\n• Monitor system performance and reliability\n• Automate deployment processes',
    urls: [
      { name: 'Job Application Page', url: 'https://cloudtech.com/careers/devops-engineer' },
      { name: 'Company Website', url: 'https://cloudtech.com' }
    ],
    cv: 'John Doe\nDevOps Engineer\nEmail: john.doe@email.com | Phone: (555) 123-4567\n\nSummary: DevOps engineer with 5+ years of experience managing cloud infrastructure and implementing CI/CD pipelines. Proven track record of improving system reliability and deployment efficiency.\n\nKey Skills: AWS, Docker, Kubernetes, CI/CD, Terraform, Git\n\nRelevant Experience:\n• Managed infrastructure for 10+ production applications\n• Reduced deployment time by 70% with CI/CD automation\n• Implemented monitoring and alerting systems\n• Achieved 99.9% uptime for critical systems',
    coverLetter: 'Dear Hiring Manager,\n\nI am excited to apply for the DevOps Engineer position at CloudTech Solutions. With 5+ years of experience in cloud infrastructure management and a strong background in AWS, Docker, and Kubernetes, I am confident I can contribute to your team\'s success.\n\nMy experience aligns perfectly with your requirements. I have successfully managed cloud infrastructure for multiple production applications and implemented efficient CI/CD pipelines that significantly improved deployment processes.\n\nI am particularly drawn to CloudTech Solutions\' focus on scalable cloud solutions and commitment to operational excellence. I would welcome the opportunity to help scale your platform and improve system reliability.\n\nThank you for considering my application.\n\nBest regards,\nJohn Doe'
  }
])

const selectedApplications = ref(new Set())
const currentSort = ref('status-creation')
const showModal = ref(false)
const selectedJob = ref(null)

// Computed properties
const sortedApplications = computed(() => {
  const apps = [...applications.value]
  
  switch (currentSort.value) {
    case 'title':
      return apps.sort((a, b) => a.title.localeCompare(b.title))
    
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
        
        return a.id - b.id
      })
  }
})

const selectedCount = computed(() => selectedApplications.value.size)

// Methods
const toggleSelection = (applicationId) => {
  if (selectedApplications.value.has(applicationId)) {
    selectedApplications.value.delete(applicationId)
  } else {
    selectedApplications.value.add(applicationId)
  }
}

const rejectApplication = (applicationId) => {
  console.log(`Rejecting application ${applicationId}`)
  const app = applications.value.find(a => a.id === applicationId)
  if (app) {
    app.status = 'rejected'
    selectedApplications.value.delete(applicationId)
  }
}

const deleteApplication = (applicationId) => {
  console.log(`Deleting application ${applicationId}`)
  applications.value = applications.value.filter(a => a.id !== applicationId)
  selectedApplications.value.delete(applicationId)
}

const openJobModal = (application) => {
  selectedJob.value = application
  showModal.value = true
}

const closeJobModal = () => {
  showModal.value = false
  selectedJob.value = null
}

const applyToJob = (applicationId) => {
  console.log(`Applying to job ${applicationId}`)
  const app = applications.value.find(a => a.id === applicationId)
  if (app) {
    app.status = 'applied'
  }
  closeJobModal()
}

const rejectAllSelected = () => {
  if (selectedApplications.value.size > 0) {
    if (confirm(`Reject ${selectedApplications.value.size} selected applications?`)) {
      selectedApplications.value.forEach(id => rejectApplication(id))
      selectedApplications.value.clear()
    }
  }
}

const deleteAllSelected = () => {
  if (selectedApplications.value.size > 0) {
    if (confirm(`Delete ${selectedApplications.value.size} selected applications? This action cannot be undone.`)) {
      selectedApplications.value.forEach(id => deleteApplication(id))
      selectedApplications.value.clear()
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
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4 text-gray-700">Applications</h2>
    
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
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
          {{ application.title }}
        </h3>
        
        <p class="employer-name text-sm text-gray-600 mb-3">
          {{ application.employer }}
        </p>
        
        <p class="job-description text-sm text-gray-700 line-clamp-3">
          {{ application.description }}
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