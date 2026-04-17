import { Brain, LogOut, User } from 'lucide-react';
import { useLogout } from '../hooks/useAuth';
import { useAuthStore } from '../store/authStore';

export default function Layout({ children }) {
  const user = useAuthStore((s) => s.user);
  const handleLogout = useLogout();

  return (
    <div className="min-h-screen bg-surface-950 flex flex-col">
      {/* Header */}
      <header className="h-16 border-b border-surface-800 bg-surface-950/80 backdrop-blur-xl flex items-center justify-between px-6 flex-shrink-0 z-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-md shadow-brand-600/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">
              <span className="gradient-text">DocuMind</span>
              <span className="text-surface-400 font-medium ml-1">AI</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-800/50">
            <User className="w-4 h-4 text-surface-400" />
            <span className="text-sm text-surface-300 font-medium">{user?.username}</span>
          </div>
          <button
            id="logout-button"
            onClick={handleLogout}
            className="btn-ghost flex items-center gap-2 text-sm"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
