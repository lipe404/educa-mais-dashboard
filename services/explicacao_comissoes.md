# 📊 Como Funciona o Cálculo de Comissões

> Baseado no arquivo [`commission.py`](file:///c:/Users/toled/Documents/GitHub/educa-mais-dashboard/services/commission.py)

---

## 1. Os Cargos e Suas Porcentagens

Existem dois **tipos de cargos**: `fixed` (fixo) e `partner_based` (baseado em parceiro). O cálculo é **100% linear e independente** (alterar um cargo não afeta as comissões dos demais).

### 🔵 Cargos Fixos — recebem sobre o faturamento líquido da empresa
Calculados diretamente sobre o faturamento líquido restante após a retirada da parte do parceiro (50%) e do imposto (30%).

| Cargo | % Nominal da base líquida | % Real Efetiva (do faturamento bruto) |
|---|---|---|
| Gerente de Expansão | 5.14% | ~**1.80%** |
| Coordenador / Suporte Administrativo | 3.86% | ~**1.35%** |
| Gestor de Tráfego | 0.63% | ~**0.22%** |
| Designer | 0.63% | ~**0.22%** |

### 🟠 Cargos Baseados em Parceiro — recebem sobre cada parceiro específico
Calculados diretamente sobre a receita bruta do parceiro correspondente com a dedução do imposto (30%).

| Cargo | % Nominal sobre o parceiro | % Real Efetiva (do faturamento bruto) |
|---|---|---|
| Captador | 1.60% | ~**1.12%** |
| Suporte de Performance | 1.60% | ~**1.12%** |

---

## 2. O Fluxo Completo — Passo a Passo

Veja o fluxo com um exemplo prático:

> **Cenário:** Receita bruta total de **R$ 100.000** — comissão do parceiro sempre **50%** e imposto de **30%**

```
Receita Bruta Total dos Parceiros
        R$ 100.000
             │
             ▼
  ┌──────────────────────────────┐
  │  (-) Comissões dos Parceiros │  (SEMPRE 50% fixo → R$ 50.000)
  └──────────────────────────────┘
             │
             ▼
  Base para a Equipe = R$ 50.000
             │
             ▼
  ┌──────────────────────────────┐
  │  (-) Imposto: 30% da base   │  → R$ 15.000
  └──────────────────────────────┘
             │
             ▼
  Sobra Líquida da Empresa = R$ 35.000
             │
         ┌───┴───┐
         ▼       ▼
    Cargos Fixos   Cargos de Parceiro
```

---

## 3. Cálculo Detalhado — Cada Etapa

### Etapa 1: Comissão dos Parceiros
A comissão do parceiro é de **50% fixo** sobre sua receita bruta.
```
comissão_parceiro = receita_bruta × 50%
```

### Etapa 2: Base da Equipe
```
base_equipe = receita_bruta − comissão_parceiros
            = R$ 100.000 − R$ 50.000 = R$ 50.000
```

### Etapa 3: Desconto do Imposto (30%)
O imposto incide sobre a base da equipe:
```
imposto = R$ 50.000 × 30% = R$ 15.000
sobra_líquida = R$ 50.000 − R$ 15.000 = R$ 35.000 (ou seja, 35% do bruto total)
```

### Etapa 4: Cargos Fixos
Calculado diretamente sobre a sobra líquida de R$ 35.000 de forma independente:
* **Gerente de Expansão (5.14%)**: `R$ 35.000 × 5.14% = R$ 1.800` (ou **1.80% do bruto**)
* **Coordenador/Suporte (3.86%)**: `R$ 35.000 × 3.86% = R$ 1.350` (ou **1.35% do bruto**)
* **Gestor de Tráfego (0.63%)**: `R$ 35.000 × 0.63% = R$ 220` (ou **0.22% do bruto**)
* **Designer (0.63%)**: `R$ 35.000 × 0.63% = R$ 220` (ou **0.22% do bruto**)

### Etapa 5: Cargos de Parceiro (Captador e Suporte)
Calculado sobre a receita bruta do parceiro (excluindo a parte do parceiro de 50%, ou seja, sobre R$ 50.000) descontando o imposto (30%):
* **Captador (1.60%)**: `R$ 50.000 × 1.60% × (1 - 30%) = R$ 50.000 × 1.12% = R$ 560` (ou **1.12% do bruto**)
* **Suporte de Performance (1.60%)**: `R$ 50.000 × 1.60% × (1 - 30%) = R$ 50.000 × 1.12% = R$ 560` (ou **1.12% do bruto**)

**Soma total real das comissões:**
`1.80% + 1.35% + 0.22% + 0.22% + 1.12% + 1.12% = 5.83%` do bruto total.

---

## 4. Resumo Visual do Destino do Dinheiro

```
R$ 100.000 (Bruto)
├── R$ 50.000 → Parceiros (sempre 50% fixo)
└── R$ 50.000 (Base da equipe)
    ├── R$ 15.000 → Imposto (30%)
    └── R$ 35.000 (Líquido)
        ├── R$ 1.800 → Gerente (1.80%)
        ├── R$ 1.350 → Coordenador (1.35%)
        ├── R$   220 → Gestor de Tráfego (0.22%)
        ├── R$   220 → Designer (0.22%)
        ├── R$   560 → Captador (1.12%)
        ├── R$   560 → Suporte (1.12%)
        └── R$ 29.170 → Empresa (Restante)
```
