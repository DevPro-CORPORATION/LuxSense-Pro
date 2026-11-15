import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export interface ToastNotification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  durationMs?: number;
}

interface NotificationToastContainerProps {
  notifications: ToastNotification[];
  onDismiss: (id: string) => void;
}

export const NotificationToastContainer: React.FC<NotificationToastContainerProps> = ({
  notifications,
  onDismiss,
}) => {
  return (
    <div className="fixed top-12 right-6 z-50 flex flex-col space-y-3 pointer-events-none max-w-md w-full">
      <AnimatePresence>
        {notifications.map((notif) => (
          <NotificationToastItem
            key={notif.id}
            notification={notif}
            onDismiss={() => onDismiss(notif.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

interface NotificationToastItemProps {
  notification: ToastNotification;
  onDismiss: () => void;
}

const NotificationToastItem: React.FC<NotificationToastItemProps> = ({
  notification,
  onDismiss,
}) => {
  const { type, title, message, actionLabel, onAction, durationMs = 8000 } = notification;

  useEffect(() => {
    if (type !== 'error') {
      const timer = setTimeout(() => {
        onDismiss();
      }, durationMs);
      return () => clearTimeout(timer);
    }
  }, [type, durationMs, onDismiss]);

  const borderClass =
    type === 'success'
      ? 'border-metrology-green bg-chassis-950/95 shadow-glow-green text-zinc-100'
      : type === 'warning'
      ? 'border-amber-500 bg-chassis-950/95 shadow-lg text-zinc-100'
      : type === 'error'
      ? 'border-metrology-crimson bg-chassis-950/95 shadow-lg text-zinc-100'
      : 'border-metrology-blue bg-chassis-950/95 shadow-lg text-zinc-100';

  const iconClass =
    type === 'success'
      ? 'text-metrology-green'
      : type === 'warning'
      ? 'text-amber-400'
      : type === 'error'
      ? 'text-metrology-crimson'
      : 'text-metrology-blue';

  return (
    <motion.div
      initial={{ opacity: 0, x: 40, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 40, scale: 0.95 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`pointer-events-auto border rounded-xl p-4 flex flex-col space-y-2 backdrop-blur-md ${borderClass}`}
    >
      <div className="flex items-start justify-between space-x-3">
        <div className="flex items-start space-x-3">
          <div className={`mt-0.5 shrink-0 ${iconClass}`}>
            {type === 'success' && <CheckCircle2 className="w-5 h-5" />}
            {type === 'warning' && <AlertTriangle className="w-5 h-5" />}
            {type === 'error' && <AlertCircle className="w-5 h-5" />}
            {type === 'info' && <Info className="w-5 h-5" />}
          </div>
          <div>
            <h4 className="font-mono font-bold text-xs uppercase tracking-wider text-white">
              {title}
            </h4>
            <p className="font-mono text-xs text-zinc-300 mt-1 leading-relaxed whitespace-pre-line">
              {message}
            </p>
          </div>
        </div>

        <button
          onClick={onDismiss}
          className="text-zinc-500 hover:text-white transition-colors p-1 -mr-1 -mt-1 rounded"
          title="Dismiss notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {actionLabel && onAction && (
        <div className="pt-2 flex justify-end">
          <button
            onClick={() => {
              onAction();
              onDismiss();
            }}
            className={`px-3 py-1 text-xs font-mono font-bold rounded uppercase tracking-wide transition-colors ${
              type === 'error'
                ? 'bg-metrology-crimson/20 border border-metrology-crimson/50 text-metrology-crimson hover:bg-metrology-crimson/30'
                : 'bg-metrology-green/20 border border-metrology-green/50 text-metrology-green hover:bg-metrology-green/30'
            }`}
          >
            {actionLabel}
          </button>
        </div>
      )}
    </motion.div>
  );
};
