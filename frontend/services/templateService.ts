import axios from 'axios';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace('localhost', '127.0.0.1');

export interface PromptTemplate {
    id: number;
    name: string;
    content: string;
    category: string;
    is_favorite: boolean;
    created_at: string;
}

export type TemplateCreate = Pick<PromptTemplate, 'name' | 'content' | 'category'>;
export type TemplateUpdate = Partial<Pick<PromptTemplate, 'name' | 'content' | 'category' | 'is_favorite'>>;

export const templateService = {
    list: async (): Promise<PromptTemplate[]> => {
        const res = await axios.get(`${API_URL}/api/v1/templates/list`);
        return res.data;
    },

    create: async (data: TemplateCreate): Promise<PromptTemplate> => {
        const res = await axios.post(`${API_URL}/api/v1/templates/create`, data);
        return res.data;
    },

    update: async (id: number, data: TemplateUpdate): Promise<PromptTemplate> => {
        const res = await axios.patch(`${API_URL}/api/v1/templates/${id}`, data);
        return res.data;
    },

    delete: async (id: number): Promise<void> => {
        await axios.delete(`${API_URL}/api/v1/templates/${id}`);
    }
};
