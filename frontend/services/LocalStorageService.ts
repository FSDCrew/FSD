import type { IStorageService } from './interfaces/IStorageService';

export class LocalStorageService implements IStorageService {
  getItem(key: string): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    return localStorage.getItem(key);
  }

  setItem(key: string, value: string): void {
    if (typeof window === 'undefined') {
      return;
    }
    localStorage.setItem(key, value);
  }

  removeItem(key: string): void {
    if (typeof window === 'undefined') {
      return;
    }
    localStorage.removeItem(key);
  }

  clear(): void {
    if (typeof window === 'undefined') {
      return;
    }
    localStorage.clear();
  }

  getObject<T>(key: string): T | null {
    const item = this.getItem(key);
    if (!item) {
      return null;
    }
    try {
      return JSON.parse(item) as T;
    } catch {
      return null;
    }
  }

  setObject<T>(key: string, value: T): void {
    try {
      const jsonString = JSON.stringify(value);
      this.setItem(key, jsonString);
    } catch (error) {
      console.error('Failed to serialize object:', error);
    }
  }
}
