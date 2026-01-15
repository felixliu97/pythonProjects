---
name: solution-design
description: Designs software solutions and architectures. Use when planning new features, systems, or discussing technical approaches.
---

# Solution Design Skill

When designing solutions, follow this structured approach:

## 1. Requirements Gathering

- **Functional Requirements**: What must the system do?
- **Non-Functional Requirements**: Performance, scalability, security, reliability
- **Constraints**: Technology stack, budget, timeline, team skills
- **Assumptions**: Document any assumptions made

## 2. Design Process

### Problem Analysis
1. Break down the problem into smaller components
2. Identify existing solutions or patterns that apply
3. Consider trade-offs between different approaches

### Architecture Patterns

| Pattern | Use When |
|---------|----------|
| **Monolith** | Small team, simple domain, rapid prototyping |
| **Microservices** | Large teams, independent deployments, scaling needs |
| **Event-Driven** | Async workflows, decoupled systems |
| **CQRS** | Complex queries, separate read/write scaling |

### Design Principles

- **SOLID** principles for object-oriented design
- **DRY** (Don't Repeat Yourself)
- **KISS** (Keep It Simple, Stupid)
- **YAGNI** (You Aren't Gonna Need It)

## 3. Documentation Deliverables

When creating a design document, include:

```markdown
# Solution Design: [Feature Name]

## Problem Statement
Brief description of the problem being solved.

## Proposed Solution
High-level overview of the approach.

## Technical Design
- Architecture diagram (use Mermaid)
- Component breakdown
- Data models
- API contracts

## Trade-offs & Alternatives
| Option | Pros | Cons |
|--------|------|------|

## Implementation Plan
1. Phase 1: ...
2. Phase 2: ...

## Risks & Mitigations
- Risk 1: Mitigation strategy
```

## 4. Review Checklist

Before finalizing a design:
- [ ] Does it solve the stated problem?
- [ ] Is it the simplest solution that works?
- [ ] Are edge cases considered?
- [ ] Is it testable?
- [ ] Is it maintainable?
- [ ] Does it align with existing architecture?
