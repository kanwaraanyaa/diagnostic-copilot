import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  suffix?: string;
  containerClassName?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  helperText,
  error,
  suffix,
  containerClassName = '',
  className = '',
  id,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label htmlFor={inputId} className="text-xs font-semibold text-slate-700 flex items-center justify-between">
          <span>{label}</span>
          {props.required && <span className="text-rose-500 font-normal">*</span>}
        </label>
      )}
      <div className="relative flex items-center">
        <input
          id={inputId}
          className={`w-full bg-white border rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all ${
            error
              ? 'border-rose-400 focus:ring-rose-200'
              : 'border-slate-300 focus:border-teal-600 focus:ring-teal-100'
          } ${suffix ? 'pr-12' : ''} ${className}`}
          {...props}
        />
        {suffix && (
          <span className="absolute right-3 text-xs text-slate-400 pointer-events-none font-mono">
            {suffix}
          </span>
        )}
      </div>
      {error && <p className="text-xs text-rose-600">{error}</p>}
      {!error && helperText && <p className="text-xs text-slate-400">{helperText}</p>}
    </div>
  );
};

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
  containerClassName?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  helperText,
  error,
  containerClassName = '',
  className = '',
  id,
  ...props
}) => {
  const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label htmlFor={textareaId} className="text-xs font-semibold text-slate-700 flex items-center justify-between">
          <span>{label}</span>
          {props.required && <span className="text-rose-500 font-normal">*</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`w-full bg-white border rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all resize-y ${
          error
            ? 'border-rose-400 focus:ring-rose-200'
            : 'border-slate-300 focus:border-teal-600 focus:ring-teal-100'
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-rose-600">{error}</p>}
      {!error && helperText && <p className="text-xs text-slate-400">{helperText}</p>}
    </div>
  );
};

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Array<{ value: string; label: string }>;
  helperText?: string;
  error?: string;
  containerClassName?: string;
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
  helperText,
  error,
  containerClassName = '',
  className = '',
  id,
  ...props
}) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label htmlFor={selectId} className="text-xs font-semibold text-slate-700">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`w-full bg-white border rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 transition-all ${
          error
            ? 'border-rose-400 focus:ring-rose-200'
            : 'border-slate-300 focus:border-teal-600 focus:ring-teal-100'
        } ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-rose-600">{error}</p>}
      {!error && helperText && <p className="text-xs text-slate-400">{helperText}</p>}
    </div>
  );
};
