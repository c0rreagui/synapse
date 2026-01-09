import { test, expect } from '@playwright/test';

test.describe('Synapse Full User Flow', () => {
    test('should allow a user to select a profile and upload a video', async ({ page }) => {
        // 1. Acesso Inicial
        await page.goto('/');
        await expect(page).toHaveTitle(/Synapse/);

        // 2. Garantir que a dashboard carregou (verifica se o header "Dashboard" está visível)
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 });

        // 3. Seleção de Perfil
        // O seletor usa a tag <select> próxima ao título "Central de Ingestão"
        const profileSelect = page.locator('select').first();
        await expect(profileSelect).toBeVisible();

        // Tenta selecionar o segundo perfil se houver, senão mantém o primeiro
        const options = await profileSelect.locator('option').count();
        if (options > 1) {
            await profileSelect.selectOption({ index: 1 });
        }

        // 4. Upload de Arquivo
        // Vamos injetar um arquivo no input oculto
        await page.locator('input[type="file"]').setInputFiles({
            name: 'test-video.mp4',
            mimeType: 'video/mp4',
            buffer: Buffer.from('mock video content')
        });

        // 5. Validação
        // Espera pelo Toast de sucesso OU feedback visual
        // O texto do toast é "Enviando test-video.mp4..." seguido de "sucesso"
        // Usamos .first() para evitar erro de ambiguidade se houver múltiplos elementos com texto similar
        await expect(page.getByText(/enviando/i).first()).toBeVisible();
        await expect(page.getByText(/sucesso/i).first()).toBeVisible({ timeout: 10000 });
    });
});
