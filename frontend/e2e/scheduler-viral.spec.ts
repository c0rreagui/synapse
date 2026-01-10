import { test, expect } from '@playwright/test';

test.describe('Scheduler Viral Boost Feature', () => {

    test('should render Viral Audio Boost toggle and send correct payload', async ({ page }) => {
        // 1. Navigate to Scheduler Page
        await page.goto('http://localhost:3000/scheduler');

        // 2. Verify Toggle Visibility
        const toggleLabel = page.locator('text=Viral Audio Boost');
        await expect(toggleLabel).toBeVisible();

        const toggleInput = page.locator('input[type="checkbox"]');
        // Ensure it's unchecked by default (or check current state)
        // Based on code: const [viralBoost, setViralBoost] = useState(false);
        expect(await toggleInput.isChecked()).toBeFalsy();

        // 3. User Interaction: Activate Toggle
        await page.locator('label.cursor-pointer').click();
        expect(await toggleInput.isChecked()).toBeTruthy();

        // 4. Intercept API Call to verify Payload
        // We expect a POST to /api/v1/scheduler/create
        const requestPromise = page.waitForRequest(request =>
            request.url().includes('/api/v1/scheduler/create') &&
            request.method() === 'POST'
        );

        // 5. Trigger Quick Add (The mocked Plus icon button)
        // The button has title="Quick Add Current Date" or we use the specific class/icon
        const addButton = page.locator('button[title="Quick Add Current Date"]').first();
        // Ensure button is visible (it has opacity-0 group-hover:opacity-100 logic, so we might need to force click or hover)
        await addButton.click({ force: true });

        // 6. Verify Request Data
        const request = await requestPromise;
        const postData = request.postDataJSON();

        console.log('Intercepted Payload:', postData);

        expect(postData).toMatchObject({
            viral_music_enabled: true
        });

        // 7. Verify UI Feedback (Alert is used in code, Playwright handles dialogs automatically by dismissing, 
        // but we can listen to it if we want to confirm success message)
        // However, since we intercepted the request, the most critical part (Payload) is verified.
    });

});
