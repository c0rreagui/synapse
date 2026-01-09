import { test, expect } from '@playwright/test';

test.describe('Command Center', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('página carrega com título correto', async ({ page }) => {
        await expect(page).toHaveTitle(/Synapse/i);
    });

    test('Pipeline Status cards existem', async ({ page }) => {
        // Verificar os 4 cards de status
        await expect(page.getByText('NA FILA')).toBeVisible();
        await expect(page.getByText('PROCESSANDO')).toBeVisible();
        await expect(page.getByText('CONCLUÍDOS')).toBeVisible();
        await expect(page.getByText('FALHAS')).toBeVisible();
    });

    test('upload zone está presente', async ({ page }) => {
        await expect(page.getByText(/Solte seu vídeo aqui/i)).toBeVisible();
    });

    test('seção de Aprovação Manual existe', async ({ page }) => {
        await expect(page.getByText('Aprovação Manual')).toBeVisible();
    });

    test('seção de Perfis Ativos existe', async ({ page }) => {
        await expect(page.getByText('Perfis Ativos')).toBeVisible();
    });
});
