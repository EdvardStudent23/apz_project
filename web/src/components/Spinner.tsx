import clsx from 'clsx';

interface Props {
  size?: 'sm' | 'lg';
  className?: string;
  label?: string;
}

export function Spinner({ size = 'sm', className, label = 'Loading' }: Props) {
  return (
    <span
      className={clsx('spinner', size === 'lg' && 'spinner-lg', className)}
      role="status"
      aria-label={label}
    />
  );
}
