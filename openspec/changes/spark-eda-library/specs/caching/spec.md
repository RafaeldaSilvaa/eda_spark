# Caching Specification

## Purpose

Provide optional memoization for expensive operations (profile computations, quality scores). Defines a `CacheProvider` port and an LRU in-memory adapter.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| CA-1 | CacheProvider port MUST define `get(key) → Optional[Any]`, `set(key, value, ttl_seconds)` | MUST |
| CA-2 | CacheProvider port MUST define `invalidate(key)` and `clear()` | MUST |
| CA-3 | LRUCacheProvider MUST evict least-recently-used entries when at capacity | MUST |
| CA-4 | TTL expiration SHALL be checked on `get()` — expired entries are treated as misses | SHALL |
| CA-5 | Default capacity SHALL be 128 entries | SHOULD |
| CA-6 | Cache keys MUST be strings; values MUST be serializable via pickle | MUST |
| CA-7 | LRU cache operations MUST be thread-safe | MUST |

## Scenarios

### CA-1: Happy path — cache hit

- GIVEN an LRUCacheProvider with capacity=3
- WHEN `set("a", 1)` and `set("b", 2)` are called, then `get("a")`
- THEN the cache returns 1 for key "a" and 2 for key "b"

### CA-2: Edge case — LRU eviction

- GIVEN an LRUCacheProvider with capacity=2, containing keys "a" and "b"
- WHEN `set("c", 3)` is called
- THEN key "a" (least recently used) is evicted
- AND `get("a")` returns None

### CA-3: Edge case — TTL expiration

- GIVEN an LRUCacheProvider with a TTL of 1 second on key "temp"
- WHEN 2 seconds elapse and `get("temp")` is called
- THEN None is returned (treated as cache miss)

### CA-4: Error case — invalid key type

- GIVEN a CacheProvider
- WHEN `set(123, "value")` is called with a non-string key
- THEN a `TypeError` is raised

## Input / Output Contracts

| Operation | Input | Output |
|-----------|-------|--------|
| `get` | `key: str` | `Optional[Any]` |
| `set` | `key: str, value: Any, ttl: Optional[int]` | `None` |
| `invalidate` | `key: str` | `None` |
| `clear` | — | `None` |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Domain | `CacheProvider` port (abstract interface) |
| Adapters | `LRUCacheProvider` — concrete in-memory implementation |
| Use Cases | Inject CacheProvider for optional caching between use-case steps |

## Acceptance Criteria

- [ ] CacheProvider interface is importable with zero dependencies
- [ ] LRUCacheProvider maintains correct eviction order under concurrent access
- [ ] TTL expiry is monotonic: once expired, never returns stale value
- [ ] 100% coverage on LRU logic (pure Python, no Spark)
