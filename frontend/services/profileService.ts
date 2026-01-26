import axios from 'axios';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1');

export interface SavedProfile {
    id: string;
    label: string;
    username?: string;
    avatar_url?: string;
    icon?: string;
    status?: string;
    // For backward compat, alias
    filename: string;
}

export const getSavedProfiles = async (): Promise<SavedProfile[]> => {
    try {
        const response = await axios.get(`${API_URL}/api/v1/profiles/list`);
        // Backend returns: { id, label, username, avatar_url, icon, status }
        return response.data.map((item: { id: string; label?: string; username?: string; avatar_url?: string; icon?: string }) => ({
            ...item,
            filename: item.id, // Alias for UI compat
            label: item.label || item.id.replace('tiktok_profile_', '').replace('_', ' ')
        }));
    } catch (error) {
        console.error("Failed to fetch profiles:", error);
        return [];
    }
};

