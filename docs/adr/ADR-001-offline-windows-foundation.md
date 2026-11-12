# ADR 001 — Offline Windows foundation

**Status** Accepted for M0 technical setup.

Use .NET 10 LTS and WPF for the Windows desktop, EF Core SQLite for versioned local persistence, and a C# domain independent of infrastructure. Ship the local M0 engineering package as a self-contained Windows x64 ZIP. Use framework-dependent builds for normal local development.

Create a migration-backed synthetic fixture table so later M1 work can introduce the agreed project schema independently. Seed the fixture once through the migration. Use the same on-disk code path in the UI smoke test with an isolated temporary data root.

The application defaults to the current user's LocalAppData. Keep the runtime network-free and log only operation and exception type. Future schema upgrades, package signing and backup/restore have separate acceptance work.
