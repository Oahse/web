/**
 * Refund Status Component - Shows refund progress with timeline
 */
import React from 'react';
import { format } from 'date-fns';
import { CheckCircleIcon, ClockIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface RefundStatusProps {
  refund: any;
}

export const RefundStatus: React.FC<RefundStatusProps> = ({ refund }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'requested': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string, completed: boolean) => {
    if (completed) {
      return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
    }
    if (status === 'rejected' || status === 'cancelled') {
      return <XCircleIcon className="w-5 h-5 text-red-600" />;
    }
    return <ClockIcon className="w-5 h-5 text-gray-400" />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Refund #{refund.refund_number}</h3>
          <p className="text-sm text-gray-600">
            Requested on {format(new Date(refund.requested_at), 'MMM dd, yyyy')}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(refund.status)}`}>
          {refund.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {refund.timeline?.map((step, index) => (
          <div key={index} className="flex items-start space-x-3">
            {getStatusIcon(step.status, step.completed)}
            <div className="flex-1">
              <div className="font-medium text-gray-900">{step.title}</div>
              <div className="text-sm text-gray-600">{step.description}</div>
              {step.timestamp && (
                <div className="text-xs text-gray-500 mt-1">
                  {format(new Date(step.timestamp), 'MMM dd, yyyy at h:mm a')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Refund amount */}
      <div className="mt-6 pt-6 border-t">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Refund Amount</span>
          <span className="text-xl font-bold text-green-600">
            ${refund.processed_amount || refund.approved_amount || refund.requested_amount}
          </span>
        </div>
      </div>
    </div>
  );
};