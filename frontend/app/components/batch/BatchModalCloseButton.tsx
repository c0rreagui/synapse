import React from 'react';
import { useBatch } from './BatchContext';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface BatchModalCloseButtonProps {
    onClose: () => void;
}

export function BatchModalCloseButton({ onClose }: BatchModalCloseButtonProps) {
    const { editingFileId } = useBatch();

    // If an editor is open, hide this global close button
    // The editor has its own "Back/Close" button in the same spot.
    if (editingFileId) return null;

    return (
        <button
            onClick={onClose}
            className="absolute top-6 right-6 p-2 rounded-full bg-black/50 hover:bg-white/10 text-gray-500 hover:text-white transition-colors z-[60]"
        >
            <XMarkIcon className="w-5 h-5" />
        </button>
    );
}
