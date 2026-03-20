# Financial Intelligence System

Projeto de dados sintéticos e inteligência financeira para simular contas bancárias, analisar transações e identificar comportamentos suspeitos.

## Visão geral

O sistema foi construído para gerar um ambiente financeiro fictício e aplicar análise comportamental em cima dele. Em vez de depender de dados externos, todo o fluxo operacional usa apenas dados sintéticos criados dentro do próprio projeto.

Hoje o projeto faz quatro coisas principais:

1. gera contas sintéticas com perfis financeiros
2. gera transações sintéticas com comportamento normal e suspeito
3. detecta e explica anomalias em transações
4. gera recomendações financeiras personalizadas por conta

## Fluxo do sistema

O uso normal do projeto acontece em duas execuções:

1. `python run_generation.py`
   gera contas e transações sintéticas e salva os arquivos brutos em `data/raw/generated/`

2. `python main.py`
   carrega apenas o dataset sintético gerado internamente, cria features, perfis financeiros, detecta anomalias, explica os casos e exporta os relatórios analíticos

Importante:

- o projeto não aceita mais CSV externo no fluxo principal
- a análise sempre usa `data/raw/generated/transactions.csv`

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

### 1. Geração sintética

Em [run_generation.py](C:/Users/muril/Códigos/financial-intelligence-system/run_generation.py), o sistema:

1. cria contas com salário, saldo inicial, cidade, categoria favorita e janela de atividade
2. simula movimentações como salário, PIX, compras, boletos e saques
3. injeta parte de comportamento anômalo de forma controlada
4. valida consistência de IDs, valores e continuidade de saldo
5. salva os CSVs brutos

### 2. Análise financeira

Em [main.py](C:/Users/muril/Códigos/financial-intelligence-system/main.py), o sistema:

1. carrega o dataset gerado internamente
2. trata tipos e valida colunas obrigatórias
3. cria features comportamentais
4. constrói um perfil financeiro explícito para cada conta
5. roda o Isolation Forest
6. explica cada anomalia detectada
7. gera recomendações financeiras acionáveis
8. exporta os relatórios finais

## Relatórios finais

### `anomaly_report.csv`

Agora esse arquivo ficou mais limpo:

- contém apenas as transações classificadas como anomalia
- não repete todas as features internas do modelo
- prioriza colunas úteis para leitura humana

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

Contém um resumo consolidado por conta, com foco em comportamento financeiro.

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

Agora exporta apenas recomendações acionáveis, para evitar repetição de linhas sem utilidade prática.

Campos principais:

- `recommendation_rank`
- `account_id`
- `top_spending_category`
- `spend_to_income_ratio`
- `recommendation_priority`
- `recommendations_text`

## Saída no terminal

As saídas no terminal foram reorganizadas para ficarem mais claras.

Na geração, o terminal mostra:

- período simulado
- número de contas
- número de transações
- média de transações por conta
- quantidade de fraudes rotuladas
- caminhos dos arquivos gerados

Na análise, o terminal mostra:

- fonte analisada
- período da análise
- volume total analisado
- anomalias detectadas e explicadas
- contas com recomendação acionável
- caminhos dos relatórios
- ranking das principais anomalias
- recomendações em destaque

## Como rodar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Gerar os dados sintéticos

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Rodar a análise

```bash
python main.py --top-n 10
```

## Módulos principais

- [src/generators/account_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/account_generator.py)
  gera os perfis de conta

- [src/generators/transaction_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/transaction_generator.py)
  gera o histórico de transações

- [src/features/feature_engineering.py](C:/Users/muril/Códigos/financial-intelligence-system/src/features/feature_engineering.py)
  transforma transações em variáveis para o modelo

- [src/profiles/account_profiles.py](C:/Users/muril/Códigos/financial-intelligence-system/src/profiles/account_profiles.py)
  constrói o perfil financeiro por conta

- [src/explainability/anomaly_explainer.py](C:/Users/muril/Códigos/financial-intelligence-system/src/explainability/anomaly_explainer.py)
  gera explicações legíveis das anomalias

- [src/recommendations/financial_recommendations.py](C:/Users/muril/Códigos/financial-intelligence-system/src/recommendations/financial_recommendations.py)
  produz recomendações financeiras personalizadas

- [src/reporting/report_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/reporting/report_generator.py)
  organiza os relatórios e a saída do terminal

## Documento principal do projeto

Para uma explicação mais completa sobre objetivo, escopo, arquitetura e limitações, consulte [DOCUMENTO-DO-PROJETO.md](C:/Users/muril/Códigos/financial-intelligence-system/DOCUMENTO-DO-PROJETO.md).
