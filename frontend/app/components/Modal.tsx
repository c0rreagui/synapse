import { Fragment, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';

const SIZE_CLASSES: Record<ModalSize, string> = {
    'sm':  'sm:max-w-sm',
    'md':  'sm:max-w-lg',
    'lg':  'sm:max-w-xl',
    'xl':  'sm:max-w-2xl',
    '2xl': 'sm:max-w-3xl',
    '3xl': 'sm:max-w-4xl',
    '4xl': 'sm:max-w-5xl',
    '5xl': 'sm:max-w-6xl',
    '6xl': 'sm:max-w-7xl',
};

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    className?: string;
    contentClassName?: string;
    size?: ModalSize;
}

export default function Modal({ isOpen, onClose, title, children, className, contentClassName, size = 'md' }: ModalProps) {
    const cancelButtonRef = useRef(null);

    return (
        <Transition.Root show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-[100]" initialFocus={cancelButtonRef} onClose={onClose}>
                {/* Backdrop */}
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-200"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-150"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" />
                </Transition.Child>

                <div className="fixed inset-0 z-10 overflow-y-auto">
                    <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-[cubic-bezier(0.34,1.56,0.64,1)] duration-300"
                            enterFrom="opacity-0 scale-[0.92]"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-150"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-[0.95]"
                        >
                            <Dialog.Panel className={clsx(
                                "relative transform text-left transition-all sm:my-8 sm:w-full",
                                SIZE_CLASSES[size],
                                "rounded-[20px] overflow-hidden",
                                "bg-gradient-to-b from-[rgba(22,15,35,0.92)] to-[rgba(11,8,18,0.97)]",
                                "backdrop-blur-[40px] saturate-[180%]",
                                "border border-white/[0.08]",
                                "shadow-[0_32px_64px_-12px_rgba(0,0,0,0.85),0_0_80px_rgba(139,92,246,0.05),inset_0_1px_0_rgba(255,255,255,0.07)]",
                                className
                            )}>
                                {/* Borda prismática — efeito Apple top edge */}
                                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent pointer-events-none z-10" />

                                {/* Header */}
                                <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.05]">
                                    {title && (
                                        <Dialog.Title as="h3" className="text-sm font-semibold text-white/90 tracking-wide">
                                            {title}
                                        </Dialog.Title>
                                    )}
                                    <button
                                        type="button"
                                        className={clsx(
                                            "w-8 h-8 rounded-xl flex items-center justify-center",
                                            "bg-white/[0.04] hover:bg-white/[0.10]",
                                            "border border-white/[0.06]",
                                            "text-gray-400 hover:text-white",
                                            "transition-all duration-200 focus:outline-none",
                                            !title && "ml-auto"
                                        )}
                                        onClick={onClose}
                                        ref={cancelButtonRef}
                                    >
                                        <span className="sr-only">Fechar</span>
                                        <XMarkIcon className="h-4 w-4" aria-hidden="true" />
                                    </button>
                                </div>

                                {/* Content */}
                                <div className={clsx("p-6", contentClassName)}>
                                    {children}
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition.Root>
    );
}
