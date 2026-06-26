import { useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const location = useLocation();
  const navigate = useNavigate();
  const { completeGoogleSession } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;
    const params = new URLSearchParams(location.hash.replace(/^#/, ''));
    const sessionId = params.get('session_id');
    if (!sessionId) {
      navigate('/login', { replace: true });
      return;
    }
    completeGoogleSession(sessionId)
      .then(() => navigate('/', { replace: true }))
      .catch(() => navigate('/login', { replace: true }));
  }, [location.hash, completeGoogleSession, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="w-7 h-7 animate-spin text-purple-400" />
    </div>
  );
}
