# ADR-0014 - Export Engine: Escopo de Exportacao Local de Artefatos

**Status:** Aceito

## Contexto

O Module Specifications define o Capitulo 16 (Prompt 17, apos a renumeracao
da ADR-0013) como "Export Engine - Exportacao dos artefatos", sem nenhum
outro detalhe tecnico (objetivo, responsabilidades, interfaces).

O SAD, por outro lado, **nao possui nenhum capitulo, componente ou secao
dedicada ao Export Engine**. Gap confirmado por busca no documento
completo (58 paginas, 33 capitulos): catalogos de componentes (SAD 3.3,
4.5, 7.3, 7.6), categorias de configuracao (SAD 21.3), glossario (SAD
33.2), siglas (SAD 33.3) e resumo da estrutura de diretorios (SAD 33.5)
nao mencionam "Export" em nenhum lugar. O AI Coding Standards, o AI
Development Guide e o Business Rules tambem nao mencionam o componente.
A estrutura de diretorios fisica ja scaffolded no Prompt 1
(`infrastructure/reporting/`, `infrastructure/screenshots/`,
`infrastructure/checkpoints/`) tambem nao inclui um diretorio `export/`,
confirmando que o modulo nao foi antecipado durante o planejamento
arquitetural.

Este e o mesmo tipo de gap documental que motivou a ADR-0013 (Log Engine),
porem invertido: la, o SAD tinha o capitulo e o Module Specifications nao
tinha o Prompt; aqui, o Module Specifications tem o Prompt e o SAD nao tem
nenhum conteudo.

A unica pista indireta e a SAD 3.5 (Integracoes Externas), que cita
"ServiceNow Test Management - Web - Cadastro dos artefatos" - mas nenhum
documento do projeto especifica endpoint, autenticacao ou contrato de
payload para essa integracao.

## Alternativas Consideradas

1. **Exportacao local de artefatos**: Export Engine consolida/empacota
   artefatos ja produzidos localmente por outros modulos (relatorios do
   Reporting Engine, evidencias, logs) em um pacote unico (arquivo ZIP)
   para consumo externo manual. Sem integracao de rede/API.
2. **Integracao com ServiceNow Test Management**: Export Engine faz
   upload/cadastro automatico dos artefatos via API HTTP do ServiceNow
   Test Management. Rejeitada nesta ADR por falta de qualquer
   especificacao de contrato (endpoint, autenticacao, payload) em
   qualquer documento do projeto - implementar sem isso seria adivinhar
   uma integracao externa real.
3. **Aguardar documentacao adicional** antes de implementar qualquer
   coisa.

## Decisao

Adotar a alternativa 1: o Export Engine e um utilitario local de
empacotamento de artefatos ja existentes em disco, produzindo um arquivo
ZIP por execucao (identificada por `execution_id`) com um manifesto
(`manifest.json`) descrevendo o conteudo. Nenhuma chamada de rede e
implementada.

Escopo do Prompt 17:

- `ExportConfiguration` (novo, adicionado ao Configuration Manager -
  `directory` e `archive_format`, este ultimo restrito a `{"zip"}`).
- `ExportRequest`/`ExportItem`: o chamador (futuro Workflow Engine)
  informa quais arquivos ja existentes em disco (relatorios, evidencias,
  logs) devem compor o pacote - Export Engine nao depende diretamente de
  Reporting Engine, Screenshot Engine ou Log Engine, seguindo o mesmo
  precedente de DTOs caller-supplied usado por `ExecutionResult`
  (Reporting Engine) e `Checkpoint` (Checkpoint Engine).
- `ExportManifest`: sumario do que foi exportado (descricao, nome no
  arquivo, tamanho), tambem gravado dentro do proprio ZIP.
- `ExportRepositoryPort` + `ZipExportRepository`: empacotamento real via
  `zipfile` da biblioteca padrao.
- `ExportEngine`: valida a consistencia da requisicao (execution_id e ao
  menos um item), delega o empacotamento e retorna um resultado
  estruturado (nunca lanca excecao para falhas de I/O), seguindo o padrao
  usado por Checkpoint Engine e Reporting Engine.

Se uma integracao real com ServiceNow Test Management (alternativa 2) for
necessaria no futuro, ela exige uma nova ADR com especificacao completa
(endpoint, autenticacao, payload) antes de ser implementada - nao deve ser
adicionada retroativamente a este Export Engine sem essa decisao
explicita.

## Consequencias

Fecha o gap documental de forma consistente com o restante da
arquitetura: nenhuma dependencia de rede ou de um contrato de API nao
especificado e introduzida. `ApplicationConfiguration` ganha um novo campo
`export` com valor padrao, sem quebrar configuracoes existentes (mesmo
padrao usado quando `CheckpointConfiguration`/`ReportingConfiguration`
foram adicionadas). O Export Engine fica limitado a reempacotar artefatos
que outros modulos ja produziram - nao gera relatorios, evidencias ou
logs por conta propria, e nao publica nada fora do sistema de arquivos
local.

## Referencias

- Module Specifications (Capitulo 16 - Export Engine)
- SAD 3.5 (Integracoes Externas - ServiceNow Test Management)
- SAD 29.2 (Execucao via CLI - ferramenta single-process)
- ADR-0013 (precedente metodologico para lidar com gaps de documentacao)
