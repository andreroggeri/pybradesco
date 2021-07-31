from datetime import datetime
from time import sleep
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError

from pybradesco.bradesco_transaction import BradescoTransaction


def parse_brl_to_float(value: str) -> float:
    return float(value.replace('.', '').replace(',', '.').replace(' ', ''))


class Bradesco:
    BASE_PATH = 'https://banco.bradesco/html/classic/index.shtm'

    def __init__(self, preview=False):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=not preview)
        self.page = self.browser.new_page()

    def prepare(self, branch: str, account: str, verifying_digit: str, retry=False):
        self.page.goto(self.BASE_PATH)
        # Agência
        self.page.type('id=AGN', branch)

        # Conta Corrente
        self.page.type('id=CTA', account)

        # Digito Verificador
        self.page.type('id=DIGCTA', verifying_digit)

        # Botão Entrar
        self.page.click('css=.btn-ok')

        # Modal que aparece no login
        try:
            self.page.wait_for_selector('css=.mfp-close', timeout=3000).click()
        except TimeoutError:
            print('Modal de login não apareceu')

        try:
            self.page.wait_for_selector('css=.img-negado', timeout=5000)

            if retry:
                raise Exception('Erro ao abrir página de login')
            else:
                print('Acesso negado, tentando novamente')
                self.prepare(branch, account, verifying_digit, True)
        except TimeoutError:
            pass

    def _type_safe_keyboard(self, password: str):
        for char in password:
            self.page.click(f'xpath=//a[.="{char}"]')

    def authenticate(self, web_password: str, token):
        # Token
        self.page.type('id=Password1', token)

        # Avançar
        self.page.click('id=loginbotoes:botaoAcessar')

        # Senha Web
        self._type_safe_keyboard(web_password)

        # Entrar
        self.page.click('id=loginbotoes:botaoAcessar')

    def get_checking_account_statements(self) -> List[BradescoTransaction]:
        data = []

        # Acessa a tela de extrato nos últimos 90 dias
        self.page.click('css=button[title="Saldos e Extratos"]')

        iframe = self.page.query_selector('id=paginaCentral').content_frame()

        iframe.click('css=a[title="Conta-Corrente - Extrato (Últimos Lançamentos)"]')

        iframe.click('id=fEx:viewFiltroBusca:_id102')

        # Faz o parse
        sleep(5)

        table = iframe.wait_for_selector('css=table[id="fEx:dexs_0:vexd:dex"]')

        rows = table.query_selector_all('css=tbody > tr')

        last_date = None

        for r in rows:
            current_date = r.query_selector('css=td:nth-of-type(1)').text_content().strip()
            description = r.query_selector('css=td:nth-of-type(2)').text_content().strip()
            credit = r.query_selector('css=td:nth-of-type(4)').text_content().strip()
            debit = r.query_selector('css=td:nth-of-type(5)').text_content().strip()

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

    def get_credit_card_statements(self) -> List[BradescoTransaction]:
        data = []
        self.page.click('css=button[title="Cartões"]')

        iframe = self.page.query_selector('id=paginaCentral').content_frame()

        iframe.click('css=.colMenu a[title="Extratos"]')

        iframe.wait_for_selector('css=#divContainerLancamentos .lnk-expansor')

        expand_buttons = iframe.query_selector_all('css=#divContainerLancamentos .lnk-expansor')

        for idx, button in enumerate(expand_buttons):
            button.click()
            sleep(0.5)
            table = iframe.query_selector_all('css=.tabGenerica.vAm.topb')[idx]
            rows = table.query_selector_all('tbody > tr')

            for row in rows:
                current_date = row.query_selector('css=td:nth-of-type(1)').text_content().strip()
                description = row.query_selector('css=td:nth-of-type(2)').text_content().strip()
                amount = row.query_selector('css=td:nth-of-type(6)').text_content().strip()
                amount = parse_brl_to_float(amount)

                parsed_date = datetime.strptime(current_date, '%d/%m').replace(year=datetime.now().year)
                data.append(BradescoTransaction(
                    parsed_date,
                    description,
                    amount
                ))

        iframe.click('css=a[title="Extrato Fechado Pressione Enter para selecionar."]')

        iframe.click('css=#divDadosExtrato .lnk-expansor')

        table = iframe.wait_for_selector('css=.tabGenerica.vAm.topb')

        rows = table.query_selector_all('tbody > tr')

        for row in rows:
            current_date = row.query_selector('css=td:nth-of-type(1)').text_content().strip()
            description = row.query_selector('css=td:nth-of-type(2)').text_content().strip()
            amount = row.query_selector('css=td:nth-of-type(6)').text_content().strip()
            amount = parse_brl_to_float(amount)

            parsed_date = datetime.strptime(current_date, '%d/%m').replace(year=datetime.now().year)
            data.append(BradescoTransaction(
                parsed_date,
                description,
                amount * -1
            ))

        return data
