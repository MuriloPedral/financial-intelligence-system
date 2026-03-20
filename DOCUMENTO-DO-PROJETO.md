# Documento Do Projeto

## Nome

Financial Intelligence System

## Propósito

O Financial Intelligence System é um projeto de simulação e análise de comportamento financeiro. Ele foi criado para representar um pequeno ecossistema bancário fictício e, sobre esse ambiente, aplicar lógica analítica para detectar padrões anômalos e produzir recomendações financeiras personalizadas.

O projeto existe para resolver um problema comum em estudos de dados financeiros: é difícil experimentar com dados reais por questões de privacidade, sensibilidade e acesso. Por isso, o sistema usa dados sintéticos gerados internamente.

## Escopo

O escopo atual do sistema inclui:

1. geração de contas sintéticas
2. geração de transações sintéticas
3. construção de perfis financeiros por conta
4. detecção de anomalias com Isolation Forest
5. explicação heurística das anomalias
6. geração de recomendações financeiras acionáveis
7. exportação de relatórios analíticos em CSV

O sistema não tem como objetivo atual:

- operar com dados bancários reais
- processar transações em tempo real
- substituir um sistema antifraude de produção
- executar tomada de decisão automática sobre bloqueio de conta

## Ideia central

O sistema parte da hipótese de que cada conta possui um comportamento financeiro relativamente reconhecível ao longo do tempo. Quando uma transação foge demais desse padrão, ela pode ser tratada como suspeita ou incomum.

Para viabilizar isso, o projeto trabalha em três camadas:

1. simulação
2. modelagem comportamental
3. interpretação do resultado

Em vez de parar na detecção de outlier, o projeto também tenta responder:

- por que a transação parece anômala
- o que o comportamento da conta revela
- que tipo de recomendação financeira pode ser extraída desse histórico

## Funcionamento geral

### Etapa 1. Geração de dados

O sistema cria contas sintéticas com atributos como:

- cidade base
- salário
- saldo inicial
- nível de atividade
- horário mais comum de operação
- categorias favoritas de gasto

Depois disso, ele gera transações compatíveis com esse perfil:

- depósito de salário
- transferências PIX
- compras com cartão
- compras online
- pagamento de contas
- saques

Também existe injeção controlada de comportamento suspeito para permitir avaliação do pipeline.

### Etapa 2. Engenharia de comportamento

Com o histórico pronto, o sistema constrói variáveis que representam o comportamento financeiro da conta, como:

- média de valor por transação
- desvio padrão
- frequência diária e semanal
- distribuição por categoria
- localidade mais comum
- horários mais frequentes
- distância da transação atual em relação ao padrão

### Etapa 3. Detecção de anomalias

O modelo principal é o Isolation Forest. Ele recebe as features tratadas e atribui um score de anomalia para cada transação.

Quanto mais alta a pontuação, mais distante aquela transação está do comportamento esperado.

### Etapa 4. Explicabilidade

As anomalias detectadas recebem explicações legíveis, construídas por regras heurísticas comparando a transação com o perfil histórico da conta.

Exemplos de explicação:

- valor muito acima da média da conta
- horário incomum
- categoria pouco frequente
- localização incomum
- frequência acima do padrão recente

### Etapa 5. Recomendações financeiras

Além da camada de risco, o sistema também observa o comportamento financeiro da conta para gerar recomendações simples, como:

- gasto concentrado em poucas categorias
- peso excessivo de compras impulsivas
- gasto acima da renda estimada
- categoria dominante no orçamento

## Arquitetura

O projeto é modular.

Principais blocos:

- `src/generators`
  criação de contas e transações

- `src/dataset`
  carga e preparação do dataset sintético gerado internamente

- `src/features`
  criação das features de modelagem

- `src/profiles`
  construção do perfil financeiro por conta

- `src/models`
  detecção de anomalias

- `src/explainability`
  explicação textual das anomalias

- `src/recommendations`
  recomendações financeiras personalizadas

- `src/reporting`
  exportação dos relatórios e organização da saída no terminal

## Saídas do sistema

O sistema produz três arquivos principais:

### `data/reports/anomaly_report.csv`

Relatório enxuto apenas com transações anômalas, ordenadas por importância.

### `data/reports/account_profiles.csv`

Resumo consolidado do perfil financeiro de cada conta.

### `data/reports/financial_recommendations.csv`

Relatório de recomendações acionáveis, sem repetir mensagens genéricas para todas as contas.

## Qualidade e organização

O projeto foi organizado para ser:

- modular
- legível
- fácil de testar
- fácil de evoluir

Ele também tenta separar bem:

- dado bruto gerado
- feature interna do modelo
- informação útil para consumo humano

Por isso, os relatórios finais foram reduzidos para conter apenas o que faz sentido para leitura e análise.

## Valor do projeto

Este projeto é útil para:

- portfólio em dados e machine learning
- estudo de comportamento financeiro
- estudo de detecção de anomalias
- treino de modelagem com dados sintéticos
- demonstração de pipeline analítico de ponta a ponta

## Limitações atuais

Apesar de funcional, o sistema ainda tem limites claros:

- usa heurísticas simples nas explicações
- não trabalha com streaming ou produção
- não usa modelos supervisionados de fraude
- não modela relação entre múltiplas contas em rede
- não possui dashboard ou API

## Evoluções futuras possíveis

Caminhos naturais para evolução:

- dashboard analítico
- API para execução do pipeline
- análise temporal mais sofisticada
- análise de rede entre contas
- classificação supervisionada de fraude
- score de risco por conta
- monitoramento contínuo

## Resumo executivo

O Financial Intelligence System é uma plataforma de simulação e análise de comportamento financeiro baseada em dados sintéticos. Seu foco é gerar contas e transações plausíveis, detectar anomalias, explicar o motivo dessas anomalias e produzir recomendações financeiras úteis por conta.

Em termos simples, ele transforma dados financeiros simulados em inteligência analítica legível.
