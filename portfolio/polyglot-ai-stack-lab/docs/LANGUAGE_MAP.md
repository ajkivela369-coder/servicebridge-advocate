# Language Map

## Python — AI/ML core
Use it for preprocessing, model training, evaluation, APIs, and experiment code.

Example question AJ should be able to answer:
> Why is Python dominant in ML even though the underlying high-performance operations may run in C++ or CUDA?

## SQL — data layer
Use it to create reproducible datasets and aggregate model results.

Example:
```sql
SELECT expected_label, COUNT(*)
FROM evaluations
GROUP BY expected_label;
```

## TypeScript — human-in-the-loop UI
Use it for typed browser applications where reviewers inspect model outputs.

Example:
```ts
type Label = "PASS" | "REVIEW" | "FAIL";
```

## JavaScript
TypeScript is compiled to JavaScript. Understanding the runtime, promises, modules, and browser behavior matters even when TypeScript is the authoring language.

## Bash
Use it to make experiments repeatable:
```bash
python train.py
python evaluate.py
```

## R
Use it for statistical summaries, confidence intervals, exploratory analysis, and research-style reporting.

## C++
Use it to understand performance-sensitive components and what sits underneath many Python ML libraries.

## HTML/CSS
HTML structures a web page; CSS controls layout and presentation. They are not general-purpose programming languages, but they are part of a usable ML dashboard.

## JSON / JSONL
Data formats, not programming languages. Useful for model inputs, API payloads, benchmark cases, and structured evaluator outputs.

## YAML
Configuration format, not a programming language. Common in CI/CD and experiment configuration.

## Specialized languages we are not claiming yet

CUDA, Scala, Java, Go, and Rust belong in later modules only if we build something substantive enough to explain and test.
