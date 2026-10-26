# 0002 — Separate Parcel Lifecycle Logic from the API

## Status

Accepted

## Context

Parcel state transitions must follow specific business rules, such as preventing a delivered parcel from being marked as failed. Implementing these rules directly inside API endpoints would mix business logic with HTTP handling and make the rules harder to test independently.

## Decision

We will implement parcel lifecycle rules in `app/domain.py`, independently of FastAPI and other web framework dependencies. The API layer in `app/api.py` will call the domain functions and translate their results into appropriate HTTP responses.

## Consequences

The lifecycle rules are easier to test independently, reuse, and maintain. However, the API layer must correctly handle domain errors and translate them into the appropriate HTTP status codes and problem responses.