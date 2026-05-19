import { ReactNode } from 'react';
import clsx from 'clsx';

type Tone = 'info' | 'success' | 'error' | 'warn';

interface Props {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}

export function Banner({ tone = 'info', children, className }: Props) {
  return (
    <div className={clsx('banner', `banner-${tone}`, className)} role={tone === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
    </div>
  );
}
