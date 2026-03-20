# Financial Intelligence System

Projeto de dados sinteticos, analise comportamental, explicabilidade de anomalias e recomendacoes financeiras.

## Visao geral

O objetivo deste projeto e simular um ambiente financeiro plausivel e transformar esse historico em inteligencia acionavel.

Hoje o sistema faz quatro coisas principais:

1. gera contas sinteticas com perfis financeiros
2. gera historico de transacoes com comportamento normal e comportamento suspeito
3. detecta anomalias com base no padrao de cada conta
4. produz explicacoes e recomendacoes financeiras personalizadas

Em outras palavras, o projeto deixou de ser apenas um detector de outliers e passou a funcionar como uma pequena plataforma de inteligencia financeira.

## O pipeline completo

Quando o fluxo completo e executado, o sistema segue esta ordem:

1. cria contas sinteticas com salario, saldo, cidade, horario de atividade e preferencias de gasto
2. simula varias transacoes por conta ao longo do periodo definido
3. valida a consistencia dos arquivos gerados
4. carrega o dataset de transacoes
5. cria features numericas e comportamentais para o modelo
6. monta um perfil financeiro explicito para cada conta
7. aplica o Isolation Forest para detectar anomalias
8. explica cada anomalia comparando a transacao com o perfil da conta
9. gera recomendacoes financeiras personalizadas por conta
10. exporta relatorios e mostra um resumo claro no terminal

## O que existe hoje no projeto

### Geracao de dados

- contas sinteticas com renda, saldo e preferencias de consumo
- transacoes com deposito de salario, pix, compras, pagamentos e saques
- injecao de comportamento suspeito para permitir avaliacao do modelo

### Analise comportamental

- feature engineering por conta
- deteccao de anomalias com Isolation Forest
- score normalizado de anomalia
- ranking das transacoes mais suspeitas

### Inteligencia financeira

- perfil financeiro por conta
- explicacao textual das anomalias
- recomendacoes financeiras simples e personalizadas

## Estrutura principal

```text
financial-intelligence-system/
  data/
    raw/
      generated/
    reports/
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
  requirements.txt
```

## Papel de cada modulo

- `run_generation.py`
  Orquestra a geracao de contas e transacoes sinteticas.

- `main.py`
  Orquestra o pipeline analitico completo: carga, features, perfis, modelo, explicacoes, recomendacoes e relatorios.

- `src/config.py`
  Centraliza caminhos padrao e configuracoes de geracao e analise.

- `src/generators/account_generator.py`
  Gera o perfil base das contas sinteticas.

- `src/generators/transaction_generator.py`
  Simula as transacoes e mantem a continuidade dos saldos.

- `src/dataset/load_dataset.py`
  Carrega o CSV e valida a estrutura minima exigida.

- `src/features/feature_engineering.py`
  Construi variaveis numericas e comportamentais para o modelo.

- `src/profiles/account_profiles.py`
  Construi o perfil financeiro explicito de cada conta com media, desvio, frequencia, horarios e distribuicoes de uso.

- `src/models/anomaly_detection.py`
  Executa o Isolation Forest e devolve score e classificacao de anomalia.

- `src/explainability/anomaly_explainer.py`
  Explica cada anomalia comparando a transacao com o perfil da conta.

- `src/recommendations/financial_recommendations.py`
  Gera recomendacoes financeiras personalizadas com base no comportamento historico da conta.

- `src/reporting/report_generator.py`
  Salva os CSVs finais e monta a saida do terminal em portugues.

## Como a geracao funciona

Ao rodar `python run_generation.py`, o sistema:

1. garante a existencia das pastas em `data/`
2. monta a configuracao de geracao
3. cria as contas sinteticas
4. simula as transacoes dentro do periodo escolhido
5. atualiza o saldo antes e depois de cada operacao
6. valida integridade dos datasets
7. salva:
   - `data/raw/generated/accounts.csv`
   - `data/raw/generated/transactions.csv`

## Como a analise funciona

Ao rodar `python main.py`, o sistema:

1. encontra o dataset de entrada
2. valida colunas e tipos
3. cria as features de modelagem
4. construi um perfil financeiro por conta com:
   - valor medio
   - desvio padrao
   - frequencia diaria e semanal
   - distribuicao por categoria
   - horarios mais comuns
   - tipos de transacao mais frequentes
5. executa o Isolation Forest
6. explica cada anomalia com regras legiveis
7. gera recomendacoes personalizadas por conta
8. salva:
   - `data/reports/anomaly_report.csv`
   - `data/reports/account_profiles.csv`
   - `data/reports/financial_recommendations.csv`

## O que sai em cada relatorio

### `anomaly_report.csv`

Cada linha representa uma transacao analisada com score, classificacao de anomalia e campos de explicacao.

Campos importantes:

- `anomaly_score`
- `raw_anomaly_score`
- `is_anomaly`
- `anomaly_explanation`
- `explanation_count`

### `account_profiles.csv`

Cada linha representa uma conta com seu perfil financeiro consolidado.

Campos importantes:

- `mean_amount`
- `amount_std`
- `avg_daily_transactions`
- `avg_weekly_transactions`
- `transaction_type_distribution`
- `spending_category_amount_share`
- `usual_activity_hours`
- `estimated_monthly_income`
- `average_monthly_spend`

### `financial_recommendations.csv`

Cada linha representa uma conta com recomendacoes personalizadas.

Campos importantes:

- `top_spending_category`
- `top_spending_share`
- `spend_to_income_ratio`
- `impulsive_spending_share`
- `recommendations_text`
- `recommendation_count`

## Como rodar

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Gerar os dados sinteticos

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Rodar a analise completa

```bash
python main.py
```

### 4. Rodar com um CSV proprio

```bash
python main.py --input-path data/raw/financial_transactions.csv --top-n 15
```

Esse comando serve para analisar um CSV externo no mesmo formato esperado pelo projeto, sem depender do dataset sintetico gerado localmente.

## Campos minimos esperados no CSV de transacoes

Se voce quiser usar um arquivo proprio, o pipeline espera pelo menos estas colunas:

- `transaction_id`
- `account_id`
- `timestamp`
- `transaction_type`
- `amount`
- `balance_before`
- `balance_after`
- `merchant_category`
- `transaction_channel`
- `location`
- `origin_account`
- `destination_account`

## Saida do terminal

A experiencia no terminal foi organizada para ficar mais explicativa.

Na geracao, o terminal mostra:

- periodo simulado
- quantidade de contas
- quantidade de transacoes
- quantidade de fraudes rotuladas
- caminhos dos arquivos gerados

Na analise, o terminal mostra:

- dataset analisado
- quantidade de contas e transacoes
- perfis financeiros gerados
- anomalias detectadas e explicadas
- caminhos dos tres relatorios
- ranking das transacoes mais suspeitas com explicacao
- recomendacoes financeiras em destaque

## Observacao sobre o codigo

Os nomes de funcoes, classes e variaveis continuam em ingles para manter um padrao tecnico comum em projetos de programacao, mas:

- as mensagens do terminal estao em portugues
- os comentarios foram ampliados para estudo
- a documentacao ficou mais orientada ao processo

## Testes

O projeto possui testes em `tests/test_pipeline_integrity.py` cobrindo:

- consistencia de saldo entre conta e transacoes
- consistencia de categoria em `pix_out`
- comportamento seguro do modelo em datasets pequenos
- construcao de perfil financeiro
- explicacao de anomalias
- geracao de recomendacoes

## Autor

Murilo Pedral
