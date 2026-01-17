---
name: product-owner
description: Helps with product ownership tasks like writing user stories, defining requirements, prioritizing backlogs, and creating PRDs. Use when discussing features, requirements, or product planning.
---

# Product Owner Skill

When acting as a product owner, apply these frameworks and practices:

## User Story Format

```
As a [type of user],
I want [goal/desire],
So that [benefit/value].
```

### Acceptance Criteria (Given-When-Then)

```
Given [precondition]
When [action]
Then [expected result]
```

### Example

```
As a registered user,
I want to reset my password via email,
So that I can regain access to my account.

Acceptance Criteria:
- Given I am on the login page
  When I click "Forgot Password"
  Then I see a form to enter my email

- Given I enter a valid registered email
  When I submit the form
  Then I receive a password reset email within 5 minutes
```

## INVEST Criteria for User Stories

| Criteria | Description |
|----------|-------------|
| **I**ndependent | Can be developed separately from other stories |
| **N**egotiable | Details can be discussed and refined |
| **V**aluable | Delivers value to users or business |
| **E**stimable | Team can estimate the effort |
| **S**mall | Completable in one sprint |
| **T**estable | Clear pass/fail criteria |

## Product Requirements Document (PRD) Template

```markdown
# PRD: [Feature Name]

## Overview
Brief description of the feature and its purpose.

## Problem Statement
What problem does this solve? Who experiences it?

## Goals & Success Metrics
- Goal 1: Metric to measure success
- Goal 2: Metric to measure success

## User Stories
1. As a [user]...
2. As a [user]...

## Scope
### In Scope
- Feature A
- Feature B

### Out of Scope
- Feature X (future consideration)

## Requirements
### Functional Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Description | Must Have |

### Non-Functional Requirements
- Performance: Response time < 200ms
- Security: Data encrypted at rest

## Wireframes / Mockups
[Include or link to designs]

## Dependencies
- External API integration
- Database schema changes

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|

## Timeline
| Phase | Duration | Deliverables |
|-------|----------|--------------|
```

## Prioritization Frameworks

### MoSCoW Method
- **Must Have**: Critical for release
- **Should Have**: Important but not critical
- **Could Have**: Nice to have
- **Won't Have**: Out of scope for now

### RICE Scoring
```
Score = (Reach × Impact × Confidence) / Effort
```
- **Reach**: How many users affected?
- **Impact**: How much value? (3=massive, 2=high, 1=medium, 0.5=low)
- **Confidence**: How sure are we? (100%, 80%, 50%)
- **Effort**: Person-months required

## Stakeholder Communication

When presenting features or updates:
1. **Start with the "why"** - business value and user impact
2. **Show, don't tell** - demos and prototypes
3. **Be transparent** about trade-offs and risks
4. **Provide options** when seeking decisions
