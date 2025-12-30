# Product Requirements Document: Monopoly Board Game

## 1. Project Overview

### Description
A graphical implementation of the classic Monopoly board game in Python using Tkinter. Players take turns rolling dice, moving around the board, buying properties, collecting rent, and competing to bankrupt their opponents.

### Target Platform
- **Primary**: Python GUI (Tkinter)
- **Secondary**: Command-Line Interface (CLI) for testing
- **Python Version**: 3.10+

### Core Objectives
1. Implement all standard Monopoly rules faithfully
2. Support 2-4 human players
3. Provide an intuitive graphical interface with visual board
4. Create modular, extensible codebase

---

## 2. Game Rules Summary

### Board Layout (40 Spaces)
| Position | Type | Name |
|----------|------|------|
| 0 | Corner | GO |
| 1-2 | Property | Mediterranean Ave, Community Chest |
| 3 | Tax | Income Tax |
| 4 | Railroad | Reading Railroad |
| 5-9 | Property/Chance | Oriental Ave, etc. |
| 10 | Corner | Jail / Just Visiting |
| 11-19 | Properties/Utilities | |
| 20 | Corner | Free Parking |
| 21-29 | Properties/Chance | |
| 30 | Corner | Go To Jail |
| 31-39 | Properties/Tax | |

### Property Types
- **Streets (22)**: Grouped by color (8 color groups)
- **Railroads (4)**: Reading, Pennsylvania, B&O, Short Line
- **Utilities (2)**: Electric Company, Water Works

### Game Flow
1. Players start with $1,500
2. Roll two dice, move clockwise
3. Perform space action (buy, pay rent, draw card, etc.)
4. Doubles = roll again (3 doubles = jail)
5. Pass GO = collect $200

### Default Players
| Player | Default Name | Avatar | Color |
|--------|--------------|--------|-------|
| 1 | Alice | 🎩 Top Hat | Red |
| 2 | Bob | 🚗 Car | Blue |
| 3 | Charlie | 🐕 Dog | Green |
| 4 | Diana | ⛵ Boat | Purple |

Players use default names, avatars, and colors automatically. Each player's token is displayed on the board with a colored circle background matching their assigned color.

### Buying/Selling Properties
- Land on unowned property → option to buy at listed price
- Decline → property goes to auction (optional for MVP)
- Properties can be sold back to bank at half price

### Rent Calculation
| Property Type | Rent Formula |
|---------------|--------------|
| Street (no houses) | Base rent (doubled if monopoly owned) |
| Street (1-4 houses) | Specified rent per house count |
| Street (hotel) | Hotel rent |
| Railroad | $25 × 2^(railroads_owned - 1) |
| Utility | 4× dice roll (1 owned), 10× dice roll (2 owned) |

### Houses and Hotels
- Must own complete color set (monopoly)
- Build evenly across properties in set
- Max 4 houses per property, then upgrade to hotel
- Limited supply: 32 houses, 12 hotels in bank

### Chance and Community Chest Cards
- 16 cards in each deck
- Effects: movement, money gain/loss, get out of jail free

### Jail Mechanics
- **Enter via**: Go To Jail space, card, or 3 consecutive doubles
- **Exit via**: Pay $50, use Get Out of Jail Free card, or roll doubles (3 attempts)
- After 3 failed attempts, must pay $50

### Winning Conditions
- Last player remaining after all others are bankrupt
- Bankruptcy = cannot pay debt and no assets to liquidate

---

## 3. User Stories with Acceptance Criteria

### US-001: Roll Dice and Move
**As a** player  
**I want to** roll dice and move my token  
**So that** I can progress around the board

**Acceptance Criteria:**
- [ ] Two dice are rolled with random values 1-6
- [ ] Token moves clockwise by sum of dice
- [ ] Rolling doubles grants another turn
- [ ] Three consecutive doubles sends player to jail
- [ ] Passing GO awards $200

---

### US-002: Buy Unowned Properties
**As a** player  
**I want to** buy unowned properties I land on  
**So that** I can collect rent from opponents

**Acceptance Criteria:**
- [ ] Option to buy appears only for unowned properties
- [ ] Property price is displayed
- [ ] Purchase deducts correct amount from balance
- [ ] Property is added to player's portfolio
- [ ] Declining purchase ends the buying phase

---

### US-003: Pay Rent
**As a** player  
**I want to** pay rent when landing on owned properties  
**So that** the game economy functions correctly

**Acceptance Criteria:**
- [ ] Rent is calculated based on property type and improvements
- [ ] Rent doubles for monopoly-owned streets without houses
- [ ] Railroad rent scales with number owned
- [ ] Utility rent based on dice roll
- [ ] Mortgaged properties charge no rent

---

### US-004: Build Houses and Hotels
**As a** player  
**I want to** build houses and hotels  
**So that** I can increase rent income

**Acceptance Criteria:**
- [ ] Building requires complete color set ownership
- [ ] Houses must be built evenly across set
- [ ] Maximum 4 houses before hotel
- [ ] Building costs deducted from balance
- [ ] Bank house/hotel supply is tracked

---

### US-005: Mortgage Properties
**As a** player  
**I want to** mortgage properties for cash  
**So that** I can avoid bankruptcy

**Acceptance Criteria:**
- [ ] Mortgaged property provides 50% of purchase price
- [ ] Mortgaged properties cannot collect rent
- [ ] Unmortgaging costs 110% of mortgage value
- [ ] Houses must be sold before mortgaging

---

### US-006: Trade with Players
**As a** player  
**I want to** trade properties and money with other players  
**So that** I can negotiate strategic deals

**Acceptance Criteria:**
- [ ] Players can offer properties, money, or Get Out of Jail cards
- [ ] Both parties must accept trade
- [ ] Trade executes instantly upon agreement
- [ ] Cannot trade mortgaged properties without disclosure

---

### US-007: Handle Chance/Community Chest
**As a** player  
**I want to** draw and execute cards  
**So that** the game has variability

**Acceptance Criteria:**
- [ ] Cards drawn from shuffled deck
- [ ] Card effect is displayed and executed
- [ ] Movement cards trigger space actions
- [ ] Get Out of Jail Free cards can be held

---

### US-008: Go to and Exit Jail
**As a** player  
**I want to** manage jail entry and exit  
**So that** jail mechanics work correctly

**Acceptance Criteria:**
- [ ] Jail triggered by: Go To Jail space, card, 3 doubles
- [ ] Exit options: pay $50, use card, roll doubles
- [ ] Forced payment after 3 failed attempts
- [ ] Jail does not prevent rent collection

---

### US-009: Declare Bankruptcy
**As a** player  
**I want to** go bankrupt when I cannot pay debts  
**So that** the game can conclude

**Acceptance Criteria:**
- [ ] Bankruptcy triggered when debt exceeds assets
- [ ] Assets transferred to creditor (player or bank)
- [ ] Player removed from game
- [ ] Last remaining player wins

---

## 4. Technical Requirements

### Language and Version
- Python 3.10+
- No external dependencies for core game logic

### Architecture
```
monopoly/
├── __init__.py
├── game.py          # Main game loop and orchestration
├── board.py         # Board representation and spaces
├── player.py        # Player state and actions
├── property.py      # Property types and ownership
├── cards.py         # Chance and Community Chest
├── dice.py          # Dice rolling
├── bank.py          # Bank operations
└── cli.py           # Command-line interface
```

### Design Principles
- **Single Responsibility**: Each class handles one concern
- **Open/Closed**: Easy to extend (e.g., add new card types)
- **Dependency Injection**: Components receive dependencies
- **Encapsulation**: Internal state protected via properties

### Interface
- **Primary**: Tkinter-based graphical user interface styled like the real Monopoly board game

#### Board Design (Realistic Layout)
- Classic square board layout with properties arranged around the perimeter
- Corner squares larger (GO, Jail, Free Parking, Go to Jail)
- Property spaces show:
  - Color band at top matching property group
  - Property name
  - Price at bottom
  - House/hotel indicators (green houses, red hotels)
  - **Ownership indicator**: Border or highlight in owner's color when property is owned
- Center of board displays:
  - "MONOPOLY" logo
  - Current dice roll with animated dice images
  - Game status messages

#### Property Cards
- When hovering/clicking property, show detailed property card:
  - Full property name
  - Color group
  - Purchase price
  - Rent levels (base, with 1-4 houses, hotel)
  - Mortgage value
  - Current owner (if any)

#### Player Panel
- Each player has dedicated panel showing:
  - Player name and avatar token
  - Current cash balance (with money icon)
  - **List of properties owned** (grouped by color, showing names)
  - Number of properties owned count
  - "In Jail" indicator if applicable
  - Get Out of Jail Free cards held
- Active player highlighted with border/glow

#### Dice Display
- Visual 3D-style dice showing dots
- Dice roll animation (brief shake/spin)
- "DOUBLES!" indicator when rolled

#### Action Buttons (Styled like real game)
- "Roll Dice" - Primary action button
- "Buy Property" - Appears when landing on unowned property
- "Build House" - Available when player has monopoly
- "Mortgage" - Sell property to bank
- "End Turn" - Pass to next player
- Buttons disabled/enabled based on game state

#### Visual Polish
- Classic Monopoly color scheme (green board, red hotels, etc.)
- Rounded corners on cards and panels
- Drop shadows for depth
- Smooth token movement animation on board
- Victory celebration animation when winner declared

- **Secondary**: Text-based CLI for testing and automation

---

## 5. Out of Scope (MVP)

| Feature | Reason |
|---------|--------|
| Network Multiplayer | Complexity; local play sufficient |
| Save/Load Game | Non-essential for demo |
| Auction on Declined Purchase | Can be added post-MVP |
| Custom Rules | Standard rules only |
| AI Players | Human players only |
| 3D Graphics | Tkinter 2D sufficient |

---

## 6. Success Metrics

### Functional Requirements
- [ ] All 40 board spaces implemented correctly
- [ ] All property types with accurate rent calculation
- [ ] Complete Chance and Community Chest decks
- [ ] Jail mechanics fully functional
- [ ] Building (houses/hotels) system works
- [ ] Trading between players operational

### Quality Requirements
- [ ] 2-4 players supported simultaneously
- [ ] Full game loop: start → play → winner declared
- [ ] No crashes during normal gameplay
- [ ] Clear error messages for invalid actions

### Code Quality
- [ ] Modular architecture (separate concerns)
- [ ] Docstrings on all public methods
- [ ] Type hints on function signatures
- [ ] Unit tests for core game logic (stretch goal)

---

## Appendix: Standard Monopoly Property Data

### Color Groups and Prices
| Color | Properties | Price Range | House Cost |
|-------|------------|-------------|------------|
| Brown | Mediterranean, Baltic | $60-$60 | $50 |
| Light Blue | Oriental, Vermont, Connecticut | $100-$120 | $50 |
| Pink | St. Charles, States, Virginia | $140-$160 | $100 |
| Orange | St. James, Tennessee, New York | $180-$200 | $100 |
| Red | Kentucky, Indiana, Illinois | $220-$240 | $150 |
| Yellow | Atlantic, Ventnor, Marvin Gardens | $260-$280 | $150 |
| Green | Pacific, N. Carolina, Pennsylvania | $300-$320 | $200 |
| Dark Blue | Park Place, Boardwalk | $350-$400 | $200 |

### Starting Money Distribution
| Denomination | Count | Total |
|--------------|-------|-------|
| $500 | 2 | $1,000 |
| $100 | 2 | $200 |
| $50 | 2 | $100 |
| $20 | 6 | $120 |
| $10 | 5 | $50 |
| $5 | 5 | $25 |
| $1 | 5 | $5 |
| **Total** | | **$1,500** |
