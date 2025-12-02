export interface IStorageService {
  /**
   * Retrieves an item from storage
   * @param key - The storage key
   * @returns The stored value or null if not found
   */
  getItem(key: string): string | null;

  /**
   * Stores an item in storage
   * @param key - The storage key
   * @param value - The value to store
   */
  setItem(key: string, value: string): void;

  /**
   * Removes an item from storage
   * @param key - The storage key
   */
  removeItem(key: string): void;

  /**
   * Clears all items from storage
   */
  clear(): void;

  /**
   * Gets a parsed JSON object from storage
   * @param key - The storage key
   * @returns The parsed object or null if not found or invalid JSON
   */
  getObject<T>(key: string): T | null;

  /**
   * Stores an object as JSON in storage
   * @param key - The storage key
   * @param value - The object to store
   */
  setObject<T>(key: string, value: T): void;
}
