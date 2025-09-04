Here’s a simple **README.md** draft that matches your current implementation and folder structure, focused on clarity and incremental evolution:

---

# Incident Mirror (Core Orchestrator)

This project implements the **core orchestration layer** for synchronizing incidents across different systems (first target: **GLPI**).
It focuses on **domain modeling, entities, and state handling** while keeping infrastructure details (DB, queues, HTTP servers) abstracted and swappable.

*motivation*:
https://www.notion.so/Reuni-o-Vila-11-27-08-2025-25c8fd07785d80dcac90ed63fdb419e9

---

## ✨ Goals

* Provide a **domain-first design** (incidents, bindings, events, snapshots).
* Enable **state-based synchronization** between heterogeneous systems.
* Stay **infra-agnostic**: in-memory adapters today, replaceable with SQL/Redis/Kafka tomorrow.
* Support **idempotency, snapshots, and hashing** to decide when an incident state actually changed.

---

## 📂 Project Structure

```
app/
  domain/           # Pure domain logic
    entities.py     # Incident, Binding, etc.
    events.py       # InboundEvent, MirrorCommand
    reducer.py      # Reducer: event -> new snapshot
    snapshots.py    # Snapshot model + hashing
    value_objects.py# Value objects (Status, IDs)
  application/      # Use-cases & ports
    ports.py        # Repository & outbox interfaces
    use_cases.py    # ApplyInbound orchestration
  adapters/         # Infrastructure (in-memory for now)
    memory_repos.py # In-memory incidents & bindings
    memory_outbox.py# Simple logging outbox
```

---

## 🚀 Current Capabilities

* Define incidents as **snapshots** with canonical fields (`status`, `title`, `description`).
* Reduce inbound events into new snapshots.
* Compute **fingerprints (hashes)** of snapshots to detect real state changes.
* Emit **MirrorCommands** to all target systems except the source.
* Guarantee **idempotency** with `idempotency_key`.
* Run fully **in-memory** for quick testing and iteration.

---

## 🔮 Next Steps

* Implement **file-based or SQL-backed snapshot repository**.
* Introduce **real outbox** (Redis Streams / Kafka).
* Build reconciliation jobs for drift detection.
* Add adapters for GLPI REST API and webhooks.

---

## 📖 Design Principles

* **Domain-driven**: incidents, events, and commands are the core.
* **Immutable snapshots**: new state replaces old, not field-by-field diffs.
* **Idempotent by construction**: state hash doubles as command key.
* **Hexagonal architecture**: domain and application are infra-agnostic; adapters can evolve.

---
