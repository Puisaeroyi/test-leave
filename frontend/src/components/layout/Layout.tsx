import { type ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

/**
 * Modern Minimal Layout Component
 * Sidebar + Header + Main Content Area
 */
export default function Layout({ children, title }: LayoutProps) {
  return (
    <div className="min-h-screen bg-white-soft">
      <Sidebar />
      <div className="ml-64">
        <Header title={title} />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
