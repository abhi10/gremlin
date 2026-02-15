# Gremlin Critique: pydantic/pydantic

> Risk analysis of [Pydantic](https://github.com/pydantic/pydantic) — data validation using Python type annotations

**Date:** 2026-02-14
**Gremlin Version:** 0.2.0
**Depth:** deep | **Threshold:** 70%

## Summary

| Area | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| Schema Generation & Type Coercion | 0 | 0 | 0 | 0 | 0 |
| Validation Pipeline & Field Validators | 2 | 4 | 4 | 0 | 10 |
| Generics & Type Parameterization | 2 | 3 | 3 | 0 | 8 |
| Serialization & JSON Schema | 2 | 3 | 3 | 0 | 8 |
| Model Construction & Metaclass | 2 | 4 | 4 | 0 | 10 |
| Discriminated Unions | 1 | 3 | 4 | 0 | 8 |
| Configuration System | 2 | 4 | 4 | 0 | 10 |
| TypeAdapter & Dataclasses | 2 | 3 | 4 | 1 | 10 |
| **Total** | **13** | **24** | **26** | **1** | **64** |

## Top Critical Risks

### 🔴 Validator Ordering Chain Corruption (85%)
**Area:** Validation Pipeline & Field Validators | **Files:** `pydantic/_internal/_decorators.py`, `pydantic/functional_validators.py`

> What if validators with identical priority execute in different orders across processes due to dict/set iteration randomization?

**Impact:** Inconsistent validation behavior between dev/prod environments, race conditions in validator chains where later validators assume earlier ones ran, silent data corruption when wrap validators execute out of expected sequence

### 🔴 Info Parameter Memory Leak via Circular References (80%)
**Area:** Validation Pipeline & Field Validators | **Files:** `pydantic/_internal/_decorators.py`, `pydantic/functional_validators.py`

> What if info parameter creates circular references between validator context and model instances during re-validation cycles?

**Impact:** Memory exhaustion as validator contexts accumulate in memory, garbage collection failures, eventual OOM crashes affecting all users

### 🔴 Recursive Generic Model Stack Overflow (85%)
**Area:** Generics & Type Parameterization | **Files:** `pydantic/_internal/_generics.py`

> What if deeply nested recursive generic models exceed Python's default recursion limit during type parameter substitution?

**Impact:** Python crashes with RecursionError, bringing down the entire application. Happens during model creation/validation, not just edge cases.

### 🔴 WeakValueDictionary Race Condition (80%)
**Area:** Generics & Type Parameterization | **Files:** `pydantic/_internal/_generics.py`

> What if concurrent threads access `_GENERIC_TYPES_CACHE` while garbage collection removes weakly referenced models?

**Impact:** KeyError crashes during model creation, or worse - returning partially garbage-collected model instances that cause unpredictable behavior downstream.

### 🔴 Infinite Recursion in Schema References (85%)
**Area:** Serialization & JSON Schema | **Files:** `pydantic/json_schema.py`

> What if circular schema references create infinite recursion during schema generation?

**Impact:** Stack overflow crashes, application DoS, especially with complex nested models or self-referencing schemas

### 🔴 Memory Exhaustion from Unbounded Definition Expansion (80%)
**Area:** Serialization & JSON Schema | **Files:** `pydantic/json_schema.py`

> What if deeply nested or highly branched schema structures cause exponential memory growth during the 100-iteration fixed-point resolution loop?

**Impact:** OOM crashes affecting all users, server becomes unresponsive during schema generation

### 🔴 MRO Diamond Problem with Field Inheritance (85%)
**Area:** Model Construction & Metaclass | **Files:** `pydantic/_internal/_model_construction.py`

> What if multiple inheritance creates diamond patterns where the same field is defined differently in different base classes, causing unpredictable field resolution?

**Impact:** Silent data corruption as wrong field validators/types get applied, breaking business logic with no obvious error

### 🔴 Metaclass Recursion During Schema Generation (80%)
**Area:** Model Construction & Metaclass | **Files:** `pydantic/_internal/_model_construction.py`

> What if circular model references during `GenerateSchema` creation cause infinite recursion in the metaclass `__new__` method?

**Impact:** Stack overflow crash during import time, making the entire application unloadable

### 🔴 Discriminator Value Collision with Type Coercion (85%)
**Area:** Discriminated Unions | **Files:** `pydantic/_internal/_discriminated_union.py`

> What if two union members have discriminator literals that are equal after type coercion but different in source ("1" vs 1, True vs "true")?

**Impact:** Silent data corruption where wrong union branch is selected, leading to incorrect field mapping and potentially security bypasses if permissions differ between branches

### 🔴 Config Inheritance Override Corruption (85%)
**Area:** Configuration System | **Files:** `pydantic/config.py`, `pydantic/_internal/_config.py`

> What if child model config overrides parent config in unexpected ways, causing silent validation bypass?

**Impact:** Security vulnerabilities when child models accidentally inherit `extra='allow'` from parent but developer expects `extra='forbid'`. Sensitive data leaks through unvalidated extra fields.

### 🔴 String Transformation Memory Exhaustion (80%)
**Area:** Configuration System | **Files:** `pydantic/config.py`, `pydantic/_internal/_config.py`

> What if `str_to_lower`/`str_to_upper` is applied to extremely large strings during validation, causing memory exhaustion?

**Impact:** DoS attack vector through crafted payloads. Single request with massive string field can crash application when string transformations create multiple copies in memory.

### 🔴 Forward Reference Resolution Poisoning (85%)
**Area:** TypeAdapter & Dataclasses | **Files:** `pydantic/type_adapter.py`, `pydantic/dataclasses.py`

> What if a TypeAdapter is instantiated with forward references in one module, but symbols with the same names exist in the instantiation context with different types?

**Impact:** Silent type validation bypass - data validated against wrong schema, potentially allowing malicious payloads through validation that should fail

### 🔴 Parent Frame Access Race Condition (80%)
**Area:** TypeAdapter & Dataclasses | **Files:** `pydantic/type_adapter.py`, `pydantic/dataclasses.py`

> What if `_fetch_parent_frame()` is called concurrently across threads and frame references become invalid or mixed between instances?

**Impact:** Schema built with wrong namespace context, leading to validation against incorrect types or complete validation failure

---

## Detailed Results by Area

### Schema Generation & Type Coercion
**Files:** `pydantic/_internal/_generate_schema.py`
**Risks:** 0 (0C / 0H / 0M / 0L)

---

### Validation Pipeline & Field Validators
**Files:** `pydantic/_internal/_decorators.py`, `pydantic/functional_validators.py`
**Risks:** 10 (2C / 4H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Validator Ordering Chain Corruption

> What if validators with identical priority execute in different orders across processes due to dict/set iteration randomization?

**Impact:** Inconsistent validation behavior between dev/prod environments, race conditions in validator chains where later validators assume earlier ones ran, silent data corruption when wrap validators execute out of expected sequence

#### 🔴 CRITICAL (80%) — Info Parameter Memory Leak via Circular References

> What if info parameter creates circular references between validator context and model instances during re-validation cycles?

**Impact:** Memory exhaustion as validator contexts accumulate in memory, garbage collection failures, eventual OOM crashes affecting all users

#### 🟠 HIGH (90%) — Wrap Validator Infinite Recursion

> What if wrap validator calls the wrapped function which triggers another validator that calls back to the original wrap validator?

**Impact:** Stack overflow crash, application DoS, validation system completely broken for affected models

#### 🟠 HIGH (85%) — Re-validation State Corruption on Mutation

> What if field mutation triggers re-validation while another thread is mid-validation, causing validator state to be shared/corrupted?

**Impact:** Invalid data passing validation, validation errors on valid data, race conditions in multi-threaded applications

#### 🟠 HIGH (80%) — Validator Exception Breaks Chain

> What if a before validator throws an exception but the error handling doesn't properly clean up decorator proxy state, causing subsequent validators on other fields to malfunction?

**Impact:** Validation system enters corrupted state, other fields fail validation unexpectedly, difficult to debug cascading failures

#### 🟠 HIGH (78%) — Dynamic Field Validator Memory Exhaustion

> What if field names tuple in FieldValidatorDecoratorInfo contains unbounded user-controlled data, and validators are dynamically created for large numbers of generated field names?

**Impact:** Memory exhaustion from storing massive field name tuples, performance degradation, potential DoS through crafted model definitions

#### 🟡 MEDIUM (85%) — Descriptor Proxy __get__ Recursion

> What if PydanticDescriptorProxy.__get__ is called on an object that has another descriptor in the inheritance chain with the same __get__ logic?

**Impact:** Stack overflow in descriptor resolution, model instantiation failures, confusing error messages about descriptor chains

#### 🟡 MEDIUM (80%) — Validator Mode String Injection

> What if validator mode parameters ('before', 'after', 'wrap') are constructed from user input or configuration that gets sanitized incorrectly, leading to unexpected mode behavior?

**Impact:** Validators run in wrong order, validation logic bypassed, security rules applied incorrectly

#### 🟡 MEDIUM (75%) — Shim Function Double-Wrapping

> What if the shim wrapper function gets applied multiple times during inheritance or decorator composition, creating nested function call overhead?

**Impact:** Performance degradation on every validation, potential stack depth issues with deeply nested inheritance, debugging difficulties with wrapped call stacks

#### 🟡 MEDIUM (72%) — ClassVar Name Collision

> What if validator cls_var_name collides with Python built-in attributes or descriptor names when using get_attribute_from_bases?

**Impact:** Validator functions overwrite essential class behavior, methods like __init__ or __new__ get replaced with validators, class becomes non-instantiable

---

### Generics & Type Parameterization
**Files:** `pydantic/_internal/_generics.py`
**Risks:** 8 (2C / 3H / 3M / 0L)

#### 🔴 CRITICAL (85%) — Recursive Generic Model Stack Overflow

> What if deeply nested recursive generic models exceed Python's default recursion limit during type parameter substitution?

**Impact:** Python crashes with RecursionError, bringing down the entire application. Happens during model creation/validation, not just edge cases.

#### 🔴 CRITICAL (80%) — WeakValueDictionary Race Condition

> What if concurrent threads access `_GENERIC_TYPES_CACHE` while garbage collection removes weakly referenced models?

**Impact:** KeyError crashes during model creation, or worse - returning partially garbage-collected model instances that cause unpredictable behavior downstream.

#### 🟠 HIGH (90%) — LimitedDict Memory Leak via Retention

> What if the commented-out `DeepChainMap(_GENERIC_TYPES_CACHE, LimitedDict())` pattern still exists elsewhere and LimitedDict retains references to models that should be garbage collected?

**Impact:** Memory grows unbounded as generic model instances accumulate, eventually causing OOM. The comment suggests this was a known issue they tried to fix.

#### 🟠 HIGH (75%) — Global Reference Name Collision

> What if `create_generic_submodel` generates duplicate global reference names when multiple threads create models with the same name simultaneously?

**Impact:** Models get overwritten in `sys.modules[created_model.__module__].__dict__`, breaking pickling and causing wrong model instances to be used. The `while` loop with `reference_name += '_'` isn't thread-safe.

#### 🟠 HIGH (80%) — Type Parameter Substitution with Malformed Metadata

> What if `__pydantic_generic_metadata__` contains mismatched args/parameters lengths or invalid TypeVar instances during `replace_types`?

**Impact:** `zip(parameters, args)` creates wrong mappings or `dict(zip(...))` silently drops parameters, leading to incorrect type substitution and runtime type errors in validation.

#### 🟡 MEDIUM (85%) — Frame Inspection Failure in Restricted Environments

> What if `sys._getframe(depth)` fails in environments where frame introspection is disabled (PyPy, security-hardened Python)?

**Impact:** `_get_caller_frame_info` raises `AttributeError`, causing `create_generic_submodel` to skip global reference creation, breaking model pickling in production.

#### 🟡 MEDIUM (75%) — Infinite Loop in iter_contained_typevars

> What if circular references exist in generic model metadata where model A references model B which references model A?

**Impact:** `iter_contained_typevars` recurses infinitely until stack overflow. Less likely than the recursive model case but still possible with complex inheritance chains.

#### 🟡 MEDIUM (70%) — Cache Key Collision with Complex Generic Types

> What if different generic type combinations produce identical `GenericTypesCacheKey` tuples due to hash collisions or type representation ambiguities?

**Impact:** Wrong cached model returned, causing validation to pass/fail incorrectly. Subtle bugs where `User[int]` returns cached `User[str]` model.

---

### Serialization & JSON Schema
**Files:** `pydantic/json_schema.py`
**Risks:** 8 (2C / 3H / 3M / 0L)

#### 🔴 CRITICAL (85%) — Infinite Recursion in Schema References

> What if circular schema references create infinite recursion during schema generation?

**Impact:** Stack overflow crashes, application DoS, especially with complex nested models or self-referencing schemas

#### 🔴 CRITICAL (80%) — Memory Exhaustion from Unbounded Definition Expansion

> What if deeply nested or highly branched schema structures cause exponential memory growth during the 100-iteration fixed-point resolution loop?

**Impact:** OOM crashes affecting all users, server becomes unresponsive during schema generation

#### 🟠 HIGH (90%) — Schema Reference Collision After Simplification

> What if the `_DefinitionsRemapping.from_prioritized_choices` produces name collisions where different schemas get mapped to the same DefsRef, breaking schema validation?

**Impact:** Schema validation failures in production, incorrect API contract enforcement, data corruption from accepting invalid inputs

#### 🟠 HIGH (85%) — Mode Selection Mismatch Breaking Schema Contracts

> What if validation mode schemas are used for serialization or vice versa, causing computed fields to appear in validation schemas or be missing from serialization schemas?

**Impact:** API contract violations, client integration failures, computed fields incorrectly required during validation

#### 🟠 HIGH (75%) — OpenAPI Compatibility Breaking with Edge Case Schemas

> What if discriminated union schemas with complex inheritance hierarchies generate JSON schemas that are valid JSON Schema but break OpenAPI spec parsers?

**Impact:** API documentation tools fail, client SDK generation breaks, integration partner tooling incompatible

#### 🟡 MEDIUM (80%) — Reference Template Injection via Model Names

> What if model class names contain path traversal characters (../, ..\) or URL-unsafe characters that break the DEFAULT_REF_TEMPLATE formatting?

**Impact:** Malformed $ref URLs, schema reference resolution failures, potential path traversal if references are used for file operations

#### 🟡 MEDIUM (75%) — Fixed-Point Resolution Timeout

> What if the 100-iteration limit in `from_prioritized_choices` is reached without convergence, causing the PydanticInvalidForJsonSchema exception?

**Impact:** Schema generation fails for complex models, application startup failures if schemas are generated at boot time

#### 🟡 MEDIUM (70%) — Deep Copy Memory Spike

> What if `deepcopy(definitions)` in the fixed-point resolution creates memory pressure spikes for large schema definition dictionaries?

**Impact:** Temporary memory exhaustion, GC pauses, potential OOM on memory-constrained systems

---

### Model Construction & Metaclass
**Files:** `pydantic/_internal/_model_construction.py`
**Risks:** 10 (2C / 4H / 4M / 0L)

#### 🔴 CRITICAL (85%) — MRO Diamond Problem with Field Inheritance

> What if multiple inheritance creates diamond patterns where the same field is defined differently in different base classes, causing unpredictable field resolution?

**Impact:** Silent data corruption as wrong field validators/types get applied, breaking business logic with no obvious error

#### 🔴 CRITICAL (80%) — Metaclass Recursion During Schema Generation

> What if circular model references during `GenerateSchema` creation cause infinite recursion in the metaclass `__new__` method?

**Impact:** Stack overflow crash during import time, making the entire application unloadable

#### 🟠 HIGH (90%) — Annotation Evaluation Timing with Forward References

> What if `eval_type_backport` tries to resolve forward references before all classes in the module are fully defined, causing NameError during metaclass creation?

**Impact:** Import-time crashes in complex model hierarchies, breaking application startup

#### 🟠 HIGH (85%) — Descriptor Protocol Collision with User Attributes

> What if user-defined `__set__`/`__get__` methods on a model class interfere with Pydantic's `PydanticDescriptorProxy`, causing attribute access to bypass validation?

**Impact:** Validation bypassed silently, allowing invalid data into the system

#### 🟠 HIGH (80%) — Schema Cache Poisoning Across Model Variants

> What if the `@cache` decorator on schema generation doesn't account for different generic type parameters, causing one generic model variant to use another's cached schema?

**Impact:** Wrong validation rules applied to data, type safety violated

#### 🟠 HIGH (75%) — Memory Leak via Weakref Circular References

> What if the `weakref` usage in decorator collection creates circular references between model classes and their metadata that aren't properly garbage collected?

**Impact:** Memory leak in long-running applications that dynamically create many model classes

#### 🟡 MEDIUM (85%) — Generic Parameter Resolution with Complex Inheritance

> What if `get_model_typevars_map` fails to correctly resolve type variables when a model inherits from multiple generic bases with conflicting type parameter names?

**Impact:** Wrong types inferred for fields, runtime type errors in production

#### 🟡 MEDIUM (80%) — Private Attribute Namespace Collision

> What if `__private_attributes__` from different base classes contain keys with the same name but different `ModelPrivateAttr` configurations?

**Impact:** Private attribute behavior becomes unpredictable, breaking encapsulation assumptions

#### 🟡 MEDIUM (75%) — Stack Overflow from Nested Decorator Wrapping

> What if `replace_wrapped_methods=True` in `DecoratorInfos.build` creates deeply nested wrapper functions that exceed Python's recursion limit during method calls?

**Impact:** Runtime crashes when calling heavily decorated methods

#### 🟡 MEDIUM (70%) — Import-Time Side Effects in Dynamic Creation

> What if `_create_model_module` parameter causes the metaclass to execute in the wrong module context, making relative imports and `__name__` references resolve incorrectly?

**Impact:** Model creation fails in dynamic scenarios like testing or code generation

---

### Discriminated Unions
**Files:** `pydantic/_internal/_discriminated_union.py`
**Risks:** 8 (1C / 3H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Discriminator Value Collision with Type Coercion

> What if two union members have discriminator literals that are equal after type coercion but different in source ("1" vs 1, True vs "true")?

**Impact:** Silent data corruption where wrong union branch is selected, leading to incorrect field mapping and potentially security bypasses if permissions differ between branches

#### 🟠 HIGH (90%) — Recursive Union Reference Deadlock

> What if nested discriminated unions create circular references where Union A contains Union B which references back to Union A through the definitions dict?

**Impact:** Infinite recursion during schema application, stack overflow crash, service unavailable

#### 🟠 HIGH (80%) — Alias Inconsistency with Partial Schema Loading

> What if some union members have discriminator aliases loaded from definitions while others are inline, and the alias check happens before all definitions are resolved?

**Impact:** PydanticUserError thrown incorrectly claiming "discriminator fields have different aliases" when they're actually consistent, breaking valid schemas

#### 🟠 HIGH (75%) — Memory Exhaustion from Discriminator Value Explosion

> What if a union contains hundreds of members each with multiple literal discriminator values, creating an exponential explosion in `_tagged_union_choices` dict?

**Impact:** Memory exhaustion during schema construction, OOM crash affecting entire service

#### 🟡 MEDIUM (85%) — None Handling with Nested Nullable Wrapper

> What if the input schema has multiple nested nullable wrappers around the union, and `_is_nullable` logic incorrectly tracks state across recursive calls?

**Impact:** Double-wrapped nullable schemas or missing nullable wrapper, causing validation to reject valid None values or accept None where it shouldn't

#### 🟡 MEDIUM (80%) — Discriminator Field Name vs Python Attribute Mismatch

> What if the discriminator string refers to a field's python name but the actual schema uses the field's alias exclusively, with no mapping between them?

**Impact:** PydanticUserError claiming "model doesn't have discriminator field" for valid models, breaking working schemas during upgrade

#### 🟡 MEDIUM (75%) — Race Condition in Shared Definitions Dict

> What if multiple threads apply discriminators simultaneously using the same definitions dict reference, and one thread modifies it during another's schema traversal?

**Impact:** KeyError or corrupted schema references, intermittent validation failures under concurrent load

#### 🟡 MEDIUM (70%) — Stack State Corruption with Nested Union Processing

> What if `_choices_to_handle` stack gets corrupted when a nested union adds choices while the outer union is still being processed, especially if an exception occurs mid-processing?

**Impact:** Incomplete tagged union choices, missing valid union branches, some data patterns become unvalidatable

---

### Configuration System
**Files:** `pydantic/config.py`, `pydantic/_internal/_config.py`
**Risks:** 10 (2C / 4H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Config Inheritance Override Corruption

> What if child model config overrides parent config in unexpected ways, causing silent validation bypass?

**Impact:** Security vulnerabilities when child models accidentally inherit `extra='allow'` from parent but developer expects `extra='forbid'`. Sensitive data leaks through unvalidated extra fields.

#### 🔴 CRITICAL (80%) — String Transformation Memory Exhaustion

> What if `str_to_lower`/`str_to_upper` is applied to extremely large strings during validation, causing memory exhaustion?

**Impact:** DoS attack vector through crafted payloads. Single request with massive string field can crash application when string transformations create multiple copies in memory.

#### 🟠 HIGH (90%) — Config Propagation Race Condition

> What if model config is modified after model creation but before validation in multi-threaded environment?

**Impact:** Inconsistent validation behavior across concurrent requests. Critical validation rules (like `extra='forbid'`) might not apply, leading to data corruption or security bypass.

#### 🟠 HIGH (85%) — Computed Field Config Inheritance Mismatch

> What if computed field configuration doesn't propagate correctly through model inheritance, causing computed fields to be evaluated with wrong context?

**Impact:** Business logic errors where computed fields use parent model's config instead of child's. Financial calculations or access control computed fields could return incorrect results.

#### 🟠 HIGH (80%) — ValidationError Information Disclosure

> What if validation error messages with detailed config info leak internal model structure and field names to external APIs?

**Impact:** Reconnaissance attack enablement. Error messages containing field names, validation rules, and internal model structure help attackers understand system internals.

#### 🟠 HIGH (75%) — Config Override Persistence Bug

> What if runtime config overrides (like `Model.model_validate(data, extra="forbid")`) persist beyond single validation call due to shared config objects?

**Impact:** Validation rules "stick" across different validation contexts. Model that should normally allow extra fields starts rejecting them globally after single strict validation.

#### 🟡 MEDIUM (85%) — String Transform Encoding Corruption

> What if `str_to_lower`/`str_to_upper` breaks unicode normalization for non-ASCII characters, corrupting international data?

**Impact:** Data corruption for international users. Turkish dotted/dotless i conversion, German ß handling, etc. could break user authentication or data integrity.

#### 🟡 MEDIUM (80%) — Feature Flag Config Deployment Gap

> What if new validation mode (`strict`/`lax`) is deployed but dependent services still expect old validation behavior?

**Impact:** Integration failures when upstream services send data that new strict validation rejects but was previously accepted. Service communication breakdown.

#### 🟡 MEDIUM (75%) — Config Dict Type Coercion Surprise

> What if ConfigDict fields are silently coerced to wrong types during inheritance (bool becomes string, etc.)?

**Impact:** Subtle validation behavior changes. `frozen: bool` becomes `frozen: "true"` string, disabling immutability without obvious failure.

#### 🟡 MEDIUM (75%) — Circular Config Reference Infinite Loop

> What if model hierarchy creates circular reference in config inheritance, causing infinite recursion during schema generation?

**Impact:** Application startup failure or validation hanging indefinitely. Stack overflow crashes during model initialization in complex inheritance hierarchies.

---

### TypeAdapter & Dataclasses
**Files:** `pydantic/type_adapter.py`, `pydantic/dataclasses.py`
**Risks:** 10 (2C / 3H / 4M / 1L)

#### 🔴 CRITICAL (85%) — Forward Reference Resolution Poisoning

> What if a TypeAdapter is instantiated with forward references in one module, but symbols with the same names exist in the instantiation context with different types?

**Impact:** Silent type validation bypass - data validated against wrong schema, potentially allowing malicious payloads through validation that should fail

#### 🔴 CRITICAL (80%) — Parent Frame Access Race Condition

> What if `_fetch_parent_frame()` is called concurrently across threads and frame references become invalid or mixed between instances?

**Impact:** Schema built with wrong namespace context, leading to validation against incorrect types or complete validation failure

#### 🟠 HIGH (90%) — Cached Schema Staleness

> What if a TypeAdapter instance is cached/reused but the underlying type definition changes (dataclass fields modified, BaseModel updated) between uses?

**Impact:** Validation against outdated schema allows invalid data through or rejects valid data, causing data integrity issues

#### 🟠 HIGH (85%) — Memory Exhaustion via Schema Caching

> What if deeply recursive or highly complex types cause the core schema generation to create enormous cached structures that aren't garbage collected?

**Impact:** Memory exhaustion leading to OOM crashes, especially problematic since TypeAdapter instances may be long-lived

#### 🟠 HIGH (75%) — Module Name Injection

> What if the `module` parameter is set to a malicious module name that affects plugin behavior or schema resolution in unexpected ways?

**Impact:** Plugin system could load unintended behavior or resolve types from wrong contexts, potentially bypassing security validations

#### 🟡 MEDIUM (90%) — Function Type Special Handling Bypass

> What if a callable object (not `types.FunctionType`) is passed that looks like a function but doesn't trigger the special namespace handling for functions?

**Impact:** Forward references in pseudo-function types resolve incorrectly, causing validation to use wrong schema

#### 🟡 MEDIUM (80%) — Parent Depth Miscalculation

> What if `_parent_depth` is set incorrectly and the frame resolution grabs globals/locals from an unexpected scope with name collisions?

**Impact:** Type resolution uses wrong symbols, causing subtle validation bugs that are hard to debug

#### 🟡 MEDIUM (75%) — Config Override Detection Race

> What if `_type_has_config()` check passes but the type gains config between the check and schema generation?

**Impact:** Config parameter silently ignored when user expects it to be applied, leading to unexpected validation behavior

#### 🟡 MEDIUM (75%) — Pydantic Complete Flag Inconsistency

> What if `pydantic_complete` flag is set to True but schema building actually failed partially, leaving corrupted validator/serializer state?

**Impact:** Downstream code assumes TypeAdapter is fully functional when it's not, causing runtime failures during validation/serialization

#### 🟢 LOW (85%) — Frame Reference Memory Leak

> What if parent frame references are held longer than needed and prevent garbage collection of large objects in the frame's local scope?

**Impact:** Memory usage gradually increases over time in long-running applications that create many TypeAdapters

---

## Methodology

This critique was generated by [Gremlin](https://pypi.org/project/gremlin-critic/) v0.2.0 using:
- **93 curated QA patterns** across 12 domains
- **Claude Sonnet** for risk reasoning with code context
- **Deep analysis** mode with 70% confidence threshold
- Source code from each feature area passed as context