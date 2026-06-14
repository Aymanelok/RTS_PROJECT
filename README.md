# 🚦 Smart Traffic Controller — ROS2

> Système de contrôle de feux de signalisation **Hard Real-Time** basé sur ROS2.  
> Architecture 4-nœuds | Cycle ≤ 200 ms | Vérification formelle de sécurité

---

## 📁 Structure du Projet

```
smart_traffic/
├── smart_traffic/
│   ├── __init__.py
│   ├── sensor_node.py        ← Capteur trafic (10 Hz)
│   ├── controller_node.py    ← Décision feux (≤ 80 ms)
│   ├── actuator_node.py      ← Application + sécurité (≤ 50 ms)
│   └── dashboard_node.py     ← Tableau de bord temps réel
├── launch/
│   └── traffic_launch.py     ← Lancement automatique 4 nœuds
├── test/
│   └── simulation.py         ← Simulation Phase 1 (sans ROS2)
├── package.xml
├── setup.py
└── README.md
```

---

## ⚙️ Architecture du Système

```
┌─────────────────────────────────────────────────────────────┐
│                  SMART TRAFFIC CONTROLLER                    │
│                                                              │
│  ┌──────────────┐    /traffic_data    ┌──────────────────┐  │
│  │  sensor_node │ ──────────────────► │ controller_node  │  │
│  │   (10 Hz)    │                     │  (décision ≤80ms)│  │
│  └──────────────┘                     └────────┬─────────┘  │
│         │                                      │            │
│  /sensor_stats                        /light_commands       │
│         │                                      │            │
│         ▼                             ┌────────▼─────────┐  │
│  ┌──────────────┐   /actuator_stats   │  actuator_node   │  │
│  │ dashboard_   │ ◄────────────────── │  (applic. ≤50ms) │  │
│  │    node      │ ◄── /ctrl_stats     │  + safety check  │  │
│  │  (viz RT)    │ ◄── /feedback       └──────────────────┘  │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### Topics ROS2

| Topic | Type | Émetteur | Abonnés |
|-------|------|----------|---------|
| `/traffic_data` | `std_msgs/String` (JSON) | sensor | controller |
| `/light_commands` | `std_msgs/String` (JSON) | controller | actuator |
| `/actuator_feedback` | `std_msgs/String` (JSON) | actuator | dashboard |
| `/sensor_stats` | `std_msgs/String` (JSON) | sensor | dashboard |
| `/controller_stats` | `std_msgs/String` (JSON) | controller | dashboard |
| `/actuator_stats` | `std_msgs/String` (JSON) | actuator | dashboard |

---

## 🕐 Contraintes Temps Réel

| Nœud | Période | Deadline | WCET estimé |
|------|---------|----------|-------------|
| sensor_node | 100 ms | 100 ms | < 5 ms |
| controller_node | event-driven | 80 ms | < 10 ms |
| actuator_node | event-driven | 50 ms | < 5 ms |
| **Cycle E2E** | — | **200 ms** | < 20 ms |

---

## 🧠 Algorithme de Contrôle

### Priorité Maximale avec Hysteresis

```
function decide(counts[N,S,E,O]) → direction_verte:
    best ← argmax(counts)
    
    if active_green is None:
        return INIT(best)
    
    if green_duration ≥ MAX_GREEN (30s):
        return FORCE_SWITCH(best)        # équité
    
    if green_duration < MIN_GREEN (5s):
        return HOLD(active_green)        # anti-flicker
    
    if best ≠ active_green AND
       counts[best] - counts[active_green] ≥ HYSTERESIS (3):
        return SWITCH(best)              # changement justifié
    
    return HOLD(active_green)
```

### Paramètres de l'algorithme

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `MIN_GREEN_TIME` | 5 s | Temps minimum de vert (anti-oscillation) |
| `MAX_GREEN_TIME` | 30 s | Temps maximum de vert (équité) |
| `HYSTERESIS` | 3 véh. | Seuil min de différence pour changer |
| `MAX_VEHICLES` | 30 | Saturation capteur |

---

## 📈 Analyse de Schedulabilité

### 1. Rate Monotonic (RM)

L'algorithme RM assigne les priorités selon les périodes (période courte = priorité haute).

**Tâches du système :**

| Tâche | Période Tᵢ | WCET Cᵢ | Utilisation Uᵢ = Cᵢ/Tᵢ |
|-------|-----------|---------|------------------------|
| τ₁ sensor | 100 ms | 5 ms | 0.050 |
| τ₂ controller | 100 ms* | 10 ms | 0.100 |
| τ₃ actuator | 100 ms* | 5 ms | 0.050 |
| **Total** | | | **U = 0.200** |

*Le contrôleur et l'actionneur sont event-driven, on modélise leur pire cas avec T = 100 ms.

**Test d'admission RM (Liu & Layland, 1973) :**

```
Borne de Liu & Layland pour n=3 tâches :
    U_RM = n × (2^(1/n) - 1) = 3 × (2^(1/3) - 1) ≈ 0.779

Condition : U_total ≤ U_RM
           0.200 ≤ 0.779  ✅ SYSTÈME SCHEDULABLE sous RM
```

**Analyse exact (Response Time Analysis) pour τ₃ (priorité la plus basse) :**

```
R₃⁰ = C₃ = 5 ms

R₃¹ = C₃ + ⌈R₃⁰/T₁⌉×C₁ + ⌈R₃⁰/T₂⌉×C₂
     = 5 + ⌈5/100⌉×5 + ⌈5/100⌉×10
     = 5 + 5 + 10 = 20 ms

R₃² = 5 + ⌈20/100⌉×5 + ⌈20/100⌉×10
     = 5 + 5 + 10 = 20 ms  → convergence

R₃ = 20 ms ≤ D₃ = 50 ms ✅
```

**Conclusion RM : Système schedulable avec marge confortable (20 ms vs deadline 50 ms).**

---

### 2. Earliest Deadline First (EDF)

EDF est optimal pour les systèmes monoprocesseur. La condition nécessaire et suffisante est :

```
Condition EDF (pour tâches périodiques à deadlines = périodes) :
    U_total ≤ 1.0

    0.200 ≤ 1.000  ✅ SYSTÈME SCHEDULABLE sous EDF

Charge CPU disponible pour extensions : 80% de marge !
```

**Comparaison RM vs EDF :**

| Critère | RM | EDF |
|---------|----|----|
| Optimalité | Non optimal | Optimal (monoprocesseur) |
| Complexité | O(1) (priorités fixes) | O(log n) (dynamique) |
| Prédictibilité | Très prévisible | Moins prévisible sous surcharge |
| **Verdict système** | ✅ Schedulable | ✅ Schedulable |

---

## 🔒 Vérification Formelle

### Propriété de Sécurité Critique

> **P_safety** : *"À tout instant t, au plus une direction peut avoir le feu VERT."*

**Formalisation en logique temporelle (LTL) :**

```
□ (Σ_{d ∈ {N,S,E,O}} [lights[d] = GREEN]) ≤ 1
```

*"Globalement, la somme des feux verts est toujours ≤ 1."*

### Preuve par Invariant de Programme

**Invariant I** : `|{d | lights[d] = GREEN}| ≤ 1`

**Initialisation :**
```
∀d ∈ {N,S,E,O} : lights[d] = RED
→ |{d | lights[d] = GREEN}| = 0 ≤ 1  ✓
```

**Conservation (méthode set_green(direction)) :**
```
Avant appel : I est vrai (hypothèse d'induction)

Corps de set_green(d*) :
  ∀d ∈ DIRECTIONS :
    lights[d] ← (d == d*) ? GREEN : RED
  
Après appel :
  {d | lights[d] = GREEN} = {d*}  (ensemble singleton)
  → |{d | lights[d] = GREEN}| = 1 ≤ 1  ✓
```

**Observation clé :** La fonction `set_green` est la SEULE opération modifiant l'état des feux. Elle est atomique et garantit structurellement la propriété.

**Vérification runtime :** Le `SafetyMonitor` dans `actuator_node.py` vérifie la propriété à CHAQUE commande reçue et rejette toute commande invalide, ajoutant une couche de défense en profondeur.

**Résultat simulation 60s :** 0 violation détectée sur 602 cycles. ✅

---

## 🚀 Installation & Lancement

### Prérequis

```bash
# ROS2 Humble (Ubuntu 22.04) ou supérieur
sudo apt install ros-humble-desktop python3-colcon-common-extensions

# Dépendances Python
pip install matplotlib pandas numpy
```

### Build

```bash
cd ~/ros2_ws/src
git clone <repo_url> smart_traffic
cd ~/ros2_ws
colcon build --packages-select smart_traffic
source install/setup.bash
```

### Lancement ROS2

```bash
# Lancement standard (4 nœuds)
ros2 launch smart_traffic traffic_launch.py

# Avec niveau de log debug
ros2 launch smart_traffic traffic_launch.py log_level:=debug

# Sans dashboard (headless)
ros2 launch smart_traffic traffic_launch.py enable_dashboard:=false
```

### Simulation Phase 1 (sans ROS2)

```bash
cd smart_traffic/test

# Simulation 60 secondes
python3 simulation.py

# Simulation personnalisée avec logs détaillés
python3 simulation.py --duration 120 --verbose
```

### Surveillance des topics

```bash
# Voir les données de trafic
ros2 topic echo /traffic/traffic_data

# Surveiller les commandes feux
ros2 topic echo /traffic/light_commands

# Fréquence de publication
ros2 topic hz /traffic/traffic_data
```

---

## 📊 Résultats de Simulation (60 secondes)

```
Cycles        : 602
Capteur P95   : 0.09 ms   (deadline 100 ms) ✅
Contrôleur P95: 0.04 ms   (deadline  80 ms) ✅
Actionneur P95: 0.01 ms   (deadline  50 ms) ✅
E2E P95       : 0.14 ms   (deadline 180 ms) ✅
Deadline miss : 0/602 = 0.00% sur tous les nœuds ✅
Violations    : 0         (invariant de sécurité) ✅
Changements   : 9 changements de phase en 60s
```

---

## 👥 Équipe & Contexte

Projet universitaire — Systèmes Embarqués Temps Réel  
Niveau Master Ingénieur | ROS2 Humble | Python 3.10+
