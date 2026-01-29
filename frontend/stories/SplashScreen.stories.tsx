import type { Meta, StoryObj } from '@storybook/nextjs';
import SplashScreen from '../app/components/SplashScreen';
import { useRouter } from 'next/navigation';

// Mock Next.js Router
const mockRouter = {
    push: () => { },
    replace: () => { },
    prefetch: () => { },
    back: () => { },
    forward: () => { },
    refresh: () => { },
};

// Mock Fetch Global
const mockFetch = (url: string): Promise<any> => {
    return new Promise((resolve) => {
        // Simulate health checks
        if (url.includes('/health') || url.includes('/profiles') || url.includes('/oracle/status')) {
            setTimeout(() => {
                resolve({ ok: true });
            }, 500);
            return;
        }
        resolve({ ok: false });
    });
};

const meta: Meta<typeof SplashScreen> = {
    title: 'App/Pages/SplashScreen',
    component: SplashScreen,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
        docs: {
            description: {
                component: 'The **SplashScreen** handles the initial boot sequence of the application. It verifies API health, prefetches routes, and establishes a "neural connection" before revealing the main interface. It includes a comprehensive error state if the backend is unreachable.'
            }
        }
    },
    decorators: [
        (Story) => {
            // Clear session storage to force Splash Screen animation every time
            if (typeof window !== 'undefined') {
                sessionStorage.removeItem('synapse_initialized');
            }

            // @ts-ignore
            global.fetch = mockFetch;
            return (
                <div className="h-screen w-full relative bg-[#050505]">
                    <Story />
                </div>
            )
        }
    ]
};

export default meta;
type Story = StoryObj<typeof SplashScreen>;

const AppContentPlaceholder = () => (
    <div className="h-full w-full bg-[#0a0a0f] text-white flex flex-col items-center justify-center p-8 animate-in fade-in duration-500">
        <div className="p-6 rounded-xl bg-white/5 border border-white/10 text-center max-w-md">
            <div className="text-4xl mb-4">🏠</div>
            <h2 className="text-xl font-bold text-gray-200 mb-2">Application Content</h2>
            <p className="text-sm text-gray-500">
                This screen appears after the Splash Screen animation completes.
            </p>
        </div>
    </div>
);

export const Integration_Flow: Story = {
    args: {
        children: <AppContentPlaceholder />
    },
    parameters: {
        docs: {
            description: {
                story: 'Demonstrates the full flow: Animation -> Completion -> App Content. Clears session storage to force replay.'
            }
        }
    }
};

export const Visual_Animation_Loop: Story = {
    decorators: [
        (Story) => {
            // Never resolve fetch to keep it loading forever
            // @ts-ignore
            global.fetch = () => new Promise(() => { });
            return <Story />
        }
    ],
    args: {
        children: <AppContentPlaceholder />
    },
    parameters: {
        docs: {
            description: {
                story: 'Stays in the "Loading" phase indefinitely. **Use this to inspect the Splash Screen design, animations, and typography.**'
            }
        }
    }
};



export const Backend_Offline: Story = {
    decorators: [
        (Story) => {
            // Force error on health check
            // @ts-ignore
            global.fetch = () => Promise.reject("Network Error");
            return <Story />
        }
    ],
    args: {
        children: <AppContentPlaceholder />
    },
    parameters: {
        docs: {
            description: {
                story: 'Triggered when the initial `/health` check fails (Backend down). Shows "SYSTEM OFFLINE" alert.'
            }
        }
    }
};
