# Manual de Desarrollo - Pokemon Añil

Guia para programadores que quieren contribuir al proyecto Pokemon Añil.
Si sabes programar pero nunca tocaste un fangame de Pokemon, este documento es para ti.

---

## Tabla de Contenidos

1. [Que es esto](#1-que-es-esto)
2. [Arquitectura general](#2-arquitectura-general)
3. [Setup del entorno](#3-setup-del-entorno)
4. [Estructura del proyecto](#4-estructura-del-proyecto)
5. [El codigo Ruby (Scripts/)](#5-el-codigo-ruby-scripts)
6. [Los datos del juego (PBS/)](#6-los-datos-del-juego-pbs)
7. [Graficos y audio](#7-graficos-y-audio)
8. [Flujo de compilacion y ejecucion](#8-flujo-de-compilacion-y-ejecucion)
9. [Como hacer cambios comunes](#9-como-hacer-cambios-comunes)
10. [Debug y testing](#10-debug-y-testing)
11. [Glosario](#11-glosario)

---

## 1. Que es esto

Pokemon Añil es un fangame construido sobre **Pokemon Essentials v21.1** (variante "La Base de Sky"), que a su vez corre sobre el motor **MKXP** (una reimplementacion open-source de RPG Maker XP).

En terminos que un programador entiende:
- **MKXP / Game.exe** = El runtime/VM. Equivale a Node.js o la JVM.
- **Pokemon Essentials** = El framework. Equivale a Rails o Spring.
- **Pokemon Añil** = La aplicacion. Tu codigo custom, datos, graficos, audio.

El lenguaje principal es **Ruby** (version ~3.1). No es assembly, no es C, no necesitas un compilador de ROM.

Version actual del juego: **4.0.3**. Mecanicas de **Generacion 9**.

---

## 2. Arquitectura general

```
Game.exe (MKXP runtime)
    |
    +-- Lee mkxp.json (config del motor)
    +-- Lee Game.ini (apunta a Scripts.rxdata)
    +-- Carga Data/Scripts.rxdata (450 scripts Ruby comprimidos en un blob binario)
    |       |
    |       +-- Scripts de infraestructura (MKXP compat, utilidades, save system)
    |       +-- Framework Pokemon Essentials (batallas, pokedex, menus, mapa)
    |       +-- Scripts custom de Añil (dificultad, pokegear, camaras, etc.)
    |       +-- Main loop (Script 449)
    |
    +-- Carga Data/*.dat (datos compilados desde PBS/)
    +-- Carga Graphics/, Audio/, Fonts/ segun necesite
```

**Flujo de datos importante:**

```
PBS/*.txt  --[Compiler scripts]--> Data/*.dat  --[Runtime]--> Juego
Scripts/*.rb --[repack_scripts.py]--> Data/Scripts.rxdata --[MKXP]--> Juego
```

---

## 3. Setup del entorno

### Requisitos
- **Windows 10/11** (el juego corre nativamente con Game.exe)
- **Python 3.8+** (para los scripts de build: extract/repack)
- **Editor de texto** con soporte Ruby (VS Code + extension Ruby recomendado)
- **Git** (el proyecto ya es un repo)

### Primer setup

```bash
# Clonar el repo
git clone https://github.com/Vodkaiser/A-il-Feliz.git
cd "Añil Feliz"

# Los scripts Ruby ya estan extraidos en Scripts/
# Si necesitas re-extraerlos del binario:
cd "Pokemon Anil"
python extract_scripts.py   # Extrae Data/Scripts.rxdata -> Scripts/*.rb

# Para probar el juego: ejecutar Game.exe directamente
```

### Workflow de desarrollo

```
1. Editar archivos .rb en Scripts/
2. Reempaquetar:  python repack_scripts.py
3. Ejecutar Game.exe para probar
```

> **IMPORTANTE:** El juego lee `Data/Scripts.rxdata`, NO los archivos .rb sueltos.
> Siempre debes reempaquetar despues de editar.

---

## 4. Estructura del proyecto

```
Pokemon Anil/
|
+-- Game.exe              # Runtime MKXP (no tocar)
+-- Game.ini              # Config basica del motor
+-- mkxp.json             # Config avanzada (resolucion, titulo, audio)
+-- preload.rb            # Shim de compatibilidad Ruby 3.2+
|
+-- Scripts/              # ** CODIGO FUENTE ** (450 archivos .rb)
|   +-- 001-006           # Settings y configuracion
|   +-- 008-034           # Infraestructura (compat, utils, save, archivos)
|   +-- 035-055           # Core del juego (mapa, personaje, pantalla, stats)
|   +-- 056-062           # Switches y variables del juego
|   +-- 063-081           # Sistema de sprites y renderizado de mapas
|   +-- 082-099           # UI, ventanas, mensajes, audio
|   +-- 100-399           # ** Pokemon Essentials ** (batallas, pokemon, items, pokedex)
|   +-- 400-403           # Compilador PBS -> .dat
|   +-- 405-446           # ** Scripts custom de Añil ** (bolsa, camara, pokegear, etc.)
|   +-- 448-449           # Entry point (Main)
|
+-- PBS/                  # ** DATOS EDITABLES ** (texto plano)
|   +-- pokemon.txt       # Definicion de cada especie
|   +-- moves.txt         # Movimientos
|   +-- items.txt         # Objetos
|   +-- abilities.txt     # Habilidades
|   +-- trainers.txt      # Entrenadores NPC
|   +-- encounters.txt    # Tablas de encuentros salvajes
|   +-- types.txt         # Tipos (Fuego, Agua, etc.)
|   +-- map_metadata.txt  # Propiedades de cada mapa
|   +-- map_connections.txt # Conexiones entre mapas
|   +-- pokemon_forms.txt # Formas alternativas (Megas, Alola, etc.)
|   +-- regional_dexes.txt # Pokedex regional
|   +-- berry_plants.txt  # Bayas
|   +-- trainer_types.txt # Tipos de entrenador (Lider, Rocket, etc.)
|   +-- battle_facility_lists.txt # Torre Batalla
|
+-- Data/                 # Datos compilados (binarios, NO editar directamente)
|   +-- Scripts.rxdata    # Scripts Ruby comprimidos
|   +-- *.dat             # Datos compilados desde PBS
|   +-- Map001-220.rxdata # Mapas (editados con RPG Maker XP o herramientas)
|
+-- Graphics/             # ~320 MB de imagenes
|   +-- Pokemon/          # Sprites de Pokemon (Front, Back, Shiny, Icons, etc.)
|   +-- Tilesets/         # Tiles para construir mapas
|   +-- Characters/       # Sprites de personajes en el overworld
|   +-- Trainers/         # Sprites de entrenadores en batalla
|   +-- Battlers/         # Otros sprites de batalla
|   +-- UI/               # Interfaz de usuario
|   +-- Titles/           # Pantalla de titulo
|   +-- Pictures/         # Imagenes varias
|
+-- Audio/                # ~345 MB de sonido
|   +-- BGM/              # Musica de fondo
|   +-- BGS/              # Sonidos ambientales
|   +-- ME/               # Jingles (victoria, curacion, etc.)
|   +-- SE/               # Efectos de sonido
|
+-- Fonts/                # Fuentes tipograficas custom
|
+-- extract_scripts.py    # Herramienta: Scripts.rxdata -> Scripts/*.rb
+-- repack_scripts.py     # Herramienta: Scripts/*.rb -> Scripts.rxdata
+-- search_events.py      # Herramienta: buscar texto en eventos de mapas
+-- dump_events_detail.py # Herramienta: volcar eventos de mapas para analisis
```

---

## 5. El codigo Ruby (Scripts/)

### Convencion de nombres

Los archivos siguen el patron `NNN_NombreDelScript.rb` donde NNN es el indice de carga.
El orden importa: se ejecutan secuencialmente del 000 al 449.

### Zonas clave del codigo

#### Settings (002_Settings.rb)
Configuracion global del juego. Aqui se definen constantes como:
```ruby
module Settings
  GAME_VERSION = "4.0.3"
  MECHANICS_GENERATION = 9       # Mecanicas de gen 9
  MAXIMUM_LEVEL = 100
  MAX_PARTY_SIZE = 6
  SHINY_POKEMON_CHANCE = 65      # sobre 65536
  MAX_MONEY = 999_999_999
end
```
Si necesitas cambiar un parametro global del juego, probablemente esta aqui.

#### Entry Point (449_Main.rb)
El bucle principal:
```ruby
def mainFunctionDebug
  MessageTypes.load_default_messages if FileTest.exist?("Data/messages_core.dat")
  PluginManager.runPlugins
  Compiler.main                    # Compila PBS si hay cambios
  Game.initialize
  Game.set_up_system
  $scene = pbCallTitle             # Carga pantalla de titulo
  $scene.main until $scene.nil?    # Game loop
end
```

#### Pokemon Essentials (100-399)
El grueso del framework. Algunos archivos importantes:
- **Batallas:** Buscar scripts con "Battle" en el nombre
- **Pokemon (datos en memoria):** Scripts con "Pokemon" (la clase Pokemon, stats, evolucion)
- **Movimientos:** Scripts con "Move" (ejecucion de movimientos en batalla)
- **Items:** Scripts con "Item" o "Bag"
- **Pokedex:** Scripts con "Pokedex"
- **Overworld:** Scripts con "Event", "Map", "Player"

#### Scripts custom de Añil (405-446)
Funcionalidades propias del fangame:
- Sistema de dificultad
- Pokegear custom (mapa, telefono, temas, reloj)
- Camara
- Debug tools custom
- Formchangers (cambios de forma)

### Patrones de codigo comunes

**Funciones con prefijo `pb`:** Convencion de Essentials. `pb` = "PokeBattle" historicamente, pero se usa para todo. Ejemplo: `pbMessage("Hola")`, `pbFadeOutIn { ... }`.

**Variables globales importantes:**
- `$player` - El jugador actual
- `$game_map` - El mapa actual
- `$scene` - La escena activa (titulo, mapa, batalla, menu)
- `$DEBUG` - Si el modo debug esta activo
- `$Trainer` - Alias para el jugador (legacy)

**Switches y Variables:**
El juego usa "switches" (booleanos) y "variables" (enteros) globales para trackear progreso. Se definen por numero y se acceden asi:
```ruby
$game_switches[42] = true     # Activar switch 42
$game_variables[10] = 5       # Variable 10 = 5
```

---

## 6. Los datos del juego (PBS/)

PBS = "Pokemon Base Stats" (nombre historico). Son archivos de texto plano con formato INI-like.

### Formato general

```ini
[IDENTIFICADOR_INTERNO]
Propiedad = Valor
OtraPropiedad = Valor1,Valor2
```

### Ejemplo: Definir un Pokemon (pokemon.txt)

```ini
[BULBASAUR]
Name = Bulbasaur
Types = GRASS,POISON
BaseStats = 45,49,49,45,65,65    # HP,Atk,Def,Spd,SpAtk,SpDef
GenderRatio = Female50Percent
Abilities = OVERGROW
HiddenAbilities = CHLOROPHYLL
Moves = 1,TACKLE,1,GROWL,6,VINEWHIP,...  # nivel,movimiento,nivel,movimiento,...
EggGroups = Monster,Grass
Evolutions = IVYSAUR,Level,16
Pokedex = Descripcion para la Pokedex.
```

### Ejemplo: Definir un movimiento (moves.txt)

```ini
[MEGAHORN]
Name = Megacuerno
Type = BUG
Category = Physical
Power = 120
Accuracy = 85
TotalPP = 10
Target = NearOther
FunctionCode = None
Flags = Contact,CanProtect,CanMirrorMove
Description = Violenta embestida con cuernos imponentes.
```

### Ejemplo: Definir un entrenador (trainers.txt)

```ini
[AZUL1,Azul,1]                  # [ID_interno, Nombre_visible, Variante]
LoseText = Bah! La suerte del principiante!
Pokemon = CHARMANDER,5           # Especie, Nivel
```

### Compilacion de PBS

Los archivos PBS se compilan a `.dat` binarios. Esto pasa automaticamente al iniciar el juego en modo debug, o manualmente via el sistema Compiler (scripts 400-403).

> **Para editar datos de Pokemon, movimientos, items, entrenadores, etc., edita los PBS.**
> No necesitas tocar Ruby para cambios de datos.

---

## 7. Graficos y audio

### Sprites de Pokemon

```
Graphics/Pokemon/
  +-- Front/          # Sprite frontal (lo que ve el rival)
  +-- Front shiny/    # Version shiny del frontal
  +-- Back/           # Sprite trasero (lo que ve el jugador)
  +-- Back shiny/     # Version shiny del trasero
  +-- Icons/          # Iconos pequeños (menus, PC)
  +-- Footprints/     # Huellas (Pokedex)
  +-- Eggs/           # Sprites de huevos
  +-- Shadow/         # Sombras en batalla
```

Los archivos se nombran por numero nacional o nombre interno.

### Tilesets y mapas

Los mapas se construyen con tilesets (conjuntos de tiles de 32x32 px).
Los mapas en si (`Data/MapNNN.rxdata`) son binarios creados con RPG Maker XP.
Los tilesets estan en `Graphics/Tilesets/`.

### Audio

- **BGM/**: Musica de fondo. Formatos: .ogg, .mid, .mp3
- **SE/**: Efectos de sonido. Formato: .ogg, .wav
- **ME/**: Jingles cortos (nivel arriba, captura, etc.)
- **BGS/**: Sonidos ambiente (lluvia, viento, etc.)

---

## 8. Flujo de compilacion y ejecucion

### Diagrama completo

```
                    DESARROLLO
                    ==========

  Scripts/*.rb                    PBS/*.txt
       |                               |
       | python repack_scripts.py      | (auto al iniciar en debug)
       v                               v
  Data/Scripts.rxdata             Data/*.dat
       |                               |
       +----------- RUNTIME -----------+
                       |
                   Game.exe
                   (MKXP motor)
                       |
                   mkxp.json (config)
                   Game.ini  (config)
                       |
                   Carga Ruby scripts
                       |
                   Carga datos (.dat)
                       |
                   Carga graficos/audio on-demand
                       |
                   JUEGO CORRIENDO
```

### Pasos concretos para probar un cambio

**Si editaste un script Ruby:**
```
Doble click en compilar_y_jugar.bat
```
Este .bat reempaqueta los scripts y lanza el juego automaticamente.
Si hay un error en el reempaquetado, te avisa y no abre el juego.

Internamente hace:
```bash
python repack_scripts.py    # Empaqueta Scripts/*.rb -> Data/Scripts.rxdata
start Game.exe              # Lanza el juego
```

**Si editaste un archivo PBS:**
```
# Solo ejecutar Game.exe (o el .bat)
# El compilador interno detecta cambios y recompila automaticamente
```

**Si cambiaste un grafico o audio:**
```
# Solo reemplazar el archivo con el nuevo
# No hay compilacion, se carga directamente en runtime
```

---

## 9. Como hacer cambios comunes

### Cambiar stats base de un Pokemon
1. Abrir `PBS/pokemon.txt`
2. Buscar `[NOMBRE_INTERNO]`
3. Modificar `BaseStats = HP,Atk,Def,Spd,SpAtk,SpDef`
4. Ejecutar el juego (recompila automaticamente en debug)

### Añadir un nuevo movimiento
1. Añadir entrada en `PBS/moves.txt` con el formato estandar
2. Si necesita logica especial, crear/editar un `FunctionCode` en los scripts de batalla
3. Asignar el movimiento a Pokemon en `PBS/pokemon.txt` (campo `Moves` o `TutorMoves`)

### Modificar un entrenador
1. Abrir `PBS/trainers.txt`
2. Buscar por su ID interno (ej: `[AZUL1,Azul,1]`)
3. Cambiar Pokemon, niveles, objetos, texto de derrota

### Cambiar logica de batalla
1. Buscar en `Scripts/` archivos relacionados con "Battle"
2. Las funciones de movimientos usan `FunctionCode` que mapea a clases Ruby
3. Editar la clase correspondiente, reempaquetar, probar

### Añadir un nuevo script custom
1. Crear archivo `Scripts/NNN_NombreScript.rb` (elegir un numero libre)
2. El numero determina el orden de carga (scripts anteriores ya estan disponibles)
3. Reempaquetar con `python repack_scripts.py`

### Buscar texto en eventos de mapas
```bash
python search_events.py "texto a buscar"
```

### Volcar eventos de un mapa para analisis
```bash
python dump_events_detail.py
```

---

## 10. Debug y testing

### Modo Debug
El juego tiene un modo debug integrado. Cuando esta activo (`$DEBUG = true`):
- Los PBS se recompilan automaticamente si detecta cambios
- Se habilitan herramientas de debug en el menu
- Se puede acceder a un editor de Pokemon, items, teletransporte, etc.

### Atajos utiles en debug
- **F12**: Soft reset (reiniciar el juego sin cerrar)
- **F1**: Menu de configuracion de controles

### Logs y errores
Si el juego crashea, genera un error Ruby con stack trace. Los errores suelen indicar:
- Archivo y linea exacta del error
- Tipo de excepcion
- Contexto del error

---

## 11. Glosario

| Termino | Significado |
|---------|-------------|
| **MKXP** | Motor open-source que reemplaza RPG Maker XP. Ejecuta Ruby + renderiza graficos. |
| **RGSS** | Ruby Game Scripting System. API original de RPG Maker XP. MKXP la reimplementa. |
| **Essentials** | Framework comunitario de Pokemon para RPG Maker. La base sobre la que se construye. |
| **La Base de Sky (LBDS)** | Fork hispanohablante de Pokemon Essentials v21.1. La version que usa este proyecto. |
| **PBS** | Pokemon Base Stats. Archivos de texto plano con datos del juego. |
| **Scripts.rxdata** | Blob binario que contiene todos los scripts Ruby comprimidos con zlib. |
| **MapNNN.rxdata** | Archivo binario de un mapa. Contiene tiles, eventos, propiedades. |
| **Switches** | Variables booleanas globales del juego. Controlan progresion y estados. |
| **Variables** | Variables enteras globales del juego. Controlan contadores, IDs, etc. |
| **FunctionCode** | Identificador que conecta un movimiento PBS con su logica Ruby en batalla. |
| **pb (prefijo)** | Convencion de Essentials para funciones publicas. Historicamente "PokeBattle". |
| **Tileset** | Imagen con tiles de 32x32 px usados para construir mapas. |
| **Events** | Objetos interactivos en los mapas (NPCs, items, triggers, puertas, etc.). |
| **rxdata** | Formato binario de RPG Maker. Ruby Marshal serializado. |
| **Overworld** | El mundo del juego fuera de batalla (caminar, hablar con NPCs, etc.). |

---

## Recursos externos

- [Wiki de Pokemon Essentials](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki) - Documentacion del framework base
- [MKXP-Z](https://github.com/mkxp-z/mkxp-z) - El runtime/motor del juego
- [La Base de Sky](https://pokemon-la-base-de-sky.fandom.com/es/wiki/Pokemon_La_Base_de_Sky) - Wiki del fork hispanohablante

---

*Documento generado para el proyecto Pokemon Añil v4.0.3*
