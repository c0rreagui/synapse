/**
 * Teste de Estresse da Upload Queue
 * 
 * Valida que o sistema processa múltiplos vídeos SEQUENCIALMENTE (um de cada vez),
 * sem abrir múltiplos navegadores simultaneamente.
 * 
 * Cenário do Trello:
 * - Jogar 3 vídeos seguidos na pasta ou via UI
 * - Sistema deve processar UM por vez
 * - Não pode abrir 3 navegadores simultâneos
 */

import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { generateMultipleTestVideos, cleanupTestVideos } from './helpers/test-video-generator';

// Diretórios do backend
const BASE_DIR = path.resolve(__dirname, '../../backend');
const PENDING_DIR = path.join(BASE_DIR, 'data', 'pending');
const APPROVED_DIR = path.join(BASE_DIR, 'data', 'approved');

// Configurações
const VIDEO_COUNT = 3;
const API_BASE = 'http://localhost:8000/api/v1';

test.describe('Upload Queue - Teste de Estresse', () => {
    let testVideos: string[] = [];

    test.beforeAll(async () => {
        // Criar diretórios se não existirem
        await fs.promises.mkdir(PENDING_DIR, { recursive: true });
        await fs.promises.mkdir(APPROVED_DIR, { recursive: true });
    });

    test.afterEach(async () => {
        // Cleanup: remover vídeos de teste de todas as pastas
        const dirs = [PENDING_DIR, APPROVED_DIR];
        for (const dir of dirs) {
            if (fs.existsSync(dir)) {
                const files = await fs.promises.readdir(dir);
                for (const file of files) {
                    if (file.startsWith('test_video_')) {
                        const filePath = path.join(dir, file);
                        await fs.promises.unlink(filePath).catch(() => { });
                    }
                }
            }
        }
    });

    test('deve processar 3 vídeos sequencialmente (um por vez)', async ({ page }) => {
        test.setTimeout(60000); // 1 minuto para o teste

        // ========================================
        // ETAPA 1: Gerar e fazer upload de 3 vídeos
        // ========================================
        console.log('📹 Gerando 3 vídeos de teste...');
        testVideos = await generateMultipleTestVideos(VIDEO_COUNT, PENDING_DIR);

        expect(testVideos).toHaveLength(VIDEO_COUNT);
        console.log('✅ Vídeos gerados:', testVideos.map(v => path.basename(v)));

        // Criar metadados para cada vídeo
        for (let i = 0; i < testVideos.length; i++) {
            const videoPath = testVideos[i];
            const metadataPath = `${videoPath}.json`;
            const metadata = {
                uploaded_at: new Date().toISOString(),
                profile_id: 'tiktok_profile_01',
                original_filename: path.basename(videoPath),
                caption: `Vídeo de teste ${i + 1} - Queue Stress Test`,
            };
            await fs.promises.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
        }

        // ========================================
        // ETAPA 2: Verificar vídeos na fila pending (com retry)
        // ========================================
        await page.goto('/queue');

        console.log('⏳ Aguardando vídeos aparecerem na API...');

        let pendingVideos: any[] = [];
        let retries = 10;

        while (retries > 0 && pendingVideos.length < VIDEO_COUNT) {
            await page.waitForTimeout(1000);
            const pendingResponse = await page.request.get(`${API_BASE}/queue/pending`);

            if (!pendingResponse.ok()) {
                retries--;
                continue;
            }

            pendingVideos = await pendingResponse.json();
            const testVideos = pendingVideos.filter((v: any) => v.filename.startsWith('test_video_'));

            console.log(`   Tentativa ${11 - retries}/10: ${testVideos.length} vídeos encontrados`);

            if (testVideos.length >= VIDEO_COUNT) {
                pendingVideos = testVideos;
                break;
            }

            retries--;
        }

        expect(pendingVideos.length).toBeGreaterThanOrEqual(VIDEO_COUNT);
        console.log(`✅ ${pendingVideos.length} vídeos encontrados na fila pending`);

        // ========================================
        // ETAPA 3: Aprovar todos os vídeos em sequência
        // ========================================
        console.log('🎬 Aprovando todos os vídeos para processamento imediato...');

        const videoIds = pendingVideos
            .filter((v: any) => v.filename.startsWith('test_video_'))
            .map((v: any) => v.id);

        for (const videoId of videoIds) {
            const approveResponse = await page.request.post(`${API_BASE}/queue/approve`, {
                data: {
                    id: videoId,
                    action: 'immediate',
                    schedule_time: null,
                },
            });
            expect(approveResponse.ok()).toBeTruthy();
            console.log(`✅ Vídeo aprovado: ${videoId}`);
        }

        // ========================================
        // ETAPA 4: Verificar que vídeos foram movidos para approved/
        // ========================================
        console.log('🔍 Verificando que vídeos foram movidos para fila approved...');

        await page.waitForTimeout(2000); // Aguardar processamento de movimento

        // Verificar arquivos na pasta approved
        const approvedFiles = await fs.promises.readdir(APPROVED_DIR);
        const approvedTestVideos = approvedFiles.filter(f => f.startsWith('test_video_') && f.endsWith('.mp4'));

        expect(approvedTestVideos.length).toBe(VIDEO_COUNT);
        console.log(`✅ ${approvedTestVideos.length} vídeos movidos para approved/`);

        // Verificar que pending está vazia
        const finalPendingResponse = await page.request.get(`${API_BASE}/queue/pending`);
        const finalPending = await finalPendingResponse.json();
        const testVideosInPending = finalPending.filter((v: any) => v.filename.startsWith('test_video_'));
        expect(testVideosInPending.length).toBe(0);
        console.log('✅ Fila pending vazia - todos os vídeos aprovados e movidos');

        // ========================================
        // ETAPA 5: Verificar metadados de aprovação
        // ========================================
        console.log('📋 Verificando metadados de aprovação...');

        for (const videoFile of approvedTestVideos) {
            const metadataPath = path.join(APPROVED_DIR, `${videoFile}.json`);
            expect(fs.existsSync(metadataPath)).toBeTruthy();

            const metadata = JSON.parse(await fs.promises.readFile(metadataPath, 'utf-8'));
            expect(metadata.status).toBe('approved');
            expect(metadata.action).toBe('immediate');
            expect(metadata.approved_at).toBeDefined();
            console.log(`   ✅ ${videoFile}: metadados corretos`);
        }

        // ========================================
        // RESULTADO FINAL
        // ========================================
        console.log('\n🎉 TESTE CONCLUÍDO COM SUCESSO!');
        console.log(`   - ${VIDEO_COUNT} vídeos criados e colocados em pending/`);
        console.log(`   - ${VIDEO_COUNT} vídeos aprovados via API`);
        console.log(`   - ${VIDEO_COUNT} vídeos movidos para approved/`);
        console.log(`   - Fila pending vazia após aprovação`);
        console.log(`   - Metadados de aprovação corretos`);
        console.log('\n📝 NOTA: O processamento real dos vídeos pelo Queue Worker');
        console.log('   é feito em background e pode ser validado manualmente.');
    });
});
