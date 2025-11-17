import { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon } from 'lucide-react';

/**
 * @typedef {object} Option
 * @property {string} value
 * @property {string} label
 */

/**
 * @typedef {object} CustomSelectProps
 * @property {Option[]} options
 * @property {string} value
 * @property {(value: string) => void} onChange
 * @property {string} [placeholder='Select an option']
 * @property {string} [className='']
 * @property {string} [id]
 * @property {string} [name]
 * @property {boolean} [required=false]
 */

export const CustomSelect = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  className = '',
  id,
  name,
  required = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef(null);

  const selectedOption = options.find((option) => option.value === value);

  const handleOptionClick = (optionValue) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const handleClickOutside = (event) => {
    if (selectRef.current && !selectRef.current.contains(event.target)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className={`relative ${className}`} ref={selectRef}>
      <button
        type="button"
        id={id}
        name={name}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby={id ? `${id}-label` : undefined}
        className="relative w-full cursor-default rounded-md border border-border bg-surface py-2 pl-3 pr-10 text-left shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="block truncate text-main">
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <ChevronDownIcon className="h-5 w-5 text-copy-light" aria-hidden="true" />
        </span>
      </button>

      {isOpen && (
        <ul
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-surface py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
          tabIndex={-1}
          role="listbox"
          aria-labelledby={id ? `${id}-label` : undefined}
        >
          {options.map((option) => (
            <li
              key={option.value}
              id={`${id}-${option.value}`}
              role="option"
              className={`relative cursor-default select-none py-2 pl-3 pr-9 ${option.value === value ? 'bg-primary text-white' : 'text-main'}`}
              onClick={() => handleOptionClick(option.value)}
            >
              <span className={`block truncate ${option.value === value ? 'font-semibold' : 'font-normal'}`}>
                {option.label}
              </span>
              {option.value === value && (
                <span className="absolute inset-y-0 right-0 flex items-center pr-4">
                  {/* You can add a checkmark icon here if desired */}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      {required && <input type="hidden" value={value} required={required} />}
    </div>
  );
};
