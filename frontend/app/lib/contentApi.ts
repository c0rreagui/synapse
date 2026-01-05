import { ContentItem } from "../types";
import { apiClient, retryWithBackoff, logger } from "./api";

// Content API
export const contentApi = {
    async getReadyContent(): Promise<ContentItem[]> {
        try {
            const data = await retryWithBackoff(() =>
                apiClient.get<ContentItem[]>("/api/v1/content/ready")
            );
            logger.info("Successfully fetched ready content", { count: data.length });
            return data;
        } catch (error) {
            logger.error("Failed to fetch ready content", error);
            // Return empty array as fallback for non-critical data
            return [];
        }
    },

    async triggerScan(): Promise<{ success: boolean; message: string }> {
        try {
            const response = await apiClient.post<{ success: boolean; message: string }>(
                "/api/v1/content/scan"
            );
            logger.info("Successfully triggered content scan");
            return response;
        } catch (error) {
            logger.error("Failed to trigger content scan", error);
            throw error;
        }
    },
};
