'use client';

import styles from './RenameChatDialog.module.css';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export function RenameChatDialog({
  open,
  setOpen,
  newTitle,
  setNewTitle,
  onSubmit
}: {
  open: boolean;
  setOpen: (open: boolean) => void;
  newTitle: string;
  setNewTitle: (val: string) => void;
  onSubmit: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className={styles.dialogContent}>
        <DialogHeader className={styles.dialogHeader}>
          <DialogTitle className={styles.dialogTitle}>Rename Chat</DialogTitle>
          <DialogDescription className={styles.dialogDescription}>
            Enter a new title for this chat
          </DialogDescription>
        </DialogHeader>
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              onSubmit();
            }
          }}
          className={styles.input}
          placeholder="Enter a new title..."
        />
        <DialogFooter className={styles.dialogFooter}>
          <button className={styles.buttonPrimary} onClick={onSubmit}>Confirm</button>
          <button className={styles.buttonSecondary} onClick={() => setOpen(false)}>Cancel</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}









