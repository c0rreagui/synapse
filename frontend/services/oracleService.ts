import axios from 'axios';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1');

export interface OracleAnalysis {
    profile: string;
    analysis: {
        profile_type?: string;
        voice_authenticity?: string;
        summary: string;
        virality_score: number;
        engagement_quality: string;
        audience_persona: {
            demographics: string;
            psychographics: string;
            pain_points: string[];
        };
        viral_hooks: Array<{
            type: string;
            description: string;
        }>;
        content_pillars: string[];
        content_gaps: string[];
        performance_metrics: {
            avg_views_estimate: string;
            engagement_rate_analysis: string;
            verified_video_count: number;
            comments_analyzed_count: number;
        };
        suggested_next_video: {
            title: string;
            concept: string;
            hook_script: string;
            reasoning: string;
        };
        sentiment_pulse?: {
            score: number;
            dominant_emotion: string;
            top_questions: string[];
            lovers: string[];
            haters: string[];
            debate_topic?: string;
        };
        best_times?: Array<{
            day: string;
            hour: number;
            reason: string;
        }>;
    };
    raw_model: string;
}

export const analyzeProfile = async (username: string): Promise<OracleAnalysis> => {
    const cleanUser = username.replace('@', '').trim();
    // Adding timestamp to prevent caching
    const response = await axios.post(`${API_URL}/api/v1/oracle/analyze?username=${cleanUser}&t=${Date.now()}`);
    return response.data;
};
