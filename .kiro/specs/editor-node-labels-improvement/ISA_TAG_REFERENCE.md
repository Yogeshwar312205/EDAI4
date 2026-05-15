# ISA Instrument Tag Reference

**Standard:** ISA-5.1 (Instrumentation Symbols and Identification)  
**Purpose:** Industry-standard identification for P&ID instruments

---

## Tag Format

```
[First Letter][Modifier Letters]-[Loop Number][Suffix]

Example: FIC-101A
         │││  │││└─ Suffix (optional): A, B, C for duplicates
         │││  ││└── Loop number: Unique identifier
         │││  │└─── Separator: Always a dash
         │││  └──── Modifier: Additional function
         ││└─────── Modifier: Additional function
         │└──────── First letter: Measured variable
         └───────── Always starts with measured variable
```

---

## First Letter (Measured Variable)

| Letter | Variable | Example |
|--------|----------|---------|
| **A** | Analysis | AIC-101 (pH Analyzer) |
| **B** | Burner/Combustion | BIC-201 (Burner Controller) |
| **C** | Conductivity | CIC-301 (Conductivity Controller) |
| **D** | Density/Specific Gravity | DT-401 (Density Transmitter) |
| **E** | Voltage (EMF) | EIC-501 (Voltage Controller) |
| **F** | Flow | FIC-101 (Flow Controller) |
| **G** | Gauging/Position | GIC-601 (Position Controller) |
| **H** | Hand (Manual) | HIC-701 (Manual Controller) |
| **I** | Current | IIC-801 (Current Controller) |
| **J** | Power | JIC-901 (Power Controller) |
| **K** | Time/Schedule | KIC-1001 (Time Controller) |
| **L** | Level | LIC-102 (Level Controller) |
| **M** | Moisture/Humidity | MIC-1101 (Moisture Controller) |
| **N** | User's Choice | NIC-1201 (Custom) |
| **O** | User's Choice | OIC-1301 (Custom) |
| **P** | Pressure | PIC-103 (Pressure Controller) |
| **Q** | Quantity/Event | QIC-1401 (Quantity Controller) |
| **R** | Radiation | RIC-1501 (Radiation Controller) |
| **S** | Speed/Frequency | SIC-104 (Speed Controller) |
| **T** | Temperature | TIC-105 (Temperature Controller) |
| **U** | Multivariable | UIC-1601 (Multi Controller) |
| **V** | Vibration | VIC-1701 (Vibration Controller) |
| **W** | Weight/Force | WIC-106 (Weight Controller) |
| **X** | Unclassified | XIC-1801 (Unclassified) |
| **Y** | Event/State | YIC-1901 (Event Controller) |
| **Z** | Position/Dimension | ZIC-107 (Position Controller) |

---

## Modifier Letters (Function)

| Letter | Function | Example |
|--------|----------|---------|
| **A** | Alarm | FAL-101 (Flow Alarm Low) |
| **C** | Controller | FIC-101 (Flow Indicator Controller) |
| **E** | Element (Sensor) | FE-101 (Flow Element) |
| **G** | Glass/Gauge | LG-102 (Level Glass) |
| **I** | Indicator | FI-101 (Flow Indicator) |
| **K** | Control Station | FIK-101 (Flow Control Station) |
| **L** | Light | FAL-101 (Flow Alarm Light) |
| **O** | Orifice | FO-101 (Flow Orifice) |
| **R** | Recorder | FR-101 (Flow Recorder) |
| **S** | Switch | FSL-101 (Flow Switch Low) |
| **T** | Transmitter | FT-101 (Flow Transmitter) |
| **V** | Valve | FCV-101 (Flow Control Valve) |
| **W** | Well | TW-105 (Temperature Well) |
| **X** | Unclassified | FX-101 (Flow Unclassified) |
| **Y** | Relay/Compute | FY-101 (Flow Relay) |
| **Z** | Final Element | FZ-101 (Flow Final Element) |

---

## Common Combinations

### Flow Instruments
```
FE-101    Flow Element (sensor)
FT-101    Flow Transmitter
FI-101    Flow Indicator
FIC-101   Flow Indicator Controller
FCV-101   Flow Control Valve
FSL-101   Flow Switch Low
FSH-101   Flow Switch High
FAL-101   Flow Alarm Low
FAH-101   Flow Alarm High
FR-101    Flow Recorder
```

### Pressure Instruments
```
PE-103    Pressure Element
PT-103    Pressure Transmitter
PI-103    Pressure Indicator
PIC-103   Pressure Indicator Controller
PCV-103   Pressure Control Valve
PSL-103   Pressure Switch Low
PSH-103   Pressure Switch High
PAL-103   Pressure Alarm Low
PAH-103   Pressure Alarm High
PR-103    Pressure Recorder
```

### Temperature Instruments
```
TE-105    Temperature Element
TT-105    Temperature Transmitter
TI-105    Temperature Indicator
TIC-105   Temperature Indicator Controller
TCV-105   Temperature Control Valve
TSL-105   Temperature Switch Low
TSH-105   Temperature Switch High
TAL-105   Temperature Alarm Low
TAH-105   Temperature Alarm High
TR-105    Temperature Recorder
TW-105    Temperature Well
```

### Level Instruments
```
LE-102    Level Element
LT-102    Level Transmitter
LI-102    Level Indicator
LIC-102   Level Indicator Controller
LCV-102   Level Control Valve
LSL-102   Level Switch Low
LSH-102   Level Switch High
LAL-102   Level Alarm Low
LAH-102   Level Alarm High
LG-102    Level Glass
```

### Analytical Instruments
```
AE-101    Analysis Element (pH, conductivity, etc.)
AT-101    Analysis Transmitter
AI-101    Analysis Indicator
AIC-101   Analysis Indicator Controller
```

---

## Valve Tags

### Control Valves
```
FCV-101   Flow Control Valve
PCV-103   Pressure Control Valve
TCV-105   Temperature Control Valve
LCV-102   Level Control Valve
```

### On/Off Valves
```
XV-201    On/Off Valve (generic)
HV-202    Hand Valve (manual)
MOV-203   Motor Operated Valve
SOV-204   Solenoid Operated Valve
PSV-205   Pressure Safety Valve
PRV-206   Pressure Relief Valve
```

---

## Equipment Tags

### Pumps
```
P-301     Pump (generic)
P-301A    Pump A (when multiple)
P-301B    Pump B (when multiple)
```

### Tanks/Vessels
```
T-401     Tank (generic)
V-402     Vessel
R-403     Reactor
D-404     Drum
```

### Heat Exchangers
```
E-501     Heat Exchanger (generic)
HE-502    Heat Exchanger
C-503     Condenser
```

### Compressors
```
K-601     Compressor
```

### Filters
```
F-701     Filter
```

---

## Loop Numbers

### Numbering Convention
```
FIC-101   First flow control loop
FIC-102   Second flow control loop
FIC-103   Third flow control loop
...
FIC-199   99th flow control loop

PIC-201   First pressure control loop (200 series)
TIC-301   First temperature control loop (300 series)
LIC-401   First level control loop (400 series)
```

### Common Numbering Schemes

**By Area:**
```
100-199   Area 1
200-299   Area 2
300-399   Area 3
```

**By System:**
```
100-199   Feed system
200-299   Reactor system
300-399   Separation system
400-499   Product system
```

**By Unit:**
```
1000-1099 Unit 1
2000-2099 Unit 2
3000-3099 Unit 3
```

---

## Suffixes

### Duplicate Equipment
```
FIC-101A  First controller
FIC-101B  Second controller (backup)
FIC-101C  Third controller (spare)
```

### Location
```
FIC-101N  North location
FIC-101S  South location
FIC-101E  East location
FIC-101W  West location
```

---

## Real-World Examples

### Distillation Column Control
```
FIC-101   Feed flow controller
LIC-102   Bottom level controller
PIC-103   Column pressure controller
TIC-104   Reboiler temperature controller
TIC-105   Overhead temperature controller
FIC-106   Reflux flow controller
```

### Reactor System
```
FIC-201   Reactant A flow controller
FIC-202   Reactant B flow controller
TIC-203   Reactor temperature controller
PIC-204   Reactor pressure controller
LIC-205   Reactor level controller
AIC-206   pH controller
```

### Pump Control
```
P-301     Main pump
P-301A    Pump A (duty)
P-301B    Pump B (standby)
FSL-301   Pump discharge flow switch low
PSL-302   Pump discharge pressure switch low
```

---

## Validation Rules

### Valid Tags
```
✅ FIC-101      (Standard format)
✅ FIC-101A     (With suffix)
✅ PT-2045      (4-digit loop number)
✅ FICA-101     (Multiple modifiers)
✅ FIC-101-N    (With location suffix)
```

### Invalid Tags
```
❌ FIC101       (Missing dash)
❌ 101-FIC      (Wrong order)
❌ fic-101      (Lowercase)
❌ FIC-         (Missing loop number)
❌ -101         (Missing first letter)
❌ FIC-ABC      (Non-numeric loop number)
```

---

## Implementation in Code

### Tag Parsing
```typescript
interface ISATag {
  measuredVariable: string;  // F, P, T, L, etc.
  modifiers: string[];       // I, C, V, etc.
  loopNumber: number;        // 101, 102, etc.
  suffix?: string;           // A, B, C, etc.
  fullTag: string;           // FIC-101A
}

function parseISATag(tag: string): ISATag | null {
  const regex = /^([A-Z])([A-Z]*)-(\d+)([A-Z]?)$/;
  const match = tag.match(regex);
  
  if (!match) return null;
  
  return {
    measuredVariable: match[1],
    modifiers: match[2].split(''),
    loopNumber: parseInt(match[3]),
    suffix: match[4] || undefined,
    fullTag: tag
  };
}
```

### Tag Generation
```typescript
function generateISATag(
  variable: string,
  modifiers: string[],
  loopNumber: number,
  suffix?: string
): string {
  const modifierStr = modifiers.join('');
  const suffixStr = suffix ? suffix : '';
  return `${variable}${modifierStr}-${loopNumber}${suffixStr}`;
}

// Example:
generateISATag('F', ['I', 'C'], 101, 'A')  // Returns: "FIC-101A"
```

### Tag Validation
```typescript
function validateISATag(tag: string): boolean {
  // Must match format: [A-Z][A-Z]*-\d+[A-Z]?
  const regex = /^[A-Z][A-Z]*-\d+[A-Z]?$/;
  return regex.test(tag);
}
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│  ISA TAG QUICK REFERENCE                            │
├─────────────────────────────────────────────────────┤
│  Format: [Variable][Modifiers]-[Number][Suffix]    │
│                                                     │
│  VARIABLES:                                         │
│  F=Flow  P=Pressure  T=Temperature  L=Level        │
│  A=Analysis  S=Speed  W=Weight  V=Vibration        │
│                                                     │
│  MODIFIERS:                                         │
│  I=Indicator  C=Controller  T=Transmitter          │
│  V=Valve  S=Switch  A=Alarm  R=Recorder            │
│                                                     │
│  EXAMPLES:                                          │
│  FIC-101  = Flow Indicator Controller #101         │
│  PT-205   = Pressure Transmitter #205              │
│  TIC-301  = Temperature Indicator Controller #301  │
│  LT-402   = Level Transmitter #402                 │
│  XV-503   = On/Off Valve #503                      │
└─────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Reference:** ISA-5.1-2009 Standard
