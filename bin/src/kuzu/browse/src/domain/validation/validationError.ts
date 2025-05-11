export function createValidationError(
  message: string,
  field?: string,
  code?: string
): Error {
  const error = new Error(message);
  error.name = 'ValidationError';
  
  // エラーに追加情報を付与
  if (field !== undefined) {
    (error as any).field = field;
  }
  if (code !== undefined) {
    (error as any).code = code;
  }
  
  return error;
}

export function isValidationError(error: unknown): boolean {
  return error instanceof Error && error.name === 'ValidationError';
}

export function getValidationErrorDetails(error: Error): {
  message: string;
  field?: string;
  code?: string;
} {
  return {
    message: error.message,
    field: (error as any).field,
    code: (error as any).code
  };
}
