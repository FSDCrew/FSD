import { toast } from 'sonner';
import type { INotificationService } from './interfaces/INotificationService';

export class ToastNotificationService implements INotificationService {
  success(message: string): void {
    toast.success(message);
  }

  error(message: string): void {
    toast.error(message);
  }

  info(message: string): void {
    toast.info(message);
  }

  warning(message: string): void {
    toast.warning(message);
  }
}
