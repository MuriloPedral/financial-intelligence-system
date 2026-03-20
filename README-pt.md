# Financial Intelligence System

Projeto de geracao de dados financeiros sinteticos e deteccao de anomalias em transacoes.

## Ideia do projeto

Este projeto foi construido para simular um pequeno ecossistema bancario ficticio e, em seguida, aplicar analise de dados e machine learning para encontrar movimentacoes suspeitas.

Em vez de depender de dados bancarios reais, o sistema gera:

1. contas sinteticas com perfis de comportamento
2. historico de transacoes ao longo do tempo
3. sinais de comportamento anomalo
4. um relatorio final com ranking das transacoes mais suspeitas

Isso permite estudar engenharia de dados, simulacao, comportamento financeiro e deteccao de anomalias dentro do mesmo projeto.

## O que o sistema entrega hoje

O projeto esta dividido em duas grandes etapas:

1. Geracao de dados sinteticos
2. Analise de anomalias

Na pratica, o fluxo completo fica assim:

1. o sistema cria contas com salario, saldo inicial, cidade, horario de atividade e categorias favoritas de gasto
2. o sistema simula varios dias de movimentacao para cada conta
3. cada transacao recebe informacoes como valor, tipo, localizacao, saldo antes e saldo depois
4. algumas transacoes sao geradas com comportamento mais estranho para representar fraude ou anomalia
5. o pipeline analitico le o CSV gerado
6. o pipeline cria features de comportamento por conta
7. o modelo Isolation Forest calcula um score de anomalia
8. o sistema exporta um CSV final com ranking das transacoes mais suspeitas

## Estrutura principal do projeto

```text
financial-intelligence-system/
  data/
    raw/
      generated/
    reports/
  src/
    dataset/
    features/
    generators/
    models/
    reporting/
    utils/
  main.py
  run_generation.py
  requirements.txt
```

## O papel de cada parte

- `run_generation.py`
  Script principal para gerar contas e transacoes sinteticas.

- `main.py`
  Script principal para carregar o dataset, criar features, rodar o modelo e salvar o relatorio.

- `src/config.py`
  Centraliza caminhos padrao e configuracoes de geracao e analise.

- `src/generators/account_generator.py`
  Gera o perfil das contas simuladas.

- `src/generators/transaction_generator.py`
  Gera as transacoes e atualiza os saldos ao longo do tempo.

- `src/dataset/load_dataset.py`
  Carrega o CSV e valida as colunas obrigatorias.

- `src/features/feature_engineering.py`
  Converte as transacoes em variaveis uteis para o modelo.

- `src/models/anomaly_detection.py`
  Executa o Isolation Forest e produz os scores de anomalia.

- `src/reporting/report_generator.py`
  Organiza o resumo final exibido no terminal e salva o CSV do relatorio.

## Como a geracao funciona

Quando voce roda `python run_generation.py`, o projeto executa este processo:

1. cria as pastas necessarias em `data/`
2. monta uma configuracao com quantidade de contas, meses, taxa de fraude e semente aleatoria
3. gera uma lista de contas sinteticas
4. para cada conta, simula um periodo completo de movimentacoes
5. inclui depositos de salario, transferencias, compras, pagamentos e saques
6. atualiza o saldo da conta a cada transacao
7. valida se nao existem erros como IDs duplicados ou saldo inconsistente
8. salva:
   - `data/raw/generated/accounts.csv`
   - `data/raw/generated/transactions.csv`

## Como a analise funciona

Quando voce roda `python main.py`, o projeto executa este processo:

1. procura um dataset para analisar
2. valida a estrutura do arquivo
3. converte colunas para tipos corretos
4. cria features como:
   - hora da transacao
   - dia da semana
   - valor relativo ao saldo
   - valor comparado com a media da conta
   - tempo entre transacoes
   - localizacao incomum
   - horario incomum
5. aplica o Isolation Forest
6. gera:
   - `anomaly_score`
   - `raw_anomaly_score`
   - `is_anomaly`
7. salva o resultado em `data/reports/anomaly_report.csv`
8. imprime no terminal um resumo em portugues com o ranking das transacoes mais suspeitas

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
python main.py
```

### 4. Rodar com um CSV proprio

```bash
python main.py --input-path data/raw/financial_transactions.csv --top-n 15
```

## O que existe dentro dos CSVs

### Arquivo de contas

Cada conta possui informacoes como:

- `account_id`
- `home_city`
- `initial_balance`
- `current_balance`
- `salary`
- `salary_day`
- `activity_level`
- `transactions_per_day`
- `favorite_categories`
- `active_hour_start`
- `active_hour_end`

### Arquivo de transacoes

Cada transacao possui informacoes como:

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
- `is_fraud`
- `origin_account`
- `destination_account`

## Saida do terminal

Os scripts agora exibem saidas em portugues e em formato mais organizado.

Na geracao, o terminal mostra:

- periodo simulado
- quantidade de contas
- quantidade de transacoes
- quantidade de transacoes marcadas como fraude
- caminhos dos arquivos gerados
- proximo comando sugerido

Na analise, o terminal mostra:

- dataset utilizado
- transacoes analisadas
- contas analisadas
- quantidade de anomalias detectadas
- fraudes rotuladas no dataset
- fraudes rotuladas encontradas pelo modelo
- caminho do CSV final
- ranking das transacoes mais suspeitas

## Observacao importante sobre o codigo

Os nomes de funcoes, classes e variaveis continuam em ingles para manter um padrao tecnico comum em projetos de programacao, mas:

- as mensagens de terminal estao em portugues
- os comentarios do codigo foram ampliados para estudo
- este README foi escrito de forma mais didatica

## Testes e validacoes

O projeto possui testes em `tests/test_pipeline_integrity.py` para validar pontos importantes, como:

- saldo final das contas batendo com as transacoes
- consistencia da categoria `transfer` em `pix_out`
- comportamento seguro do modelo em datasets muito pequenos

## Autor

Murilo Pedral
