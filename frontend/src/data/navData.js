import { LayoutDashboard, User, Compass, ClipboardCheck, CalendarCheck, Zap, TrendingUp, Library, FileText, MessageSquare } from 'lucide-react';

export const navItems = [
  { to: '/', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/profile', label: 'My Profile', short: 'Profile', icon: User },
  { to: '/exam-recommendation', label: 'Exam Recommendation', short: 'Exams', icon: Compass },
  { to: '/diagnostic', label: 'Diagnostic Assessment', short: 'Test', icon: ClipboardCheck },
  { to: '/study-plan', label: 'Study Plan', short: 'Plan', icon: CalendarCheck },
  { to: '/adaptive-quiz', label: 'Adaptive Quiz', short: 'Quiz', icon: Zap },
  { to: '/performance', label: 'Performance Analytics', short: 'Stats', icon: TrendingUp },
  { to: '/resources', label: 'Resources', short: 'Resources', icon: Library },
  { to: '/pyqs', label: 'Previous Year Questions', short: 'PYQs', icon: FileText },
  { to: '/doubts', label: 'Doubts & Community', short: 'Doubts', icon: MessageSquare },
];

// Items shown in the mobile bottom bar
export const bottomNav = ['/', '/exam-recommendation', '/study-plan', '/adaptive-quiz', '/performance'];