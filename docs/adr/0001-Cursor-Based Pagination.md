 0001-Use Cursor-Based Pagination

## Status
Accepted


<!-- One of: Proposed, Accepted, Superseded, Deprecated, Rejected. -->

## Context
Offset-based pagination can skip or duplicate parcels when records are added, removed, or change during pagination. Cursor-based pagination provides a more stable way to navigate parcel lists as the underlying data changes. However, it requires generating, encoding, and validating cursors.
<!-- The forces at play, including the ones pulling the other way. -->

## Decision
We will use cursor-based pagination instead of offset-based pagination for the listParcels operation. The API will return a next_cursor value when more results are available and reject invalid cursors with a 400 Bad Request response.

<!-- One or two sentences in active voice: "We will ..." -->

## Consequences
Pagination is more reliable when the parcel collection changes between requests, and clients can continue from the last position without relying on an offset. However, cursor generation and validation add implementation complexity, and clients must use the returned cursor rather than requesting an arbitrary page number.