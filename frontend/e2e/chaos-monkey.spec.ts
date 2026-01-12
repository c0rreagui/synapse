import { test } from '@playwright/test';

test('Chaos Monkey: Cliques Aleatórios', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Seleciona todos os botões visíveis
    const buttons = await page.$$('button');
    console.log(`🐵 Chaos Monkey encontrou ${buttons.length} botões!`);

    for (let i = 0; i < 20; i++) {
        const randomIdx = Math.floor(Math.random() * buttons.length);
        try {
            if (buttons[randomIdx]) {
                console.log(`🐵 Clicando no botão #${randomIdx}...`);
                await buttons[randomIdx].click({ timeout: 500 });
                await page.waitForTimeout(200); // Pequeno delay
            }
        } catch (e) {
            console.log('💥 Botão explodiu ou sumiu. Monkey continua.');
        }
    }
});
