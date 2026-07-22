# QA ServiceNow Assistant

Aplicação CLI que automatiza a criação de artefatos do ServiceNow Test Management
(Plano, Ciclo, Conjunto e Casos de Teste) a partir de uma planilha estruturada e de
uma Base de Conhecimento somente-leitura produzida pelo ServiceNow Knowledge Builder.

## Arquitetura

O projeto segue Clean Architecture e Hexagonal Architecture (Ports & Adapters),
conforme definido no Software Architecture Document (SAD) e nos Architecture
Decision Records (ADRs) do projeto — ver `docs/adr/`.

Estrutura de diretórios oficial: ADR-0011.
Papel do Event Bus: ADR-0012 (mecanismo complementar; o Workflow Engine permanece
o orquestrador principal via chamadas diretas por portas).
Sequência oficial de implementação (com Log Engine incluído): ADR-0013.

## Sequência oficial de implementação

```
Prompt 0  Planejamento
Prompt 1  Arquitetura Inicial            [concluído]
Prompt 2  Configuration Manager          [concluído]
Prompt 3  Log Engine                     [concluído]
Prompt 4  Event Bus                      [próximo]
...
```

## Status

Configuration Manager e Log Engine implementados e testados (50 testes
unitários e de integração). Demais módulos ainda não implementados.

## Testes

```
pytest
```

Não requer instalação do pacote: `pyproject.toml` configura `pythonpath = ["src"]`.
