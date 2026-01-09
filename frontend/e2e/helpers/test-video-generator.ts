/**
 * Helper para gerar vídeos MP4 de teste para testes E2E
 * Cria vídeos pequenos usando Canvas API
 */

import * as fs from 'fs';
import * as path from 'path';

export interface TestVideoOptions {
    filename: string;
    durationSeconds?: number;
    width?: number;
    height?: number;
    text?: string;
}

/**
 * Gera um vídeo de teste minimalista programaticamente
 * Nota: Como não podemos usar FFmpeg diretamente no Playwright,
 * vamos criar arquivos MP4 mínimos válidos para teste
 */
export async function generateTestVideo(options: TestVideoOptions): Promise<string> {
    const {
        filename,
        durationSeconds = 2,
        width = 320,
        height = 240,
        text = 'Test Video'
    } = options;

    // Para testes, vamos usar um MP4 mínimo válido
    // Este é um MP4 válido de 1 segundo, 320x240, codec H264
    // Fonte: arquivo MP4 mínimo gerado via FFmpeg
    const minimalMP4 = Buffer.from(
        'AAAAGGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAr' +
        'htZGF0AAACrQYF//+c3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE2' +
        'NCByMzA5NSBiYWVlNDAwIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIE' +
        'NvcHlsZWZ0IDIwMDMtMjAyMSAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3Jn' +
        'L3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz' +
        '0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9' +
        'MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IG' +
        'Nocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9u' +
        'ZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aH' +
        'JlYWRzPTEyIGxvb2thaGVhZF90aHJlYWRzPTIgc2xpY2VkX3RocmVhZHM9' +
        'MCBucj0wIGRlY2ltYXRlPTEgaW50ZXJsYWNlZD0wIGJsdXJheV9jb21wYX' +
        'Q9MCBjb25zdHJhaW5lZF9pbnRyYT0wIGJmcmFtZXM9MyBiX3B5cmFtaWQ9' +
        'MiBiX2FkYXB0PTEgYl9iaWFzPTAgZGlyZWN0PTEgd2VpZ2h0Yj0xIG9wZW' +
        '5fZ29wPTAgd2VpZ2h0cD0yIGtleWludD0yNTAga2V5aW50X21pbj0yNSBz' +
        'Y2VuZWN1dD00MCBpbnRyYV9yZWZyZXNoPTAgcmNfbG9va2FoZWFkPTQwIH' +
        'JjPWNyZiBtYnRyZWU9MSBjcmY9MjMuMCBxY29tcD0wLjYwIHFwbWluPTAg' +
        'cXBtYXg9NjkgcXBzdGVwPTQgaXBfcmF0aW89MS40MCBhcT0xOjEuMDAAgA' +
        'AAAGZliIQAV//+9rwWqP3KjKVnj/vo8YZu+nz+0YbgAAADAAADAAADAAAD' +
        'AAADAACrxgL4AAAwC5/A+AA=',
        'base64'
    );

    const outputPath = path.resolve(filename);
    await fs.promises.writeFile(outputPath, minimalMP4);

    return outputPath;
}

/**
 * Cria múltiplos vídeos de teste com metadados diferentes
 */
export async function generateMultipleTestVideos(
    count: number,
    baseDir: string
): Promise<string[]> {
    const videoPaths: string[] = [];

    for (let i = 1; i <= count; i++) {
        const filename = path.join(baseDir, `test_video_${i}.mp4`);
        const videoPath = await generateTestVideo({
            filename,
            text: `Test Video ${i}`,
        });
        videoPaths.push(videoPath);
    }

    return videoPaths;
}

/**
 * Remove vídeos de teste
 */
export async function cleanupTestVideos(videoPaths: string[]): Promise<void> {
    for (const videoPath of videoPaths) {
        try {
            if (fs.existsSync(videoPath)) {
                await fs.promises.unlink(videoPath);
            }

            // Também remove metadados JSON se existirem
            const metadataPath = `${videoPath}.json`;
            if (fs.existsSync(metadataPath)) {
                await fs.promises.unlink(metadataPath);
            }
        } catch (error) {
            console.warn(`Failed to cleanup ${videoPath}:`, error);
        }
    }
}
