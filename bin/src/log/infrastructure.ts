/**
 * Infrastructure layer for log module - handles external I/O dependencies
 * 
 * This layer isolates external dependencies like console output,
 * providing abstractions that can be easily mocked or replaced.
 */

/**
 * Write a message to stdout
 * 
 * This function wraps the console.log functionality to isolate the external
 * dependency of stdout output. It provides a single point of control
 * for how log messages are output to the console.
 * 
 * @param message The message to write to stdout
 * 
 * Note:
 *   This abstraction allows for future extensibility such as:
 *   - Adding timestamps
 *   - Formatting output
 *   - Redirecting to different outputs
 *   - Buffering messages
 */
export function stdoutWriter(message: string): void {
  console.log(message);
}