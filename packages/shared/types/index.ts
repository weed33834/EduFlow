export interface User {
  id: number
  email: string
  username: string
  displayName: string
  avatarUrl?: string
  bio?: string
  createdAt: string
}

export interface LearningPath {
  id: number
  title: string
  description: string
  goal: string
  difficulty: 'beginner' | 'easy' | 'medium' | 'hard'
  status: 'active' | 'paused' | 'completed'
  progress: number
  modules: Module[]
  createdAt: string
}

export interface Module {
  id: number
  pathId: number
  title: string
  description: string
  order: number
  status: 'pending' | 'in_progress' | 'completed'
  progress: number
  estimatedMinutes: number
  content: ContentItem[]
}

export interface ContentItem {
  type: 'text' | 'video' | 'quiz' | 'code' | 'embed'
  title: string
  data: any
}

export interface PracticeSession {
  id: number
  moduleId: number
  type: 'quiz' | 'challenge' | 'review'
  questions: Question[]
  score: number
  status: 'in_progress' | 'completed'
  startedAt: string
}

export interface Question {
  id: number
  type: 'choice' | 'fill' | 'short_answer' | 'code'
  question: string
  options?: string[]
  answer: string
  explanation: string
}

export interface Progress {
  userId: number
  moduleId: number
  learningTimeMinutes: number
  completionPercentage: number
  quizScores: number[]
  weakPoints: string[]
  strongPoints: string[]
}

export interface AIAgent {
  type: 'tutor' | 'buddy' | 'examiner' | 'planner'
  name: string
  description: string
}

export interface AIMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  agentType?: string
}

export interface KnowledgeState {
  topic: string
  masteryLevel: number
  reviewCount: number
  lastReviewScore: number | null
  timeSinceLastReviewHours: number
}