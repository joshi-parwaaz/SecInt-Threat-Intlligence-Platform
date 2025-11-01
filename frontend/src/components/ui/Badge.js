import React from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center justify-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-yellow-500 text-black hover:bg-yellow-600',
        secondary: 'border-transparent bg-gray-700 text-white hover:bg-gray-600',
        outline: 'text-yellow-500 border-yellow-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

const Badge = ({ className, variant, ...props }) => {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
};

export { Badge, badgeVariants };
