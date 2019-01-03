from time import sleep

from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, \
    frame_to_be_available_and_switch_to_it
from selenium.webdriver.support.wait import WebDriverWait


class Bradesco:
    BASE_PATH = 'https://banco.bradesco/html/classic/index.shtm'

    def __init__(self, branch, account, verifying_digit, web_password):
        self.branch = branch
        self.account = account
        self.verifying_digit = verifying_digit
        self.web_password = web_password

        self.driver = Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities={'browserName': 'chrome'}
        )

        self.wait = WebDriverWait(self.driver, 60)

    def _type_safe_keyboard(self, password: str):
        for char in password:
            self.driver.find_element_by_xpath(f'//a[.="{char}"]').click()

    def authenticate(self, token):
        self.driver.get(self.BASE_PATH)

        # Agência
        self.driver.find_element_by_id('AGN').send_keys(self.branch)

        # Conta Corrente
        self.driver.find_element_by_id('CTA').send_keys(self.account)

        # Digito Verificador
        self.driver.find_element_by_id('DIGCTA').send_keys(self.verifying_digit)

        # Botão Entrar
        self.driver.find_element_by_css_selector('.btn-ok').click()

        # Senha Web
        self._type_safe_keyboard(self.web_password)

        # Token
        self.wait.until(
            presence_of_element_located((By.CSS_SELECTOR, 'input[id="form_j_token:Password1"]'))
        ).send_keys(token)

        self.driver.find_element_by_css_selector('input[id="loginbotoes:botaoAvancar"]').click()

        # Espera loading
        self.wait.until(
            presence_of_element_located((By.XPATH, '//a[.="Saldos e Extratos"]'))
        )

        self._remove_home_modal()

    def _remove_home_modal(self):
        sleep(10)
        if len(self.driver.find_elements_by_css_selector('.jqmOverlay')) >= 1:
            self.driver.execute_script('document.querySelector(".jqmOverlay").remove()')

    def get_account_statements(self):
        data = []
        # Acessa a tela de extrato nos últimos 90 dias
        self.wait.until(
            presence_of_element_located((By.XPATH, '//a[.="Saldos e Extratos"]'))
        ).click()
        self.wait.until(
            frame_to_be_available_and_switch_to_it((By.ID, 'paginaCentral'))
        )
        self.wait.until(
            presence_of_element_located((By.XPATH, '//a[.="Extrato (Últimos Lançamentos)"]'))
        ).click()
        self.wait.until(
            presence_of_element_located((By.CSS_SELECTOR, 'li[id="fEx:viewFiltroBusca:l1diacont90off"'))
        ).click()

        # Faz o parse
        table = self.wait.until(
            presence_of_element_located((By.CSS_SELECTOR, 'table[id="fEx:dexs_0:vexd:dex"'))
        )
        rows = table.find_elements_by_css_selector('tbody > tr')
        last_date = None
        for row in rows:
            print(f'Looper !')
            current_date = row.find_element_by_css_selector('td:nth-of-type(1)').text.strip()
            payment_info = row.find_element_by_css_selector('td:nth-of-type(2)').text.strip()
            credit = row.find_element_by_css_selector('td:nth-of-type(4)').text.strip()
            if credit == '':
                amount = row.find_element_by_css_selector('td:nth-of-type(5)').text.strip()
            else:
                amount = credit
            if amount == '':
                amount = None
            else:
                amount = float(amount.replace('.', '').replace(',', '.').replace(' ', ''))

            if current_date != '':
                last_date = current_date

            data.append({
                'date': last_date,
                'payment_info': payment_info,
                'amount': amount
            })
        return data
