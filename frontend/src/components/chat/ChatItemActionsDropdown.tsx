// components/ChatItemActionsDropdown.tsx
import styles from './ChatItemActionsDropdown.module.css';
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { RenameChatDialog } from './RenameChatDialog';
import { DeleteChatDialog } from './DeleteChatDialog';

import { useState } from 'react';
// ...其他 import

export function ChatItemActionsDropdownMenu({ originalTitle, userID, chatID }: { originalTitle: string, userID: string, chatID: string}) {
  const router = useRouter();

  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const handleRenameSubmit = async () => {
    if (!newTitle.trim() || newTitle === originalTitle || newTitle === '') {
      setRenameOpen(false);
      return;
    } else {
      await axios.post(`/api/rename-chat`, {
        userID,
        chatID,
        newTitle
      });
      setRenameOpen(false);
      window.location.reload(); // 或用 props callback 更新狀態
    }
    
  };

  const handleDelete = async () => {
    const response = await axios.delete(`/api/delete-chat` + `?userID=${userID}&chatID=${chatID}`);
    const data = await response.data;
    if (data.status === 200) {
      setDeleteOpen(false);
      window.location.href = `/chat`;
    } else {
      alert('刪除失敗');
      console.error('Failed to delete chat:', data.error);
    }
    
  };

  return (
    <>
      <DropdownMenuContent align="end" className={styles.menuContent}>
        <DropdownMenuItem className={styles.menuItem}>
          Add To Favorites
        </DropdownMenuItem>
        <DropdownMenuSeparator className={styles.menuSeparator} />
        <DropdownMenuItem
          className={styles.menuItem}
          onClick={() => {
            setNewTitle(originalTitle);
            setRenameOpen(true)
          }}
        >
          Rename
        </DropdownMenuItem>
        <DropdownMenuItem className={styles.menuItem} onClick={() => setDeleteOpen(true)}>
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>

      <RenameChatDialog
        open={renameOpen}
        setOpen={setRenameOpen}
        newTitle={newTitle}
        setNewTitle={setNewTitle}
        onSubmit={handleRenameSubmit}
      />
      <DeleteChatDialog
        open={deleteOpen}
        setOpen={setDeleteOpen}
        onConfirm={handleDelete}
      />
    </>
  );
}
