# pybradesco
Acesse seus extratos do Bradesco pelo Python
Esse projeto não tem nenhuma associação com o Bradesco, utilize por sua conta e risco.

**Obs: Esse projeto é experimental**

# Como funciona
O `pybradesco` utiliza o Playwright para acessar a página do banco e fazer scraping dos dados da sua conta.

# Instalando
*TBD*

# Utilizando

## Inicializando
O setup inicial para ter acesso aos dados da sua conta
```python
from pybradesco import Bradesco

# Inicializar
bradesco = Bradesco()

# Abre página de login, digita agencia e conta
bradesco.prepare('AG', 'CC', 'DIGITO_VERIFICADOR')

# Autenticar com senha e  token gerado do celular
bradesco.authenticate('SENHA_WEB', '123123')
```

## Cartão de Crédito
```python

# Retorna dados da fatura aberta + dados da última fatura
print(bradesco.get_credit_card_statements())
```

## Conta corrente
```python
# Retorna o extrato dos últimos 90 dias
print(bradesco.get_checking_account_statements())
```

