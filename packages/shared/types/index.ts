export interface User {
  id: number
  email: string
  username: string
  display_name: string
  avatar_url?: string
  bio?: string
  created_at: string
}

export interface LearningPath {
  id: number
  title: string
  description: string
  goal: string
  difficulty: 'beginner' | 'easy' | 'medium' | 'hard' | 'expert'
  status: 'not_started' | 'in_progress' | 'completed'
  progress: number
  modules: Module[]
  created_at: string
}

export interface Module {
  id: number
  path_id: number
  title: string
  description: string
  order: number
  status: 'not_started' | 'in_progress' | 'completed'
  progress: number
  estimated_minutes: number
  content: ContentItem[]
}

export interface ContentItem {
  type: 'text' | 'video' | 'quiz' | 'code' | 'embed'
  title: string
  data: any
}

export interface PracticeSession {
  id: number
  module_id: number
  session_type: 'quiz' | 'challenge' | 'review'
  questions: Question[]
  score: number
  status: 'in_progress' | 'completed'
  started_at: string
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
  user_id: number
  module_id: number
  learning_time_minutes: number
  completion_percentage: number
  quiz_scores: number[]
  weak_points: string[]
  strong_points: string[]
}

export interface AIAgent {
  type: 'tutor' | 'buddy' | 'examiner' | 'planner'
  name: string
  description: string
}

export interface AIMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_type?: string
}

export interface KnowledgeState {
  topic: string
  mastery_level: number
  review_count: number
  last_review_score: number | null
  time_since_last_review_hours: number
}
