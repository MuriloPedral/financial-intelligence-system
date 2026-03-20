# Financial Intelligence System

Projeto de dados sinteticos e inteligencia financeira para simular contas bancarias, analisar transacoes e identificar comportamentos suspeitos.

## Visao geral

O sistema foi construido para gerar um ambiente financeiro ficticio e aplicar analise comportamental em cima dele. Em vez de depender de dados externos, todo o fluxo operacional usa apenas dados sinteticos criados dentro do proprio projeto.

Hoje o projeto faz quatro coisas principais:

1. gera contas sinteticas com perfis financeiros
2. gera transacoes sinteticas com comportamento normal e suspeito
3. detecta e explica anomalias em transacoes
4. gera recomendacoes financeiras personalizadas por conta

## Fluxo do sistema

O uso normal do projeto acontece em duas execucoes:

1. `python run_generation.py`
   gera contas e transacoes sinteticas e salva os arquivos brutos em `data/raw/generated/`

2. `python main.py`
   carrega apenas o dataset sintetico gerado internamente, cria features, perfis financeiros, detecta anomalias, explica os casos e exporta os relatorios analiticos

Importante:

- o projeto nao aceita mais CSV externo no fluxo principal
- a analise sempre usa `data/raw/generated/transactions.csv`

## Estrutura principal

```text
financial-intelligence-system/
  data/
    raw/
      generated/
        accounts.csv
        transactions.csv
    reports/
      account_profiles.csv
      anomaly_report.csv
      financial_recommendations.csv
  src/
    dataset/
    explainability/
    features/
    generators/
    models/
    profiles/
    recommendations/
    reporting/
    utils/
  main.py
  run_generation.py
  DOCUMENTO-DO-PROJETO.md
```

## O que cada etapa faz

### 1. Geracao sintetica

Em [run_generation.py](C:/Users/muril/Códigos/financial-intelligence-system/run_generation.py), o sistema:

1. cria contas com salario, saldo inicial, cidade, categoria favorita e janela de atividade
2. simula movimentacoes como salario, PIX, compras, boletos e saques
3. injeta parte de comportamento anomalo de forma controlada
4. valida consistencia de IDs, valores e continuidade de saldo
5. salva os CSVs brutos

### 2. Analise financeira

Em [main.py](C:/Users/muril/Códigos/financial-intelligence-system/main.py), o sistema:

1. carrega o dataset gerado internamente
2. trata tipos e valida colunas obrigatorias
3. cria features comportamentais
4. constroi um perfil financeiro explicito para cada conta
5. roda o Isolation Forest
6. explica cada anomalia detectada
7. gera recomendacoes financeiras acionaveis
8. exporta os relatorios finais

## Relatorios finais

### `anomaly_report.csv`

Agora esse arquivo ficou mais limpo:

- contem apenas as transacoes classificadas como anomalia
- nao repete todas as features internas do modelo
- prioriza colunas uteis para leitura humana

Campos principais:

- `anomaly_rank`
- `transaction_id`
- `account_id`
- `timestamp`
- `transaction_type`
- `amount`
- `anomaly_score`
- `anomaly_explanation`

### `account_profiles.csv`

Contem um resumo consolidado por conta, com foco em comportamento financeiro.

Campos principais:

- `mean_amount`
- `amount_std`
- `avg_daily_transactions`
- `avg_weekly_transactions`
- `estimated_monthly_income`
- `average_monthly_spend`
- `spend_to_income_ratio`
- `impulsive_spending_share`

### `financial_recommendations.csv`

Agora exporta apenas recomendacoes acionaveis, para evitar repeticao de linhas sem utilidade pratica.

Campos principais:

- `recommendation_rank`
- `account_id`
- `top_spending_category`
- `spend_to_income_ratio`
- `recommendation_priority`
- `recommendations_text`

## Saida no terminal

As saidas no terminal foram reorganizadas para ficarem mais claras.

Na geracao, o terminal mostra:

- periodo simulado
- numero de contas
- numero de transacoes
- media de transacoes por conta
- quantidade de fraudes rotuladas
- caminhos dos arquivos gerados

Na analise, o terminal mostra:

- fonte analisada
- periodo da analise
- volume total analisado
- anomalias detectadas e explicadas
- contas com recomendacao acionavel
- caminhos dos relatorios
- ranking das principais anomalias
- recomendacoes em destaque

## Como rodar

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Gerar os dados sinteticos

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Rodar a analise

```bash
python main.py --top-n 10
```

## Parametros de execucao

### `run_generation.py`

Esse comando gera os dados sinteticos do projeto:

```bash
python run_generation.py --accounts 150 --months 6 --fraud-rate 0.03 --seed 42
```

Parametros principais:

- `--accounts`
  quantidade de contas sinteticas que serao criadas

- `--months`
  quantidade de meses simulados no historico de transacoes

- `--fraud-rate`
  taxa aproximada de fraude ou comportamento suspeito injetado no dataset

- `--seed`
  semente aleatoria usada para reproduzir o mesmo conjunto de dados em outra execucao

- `--start-date`
  data inicial manual da simulacao no formato `YYYY-MM-DD`

- `--end-date`
  data final manual da simulacao no formato `YYYY-MM-DD`

- `--accounts-output`
  caminho do CSV de saida das contas

- `--transactions-output`
  caminho do CSV de saida das transacoes

Exemplo:

```bash
python run_generation.py --accounts 80 --months 3 --fraud-rate 0.05 --seed 7
```

### `main.py`

Esse comando executa a analise sobre o dataset sintetico gerado internamente:

```bash
python main.py --top-n 10 --contamination 0.03 --seed 42
```

Parametros principais:

- `--top-n`
  quantidade de transacoes suspeitas exibidas no ranking do terminal

- `--contamination`
  proporcao esperada de anomalias usada pelo modelo `Isolation Forest`

- `--seed`
  semente usada para manter a analise reproduzivel

- `--output-path`
  caminho do CSV exportado com as anomalias

- `--profiles-output-path`
  caminho do CSV exportado com os perfis financeiros

- `--recommendations-output-path`
  caminho do CSV exportado com as recomendacoes financeiras

Exemplo:

```bash
python main.py --top-n 5 --contamination 0.05 --seed 7
```

### O que e `seed`

`seed` e a semente do sorteio aleatorio.

Na pratica:

- com a mesma `seed`, o sistema tende a reproduzir os mesmos dados e o mesmo comportamento
- com uma `seed` diferente, a simulacao muda

Isso e util para:

- testes
- comparacao entre execucoes
- debug
- demonstracao do projeto com resultados reproduziveis

## Modulos principais

- [src/generators/account_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/account_generator.py)
  gera os perfis de conta

- [src/generators/transaction_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/transaction_generator.py)
  gera o historico de transacoes

- [src/features/feature_engineering.py](C:/Users/muril/Códigos/financial-intelligence-system/src/features/feature_engineering.py)
  transforma transacoes em variaveis para o modelo

- [src/profiles/account_profiles.py](C:/Users/muril/Códigos/financial-intelligence-system/src/profiles/account_profiles.py)
  constroi o perfil financeiro por conta

- [src/explainability/anomaly_explainer.py](C:/Users/muril/Códigos/financial-intelligence-system/src/explainability/anomaly_explainer.py)
  gera explicacoes legiveis das anomalias

- [src/recommendations/financial_recommendations.py](C:/Users/muril/Códigos/financial-intelligence-system/src/recommendations/financial_recommendations.py)
  produz recomendacoes financeiras personalizadas

- [src/reporting/report_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/reporting/report_generator.py)
  organiza os relatorios e a saida do terminal

## Documento principal do projeto

Para uma explicacao mais completa sobre objetivo, escopo, arquitetura e limitacoes, consulte [DOCUMENTO-DO-PROJETO.md](C:/Users/muril/Códigos/financial-intelligence-system/DOCUMENTO-DO-PROJETO.md).
