# ADR-0013 - Inclusao do Log Engine na Sequencia Oficial de Implementacao

**Status:** Aceito

## Contexto

O SAD (Capitulo 24) define o Log Engine como componente de primeira classe,
e o AI Coding Standards (Sec. 12) exige seu uso desde os primeiros modulos
("nunca utilizar print(); todo registro deve utilizar exclusivamente o Log
Engine"). Entretanto, o Module Specifications nao possuia capitulo ou
Prompt dedicado para sua implementacao — gap identificado durante o
planejamento (Prompt 0) e confirmado na pratica ao implementar o
Configuration Manager (Prompt 2), que precisou de um `LogPort`/adapter
minimo apenas para nao violar a Sec. 12.

## Decisao

Inserir um novo Prompt exclusivo para o Log Engine imediatamente apos o
Configuration Manager e antes do Event Bus.

Nova sequencia oficial:

```
Prompt 0  Planejamento
Prompt 1  Arquitetura Inicial
Prompt 2  Configuration Manager
Prompt 3  Log Engine          <- novo
Prompt 4  Event Bus            (era Prompt 3)
...demais prompts renumerados em +1
```

Escopo do Prompt 3: `LogPort` (camada de aplicacao), adapter Loguru
(infraestrutura), niveis TRACE a CRITICAL, correlacao por `execution_id`,
`module` e `workflow_step` via `bind()`, contexto estruturado, saida em
console e arquivo, rotacao e retencao de arquivos, mascaramento de dados
sensiveis (RNF-001), proibicao de `print()`, testes unitarios e de
integracao.

## Consequencias

Elimina o gap entre SAD, Module Specifications e AI Coding Standards,
reduzindo o risco de retrabalho nos modulos seguintes. O `LogPort` minimo
criado no Prompt 2 foi estendido (nao substituido) para atender este
escopo: os metodos `debug`/`info`/`warning`/`error` do Configuration
Manager continuam validos; `trace`, `critical` e `bind` foram adicionados.
`LoggingConfiguration` (value object de dominio) ganhou campos adicionais
(`file_name`, `rotation`, `retention`, `console_enabled`, `file_enabled`,
`mask_sensitive_data`), todos com defaults, sem quebrar configuracoes
existentes.

## Referencias

- SAD Capitulo 24 (Log Engine)
- AI Coding Standards Sec. 12 (Logging)
- SRS RNF-001 (Seguranca)
- ADR-0011, ADR-0012 (estrutura de diretorios e papel do Event Bus)
- Module Specifications (renumeracao de capitulos a partir deste ADR)
