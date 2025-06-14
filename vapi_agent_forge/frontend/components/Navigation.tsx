import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { cn } from '../utils/cn';

const Navigation: React.FC = () => {
  const router = useRouter();

  const isActive = (path: string) => router.pathname === path;

  return (
    <nav className="bg-white/10 backdrop-blur-lg border-b border-white/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link href="/" className="text-xl font-bold text-white">
                Vapi Bridge
              </Link>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  href="/"
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium',
                    isActive('/')
                      ? 'bg-white/20 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  )}
                >
                  Dashboard
                </Link>
                <Link
                  href="/agents"
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium',
                    isActive('/agents')
                      ? 'bg-white/20 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  )}
                >
                  Agents
                </Link>
                <Link
                  href="/workflows"
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium',
                    isActive('/workflows')
                      ? 'bg-white/20 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  )}
                >
                  Workflows
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 