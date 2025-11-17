
import { cn } from '../../lib/utils';



export const Checkbox = ({
  label,
  error,
  id,
  className,
  ...props
}) => {
  return (
    <div className="flex items-center">
      <input
        type="checkbox"
        id={id}
        className={cn(
          'h-4 w-4 text-primary focus:ring-primary border-border rounded bg-transparent',
          className
        )}
        {...props}
      />
      {label && (
        <label htmlFor={id} className="ml-2 block text-sm text-copy-light">
          {label}
        </label>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
};
