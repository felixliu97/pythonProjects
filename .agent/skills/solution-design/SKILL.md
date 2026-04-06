---
name: solution-design
description: Structured approach, documentation templates, and technical standards for software architecture and system design.
---

# Solution Design Skill (Technical)

Standard process and documentation requirements for proposing technical solutions.

## 1. Design Lifecycle

For any architectural change, address these pillars in order:

1. **Problem Analysis**: Identify functional requirements (FRs), non-functional requirements (NFRs), and success metrics.
2. **Architecture Blueprint**: High-level component interactions. Use **Mermaid diagrams**.
3. **Technology Selection**: Justify choices of databases, frameworks, and protocols (Sync vs. Async).
4. **Data Modeling**: Schema design, data flow, and consistency strategies.
5. **Interface Design**: API contracts, integration patterns, and contract testing.
6. **Resilience & Security**: Caching, balancing, disaster recovery, and threat modeling.
7. **Implementation Roadmap**: Phased delivery plan (MVP -> V1) with risk mitigations.

## 2. Documentation Standards

- **Visuals**: Mandatory use of Mermaid for flowcharts and ERDs.
- **Trade-offs**: Always document alternative approaches considered and the rationale for the final choice.
- **Patterns**: Leverage known patterns (Monolith, Microservices, Event-Driven, or CQRS) where appropriate.

## 3. Review Checklist
- [ ] Does it solve the FRs?
- [ ] Is it the simplest possible solution?
- [ ] Are potential bottlenecks identified?
- [ ] Is the design testable and observable?
