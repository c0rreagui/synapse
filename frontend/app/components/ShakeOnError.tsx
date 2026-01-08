'use client';

import { ReactNode } from 'react';

interface ShakeOnErrorProps {
    children: ReactNode;
    shake: boolean;
    onAnimationEnd?: () => void;
}

export default function ShakeOnError({ children, shake, onAnimationEnd }: ShakeOnErrorProps) {
    return (
        <div
            style={{
                animation: shake ? 'shake 0.5s ease' : 'none',
            }}
            onAnimationEnd={onAnimationEnd}
        >
            {children}

            <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
          20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
      `}</style>
        </div>
    );
}
