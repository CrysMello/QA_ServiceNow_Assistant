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

## Status

Scaffolding inicial (Prompt 1 da sequência oficial de implementação). Nenhuma regra
de negócio foi implementada ainda.
