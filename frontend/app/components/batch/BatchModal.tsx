import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { TikTokProfile as Profile } from '@/app/types';
import { BatchProvider } from './BatchContext';
import { BatchSidebar } from './BatchSidebar';
import { BatchMain } from './BatchMain';
import { BatchFooter } from './BatchFooter';
import { BatchCaptionEditor } from './BatchCaptionEditor';
import { BatchModalCloseButton } from './BatchModalCloseButton';
import { X } from 'lucide-react';

interface BatchUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    profiles: Profile[];
    initialFiles?: File[];
}

export default function BatchUploadModal({
    isOpen,
    onClose,
    onSuccess,
    profiles,
    initialFiles = []
}: BatchUploadModalProps) {

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/90 backdrop-blur-md" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-6xl h-[85vh] transform overflow-hidden rounded-[32px] bg-[#0c0c0c] border border-white/10 shadow-[0_0_100px_rgba(139,92,246,0.1)] transition-all flex flex-col relative">

                                <BatchProvider existingProfiles={profiles} initialFiles={initialFiles} onClose={onClose} onSuccess={onSuccess}>
                                    <div className="flex flex-1 h-full overflow-hidden relative">
                                        <BatchSidebar />
                                        <BatchMain />
                                        <BatchCaptionEditor />
                                    </div>
                                    <BatchFooter onClose={onClose} />

                                    {/* Smart Close Button (Hidden when Editor is open) */}
                                    <BatchModalCloseButton onClose={onClose} />
                                </BatchProvider>

                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
