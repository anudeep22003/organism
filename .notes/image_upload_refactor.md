# Image Upload Refactor — Design Discussion

## Before vs After — at a glance

### Before (current)

```
HTTP Handler
    │
    │  UploadFile
    ▼
CharacterService.upload_reference_image
    │
    │  builds UploadReferenceImageDTO(
    │      FileToUploadDTO(file, filename),
    │      ProjectUserCharacterDTO(user_id, project_id, story_id, character_id)
    │  )
    ▼
ImageUploadService.upload_image(dto)
    │
    ├─► _get_authorized_character(dto.project_user_character)
    ├─► _create_in_processing_edit_event(dto.project_user_character)
    ├─► _create_image_variants(dto.file_to_upload.file)
    │       └─► returns dict[ImageVariant, PIL.Image]
    │
    ├─► _pack_variants_to_upload_ready_dto(variants, dto.project_user_character)
    │       └─► returns dict[ImageVariant, ReadyToUploadImageDTO]
    │                   ← carries project_user_character (wrong)
    │
    ├─► _upload_image_variants_to_bucket(prefix, ready_variants)
    │       └─► returns dict[ImageVariant, CompletedUploadImageDTO]
    │                   ← inherits ReadyToUploadImageDTO (wrong)
    │
    └─► _add_image_to_db(completed, dto.project_user_character, dto.file_to_upload.filename)
            │   ← filename dragged all the way down here
            └─► repo.create_image_entry_in_db(12 args...)
                    └─► Image(...), db.add()   ← model built in wrong layer
```

### After (target)

```
HTTP Handler
    │
    │  UploadFile, flat path params
    ▼
CharacterService.upload_reference_image(user_id, project_id, story_id, character_id, file, filename)
    │
    │  direct call, no DTO wrapper
    ▼
ImageUploadService.upload_reference_image(user_id, project_id, story_id, character_id, file, filename)
    │
    ├─► repo.get_character(...)           — auth check
    ├─► repo.create_edit_event(...)       — mark in-progress
    │
    ├─► ImageProcessor.process(file)
    │       └─► returns list[ProcessedImage(variant, width, height, size_bytes, bytes, format)]
    │                   ← pure, no I/O, no ownership context
    │
    ├─► for each ProcessedImage:
    │       GCSImageStorage.upload(key, processed)
    │           └─► returns object_key: str
    │
    │       Image(                        — assembled HERE, all context is local
    │           project_id, user_id, character_id,
    │           filename, image_type,
    │           width, height, format, size_bytes,   ← from ProcessedImage
    │           object_key, bucket,                  ← from storage
    │           variant,                             ← from ProcessedImage
    │       )
    │       repo.create_image(image)      — one-liner, just db.add
    │
    └─► repo.update_edit_event(SUCCEEDED) — or FAILED in except block
```

---

## What you diagnosed correctly

1. **Variants were premature.** You have one upload endpoint for one use case (character reference). No consumer today queries by variant. The `Image` model having a `variant` column is fine as a schema affordance — a single column costs nothing. But building the entire upload pipeline around variant iteration before you have a second caller is over-engineering.
2. **Too many DTO types for one flow.** Right now you have:
  - `ProjectUserCharacterDTO` (dto_types.py)
  - `FileToUploadDTO` (dto_types.py)
  - `UploadReferenceImageDTO` (dto_types.py — wrapper of the two above)
  - `ReadyToUploadImageDTO` (image_upload.py — internal)
  - `CompletedUploadImageDTO(ReadyToUploadImageDTO)` (image_upload.py — internal)
  - Two type aliases (`ImageVariantsReadyForUploadDTO`, `CompletedUploadImageReadyToAddToDBDTO`)
   That is **7 types** to move bytes from an HTTP handler into GCS and record one row per variant in Postgres. The cognitive overhead is disproportionate to the complexity of the task.
3. `**ReadyToUploadImageDTO` carries `project_user_character` for no reason.** The image dimensions and bytes have nothing to do with who owns the upload. This is the "reaching around" you felt — a context blob being dragged through a pure image-processing chain.
4. `**CompletedUploadImageDTO` inherits from `ReadyToUploadImageDTO`** but only adds `object_key`, `variant`, and `bucket`. Inheritance is the wrong tool here; it just means `CompletedUploadImageDTO` carries `project_user_character` too, deepening the coupling.
5. **The naming reads like process steps, not domain concepts.** `ReadyToUploadImageDTO`, `CompletedUploadImageReadyToAddToDBDTO` — these are implementation diary entries, not types with semantic meaning.

---

## The root structural problem

`ImageUploadService` is doing three jobs:

1. **Image processing** — resize, thumbnail, JPEG encode
2. **Storage I/O** — upload to GCS bucket
3. **Domain orchestration** — auth check, edit event lifecycle, DB writes

These are different rates of change and different test surfaces. The GCS interaction, for example, should be injectable (for testing), not a module-level client baked into the service.

---

## What the right shape looks like

### Two classes, not one

```
ImageProcessor          — pure functions, no I/O, no DB
  process(file) -> list[ProcessedImage]

GCSImageStorage         — thin wrapper around bucket, injectable
  upload(key, data) -> str  (returns object_key)

ImageUploadService      — orchestrator, owns DB + edit event
  upload_reference_image(user_id, project_id, story_id, character_id, file, filename)
```

`ProcessedImage` is a small dataclass: `(variant, width, height, size_bytes, bytes, format)`. No ownership context. No inheritance.

### Flatten `CharacterService.upload_reference_image`

The current split exists because `UploadReferenceImageDTO` was invented to bridge the two. If `ImageUploadService.upload_reference_image` takes flat args (same signature as `CharacterService.upload_reference_image`), the indirection disappears. `CharacterService` calls it directly. No DTO wrapper needed at that boundary.

### On variants

Keep the `ImageVariant` enum and the `variant` column. They are correct conceptually and cost nothing at rest. Drop the loop-over-variants orchestration machinery — inline the three variant calls in `ImageProcessor.process()`, return a plain list. When you add a fourth variant later, you add one line, not a new DTO.

### Repository speaks in objects, not field lists

`ImageRepository.create_image_entry_in_db` takes 12 args and does nothing but call `Image(...)` and `db.add`. That's the model constructor wearing a method as a disguise. The correct interface is:

```python
async def create_image(self, image: Image) -> Image:
    self.db.add(image)
    return image
```

The orchestrator (`ImageUploadService`) constructs the `Image` object — it has all the context: `project_id`, `user_id`, `character_id`, `filename`, `image_type`, the `ProcessedImage` fields, and the `object_key` returned from storage. That assembly step currently doesn't exist as an explicit step anywhere; it's smeared across a 12-arg call chain. Making it explicit in the orchestrator collapses both the repository signature and the reaching-around for `filename`.

The rule: **a repository method that looks like a model constructor is a sign that object construction responsibility leaked into the persistence layer.** Push it back to the service, where all the context lives.

### On the edit event

The `edit_event` pattern in `image_upload.py` is weaker than what you did in `refine_character`. There you wrapped the external call in try/except and marked FAILED on exception. The upload service only marks SUCCEEDED, never FAILED. Fix that in the rewrite; the pattern is already established.

---

## Type count after refactor


| Before                                | After                                   |
| ------------------------------------- | --------------------------------------- |
| ProjectUserCharacterDTO               | gone — flat args                        |
| FileToUploadDTO                       | gone — flat args                        |
| UploadReferenceImageDTO               | gone — flat args                        |
| ReadyToUploadImageDTO                 | `ProcessedImage` (no ownership ctx)     |
| CompletedUploadImageDTO               | gone — object_key returned from storage |
| ImageVariantsReadyForUploadDTO        | gone                                    |
| CompletedUploadImageReadyToAddToDBDTO | gone                                    |


7 → 1.

---

## The startup-speed principle that applies here

> Don't model your pipeline stages as types. Model your domain concepts as types.

Pipeline stage types (`ReadyToUpload`, `CompletedUpload`) accrete because each function in a linear chain wants to return *something*. The signal that you've over-typed a pipeline is when the types look like renamed versions of each other with one extra field bolted on. That's just a function return value dressed up as a type.

Domain concept types (`ProcessedImage`, `Character`, `EditEvent`) survive refactors because they reflect what the system *is*, not how one particular implementation happens to pass data around.

---

## Questions before writing code

1. Will you ever need to upload non-character images (scene backgrounds, user avatars)? If yes in the near term, `GCSImageStorage` should be generic and `ImageUploadService` stays character-scoped. If no, keep it all in one service.
2. Do you need the thumb and preview variants served today, or is original sufficient for the current frontend? If only original is used, drop thumb/preview from the first pass and add them when a consumer exists.
3. The `_executor` ThreadPoolExecutor is defined at module level but never used — PIL's `thumbnail` is called synchronously. Intentional future placeholder or dead code?

