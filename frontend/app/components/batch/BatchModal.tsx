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

import clsx from 'clsx';
import { InitialFilePreload } from './BatchContext';
import SchedulerForm, { SchedulingData } from '../SchedulerForm';

interface UniversalModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    profiles: Profile[];

    // Mode Selection
    mode?: 'batch' | 'single';

    // Batch Props
    initialFiles?: File[];
    initialPreload?: InitialFilePreload[];

    // Single/Scheduler Props
    initialDate?: Date;
    initialViralBoost?: boolean;
    initialData?: Partial<SchedulingData>;
    onSingleSubmit?: (data: SchedulingData) => void;
}

export default function UniversalModal({
    isOpen,
    onClose,
    onSuccess,
    profiles,
    mode = 'batch',
    initialFiles = [],
    initialPreload = [],
    initialDate = new Date(),
    initialViralBoost = false,
    initialData,
    onSingleSubmit
}: UniversalModalProps) {

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
                            <Dialog.Panel className={clsx(
                                "transform overflow-hidden rounded-[32px] bg-[#0c0c0c] border border-white/10 shadow-[0_0_100px_rgba(139,92,246,0.1)] transition-all flex flex-col relative",
                                mode === 'batch' ? "w-full max-w-6xl h-[85vh]" : "w-full max-w-lg p-6"
                            )}>

                                {mode === 'batch' ? (
                                    <BatchProvider existingProfiles={profiles} initialFiles={initialFiles} initialPreload={initialPreload} onClose={onClose} onSuccess={onSuccess}>
                                        <div className="flex flex-1 h-full overflow-hidden relative">
                                            <BatchSidebar />
                                            <BatchMain />
                                            <BatchCaptionEditor />
                                        </div>
                                        <BatchFooter onClose={onClose} />

                                        {/* Smart Close Button (Hidden when Editor is open) */}
                                        <BatchModalCloseButton onClose={onClose} />
                                    </BatchProvider>
                                ) : (
                                    /* SINGLE MODE - Uses extracted SchedulerForm */
                                    <div className="h-full flex flex-col">
                                        <div className="flex justify-between items-center mb-6">
                                            <h3 className="text-xl font-bold text-white">Editor de Mídia</h3>
                                            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                                                <X className="w-5 h-5" />
                                            </button>
                                        </div>
                                        <SchedulerForm
                                            onSubmit={async (data) => {
                                                if (onSingleSubmit) await onSingleSubmit(data);
                                                onSuccess(); // Optional: Trigger success callback
                                            }}
                                            onCancel={onClose}
                                            initialDate={initialDate}
                                            profiles={profiles}
                                            initialViralBoost={initialViralBoost}
                                            initialData={initialData}
                                            className="overflow-y-auto custom-scrollbar pr-2"
                                        />
                                    </div>
                                )}

                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
