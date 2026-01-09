import { test, expect } from '@playwright/test';

test.describe('Navegação da Plataforma', () => {
    test('sidebar aparece em todas as páginas', async ({ page }) => {
        const paginas = ['/', '/profiles', '/factory', '/metrics', '/logs', '/settings'];

        for (const rota of paginas) {
            await page.goto(rota);

            // Sidebar deve estar visível
            const sidebar = page.locator('aside');
            await expect(sidebar).toBeVisible();

            // Logo SYNAPSE deve estar presente
            await expect(page.getByText('SYNAPSE')).toBeVisible();
        }
    });

    test('navegar entre todas as páginas via sidebar', async ({ page }) => {
        await page.goto('/');

        // Command Center
        await expect(page.getByText('Dashboard')).toBeVisible();

        // Ir para Perfis TikTok
        await page.getByRole('link', { name: /Perfis TikTok/i }).click();
        await expect(page).toHaveURL('/profiles');

        // Ir para Factory Watcher
        await page.getByRole('link', { name: /Factory Watcher/i }).click();
        await expect(page).toHaveURL('/factory');

        // Ir para Métricas
        await page.getByRole('link', { name: /Métricas/i }).click();
        await expect(page).toHaveURL('/metrics');

        // Ir para Logs
        await page.getByRole('link', { name: /Logs/i }).click();
        await expect(page).toHaveURL('/logs');

        // Ir para Configurações
        await page.getByRole('link', { name: /Configurações/i }).click();
        await expect(page).toHaveURL('/settings');

        // Voltar para Command Center
        await page.getByRole('link', { name: /Command Center/i }).click();
        await expect(page).toHaveURL('/');
    });
});
