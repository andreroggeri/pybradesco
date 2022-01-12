import asyncio
from datetime import datetime
from typing import List

from playwright.async_api import Page, Browser, Playwright, async_playwright, ElementHandle, TimeoutError

from pybradesco.bradesco_transaction import BradescoTransaction


def parse_brl_to_float(value: str) -> float:
    return float(value.replace('.', '').replace(',', '.').replace(' ', ''))


class Bradesco:
    BASE_PATH = 'https://banco.bradesco/html/classic/index.shtm'
    page: Page
    browser: Browser
    playwright: Playwright

    def __init__(self, preview=False):
        self.preview = preview

    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=not self.preview)
        self.page = await self.browser.new_page()

    async def prepare(self, branch: str, account: str, verifying_digit: str, retry=False):
        await self.page.goto(self.BASE_PATH)
        # Agência
        await self.page.type('id=AGN', branch)

        # Conta Corrente
        await self.page.type('id=CTA', account)

        # Digito Verificador
        await self.page.type('id=DIGCTA', verifying_digit)

        # Botão Entrar
        await self.page.click('css=.btn-ok')

        # Modal que aparece no login
        try:
            await(await self.page.wait_for_selector('css=.mfp-close', timeout=3000)).click()
        except TimeoutError:
            print('Modal de login não apareceu')

        try:
            await self.page.wait_for_selector('css=.img-negado', timeout=5000)

            if retry:
                raise Exception('Erro ao abrir página de login')
            else:
                print('Acesso negado, tentando novamente')
                await self.prepare(branch, account, verifying_digit, True)
        except TimeoutError:
            pass

    async def _type_safe_keyboard(self, password: str):
        for char in password:
            await self.page.click(f'xpath=//a[.="{char}"]')

    async def _get_element_text(self, element: ElementHandle, selector: str):
        nested_element = await element.query_selector(selector)
        text = await nested_element.text_content()

        return text.strip()

    async def authenticate(self, web_password: str, token):
        # Token
        await self.page.type('id=Password1', token)

        # Avançar
        await self.page.click('id=loginbotoes:botaoAcessar')

        # Senha Web
        await self._type_safe_keyboard(web_password)

        # Entrar
        await self.page.click('id=loginbotoes:botaoAcessar')

    async def get_checking_account_statements(self) -> List[BradescoTransaction]:
        data = []

        # Acessa a tela de extrato nos últimos 90 dias
        await self.page.click('css=button[title="Saldos e Extratos"]')

        iframe_element = await self.page.query_selector('id=paginaCentral')
        iframe = await iframe_element.content_frame()

        await iframe.click('css=a[title="Conta-Corrente - Extrato (Últimos Lançamentos)"]')

        await iframe.click('id=fEx:viewFiltroBusca:_id102')

        # Faz o parse
        await asyncio.sleep(5)

        table = await iframe.wait_for_selector('css=table[id="fEx:dexs_0:vexd:dex"]')

        rows = await table.query_selector_all('css=tbody > tr')

        last_date = None

        for r in rows:
            current_date = await self._get_element_text(r, 'css=td:nth-of-type(1)')
            description = await self._get_element_text(r, 'css=td:nth-of-type(2)')
            credit = await self._get_element_text(r, 'css=td:nth-of-type(4)')
            debit = await self._get_element_text(r, 'css=td:nth-of-type(5)')

            amount = credit if credit != '' else debit
            if amount == '':
                continue
            else:
                amount = parse_brl_to_float(amount)

            if current_date != '':
                last_date = current_date

            data.append(BradescoTransaction(
                datetime.strptime(last_date, '%d/%m/%y'),
                description,
                amount,
            ))

        return data

    async def get_credit_card_statements(self) -> List[BradescoTransaction]:
        data = []
        await self.page.click('css=button[title="Cartões"]')

        iframe = await(await self.page.query_selector('id=paginaCentral')).content_frame()

        await iframe.click('css=.colMenu a[title="Extratos"]')

        await iframe.wait_for_selector('css=#divContainerLancamentos .lnk-expansor')

        expand_buttons = await iframe.query_selector_all('css=#divContainerLancamentos .lnk-expansor')

        for idx, button in enumerate(expand_buttons):
            await button.click()
            await asyncio.sleep(0.5)
            table = (await iframe.query_selector_all('css=.tabGenerica.vAm.topb'))[idx]
            rows = await table.query_selector_all('tbody > tr')

            for row in rows:
                current_date = await self._get_element_text(row, 'css=td:nth-of-type(1)')
                description = await self._get_element_text(row, 'css=td:nth-of-type(2)')
                amount = await self._get_element_text(row, 'css=td:nth-of-type(6)')
                amount = parse_brl_to_float(amount)

                parsed_date = datetime.strptime(current_date, '%d/%m').replace(year=datetime.now().year)
                data.append(BradescoTransaction(
                    parsed_date,
                    description,
                    amount
                ))

        await iframe.click('css=a[title="Extrato Fechado Pressione Enter para selecionar."]')

        await iframe.click('css=#divDadosExtrato .lnk-expansor')

        table = await iframe.wait_for_selector('css=.tabGenerica.vAm.topb')

        rows = await table.query_selector_all('tbody > tr')

        for row in rows:
            current_date = await self._get_element_text(row, 'css=td:nth-of-type(1)')
            description = await self._get_element_text(row, 'css=td:nth-of-type(2)')
            amount = await self._get_element_text(row, 'css=td:nth-of-type(6)')
            amount = parse_brl_to_float(amount)

            parsed_date = datetime.strptime(current_date, '%d/%m').replace(year=datetime.now().year)
            data.append(BradescoTransaction(
                parsed_date,
                description,
                amount * -1
            ))

        return data
