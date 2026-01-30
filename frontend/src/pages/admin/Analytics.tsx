import React from 'react';
import { BarChart3Icon } from 'lucide-react';

export const AdminAnalytics = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-copy">Analytics</h1>
        <p className="text-copy-light mt-2">Business analytics and insights</p>
      </div>

      <div className="bg-surface rounded-lg border border-border-light p-12 text-center">
        <BarChart3Icon className="w-16 h-16 text-primary/20 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-copy mb-2">Analytics Dashboard</h2>
        <p className="text-copy-light">Detailed analytics and metrics coming soon</p>
      </div>
    </div>
  );
};

export default AdminAnalytics;
