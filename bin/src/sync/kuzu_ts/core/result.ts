/**
 * Result type pattern for error handling
 * エラー処理のためのResult型パターン
 */

export type Success<T> = {
  ok: true;
  data: T;
};

export type Failure<E> = {
  ok: false;
  error: E;
};

export type Result<T, E> = Success<T> | Failure<E>;

// Helper functions
export function success<T>(data: T): Success<T> {
  return { ok: true, data };
}

export function failure<E>(error: E): Failure<E> {
  return { ok: false, error };
}

// Type guard
export function isSuccess<T, E>(result: Result<T, E>): result is Success<T> {
  return result.ok === true;
}

export function isFailure<T, E>(result: Result<T, E>): result is Failure<E> {
  return result.ok === false;
}