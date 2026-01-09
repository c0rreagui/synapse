import { test, expect } from '@playwright/test';

test.describe('Página de Configurações', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/settings');
    });

    test('título Configuration Hub visível', async ({ page }) => {
        await expect(page.getByText('Configuration Hub')).toBeVisible();
    });

    test('seção de Integrações existe', async ({ page }) => {
        await expect(page.getByText('Integrações')).toBeVisible();

        // Verificar integrações
        await expect(page.getByText('YouTube Shorts')).toBeVisible();
        await expect(page.getByText('LinkedIn')).toBeVisible();
        await expect(page.getByText('TikTok')).toBeVisible();
    });

    test('seção de Automation Logic existe', async ({ page }) => {
        await expect(page.getByText('Automation Logic')).toBeVisible();
        await expect(page.getByText('NEW RULE')).toBeVisible();
    });

    test('seção de Dark Profiles existe', async ({ page }) => {
        await expect(page.getByText('Dark Profiles')).toBeVisible();
        await expect(page.getByText('Add Neural Profile')).toBeVisible();
    });

    test('toggle de integração funciona', async ({ page }) => {
        // Clicar no toggle do YouTube
        const youtubeToggle = page.getByRole('button', { name: /Toggle YouTube/i });
        await youtubeToggle.click();

        // Aguardar um momento para a mudança de estado
        await page.waitForTimeout(500);
    });
});
