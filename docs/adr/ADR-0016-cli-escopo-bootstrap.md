# ADR-0016 - CLI: Escopo Limitado ao Bootstrap da Aplicacao

**Status:** Aceito

## Contexto

O Module Specifications define o Capitulo 21 (Prompt 22, apos a
renumeracao da ADR-0013) como "CLI - Interface de linha de comando", sem
detalhe tecnico adicional.

O SAD, assim como Export Engine (ADR-0014) e Application Controller
(ADR-0015), **nao possui nenhum capitulo dedicado a CLI**. Confirmado por
enumeracao dos 33 capitulos do documento. Diferente dos dois gaps
anteriores, porem, a CLI e mencionada com bastante detalhe espalhado por
varios capitulos:

- SAD 2.2 (Drivers Funcionais): "DF-04 CLI - Executar por linha de
  comando."
- SAD 5.3 (Estrutura de Diretorios): "cli/ - Comandos da interface de
  linha de comando" (diretorio ja scaffolded desde o Prompt 1).
- SAD 5.4: "CLI - Presentation - Entrada da aplicacao."
- SAD 6.2/6.3 (Arquitetura de Execucao - Fluxo Geral): "A execucao e
  iniciada pela CLI, que interpreta os parametros informados pelo
  usuario. Apos validar a configuracao, a aplicacao carrega a Base de
  Conhecimento, processa a planilha Excel e inicia os workflows..." Passos:
  (1) Inicializacao da CLI, (2) Leitura/validacao das configuracoes,
  (3) Carregamento da Base de Conhecimento, (4) Leitura/validacao da
  planilha Excel, (5) Inicializacao do navegador Playwright,
  (6) Autenticacao manual do usuario (quando necessaria), (7) Execucao do
  Workflow Engine.
- SAD 26.6 (Deployment - Fluxo de Inicializacao): praticamente identico
  ao 6.3, confirmando a mesma sequencia.
- SAD 29.2: "Execucao via CLI - A aplicacao e iniciada exclusivamente por
  linha de comando... Nao possui interface grafica."

`pyproject.toml` ja declara `typer` como dependencia desde o
scaffolding do Prompt 1 (nao instalada ate agora - instalada nesta
implementacao para honrar essa escolha ja registrada).

## Decisao

A CLI implementa fielmente os passos 1, 2, 3 e 5 do fluxo da SAD 6.3/26.6
(inicializacao, configuracao, Base de Conhecimento, navegador), delegando
neles inteiramente ao `ApplicationController` (raiz de composicao, Prompt
21/ADR-0015). Os passos 4, 6 e 7 permanecem fora de escopo, pelos mesmos
motivos ja registrados na ADR-0015:

- **Passo 4 (planilha Excel)**: Excel Importer nao existe - sem capitulo
  SAD, sem Prompt no Module Specifications.
- **Passo 6 (autenticacao manual)**: depende de um workflow real em
  execucao (o usuario autentica na pagina que a automacao abriu); sem
  Workflow concreto, nao ha o que autenticar.
- **Passo 7 (Workflow Engine)**: nenhum Workflow concreto pode ser
  montado sem dados da planilha (passo 4) e regras de negocio do
  ServiceNow, que nenhum modulo deste codebase implementa.

A CLI, portanto, e um comando de **bootstrap e validacao**: recebe os
parametros do usuario, monta um `LoadConfigurationRequest`, instancia o
`ApplicationController` (validando configuracao e Base de Conhecimento) e,
salvo `--skip-browser-check`, valida que um navegador real consegue ser
iniciado - reportando sucesso ou uma mensagem de erro clara, nunca um
traceback Python cru (SAD 2.3 - Confiabilidade).

Implementada com Typer (dependencia ja declarada), um unico comando,
argumentos mapeando 1:1 para `LoadConfigurationRequest`. Nenhuma validacao
de existencia de arquivo/formato de URL e feita na propria CLI (via
`exists=True` do Typer/Click, por exemplo) - toda validacao permanece
centralizada no `ConfigurationValidator` ja existente (SAD 21.8: "Todas as
configuracoes devem ser centralizadas no Configuration Manager"), evitando
duas fontes de verdade com mensagens potencialmente inconsistentes.

Codigos de saida do processo:

```
0  sucesso
1  erro de configuracao (ConfigurationError)
2  erro de Base de Conhecimento (KnowledgeBaseError)
3  erro de navegador (BrowserError)
4  outro erro de dominio conhecido (QaServiceNowAssistantError)
5  erro inesperado (isolamento deliberado e documentado, mesmo padrao
   ja usado em InMemoryEventBus/RetryEngine/WorkflowEngine)
```

## Consequencias

Fecha o gap documental de forma consistente com o restante da
arquitetura (ADR-0014, ADR-0015): a CLI entrega o que a documentacao
espalhada realmente descreve e pode ser cumprido hoje, sem inventar
leitura de planilha ou execucao de workflows concretos. Quando Excel
Importer e a construcao de Workflows concretos existirem, a CLI podera
ser estendida (nao substituida) para cobrir os passos 4, 6 e 7 - a
mesma logica incremental ja usada para o LogPort (ADR-0013).

## Referencias

- Module Specifications (Capitulo 21 - CLI)
- SAD 2.2, 5.3, 5.4, 6.2, 6.3, 26.5, 26.6, 29.2
- ADR-0014, ADR-0015 (precedente metodologico para gaps de documentacao)
- ADR-0015 (Application Controller - raiz de composicao consumida aqui)
