# testing agent instructions

this file describes **universal expectations** for tests in this repository, regardless of language or test runner.

## core rules

- **isolation**: each test must be independent and runnable alone.
- **no real externals**: do not rely on real user files, real api keys, real databases, or real external services.
- **determinism**: tests must be repeatable (fixed seeds, stable ordering, controlled clocks/randomness).
- **fast feedback**: keep tests small and targeted; prefer narrow units over end-to-end unless explicitly needed.

## test shape

each test should follow arrange / act / assert:

- **arrange**: create fake data, temp directories, mocks/fakes, config, or database state.
- **act**: run the function, command, endpoint, or workflow.
- **assert**: verify outputs and meaningful side effects (state changes, logs, files, requests).

## test scope

- **unit tests**: default choice; test one function/class/module with fake dependencies.
- **integration tests**: use when behavior depends on real interaction between modules, database layers, file systems, or framework wiring.
- **end-to-end tests**: use sparingly for critical user workflows only.

Prefer the narrowest test that proves the behavior.

## test naming

Use names that describe behavior, not implementation.

Good:
- "returns empty list when feed has no entries"
- "rejects upload when file type is unsupported"
- "retries request after transient failure"

Bad:
- "test parser"
- "works correctly"
- "handles data"

## fixtures and helpers

- **prefer fixtures over repetition**: centralize setup so tests stay readable.
- **self-cleaning**: fixtures must clean up after themselves automatically.
- **minimal surface area**: keep helpers small and purpose-built.

examples of fixture responsibilities (names are illustrative):

- create a temp workspace/project layout
- build a fake config with safe defaults
- seed a test database with known data
- stub/mock an external http api
- construct a fake file tree / sample document corpus

## filesystem rules

- **use temp directories** for any writes.
- **never write to repo root** unless the behavior under test is explicitly “writes to project root”.
- **treat committed test inputs as read-only** (copy into temp space before modifying).

## api / service rules

- **mock external services** (http, queues, cloud apis, paid services).
- **cover both success and failure** paths.
- **include edge cases** relevant to the feature:
  - missing data
  - invalid input
  - timeouts / retries / transient failures
  - unauthorized / forbidden (if relevant)
  - empty result
  - malformed response

## async / background work

- **avoid fixed sleeps** (they introduce flakiness).
- **wait on a condition** with a bounded timeout instead:
  - poll until a status/flag changes
  - wait for an expected event/callback
  - wait until an expected request count / side effect is observed
- **sleep is only allowed** when the timing behavior itself is the thing being tested (debounce, throttle, timeouts).

## mocking rules

- **mock only what the test needs**.
- **unexpected calls should fail** (avoid permissive “anything goes” mocks).
- **prefer focused fakes** over huge fake services with unused methods.

## what good tests prove

- **prove behavior, not implementation**.
- **assert outcomes** (return values, persisted state, emitted events, observable effects).
- **avoid fragile internal assertions** unless the internals are explicitly the contract under test.

## minimum coverage for a major feature

- **happy path**
- **invalid input**
- **missing dependency/config**
- **external service failure** (mocked)
- **empty state**
- **permission/auth failure** (if relevant)
- **regression test** for any fixed bug

## pseudocode examples

language-agnostic patterns only; adapt names and syntax to your stack.

### basic test (arrange / act / assert)

```
test "returns success for valid input":
  // arrange
  input = valid_input()
  deps = fake_dependencies()

  // act
  result = run_feature(input, deps)

  // assert
  assert result.status == "success"
  assert result.output_path exists
  assert deps.external_api.call_count == 1
```

### wait for condition (not fixed sleep)

```
test "job completes and writes output":
  job = start_background_job(config)

  wait_until(
    condition: job.status == "done",
    timeout: 5s,
    poll_interval: 50ms
  )

  assert file_exists(job.output_path)
```

```
// only when timing behavior is the contract under test
test "debounce delays emit by 300ms":
  clock = fake_clock()
  emitted = []
  subscribe(handler: (x) => emitted.push(x))

  trigger("a")
  clock.advance(299ms)
  assert emitted is empty

  clock.advance(1ms)
  assert emitted == ["a"]
```

### external api success and failure

```
test "fetches and parses remote payload":
  mock_http.on_get("/articles/1").return(
    status: 200,
    body: { "title": "example", "body": "..." }
  )

  article = fetch_article("1")

  assert article.title == "example"
  assert mock_http.called_once_with("GET", "/articles/1")
```

```
test "surfaces service failure":
  mock_http.on_get("/articles/1").return(status: 503, body: "unavailable")

  assert_raises(ServiceError, () => fetch_article("1"))
```

### filesystem test (read-only inputs, temp writes)

```
test "writes report to output dir":
  workspace = create_temp_dir()
  copy(read_only_fixture("sample.html"), workspace / "input.html")

  run_report(workspace / "input.html", output_dir: workspace / "out")

  assert file_exists(workspace / "out" / "report.json")
  assert fixture_unchanged("sample.html")
```

### regression test for a fixed bug

```
test "issue-42: empty feed does not crash aggregator":
  // bug: empty rss feed caused divide-by-zero in score normalization
  feed = fake_feed(entries: [])
  config = default_config()

  result = aggregate(feed, config)

  assert result.articles == []
  assert result.errors == []
```

### focused mock (unexpected calls fail)

```
test "only calls embed once per article":
  embedder = strict_mock(methods: ["embed"])
  embedder.embed.return([0.1, 0.2, 0.3])

  score_article(article_text, embedder)

  assert embedder.embed.call_count == 1
  assert embedder.no_unexpected_calls()
```

## agent behavior (when adding/modifying tests)

- **reuse existing patterns** and fixtures before creating new ones.
- **do not introduce flaky timing**.
- **do not require real credentials**.
- **do not depend on test execution order**.
- **keep tests readable**: one clear behavioral assertion is better than many unrelated assertions.