import { useQuery } from '@tanstack/react-query';
import { leavesApi } from '../../api/leaves';
import Card from '../common/Card';

interface LeaveBalanceCardProps {
  year?: number;
}

export default function LeaveBalanceCard({ year }: LeaveBalanceCardProps) {
  const { data: balance, isLoading } = useQuery({
    queryKey: ['leaveBalance', year],
    queryFn: () => leavesApi.getMyLeaveBalance(year),
  });

  if (isLoading) {
    return (
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Leave Balance</h2>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </Card>
    );
  }

  if (!balance) {
    return (
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Leave Balance</h2>
        <p className="text-gray-500">No balance data available</p>
      </Card>
    );
  }

  const percentageUsed = (balance.used_hours / balance.allocated_hours) * 100;
  const circumference = 2 * Math.PI * 54; // r=54
  const strokeDashoffset = circumference - (percentageUsed / 100) * circumference;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Leave Balance</h2>
        <span className="text-sm text-gray-500">{balance.year}</span>
      </div>

      <div className="flex items-center gap-6">
        {/* Circular Progress */}
        <div className="relative w-32 h-32 flex-shrink-0">
          <svg viewBox="0 0 120 120" className="w-full h-full transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="#F3F4F6"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="#DC2626"
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-500 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {(balance.remaining_days ?? balance.remaining_hours / 8).toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">days</div>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Remaining</span>
            <span className="font-semibold text-gray-900">
              {balance.remaining_hours.toFixed(1)}h
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Used</span>
            <span className="font-medium text-red-600">
              {balance.used_hours.toFixed(1)}h
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Allocated</span>
            <span className="font-medium text-gray-700">
              {balance.allocated_hours.toFixed(1)}h
            </span>
          </div>
          {balance.adjusted_hours > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Adjusted</span>
              <span className="font-medium text-green-600">
                +{balance.adjusted_hours.toFixed(1)}h
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
