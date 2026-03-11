# Sistema de Inteligência Financeira

## Visão Geral

O **Sistema de Inteligência Financeira** é um projeto desenvolvido para simular comportamentos financeiros e detectar anomalias em dados de transações.

O objetivo é construir um dataset financeiro sintético e desenvolver ferramentas analíticas capazes de identificar padrões incomuns, como transações fraudulentas ou comportamentos atípicos em contas bancárias.

Este projeto está sendo desenvolvido com foco em **aprendizado prático**, abordando:

* Simulação de dados
* Modelagem de comportamento financeiro
* Detecção de anomalias
* Análise de transações financeiras

O sistema gera dados bancários sintéticos incluindo **contas e transações** que simulam comportamentos financeiros realistas.

---

# Objetivos do Projeto

Os principais objetivos do projeto são:

* Gerar um **dataset financeiro sintético**
* Simular **contas bancárias com perfis de comportamento**
* Simular **transações financeiras diárias**
* Injetar **comportamentos anômalos**
* Construir **ferramentas para detecção de anomalias**

O dataset conterá informações como:

* contas
* transações
* timestamps de transações
* tipos de transação
* localização das transações
* saldos das contas
* indicadores de fraude

---

# Estrutura do Dataset

O dataset simulado conterá duas entidades principais:

## Contas

Cada conta representa um usuário bancário simulado com características comportamentais.

Exemplo de campos:

* `account_id`
* `home_city`
* `initial_balance`
* `current_balance`
* `salary`
* `activity_level`
* `transactions_per_day`
* `favorite_categories`
* `active_hour_start`
* `active_hour_end`

Esses atributos definem **como a conta se comporta financeiramente**.

---

## Transações

As transações simulam a atividade financeira de cada conta ao longo do tempo.

Exemplo de campos:

* `transaction_id`
* `account_id`
* `timestamp`
* `transaction_type`
* `amount`
* `balance_before`
* `balance_after`
* `merchant_category`
* `transaction_channel`
* `location`
* `is_fraud`
* `origin_account`
* `destination_account`

---

# Estágio Atual de Desenvolvimento

O projeto atualmente está na **fase de geração de dados**.

O primeiro módulo implementado é:

### Gerador de Contas (Account Generator)

Este módulo cria contas bancárias sintéticas com atributos realistas.

Cada conta gerada possui:

* saldo inicial baseado no salário
* nível de atividade financeira
* frequência de transações por dia
* categorias de gasto preferidas
* horário ativo para transações
* cidade de origem

Exemplo de conta gerada:

```json
{
  "account_id": 1,
  "home_city": "Aracaju",
  "initial_balance": 5400,
  "current_balance": 5400,
  "salary": 3200,
  "activity_level": "medium",
  "transactions_per_day": 5,
  "favorite_categories": {
    "groceries": 0.52,
    "transport": 0.31,
    "restaurant": 0.17
  },
  "active_hour_start": 8,
  "active_hour_end": 20
}
```

---

# Estrutura do Projeto

financial-intelligence-system/

data/
    generated/

src/
    generators/
        account_generator.py
        transaction_generator.py

README.md

---

# Próximos Passos de Desenvolvimento

O próximo módulo a ser implementado é o **Gerador de Transações (Transaction Generator)**, responsável por simular a atividade financeira diária.

O gerador irá:

* simular transações ao longo de **6 meses**
* gerar **2 a 10 transações por dia por conta**
* atualizar o saldo das contas
* simular categorias de comércio
* simular canais de transação
* gerar timestamps das transações
* inserir padrões anômalos

Isso produzirá um dataset com **milhares de transações financeiras realistas**.

---

# Trabalhos Futuros

Melhorias planejadas incluem:

* módulo de injeção de anomalias
* análise estatística do comportamento financeiro
* modelos de detecção de anomalias
* dashboards de visualização
* experimentos de detecção de fraude

---

# Tecnologias

O projeto atualmente está sendo implementado utilizando:

* Python
* Simulação de dados com geração aleatória
* Geração estruturada de dataset

Ferramentas futuras podem incluir:

* Pandas
* PostgreSQL
* Modelos de Machine Learning
* Ferramentas de visualização de dados

---

# Autor

Murilo Pedral

Estudante de Ciência da Computação explorando simulação de dados, detecção de anomalias e modelagem de dados financeiros.