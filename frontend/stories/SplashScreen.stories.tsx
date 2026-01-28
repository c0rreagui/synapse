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

const MockDashboard = () => (
    <div className="h-full w-full flex items-center justify-center p-10 animate-in fade-in duration-1000">
        <div className="text-center space-y-4">
            <div className="text-6xl mb-4">✨</div>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
                System Initialized
            </h1>
            <p className="text-gray-400">Welcome to Synapse Command Center</p>
            <div className="grid grid-cols-3 gap-4 mt-8 max-w-2xl mx-auto">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-32 bg-white/5 rounded-xl border border-white/10" />
                ))}
            </div>
        </div>
    </div>
);

export const Default: Story = {
    args: {
        children: <MockDashboard />
    },
    parameters: {
        docs: {
            description: {
                story: 'Simulates a successful boot sequence. After the progress bar completes (approx 2s in mock), the "Mock Dashboard" is revealed.'
            }
        }
    }
};

export const LoadingIndefinitely: Story = {
    decorators: [
        (Story) => {
            // Never resolve fetch to keep it loading
            // @ts-ignore
            global.fetch = () => new Promise(() => { });
            return <Story />
        }
    ],
    args: {
        children: <MockDashboard />
    },
    parameters: {
        docs: {
            description: {
                story: 'Simulates a scenario where backend or network is slow/hanging. Useful for inspecting the loading animations and "floating orbs" effects.'
            }
        }
    }
};

export const ErrorState: Story = {
    decorators: [
        (Story) => {
            // Force error on health check
            // @ts-ignore
            global.fetch = () => Promise.reject("Network Error");
            return <Story />
        }
    ],
    args: {
        children: <MockDashboard />
    },
    parameters: {
        docs: {
            description: {
                story: 'Triggered when the initial `/health` check fails. Shows a "System Offline" red alert state with a retry button.'
            }
        }
    }
};
