"""
Selector Validator - Valida e testa seletores antes de usar em produção
"""
import logging
from typing import List, Dict, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class SelectorValidator:
    """Valida e testa seletores para garantir robustez"""
    
    @staticmethod
    async def test_selector(
        page: Page, 
        selector: str, 
        timeout: int = 5000,
        check_visibility: bool = True
    ) -> Dict:
        """
        Testa se um seletor existe e opcionalmente se está visível
        
        Returns:
            dict: {"exists": bool, "visible": bool, "selector": str, "count": int}
        """
        try:
            count = await page.locator(selector).count()
            
            if count == 0:
                return {
                    "exists": False,
                    "visible": False,
                    "selector": selector,
                    "count": 0
                }
            
            is_visible = False
            if check_visibility and count > 0:
                try:
                    first_element = page.locator(selector).first
                    is_visible = await first_element.is_visible(timeout=timeout)
                except:
                    is_visible = False
            
            return {
                "exists": True,
                "visible": is_visible if check_visibility else None,
                "selector": selector,
                "count": count
            }
            
        except Exception as e:
            logger.error(f"Error testing selector '{selector}': {e}")
            return {
                "exists": False,
                "visible": False,
                "selector": selector,
                "count": 0,
                "error": str(e)
            }
    
    @staticmethod
    async def find_best_selector(
        page: Page,
        selectors_list: List[str],
        prefer_visible: bool = True,
        timeout: int = 5000
    ) -> Optional[str]:
        """
        Encontra o melhor seletor de uma lista
        
        Args:
            page: Playwright Page object
            selectors_list: Lista de seletores para testar
            prefer_visible: Se True, prefere seletores visíveis
            timeout: Timeout para cada teste
            
        Returns:
            str: Melhor seletor encontrado, ou None
        """
        results = []
        
        for selector in selectors_list:
            result = await SelectorValidator.test_selector(
                page, selector, timeout, check_visibility=prefer_visible
            )
            results.append(result)
            
            # Se encontrou um que existe E é visível, retorna imediatamente
            if result["exists"]:
                if not prefer_visible or result["visible"]:
                    logger.info(f"✅ Melhor seletor encontrado: '{selector}' (visível={result['visible']}, count={result['count']})")
                    return selector
        
        # Se não encontrou nenhum visível mas prefer_visible=True, 
        # tenta retornar qualquer um que exista
        if prefer_visible:
            for result in results:
                if result["exists"]:
                    logger.warning(f"⚠️ Seletor encontrado mas não visível: '{result['selector']}'")
                    return result["selector"]
        
        logger.error("❌ Nenhum seletor encontrado na lista")
        return None
    
    @staticmethod
    async def diagnose_page(page: Page, selectors_dict: Dict[str, List[str]]) -> Dict:
        """
        Diagnostica múltiplos grupos de seletores em uma página
        
        Args:
            page: Playwright Page object
            selectors_dict: {"elemento_nome": ["selector1", "selector2"]}
            
        Returns:
            dict: Relatório completo de diagnóstico
        """
        report = {
            "url": page.url,
            "title": await page.title(),
            "elements": {}
        }
        
        for element_name, selectors in selectors_dict.items():
            logger.info(f"🔍 Diagnosticando: {element_name}")
            best = await SelectorValidator.find_best_selector(page, selectors)
            
            report["elements"][element_name] = {
                "best_selector": best,
                "all_selectors_tested": selectors,
                "found": best is not None
            }
        
        return report


# Dicionário de seletores conhecidos para TikTok Studio
TIKTOK_STUDIO_SELECTORS = {
    "upload_input": [
        'input[type="file"]',
        'input[accept*="video"]',
        'input[accept*="mp4"]',
        '[data-e2e="upload-input"]',
        '.upload-input'
    ],
    "upload_button": [
        'button:has-text("Selecionar vídeo")',
        'button:has-text("Select video")',
        'button:has-text("Selecionar")',
        'button:has-text("Upload")'
    ],
    "caption_input": [
        '.public-DraftEditor-content',
        '[contenteditable="true"]',
        '.DraftEditor-root',
        'textarea[placeholder*="caption"]'
    ],
    "post_button": [
        'button:has-text("Publicar")',
        'button:has-text("Post")',
        'button:has-text("Postar")',
        '[data-e2e="post-button"]'
    ],
    "schedule_toggle": [
        'input[value="schedule"]',
        'input[type="radio"][value="schedule"]',
        'button:has-text("Agendar")',
        'button:has-text("Schedule")'
    ]
}
