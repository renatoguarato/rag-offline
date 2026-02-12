# SPEC v2 — Aplicação Offline RAG Multi-Tenant (Production-Grade)

## Objetivo
Aplicação offline, production-ready, RAG com Ollama, multi-tenant seguro.

## Stack
Python 3.11, FastAPI, Ollama (llama3), Chroma, SQLite.

## Multi-Tenant
Headers:
- X-Tenant-ID
- X-API-KEY

UUID interno por tenant.

## Regras OpenCode
Criar tudo automaticamente.
Não simplificar.
Não remover segurança.

FIM
