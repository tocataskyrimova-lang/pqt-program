# No Direct DB Write

Application code must not persist memory by raw SQL inserts as an intake path. Persistence requires `WritePlan` and `MemoryWriteGateway.commit()`.

SQLite stores the result of cognition; it does not decide what is memory.
