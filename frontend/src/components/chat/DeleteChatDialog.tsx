'use client';

import styles from './DeleteChatDialog.module.css';
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface DeleteChatDialogProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  onConfirm: () => void;
}

export function DeleteChatDialog({ open, setOpen, onConfirm }: DeleteChatDialogProps) {
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className={styles.dialogContent}>
        <DialogHeader className={styles.dialogHeader}>
          <DialogTitle className={styles.dialogTitle}>Delete Chat</DialogTitle>
        </DialogHeader>
        <p className={styles.dialogMessage}>
          Are you sure you want to delete this chat?
        </p>
        <DialogFooter className={styles.dialogFooter}>
          <button
            className={styles.buttonDestructive}
            onClick={onConfirm}
            >
            Delete
          </button>
          <DialogClose asChild>
            <button className={styles.buttonSecondary}>Cancel</button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


