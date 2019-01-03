# pybradesco
Acesse seus extratos do Bradesco pelo Python
Esse projeto não tem nenhuma associação com o Bradesco, utilize por sua conta e risco.

# Como funciona
O `pybradesco` utiliza o Selenium para acessar a página do banco e fazer scraping dos dados da sua conta.

# Instalando
*TBD*

# Utilizando

## Inicializando
O setup inicial para ter acesso aos dados da sua conta
```
from pybradesco import Bradesco

# Inicializar
bradesco = Bradesco('AG', 'CC', 'DIGITO_VERIFICADOR', 'SENHA_WEB')

# Autenticar com token gerado do celular
bradesco.authenticate('123123')
```

## Cartão de Crédito
*TBD*

## Conta corrente
```
# Retorna o extrato dos últimos 90 dias
print(bradesco.get_account_statements())
```

