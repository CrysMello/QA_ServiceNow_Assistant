# ADR-0015 - Application Controller: Escopo como Raiz de Composicao

**Status:** Aceito

## Contexto

O Module Specifications define o Capitulo 20 (Prompt 21, apos a renumeracao
da ADR-0013) como "Application Controller - Coordenacao da aplicacao", sem
nenhum outro detalhe tecnico.

O SAD **nao possui nenhum capitulo dedicado ao Application Controller**.
Confirmado por enumeracao de todos os 33 capitulos do documento (SAD
1-33): nenhum se chama "Application Controller". O componente aparece
apenas duas vezes, de passagem, nas tabelas de integracao de outros
capitulos:

- SAD 21.7 (Configuration Manager): "Application Controller -
  Inicializar configuracoes."
- SAD 24.3 (Log Engine, "Log Manager"): depende de "Application
  Controller" para orquestracao.

Nao aparece nos catalogos de componentes (SAD 3.3, 4.5, 7.3), o que
confirma que a arquitetura em si nunca o tratou como um componente de
primeira classe com responsabilidades proprias detalhadas - apenas como
"o que inicializa os outros".

A SAD 3.4 (Fluxo Arquitetural de Alto Nivel) descreve, em alto nivel, a
sequencia que esse "algo que inicializa" deve seguir: usuario executa via
CLI -> configuracao e carregada -> planilha Excel e validada e
interpretada -> Base de Conhecimento e carregada -> Workflow Engine
define a sequencia -> Automation Engine executa no navegador -> Logs,
checkpoints e relatorios sao produzidos durante toda a execucao.

Duas pecas dessa sequencia nao existem e nao tem Prompt oficial no Module
Specifications: "Excel Importer" (mencionado em SAD 7.3/10.3 mas sem
capitulo/Prompt proprio) e a propria CLI (Prompt 22, o proximo, ainda nao
implementado). Isso limita o que o Application Controller pode
legitimamente fazer agora.

## Decisao

Application Controller e implementado como a **raiz de composicao**
(composition root) da aplicacao: o unico modulo autorizado a conhecer e
instanciar diretamente os adaptadores concretos de infraestrutura ja
implementados (todos os outros modulos permanecem desacoplados via
Ports, por design). Sua responsabilidade e estritamente a "coordenacao"
ja documentada (SAD 21.7, 24.3) mais o passo de carregar a Base de
Conhecimento (SAD 3.4) - nada alem disso.

Escopo do Prompt 21:

1. Carregar configuracao (`LoadConfigurationUseCase`, ja existente,
   Prompt 2), a partir de uma `LoadConfigurationRequest` fornecida pelo
   chamador (futura CLI).
2. Inicializar o Log Engine em duas fases: um `LoguruLogAdapter`
   provisorio com `LoggingConfiguration()` padrao (para o proprio
   carregamento de configuracao poder logar), reconstruido com a
   `LoggingConfiguration` real assim que a configuracao carrega -
   resolvendo a dependencia circular "logar o carregamento da
   configuracao que define como logar".
3. Carregar a Base de Conhecimento (`JsonKnowledgeRepository` +
   `KnowledgeManager`, ja existentes, Prompt 18), a partir de
   `configuration.knowledge_base_path`. Falhas de carregamento (manifest
   ausente, versao incompativel) propagam como excecao durante a
   inicializacao, por design ja estabelecido no Knowledge Manager (SAD
   11.7/11.8).
4. Compor os servicos transversais de sessao, todos ja implementados:
   Retry Engine, Checkpoint Engine, Reporting Engine, Export Engine, e o
   Workflow Engine montado sobre os tres primeiros.
5. Gerenciar o ciclo de vida do navegador (`PlaywrightBrowserManager`,
   ja existente) via `start()`/`stop()` e um context manager
   (`with ApplicationController(...) as app:`), garantindo liberacao de
   recursos ao final (SAD 10.7).
6. Expor uma fachada minima para quem for montar e executar workflows:
   `new_page()`, `run_workflow()`, `calculate_metrics()`, `export()`, e
   acesso somente-leitura aos componentes ja compostos (`knowledge`,
   `retry_engine`, `checkpoint_engine`, `reporting_engine`,
   `export_engine`, `workflow_engine`).

**Explicitamente fora de escopo, documentado no proprio modulo:**

- Excel Importer nao existe (sem capitulo SAD, sem Prompt no Module
  Specifications) - Application Controller nao le nem interpreta
  planilhas. `LoadConfigurationRequest.spreadsheet_path` continua sendo
  apenas validado como caminho `.xlsx` existente (ja feito pelo
  Configuration Manager desde o Prompt 2), nao interpretado.
- CLI nao existe ainda (Prompt 22) - Application Controller nao faz
  parsing de argumentos de linha de comando; recebe uma
  `LoadConfigurationRequest` ja montada.
- Pre-composicao de Navigation Engine, Page Recognition, Automation
  Engine, Frame Resolution Engine e Selector Resolution Engine **nao e
  feita aqui**. Esses sao componentes de nivel de ETAPA (usados dentro de
  um `WorkflowStep.action`), nao de sessao - o mesmo principio ja
  aplicado pelo proprio `WorkflowStep` (acoes sao callables fornecidos
  pelo chamador). Quem monta um `Workflow` concreto decide quais desses
  motores usar e os instancia usando `new_page()`/`knowledge` como
  blocos de construcao. Pre-compor todos eles aqui equivaleria a
  implementar a aplicacao inteira neste unico Prompt.
- Construcao de um `Workflow` concreto (ex.: "criar um incidente") nao e
  feita aqui - exigiria dados de teste (do Excel Importer inexistente) e
  regras de negocio do ServiceNow, que todo modulo ja implementado
  explicitamente recusa conter.

## Consequencias

Fecha o gap documental de forma consistente com o restante da
arquitetura, seguindo o mesmo metodo da ADR-0014: nenhuma funcionalidade
e inventada para preencher os gaps de Excel Importer/CLI. Application
Controller fica pronto para ser o ponto de entrada de uma futura CLI
(Prompt 22), que sera responsavel por parsing de argumentos, montagem de
`Workflow`s concretos e, quando existir, integracao com o Excel Importer.

## Referencias

- Module Specifications (Capitulo 20 - Application Controller)
- SAD 21.7, 24.3 (unicas referencias ao componente)
- SAD 3.4 (Fluxo Arquitetural de Alto Nivel)
- SAD 10.7 (liberacao de recursos)
- ADR-0014 (precedente metodologico para gaps de documentacao)
