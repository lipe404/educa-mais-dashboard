# 📊 Como Funciona o Cálculo de Comissões

> Baseado no arquivo [`commission.py`](file:///c:/Users/toled/Documents/GitHub/educa-mais-dashboard/services/commission.py)

---

## 1. Os Cargos e Suas Porcentagens

Existem dois **tipos de cargos**: `fixed` (fixo) e `partner_based` (baseado em parceiro).

### 🔵 Cargos Fixos — recebem sobre o pool geral da equipe

| Cargo | % Bruta |
|---|---|
| Gerente de Expansão | 3.0% |
| Coordenador / Suporte Administrativo | 2.5% |
| Gestor de Tecnologia | 1.5% |
| Gestor de Tráfego | 1.0% |
| Designer | 1.0% |
| **TOTAL MÁXIMO FIXO** | **9.0%** *(teto: 13%)* |

> [!NOTE]
> O código define `MAX_FIXED_TEAM_PERCENTAGE = 13.0`. O **teto total de toda a equipe é 13%** da base líquida após imposto.

### 🟠 Cargos Baseados em Parceiro — recebem sobre cada parceiro específico

| Cargo | % sobre a receita do parceiro |
|---|---|
| Captador | 1.0% |
| Suporte de Performance | 3.0% |

> [!IMPORTANT]
> O Captador e o Suporte de Performance **não recebem do pool geral**. Eles são atribuídos individualmente a cada parceiro e recebem sobre a receita daquele parceiro.

---

## 2. O Fluxo Completo — Passo a Passo

Veja o fluxo com um exemplo prático:

> **Cenário:** 2 parceiros gerando receita bruta total de **R$ 100.000** — comissão do parceiro sempre **50%**

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
  Restante após imposto = R$ 35.000
             │
             ▼
  ┌──────────────────────────────┐
  │  Pool da Equipe = 13% disso │  → R$ 4.550
  └──────────────────────────────┘
             │
        ┌────┴────┐
        ▼         ▼
   Fixos      Partner-Based
 (proporc.)   (Captador/Suporte)
```

---

## 3. Cálculo Detalhado — Cada Etapa

### Etapa 1: Comissão dos Parceiros

A comissão de todo e qualquer parceiro é **sempre 50% fixo** sobre sua receita. Não há variação por parceiro.

```
comissão_parceiro = receita_parceiro × 50%
```

**Exemplo:**
- Parceiro A: R$ 60.000 × 50% = **R$ 30.000**
- Parceiro B: R$ 40.000 × 50% = **R$ 20.000**
- Total de comissão paga a parceiros: **R$ 50.000**

---

### Etapa 2: Base da Equipe

```
base_equipe = receita_total − comissão_total_parceiros
            = R$ 100.000 − R$ 50.000 = R$ 50.000
```

---

### Etapa 3: Desconto do Imposto (30%)

```
imposto    = base_equipe × 30%  = R$ 50.000 × 0,30 = R$ 15.000
líquido    = base_equipe − imposto = R$ 50.000 − R$ 15.000 = R$ 35.000
```

> [!WARNING]
> O imposto é aplicado **depois** de descontar as comissões dos parceiros, mas **antes** de calcular qualquer comissão da equipe interna.

---

### Etapa 4: Pool de 13% para a Equipe

```
pool_equipe = líquido × 13% = R$ 35.000 × 0,13 = R$ 4.550
```

Este é o **bolo total** que será dividido entre toda a equipe.

---

### Etapa 5: Cargos Baseados em Parceiro (Captador e Suporte)

Calculados **primeiro**, direto sobre a receita de cada parceiro, com desconto do imposto já embutido:

```
comissão_captador(parceiro X) = receita_X × 1% × (1 − 30%)
                               = receita_X × 1% × 0,70

comissão_suporte(parceiro X)  = receita_X × 3% × (1 − 30%)
                               = receita_X × 3% × 0,70
```

**Exemplo — Parceiro A (R$ 60.000):**
- Captador:          R$ 60.000 × 1% × 0,70 = **R$ 420**
- Suporte Perf.:     R$ 60.000 × 3% × 0,70 = **R$ 1.260**

**Exemplo — Parceiro B (R$ 40.000):**
- Captador:          R$ 40.000 × 1% × 0,70 = **R$ 280**
- Suporte Perf.:     R$ 40.000 × 3% × 0,70 = **R$ 840**

**Total partner-based = R$ 420 + R$ 1.260 + R$ 280 + R$ 840 = R$ 2.800**

> [!NOTE]
> As receitas usadas aqui (R$ 60k e R$ 40k) já **excluem** a comissão de 50% do parceiro. Ou seja, são os valores brutos que chegam à plataforma, dos quais metade foi para o parceiro e metade entra como base de cálculo da equipe.

---

### Etapa 6: Disponível para Cargos Fixos

```
disponível_fixos = pool_equipe − total_partner_based
                 = R$ 4.550 − R$ 2.800 = R$ 1.750
```

---

### Etapa 7: Distribuição Proporcional dos Fixos

Cada membro de cargo fixo recebe proporcionalmente à sua % dentro do total de % fixa da equipe.

**Exemplo com equipe completa:**

| Membro | Cargo | % cargo | Proporção | Comissão bruta |
|---|---|---|---|---|
| João | Gerente de Expansão | 3.0% | 3/9 = 33.3% | R$ 1.750 × 33.3% = **R$ 583** |
| Ana | Coord./Suporte | 2.5% | 2.5/9 = 27.8% | R$ 1.750 × 27.8% = **R$ 487** |
| Carlos | Gestor Tecnologia | 1.5% | 1.5/9 = 16.7% | R$ 1.750 × 16.7% = **R$ 292** |
| Maria | Gestor Tráfego | 1.0% | 1/9 = 11.1% | R$ 1.750 × 11.1% = **R$ 194** |
| Pedro | Designer | 1.0% | 1/9 = 11.1% | R$ 1.750 × 11.1% = **R$ 194** |

> Fórmula exata do código:
> ```
> proportional_share = (% do membro / % total fixo) × 13.0
> comissão = líquido × proportional_share / 100
> ```

---

### Etapa 8: Normalização (caso o pool fixo estoure)

Se o total de comissões fixas calculadas ultrapassar o disponível, um **fator de normalização** é aplicado:

```
fator = disponível_fixos / soma_fixos_calculados
comissão_normalizada = comissão_original × fator
```

Isso garante que nunca se pague mais do que o orçado.

---

## 4. Porcentagem Real Efetiva por Cargo

Sobre a **receita bruta total**, qual é a % real que cada cargo recebe?

| Cargo | % Nominal | Base de cálculo | % Real efetiva (aprox.) |
|---|---|---|---|
| Gerente de Expansão | 3% do pool fixo | 13% × líquido | ~**0.58%** do bruto |
| Coord./Suporte | 2.5% do pool fixo | 13% × líquido | ~**0.49%** do bruto |
| Gestor Tecnologia | 1.5% do pool fixo | 13% × líquido | ~**0.29%** do bruto |
| Gestor Tráfego | 1% do pool fixo | 13% × líquido | ~**0.19%** do bruto |
| Designer | 1% do pool fixo | 13% × líquido | ~**0.19%** do bruto |
| Captador | 1% por parceiro | receita × 70% | ~**0.70%** do bruto do parceiro |
| Suporte de Performance | 3% por parceiro | receita × 70% | ~**2.10%** do bruto do parceiro |

> [!TIP]
> A % real é menor que a nominal porque ela incide sobre a **base líquida** (após descontar comissão de parceiros e imposto de 30%), não sobre o bruto total.

---

## 5. Resumo Visual do Destino do Dinheiro

```
R$ 100.000 (Bruto)
├── R$ 50.000 → Parceiros (sempre 50% fixo)
└── R$ 50.000 (Base da equipe)
    ├── R$ 15.000 → Imposto (30%)
    └── R$ 35.000 (Líquido)
        ├── R$ 4.550 → Pool da equipe (13%)
        │   ├── R$ 2.800 → Captadores + Suporte (partner-based)
        │   └── R$ 1.750 → Fixos (proporcional por cargo)
        └── R$ 30.450 → Empresa (87% restante)
```

---

## 6. Pontos Importantes

> [!NOTE]
> **Um membro pode ter múltiplos cargos.** Nesse caso, suas porcentagens se somam. Por exemplo, alguém que é Gerente (3%) + Designer (1%) recebe a soma dos dois na distribuição proporcional.

> [!WARNING]
> **Captador e Suporte são exclusivos por parceiro.** Cada parceiro tem apenas um Captador e um Suporte atribuído. Se não houver atribuição, aquele percentual simplesmente não é pago a ninguém — ele fica no pool.

> [!IMPORTANT]
> **O imposto (30%) é configurável.** O parâmetro `tax_rate` pode ser alterado na chamada do motor de comissões. O padrão atual é 30%.
