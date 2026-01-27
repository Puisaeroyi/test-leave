type BadgeVariant = 'approved' | 'pending' | 'rejected' | 'cancelled' | 'info';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

const variantStyles = {
  approved: 'bg-green-100 text-green-800 border-green-200',
  pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  rejected: 'bg-red-100 text-red-800 border-red-200',
  cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
};

/**
 * Modern Minimal Badge Component
 * Status badges with semantic colors
 */
export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]}`}>
      {children}
    </span>
  );
}
