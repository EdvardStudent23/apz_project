import { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

interface Props extends HTMLAttributes<HTMLDivElement> {
  tight?: boolean;
  children: ReactNode;
}

export function Card({ tight, className, children, ...rest }: Props) {
  return (
    <div className={clsx('card', tight && 'card-tight', className)} {...rest}>
      {children}
    </div>
  );
}
