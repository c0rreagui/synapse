export const getApiUrl = () => {
    // Check if we are in the browser (client-side)
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;

        // If running on localhost, bypass the Next.js proxy if it's flaky
        // and connect directly to the FastAPI backend (usually port 8000)
        // unless NEXT_PUBLIC_API_URL is explicitly set to something else.
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Prioritize environmental variable if it's a full URL
            const envUrl = process.env.NEXT_PUBLIC_API_URL;
            if (envUrl && envUrl.startsWith('http')) {
                return envUrl;
            }
            // Fallback to direct backend port for local dev excellence
            return 'http://localhost:8000';
        }
    }

    // Default to strict env var or relative path for production (proxy)
    return process.env.NEXT_PUBLIC_API_URL || '';
};

export const safeFetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const urlStr = input.toString();
    const finalUrl = urlStr.startsWith('http') || urlStr.startsWith('/')
        ? urlStr
        : `${getApiUrl()}${urlStr.startsWith('/') ? '' : '/'}${urlStr}`;

    // If original URL was relative, prepend base
    let target = input;
    if (typeof input === 'string' && !input.startsWith('http')) {
        target = `${getApiUrl()}${input}`;
    }

    try {
        const res = await fetch(target, init);
        return res;
    } catch (error) {
        console.error(`Fetch error for ${target}:`, error);
        throw error;
    }
};
