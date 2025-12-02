export interface INotificationService {
  /**
   * Displays a success notification
   * @param message - The success message to display
   */
  success(message: string): void;

  /**
   * Displays an error notification
   * @param message - The error message to display
   */
  error(message: string): void;

  /**
   * Displays an informational notification
   * @param message - The info message to display
   */
  info(message: string): void;

  /**
   * Displays a warning notification
   * @param message - The warning message to display
   */
  warning(message: string): void;
}
