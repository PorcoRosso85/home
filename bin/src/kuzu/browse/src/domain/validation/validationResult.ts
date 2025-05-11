export type ValidationResult<T> = {
  isValid: boolean;
  data?: T;
  error?: string;
  errors?: Array<{ field: string; message: string }>;
};
