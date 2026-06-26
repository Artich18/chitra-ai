import { Search, FileSearch, Gauge, MessageSquare, Map, BookOpen, PenLine, Building2, IndianRupee, GraduationCap, Brain, Mail, Mic } from 'lucide-react';

const ACTIONS = [
  { id: 'find_jobs', label: 'Find Jobs', icon: Search, prompt: 'Find me jobs that match my profile.' },
  { id: 'improve_resume', label: 'Improve Resume', icon: FileSearch, prompt: 'Review my resume and suggest improvements.' },
  { id: 'increase_ats', label: 'Increase ATS', icon: Gauge, prompt: 'How do I increase my ATS score?' },
  { id: 'interview_questions', label: 'Interview Q&A', icon: MessageSquare, prompt: 'Give me likely interview questions with strong answers.' },
  { id: 'career_roadmap', label: 'Career Roadmap', icon: Map, prompt: 'Generate my 6-month career roadmap.' },
  { id: 'explain_jd', label: 'Explain JD', icon: BookOpen, prompt: 'Help me understand a job description.' },
  { id: 'missing_skills', label: 'Missing Skills', icon: Brain, prompt: 'What skills am I missing for my target role?' },
  { id: 'learning_resources', label: 'Learning Resources', icon: GraduationCap, prompt: 'Recommend the best learning resources for my missing skills.' },
  { id: 'salary_insights', label: 'Salary Insights', icon: IndianRupee, prompt: 'What is the salary range for my target role?' },
  { id: 'company_research', label: 'Company Research', icon: Building2, prompt: 'Research a company for me.' },
  { id: 'resume_rewrite', label: 'Resume Rewrite', icon: PenLine, prompt: 'Rewrite my resume targeted to my goal.' },
  { id: 'mock_interview', label: 'Mock Interview', icon: Mic, prompt: 'Start a mock interview with me.' },
  { id: 'generate_cover_letter', label: 'Cover Letter', icon: Mail, prompt: 'Generate a strong cover letter for my target role.' },
];

export default function QuickActions({ onSelect }) {
  return (
    <div className="flex flex-wrap gap-2" data-testid="quick-actions">
      {ACTIONS.map((a) => (
        <button
          key={a.id}
          onClick={() => onSelect(a.id, a.prompt)}
          data-testid={`quick-action-${a.id}`}
          className="group flex items-center gap-2 text-xs font-medium px-3.5 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/50 text-slate-300 hover:text-white transition-all"
        >
          <a.icon className="w-3.5 h-3.5 text-purple-400 group-hover:text-purple-300" />
          {a.label}
        </button>
      ))}
    </div>
  );
}
