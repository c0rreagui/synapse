import { test, expect } from '@playwright/test';

test('Cenário: Comparação Visual do Dashboard', async ({ page }) => {
    // 1. Acessa Dashboard
    await page.goto('/');

    // 2. Aguarda carregamento
    // Seleciona um elemento chave do dashboard para garantir que carregou
    await page.waitForSelector('main', { state: 'visible' });

    // 3. Snapshot da Página Inteira
    // Nota: Isso falhará na primeira vez sem snapshot base
    await expect(page).toHaveScreenshot('dashboard-baseline.png', {
        maxDiffPixels: 100, // Tolera pequenas diferenças de renderização
        fullPage: true
    });
});
